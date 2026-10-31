from datetime import datetime,timezone,timedelta
from math import isfinite
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import ProviderError,geocode_location,analyze_trip
from .weather import WeatherUnavailable, assess_routes
def health(request):
    # Health checks must remain JSON and available regardless of Accept headers.
    # DRF's JSON-only renderer otherwise returns 406 for Accept: text/html.
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return JsonResponse({'status': 'ok', 'service': 'routeguard-api'})
@api_view(['GET'])
def geocode(request):
 try:return Response(geocode_location(request.query_params.get('q','')))
 except ValueError as exc:return Response({'error':str(exc)},status=400)
 except ProviderError as exc:return Response({'error':str(exc)},status=503)
@api_view(['POST'])
def analyze(request):
 d=request.data
 try:
  origin=d.get('origin','');destination=d.get('destination','')
  if not isinstance(origin,str) or not isinstance(destination,str):raise ValueError('Locations must be text.')
  raw=d.get('departure_at','')
  if not isinstance(raw,str):raise ValueError('Invalid departure time.')
  departure=datetime.fromisoformat(raw.replace('Z','+00:00'))
  if departure.tzinfo is None or departure.utcoffset() is None:raise ValueError('Departure must include a timezone offset.')
  if departure.astimezone(timezone.utc)<datetime.now(timezone.utc):raise ValueError('Departure cannot be in the past.')
  weight=float(d.get('load_weight_lb',0))
  if not isfinite(weight) or not 0<=weight<=200000:raise ValueError('Load weight must be 0–200,000 lb.')
  interval=int(d.get('checkpoint_interval_miles',25))
  if interval not in (10,25,50):raise ValueError('Checkpoint spacing must be 10, 25 or 50 miles.')
  result = analyze_trip(origin,destination,departure,weight,interval)
  # Routing must remain usable when a forecast provider is offline or out of range.
  try:
   if departure.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(hours=72):
    raise WeatherUnavailable('Departure is outside the supported 72-hour forecast window.')
   # Reuse returned geometry and route metadata; avoid another OSRM request.
   raw_routes = [{'geometry': r['geometry'], 'distance': r['distance_miles']*1609.344,
                  'duration': r['duration_seconds']} for r in result['routes']]
   assessments = assess_routes(raw_routes, departure, weight, interval)
   for route, assessment in zip(result['routes'], assessments):
    route.update({k:v for k,v in assessment.items() if k!='rank'})
   eligible = [(i,a) for i,a in enumerate(assessments) if a['rank'] is not None and a['no_travel_miles'] == 0]
   if eligible:
    best_index = min(eligible, key=lambda x:x[1]['rank'])[0]
    result['routes'][best_index]['recommended'] = True
    result['recommendation'] = result['routes'][best_index]['id']
    result['weather_analyzed'] = True
    result['warnings'] = [w for w in result['warnings'] if not w.startswith('Weather-aware')]
   else:
    result['warnings'].append('No eligible route has complete forecast coverage without No Travel conditions. Review all routes before departure.')
  except WeatherUnavailable as exc:
   result['warnings'].append(str(exc))
  result['warnings'] = [w for w in result['warnings'] if w != 'Weather-aware safety analysis is not yet available in M1.']
  if not result['weather_analyzed']:
   result['warnings'].append('Weather recommendation unavailable; no route is certified safe.')
  return Response(result)
 except (ValueError,TypeError,OverflowError) as exc:return Response({'error':str(exc)},status=400)
 except ProviderError as exc:return Response({'error':str(exc)},status=503)
