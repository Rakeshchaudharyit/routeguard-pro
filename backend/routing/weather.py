"""Arrival-time weather corridor assessment. Open-Meteo hourly forecasts.

Wind uses 10 m gusts (conservative proxy); precipitation/snowfall hourly totals
are converted to per-hour intensity. These are model forecasts, not guarantees.
"""
from datetime import datetime, timezone, timedelta
from math import asin, cos, radians, sin, sqrt, isfinite
import requests
from risk.engine import classify_weather, route_rank

MILE_METERS = 1609.344
LEVELS = ['low', 'moderate', 'high', 'severe', 'no_travel']
TIMELINE_HOURS = list(range(0, 49, 6))

class WeatherUnavailable(Exception):
    pass

def distance_m(a, b):
    lat1, lon1 = radians(a[1]), radians(a[0])
    lat2, lon2 = radians(b[1]), radians(b[0])
    dlat, dlon = lat2-lat1, lon2-lon1
    return 12742000 * asin(min(1, sqrt(sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2)))

def sample_route(route, interval_miles, departure):
    coords = route['geometry']['coordinates']
    if len(coords) < 2: return []
    lengths = [distance_m(a, b) for a, b in zip(coords, coords[1:])]
    total = sum(lengths)
    if total <= 0: return []
    # OSRM route distance is authoritative for mileage; geometry cumulative
    # distance is used only to interpolate positions.
    road_miles = float(route['distance']) / MILE_METERS
    targets = [0.0]
    n = 1
    while n * interval_miles < road_miles:
        targets.append(float(n * interval_miles)); n += 1
    targets.append(road_miles)
    points = []
    segment, walked = 0, 0.0
    for mile in targets:
        target = total * mile / road_miles
        while segment < len(lengths)-1 and walked + lengths[segment] < target:
            walked += lengths[segment]; segment += 1
        frac = min(1.0, max(0.0, (target-walked)/lengths[segment])) if lengths[segment] else 0
        a, b = coords[segment], coords[segment+1]
        lat = a[1] + frac*(b[1]-a[1]); lon = a[0] + frac*(b[0]-a[0])
        eta = departure + timedelta(seconds=float(route['duration'])*mile/road_miles)
        points.append({'mile': round(mile, 2), 'lat': round(lat, 5), 'lon': round(lon, 5), 'eta': eta.isoformat()})
    return points

def fetch_forecasts(points):
    """Batch points to avoid one HTTP request per checkpoint."""
    forecasts = []
    for start in range(0, len(points), 20):
        batch = points[start:start+20]
        params = {
            'latitude': ','.join(str(p['lat']) for p in batch),
            'longitude': ','.join(str(p['lon']) for p in batch),
            'hourly': 'wind_gusts_10m,precipitation,snowfall',
            'wind_speed_unit': 'mph', 'precipitation_unit': 'inch',
            'timezone': 'GMT', 'forecast_days': 4,
        }
        try:
            response = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=25)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WeatherUnavailable('Weather provider is unavailable. Routes are shown without safety scoring.') from exc
        items = payload if isinstance(payload, list) else [payload]
        if len(items) != len(batch) or any(not isinstance(item, dict) or not isinstance(item.get('hourly'), dict) for item in items):
            raise WeatherUnavailable('Weather provider returned incomplete forecast data.')
        forecasts.extend(items)
    return forecasts

def nearest_hourly(forecast, eta):
    hourly = forecast['hourly']
    times = hourly.get('time', [])
    if not times: return None
    target = eta.astimezone(timezone.utc)
    # Open-Meteo is requested in GMT. Ignore malformed timestamps rather than
    # letting one bad provider value break the entire route assessment.
    valid_times = []
    for i, raw in enumerate(times):
        try:
            timestamp = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            valid_times.append((i, timestamp.astimezone(timezone.utc)))
        except (ValueError, TypeError, AttributeError):
            continue
    if not valid_times:
        return None
    index, timestamp = min(valid_times, key=lambda pair: abs((pair[1]-target).total_seconds()))
    if abs((timestamp-target).total_seconds()) > 3600:
        return None
    try:
        values = [float(hourly[k][index]) for k in ('wind_gusts_10m', 'precipitation', 'snowfall')]
        if not all(isfinite(v) and v >= 0 for v in values):
            return None
        return values[0], values[1], values[2] / 2.54  # cm/hour -> in/hour
    except (KeyError, IndexError, TypeError, ValueError):
        return None

def forecast_at_hour(forecast, target):
    """Return a forecast only when its valid timestamp is within one hour."""
    return nearest_hourly(forecast, target)

def timeline_at_point(forecast, now, weight):
    """Actual provider forecasts sampled at 0,6,...48 hours from the request."""
    values = []
    for offset in TIMELINE_HOURS:
        timestamp = now + timedelta(hours=offset)
        metrics = forecast_at_hour(forecast, timestamp)
        if metrics is None:
            values.append({'hour': offset, 'risk': 'unavailable', 'wind_mph': None,
                           'rain_in_hr': None, 'snow_in_hr': None})
        else:
            wind, rain, snow = metrics
            values.append({'hour': offset, 'risk': LEVELS[classify_weather(wind, rain, snow, weight)],
                           'wind_mph': round(wind, 1), 'rain_in_hr': round(rain, 3),
                           'snow_in_hr': round(snow, 3)})
    return values

def assess_routes(routes, departure, weight, interval):
    all_points = [sample_route(r, interval, departure) for r in routes]
    flattened = [p for group in all_points for p in group]
    if not flattened: raise WeatherUnavailable('Routing geometry does not support weather checkpoints.')
    forecasts = fetch_forecasts(flattened)
    if len(forecasts) != len(flattened):
        raise WeatherUnavailable('Weather provider returned an unexpected number of forecasts.')
    cursor = 0
    output = []
    timeline_base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for route, points in zip(routes, all_points):
        route_forecasts = forecasts[cursor:cursor+len(points)]; cursor += len(points)
        checkpoints = []
        for p, forecast in zip(points, route_forecasts):
            eta = datetime.fromisoformat(p['eta'])
            metrics = nearest_hourly(forecast, eta)
            checkpoint = dict(p)
            checkpoint['timeline'] = timeline_at_point(forecast, timeline_base, weight)
            if metrics is None:
                checkpoint.update({'risk': 'unavailable', 'wind_mph': None, 'rain_in_hr': None, 'snow_in_hr': None, 'reason': 'Forecast missing for arrival time'})
            else:
                wind, rain, snow = metrics
                risk = classify_weather(wind, rain, snow, weight)
                checkpoint.update({'risk': LEVELS[risk], 'wind_mph': round(wind, 1), 'rain_in_hr': round(rain, 3), 'snow_in_hr': round(snow, 3), 'reason': ('Load-weight wind override' if (45 <= wind < 55 and weight > 30000) or (35 <= wind < 45 and weight > 40000) else 'Weather threshold')})
            checkpoints.append(checkpoint)
        # Assign each segment the more conservative risk of its two endpoints.
        miles = {'high': 0.0, 'severe': 0.0, 'no_travel': 0.0}
        weighted, total, incomplete = 0.0, 0.0, False
        for a, b in zip(checkpoints, checkpoints[1:]):
            length = b['mile']-a['mile']
            if a['risk']=='unavailable' or b['risk']=='unavailable':
                incomplete = True; continue
            level = max(LEVELS.index(a['risk']), LEVELS.index(b['risk']))
            key = LEVELS[level]
            if key in miles: miles[key] += length
            weighted += level*length; total += length
        # Do not rank incomplete forecasts as safe.
        if incomplete or not total:
            status, score = 'incomplete', None
        else:
            status, score = 'analyzed', weighted/total
        output.append({'checkpoints': checkpoints, 'weather_status': status,
                       'risk_level': max((p['risk'] for p in checkpoints if p['risk']!='unavailable'), key=lambda x: LEVELS.index(x), default=None),
                       'high_miles': round(miles['high'], 1), 'severe_miles': round(miles['severe'], 1),
                       'no_travel_miles': round(miles['no_travel'], 1), 'average_risk': round(score, 3) if score is not None else None,
                       'rank': route_rank(miles['severe'], miles['high'], score or 0, route['duration']/60, miles['no_travel']) if score is not None else None,
                       'forecast_coverage': {'analyzed': sum(p['risk']!='unavailable' for p in checkpoints), 'total': len(checkpoints),
                                             'status': 'complete' if all(p['risk']!='unavailable' for p in checkpoints) else ('partial' if any(p['risk']!='unavailable' for p in checkpoints) else 'unavailable')},
                       'timeline_base': timeline_base.isoformat(),
                       'unknown_miles': round(sum(b['mile']-a['mile'] for a,b in zip(checkpoints, checkpoints[1:]) if a['risk']=='unavailable' or b['risk']=='unavailable'), 1)})
    return output
