"""DRF serializers.

* ``TripInputSerializer`` validates the POST body (mirrors the client's zod
  schema in ``create-trip.ts``) via explicit ``validate_*`` methods.
* ``TripOutputSerializer`` renders the stored trip in the exact snake_case
  shape the client's ``Trip`` type expects — input fields + id/created_at with
  the computed ``result`` dict flattened to the top level.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import Trip


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    # Float (not Decimal) so it feeds the pure-Python engine's float math.
    current_cycle_used_hours = serializers.FloatField()
    start_datetime = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    def _non_empty(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Required")
        return value.strip()

    def validate_current_location(self, value):
        return self._non_empty(value)

    def validate_pickup_location(self, value):
        return self._non_empty(value)

    def validate_dropoff_location(self, value):
        return self._non_empty(value)

    def validate_current_cycle_used_hours(self, value):
        if value < 0:
            raise serializers.ValidationError("Must be 0 or more")
        if value > 70:
            raise serializers.ValidationError("Cannot exceed 70")
        return value


class TripOutputSerializer(serializers.Serializer):
    """Read-only. Flattens ``result`` so the wire shape == the frontend ``Trip``."""

    def to_representation(self, trip: Trip) -> dict:
        return {
            "id": str(trip.id),
            "created_at": trip.created_at.isoformat(),
            "current_location": trip.current_location,
            "pickup_location": trip.pickup_location,
            "dropoff_location": trip.dropoff_location,
            "current_cycle_used_hours": float(trip.current_cycle_used_hours),
            # start_datetime, timezone, summary, route, segments, daily_logs.
            **trip.result,
        }
