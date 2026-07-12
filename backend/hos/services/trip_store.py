"""Write-side service for trips.

Keeps ``trip_service.plan()`` pure (no Django) and owns the persistence step so
views stay thin. Per the assessment spec, the plan + insert run inside a single
``transaction.atomic`` block.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils.dateparse import parse_datetime

from hos.models import Trip

from . import trip_service

logger = logging.getLogger(__name__)


def create_trip(
    *,
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    current_cycle_used_hours: float,
    start_datetime: str | None = None,
) -> Trip:
    """Plan a trip and persist it. Raises ``routing.GeocodingError`` on bad input."""
    with transaction.atomic():
        plan = trip_service.plan(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            current_cycle_used_hours=current_cycle_used_hours,
            start_datetime=start_datetime,
        )
        trip = Trip.objects.create(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            current_cycle_used_hours=current_cycle_used_hours,
            # The engine's normalised start (carries the inferred local offset).
            start_datetime=parse_datetime(plan["start_datetime"]),
            result=plan,
        )

    logger.info(
        "Planned trip %s (%s -> %s -> %s, %d segments)",
        trip.id, current_location, pickup_location, dropoff_location,
        len(plan["segments"]),
    )
    return trip
