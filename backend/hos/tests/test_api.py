"""API tests — pytest + pytest-django + factory_boy.

Run (deps required — use Docker if pip is unavailable)::

    pytest hos/tests/test_api.py

Covers the three PLAN scenarios (short intra-day, long multi-day forcing
resets/fuel, high cycle-used forcing a restart), the GET round-trip + caching,
and input validation.
"""

from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from hos.models import Trip

from .factories import TripFactory

BASE_PAYLOAD = {
    "current_location": "Los Angeles, CA",
    "pickup_location": "Phoenix, AZ",
    "dropoff_location": "Dallas, TX",
    "current_cycle_used_hours": 10,
    "start_datetime": "2026-07-10T08:00:00",
}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _post(client, **overrides):
    payload = {**BASE_PAYLOAD, **overrides}
    return client.post("/api/trips/", payload, format="json")


def _assert_gapless(segments):
    for a, b in zip(segments, segments[1:]):
        assert a["end"] == b["start"]


@pytest.mark.django_db
def test_create_short_trip(client):
    resp = _post(client, pickup_location="Las Vegas, NV", dropoff_location="Phoenix, AZ")
    assert resp.status_code == 201, resp.data
    body = resp.data
    assert "id" in body
    assert body["segments"]
    _assert_gapless(body["segments"])
    assert Trip.objects.count() == 1


@pytest.mark.django_db
def test_create_long_multiday_trip(client):
    # LA → Denver → NYC forces resets and fuel stops.
    resp = _post(client, pickup_location="Denver, CO", dropoff_location="New York, NY")
    assert resp.status_code == 201, resp.data
    body = resp.data
    assert len(body["daily_logs"]) > 1
    assert body["summary"]["num_rest_periods"] >= 1
    assert body["summary"]["num_fuel_stops"] >= 1
    _assert_gapless(body["segments"])
    for log in body["daily_logs"]:
        assert sum(log["totals"].values()) <= 24.0 + 1e-3


@pytest.mark.django_db
def test_high_cycle_forces_restart(client):
    resp = _post(client, current_cycle_used_hours=68,
                 pickup_location="Denver, CO", dropoff_location="Chicago, IL")
    assert resp.status_code == 201, resp.data
    assert resp.data["summary"]["used_34h_restart"] is True


@pytest.mark.django_db
def test_get_trip_roundtrip_and_cache(client, django_assert_num_queries):
    created = _post(client).data
    trip_id = created["id"]

    # First read hits the DB once…
    with django_assert_num_queries(1):
        resp = client.get(f"/api/trips/{trip_id}/")
    assert resp.status_code == 200
    assert resp.data["id"] == trip_id

    # …second read is served from cache with zero queries.
    with django_assert_num_queries(0):
        cached = client.get(f"/api/trips/{trip_id}/")
    assert cached.status_code == 200
    assert cached.data["id"] == trip_id


@pytest.mark.django_db
def test_get_uses_factory_created_trip(client):
    trip = TripFactory()
    resp = client.get(f"/api/trips/{trip.id}/")
    assert resp.status_code == 200
    assert resp.data["current_location"] == trip.current_location


@pytest.mark.django_db
def test_get_missing_trip_404(client):
    resp = client.get("/api/trips/00000000-0000-0000-0000-000000000000/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_invalid_cycle_hours_rejected(client):
    resp = _post(client, current_cycle_used_hours=999)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unknown_location_400(client):
    resp = _post(client, current_location="Nowheresville, ZZ")
    assert resp.status_code == 400


def test_geocode_search_returns_matches(client):
    resp = client.get("/api/geocode?q=phoe")
    assert resp.status_code == 200
    assert any("Phoenix" in r["label"] for r in resp.data)
    assert all({"label", "lat", "lng"} <= set(r) for r in resp.data)


def test_geocode_search_short_query_empty(client):
    resp = client.get("/api/geocode?q=p")
    assert resp.status_code == 200
    assert resp.data == []
