"""Geocoding and routing adapters using Nominatim and OSRM."""

from datetime import timedelta

import requests


class ProviderError(Exception):
    """Raised when an external geocoding or routing provider fails."""


HEADERS = {
    "User-Agent": "RouteGuardPro/1.0 (route planning assessment)"
}


def geocode_location(query):
    """Resolve a location name into geographic coordinates."""

    if not isinstance(query, str) or not 3 <= len(query.strip()) <= 180:
        raise ValueError("Location must contain 3–180 characters.")

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
            },
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        matches = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise ProviderError("Geocoding service unavailable.") from exc

    if not matches:
        raise ValueError(f"Location not found: {query}")

    return {
        "label": matches[0]["display_name"],
        "lat": float(matches[0]["lat"]),
        "lon": float(matches[0]["lon"]),
    }


def fetch_routes(start, end):
    """Retrieve up to three alternative driving routes from OSRM."""

    coordinates = (
        f"{start['lon']},{start['lat']};"
        f"{end['lon']},{end['lat']}"
    )

    try:
        response = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
            params={
                "alternatives": "true",
                "overview": "full",
                "geometries": "geojson",
            },
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise ProviderError("Routing service unavailable.") from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ProviderError("No drivable routes found.")

    return data["routes"][:3]


def analyze_trip(origin, destination, departure, weight, interval):
    """Build a route analysis response from available driving routes."""

    start = geocode_location(origin)
    end = geocode_location(destination)

    routes = fetch_routes(start, end)
    items = []

    for index, route in enumerate(routes):
        duration_seconds = float(route["duration"])

        items.append(
            {
                "id": f"route-{index + 1}",
                "name": f"Route {chr(65 + index)}",
                "distance_miles": round(
                    route["distance"] / 1609.344, 1
                ),
                "duration_seconds": round(duration_seconds),
                "arrival_at": (
                    departure + timedelta(seconds=duration_seconds)
                ).isoformat(),
                "geometry": route["geometry"],
                "weather_status": "not_analyzed",
                "risk_level": None,
                "recommended": False,
            }
        )

    warnings = [
        (
            "OSRM driving routes are not truck-specific: "
            "weight, clearance and truck restrictions are not verified."
        )
    ]

    if len(items) < 3:
        warnings.append(
            f"Routing provider returned {len(items)} "
            "distinct route(s), not three."
        )

    return {
        "origin": start,
        "destination": end,
        "departure_at": departure.isoformat(),
        "load_weight_lb": weight,
        "checkpoint_interval_miles": interval,
        "routes": items,
        "weather_analyzed": False,
        "recommendation": None,
        "warnings": warnings,
    }