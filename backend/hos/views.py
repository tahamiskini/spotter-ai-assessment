"""API views (class-based; thin — validation in serializers, logic in services).

* ``TripCreateView``  — ``POST /api/trips/``      plan + persist + return.
* ``TripDetailView``  — ``GET  /api/trips/{id}/`` retrieve (cached).
* ``healthcheck``     — ``GET  /api/healthcheck`` liveness probe.
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Trip
from .serializers import TripInputSerializer, TripOutputSerializer
from .services import routing
from .services.routing import GeocodingError
from .services.trip_store import create_trip

logger = logging.getLogger(__name__)


@api_view(["GET"])
def healthcheck(request):
    return Response({"ok": True})


@api_view(["GET"])
def geocode_search(request):
    """Typeahead for the location fields: GET /api/geocode?q=phoe -> [{label,lat,lng}]."""
    query = request.query_params.get("q", "")
    try:
        results = routing.search(query)
    except requests.RequestException:  # pragma: no cover - network path
        logger.exception("Geocode provider error")
        return Response(
            {"detail": "Geocoding provider error."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response(
        [{"label": gp.label, "lat": gp.lat, "lng": gp.lng} for gp in results]
    )


class TripCreateView(generics.CreateAPIView):
    serializer_class = TripInputSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            trip = create_trip(
                current_location=data["current_location"],
                pickup_location=data["pickup_location"],
                dropoff_location=data["dropoff_location"],
                current_cycle_used_hours=data["current_cycle_used_hours"],
                start_datetime=data.get("start_datetime") or None,
            )
        except GeocodingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as exc:  # pragma: no cover - network path
            logger.exception("Routing provider error while planning trip")
            return Response(
                {"detail": f"Routing provider error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(TripOutputSerializer(trip).data, status=status.HTTP_201_CREATED)


class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripOutputSerializer
    lookup_url_kwarg = "trip_id"

    def retrieve(self, request, *args, **kwargs):
        # Trips are immutable once created — serve the serialized payload from
        # cache by id, falling back to a single DB read.
        cache_key = f"trip:{self.kwargs[self.lookup_url_kwarg]}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        trip = self.get_object()
        data = self.get_serializer(trip).data
        cache.set(cache_key, data, settings.TRIP_CACHE_TTL)
        return Response(data)
