"""Routing + geocoding.

Uses OpenRouteService (``driving-hgv`` truck profile) when ``ORS_API_KEY`` is
set, and falls back to a deterministic offline estimator (geocode via a small
built-in city table, distance via haversine, a straight-line "geometry") so the
whole app — and its tests — run without any network access or API key.

Only the standard library + ``requests`` are used; ``requests`` is optional and
imported lazily so the offline path has zero third-party dependencies.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from hos.engine.models import Leg

ORS_BASE = "https://api.openrouteservice.org"
METERS_PER_MILE = 1609.344
# Offline fallback assumes a steady interstate truck speed.
FALLBACK_SPEED_MPH = 55.0


class GeocodingError(ValueError):
    """Raised when a location string cannot be resolved to coordinates."""


@dataclass
class GeoPoint:
    label: str
    lat: float
    lng: float


@dataclass
class RoutedLeg:
    """A leg with its engine :class:`Leg` plus geometry for the map."""

    leg: Leg
    geometry: list[list[float]]  # [[lat, lng], ...]


# A small offline gazetteer — enough to demo common US routes without a network.
# lat, lng in degrees.
_CITY_TABLE: dict[str, tuple[float, float]] = {
    "los angeles": (34.0522, -118.2437),
    "phoenix": (33.4484, -112.0740),
    "dallas": (32.7767, -96.7970),
    "houston": (29.7604, -95.3698),
    "san antonio": (29.4241, -98.4936),
    "el paso": (31.7619, -106.4850),
    "albuquerque": (35.0844, -106.6504),
    "denver": (39.7392, -104.9903),
    "oklahoma city": (35.4676, -97.5164),
    "kansas city": (39.0997, -94.5786),
    "st louis": (38.6270, -90.1994),
    "chicago": (41.8781, -87.6298),
    "memphis": (35.1495, -90.0490),
    "nashville": (36.1627, -86.7816),
    "atlanta": (33.7490, -84.3880),
    "new york": (40.7128, -74.0060),
    "philadelphia": (39.9526, -75.1652),
    "columbus": (39.9612, -82.9988),
    "indianapolis": (39.7684, -86.1581),
    "las vegas": (36.1699, -115.1398),
    "salt lake city": (40.7608, -111.8910),
    "seattle": (47.6062, -122.3321),
    "portland": (45.5152, -122.6784),
    "san francisco": (37.7749, -122.4194),
    "miami": (25.7617, -80.1918),
    "jacksonville": (30.3322, -81.6557),
    "charlotte": (35.2271, -80.8431),
    "detroit": (42.3314, -83.0458),
    "minneapolis": (44.9778, -93.2650),
}


def _haversine_miles(a: GeoPoint, b: GeoPoint) -> float:
    r = 3958.7613  # Earth radius, miles
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _norm(label: str) -> str:
    # "Phoenix, AZ" / "Phoenix AZ" -> "phoenix"
    return label.split(",")[0].strip().lower()


def _use_ors() -> bool:
    return bool(os.environ.get("ORS_API_KEY"))


# --------------------------------------------------------------------------- #
# Geocoding
# --------------------------------------------------------------------------- #
def geocode(label: str) -> GeoPoint:
    """Resolve a free-text location to a :class:`GeoPoint`."""
    if _use_ors():
        return _geocode_ors(label)
    return _geocode_offline(label)


def _geocode_offline(label: str) -> GeoPoint:
    key = _norm(label)
    if key in _CITY_TABLE:
        lat, lng = _CITY_TABLE[key]
        return GeoPoint(label=label, lat=lat, lng=lng)
    # Partial match (e.g. "downtown los angeles").
    for city, (lat, lng) in _CITY_TABLE.items():
        if city in key or key in city:
            return GeoPoint(label=label, lat=lat, lng=lng)
    raise GeocodingError(
        f"Could not geocode '{label}'. Set ORS_API_KEY for arbitrary "
        f"addresses, or use a known US city (offline mode)."
    )


def _geocode_ors(label: str) -> GeoPoint:
    import requests

    resp = requests.get(
        f"{ORS_BASE}/geocode/search",
        params={
            "api_key": os.environ["ORS_API_KEY"],
            "text": label,
            "size": 1,
            "boundary.country": "US",
        },
        timeout=15,
    )
    resp.raise_for_status()
    features = resp.json().get("features") or []
    if not features:
        raise GeocodingError(f"Could not geocode '{label}'.")
    lng, lat = features[0]["geometry"]["coordinates"]
    return GeoPoint(label=label, lat=lat, lng=lng)


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #
def route_leg(origin: GeoPoint, dest: GeoPoint) -> RoutedLeg:
    """Route one leg, returning an engine :class:`Leg` + polyline geometry."""
    if _use_ors():
        return _route_leg_ors(origin, dest)
    return _route_leg_offline(origin, dest)


def _route_leg_offline(origin: GeoPoint, dest: GeoPoint) -> RoutedLeg:
    # Great-circle distance inflated ~18% to approximate real road distance.
    miles = _haversine_miles(origin, dest) * 1.18
    hours = miles / FALLBACK_SPEED_MPH if FALLBACK_SPEED_MPH else 0.0
    leg = Leg(
        from_label=origin.label,
        to_label=dest.label,
        distance_miles=round(miles, 1),
        duration_hours=round(hours, 3),
    )
    geometry = [[origin.lat, origin.lng], [dest.lat, dest.lng]]
    return RoutedLeg(leg=leg, geometry=geometry)


def search(query: str, limit: int = 5) -> list[GeoPoint]:
    """Autocomplete/typeahead: resolve a partial query to candidate places.

    Backs ``GET /api/geocode``. Uses ORS autocomplete when keyed, otherwise
    substring-matches the offline gazetteer.
    """
    query = (query or "").strip()
    if len(query) < 2:
        return []
    if _use_ors():
        return _search_ors(query, limit)
    return _search_offline(query, limit)


def _search_offline(query: str, limit: int) -> list[GeoPoint]:
    key = _norm(query)
    matches: list[GeoPoint] = []
    for city, (lat, lng) in _CITY_TABLE.items():
        if key in city:
            # Title-case the gazetteer key for a friendly label.
            matches.append(GeoPoint(label=city.title(), lat=lat, lng=lng))
    matches.sort(key=lambda gp: (not gp.label.lower().startswith(key), gp.label))
    return matches[:limit]


def _search_ors(query: str, limit: int) -> list[GeoPoint]:
    import requests

    resp = requests.get(
        f"{ORS_BASE}/geocode/autocomplete",
        params={
            "api_key": os.environ["ORS_API_KEY"],
            "text": query,
            "boundary.country": "US",
        },
        timeout=15,
    )
    resp.raise_for_status()
    features = resp.json().get("features") or []
    results: list[GeoPoint] = []
    for feat in features[:limit]:
        lng, lat = feat["geometry"]["coordinates"]
        label = feat["properties"].get("label") or feat["properties"].get("name", "")
        results.append(GeoPoint(label=label, lat=lat, lng=lng))
    return results


def _route_leg_ors(origin: GeoPoint, dest: GeoPoint) -> RoutedLeg:
    import requests

    resp = requests.post(
        f"{ORS_BASE}/v2/directions/driving-hgv/geojson",
        headers={"Authorization": os.environ["ORS_API_KEY"]},
        json={"coordinates": [[origin.lng, origin.lat], [dest.lng, dest.lat]]},
        timeout=30,
    )
    resp.raise_for_status()
    feature = resp.json()["features"][0]
    summary = feature["properties"]["summary"]
    miles = summary["distance"] / METERS_PER_MILE
    hours = summary["duration"] / 3600.0
    # GeoJSON coords are [lng, lat]; Leaflet wants [lat, lng].
    geometry = [[c[1], c[0]] for c in feature["geometry"]["coordinates"]]
    leg = Leg(
        from_label=origin.label,
        to_label=dest.label,
        distance_miles=round(miles, 1),
        duration_hours=round(hours, 3),
    )
    return RoutedLeg(leg=leg, geometry=geometry)
