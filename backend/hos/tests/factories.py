"""factory_boy factories for dynamic test data (per test-pytest-fixtures)."""

from __future__ import annotations

from decimal import Decimal

import factory

from hos.models import Trip


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    current_location = "Los Angeles, CA"
    pickup_location = "Phoenix, AZ"
    dropoff_location = "Dallas, TX"
    current_cycle_used_hours = Decimal("10.00")
    start_datetime = None  # computed start lives in result["start_datetime"]
    result = factory.LazyFunction(
        lambda: {
            "start_datetime": "2026-07-10T08:00:00-08:00",
            "timezone": "UTC-08:00",
            "summary": {},
            "route": {"geometry": [], "legs": [], "stops": []},
            "segments": [],
            "daily_logs": [],
        }
    )
