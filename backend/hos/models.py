"""Persistence for planned trips.

A ``Trip`` stores the driver's inputs plus the full computed plan from
``trip_service.plan()`` in a single ``result`` JSONField, so a trip is
retrievable by id for a shareable link without recomputing.
"""

from __future__ import annotations

import uuid

from django.db import models


class Trip(models.Model):
    # UUID PK — unguessable, no enumeration of the trip table via the URL.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Inputs
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used_hours = models.DecimalField(max_digits=4, decimal_places=2)
    start_datetime = models.DateTimeField(null=True, blank=True)

    # Full computed plan output (summary, route, segments, daily_logs, …).
    result = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Backs the default -created_at ordering / any future history list.
            models.Index(fields=["-created_at"], name="trip_created_at_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(current_cycle_used_hours__gte=0),
                name="trip_cycle_used_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return f"Trip {self.id} ({self.current_location} → {self.dropoff_location})"
