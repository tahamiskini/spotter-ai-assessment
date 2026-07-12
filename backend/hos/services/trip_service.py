"""Trip orchestration: geocode → route → plan → serialize.

Produces the exact snake_case payload the React client consumes (see
``frontend/src/types/api.ts``): ``summary``, ``route`` (geometry + legs +
stops), ``segments``, and ``daily_logs``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from hos.engine.dailylog import group_by_day
from hos.engine.models import DutyStatus, Segment, StopType, TripInput
from hos.engine.planner import plan_trip

from . import routing
from .routing import GeoPoint

# Map an engine segment's remark to the map/stop type the client renders.
_REMARK_TO_STOP = {
    "Fuel stop": StopType.FUEL,
    "30-minute break": StopType.BREAK,
    "Pickup / loading": StopType.PICKUP,
    "Dropoff / unloading": StopType.DROPOFF,
}


def _stop_type_for(remark: str) -> StopType | None:
    if remark in _REMARK_TO_STOP:
        return _REMARK_TO_STOP[remark]
    if remark.startswith("10-hour reset"):
        return StopType.REST
    if remark.startswith("34-hour restart"):
        return StopType.RESTART
    return None


def _resolve_start(start_datetime: str | None, origin: GeoPoint) -> datetime:
    """Parse the optional start time; infer a local offset from longitude.

    If no start is given we use the current time. If a naive datetime is given
    we attach a rough US offset derived from the origin's longitude so
    ``.date()`` reflects the driver's local day.
    """
    offset_hours = max(-11, min(12, round(origin.lng / 15.0)))
    tz = timezone(timedelta(hours=offset_hours))

    if not start_datetime:
        return datetime.now(tz)

    dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class _MileageLocator:
    """Interpolates a [lat, lng] position at a given cumulative-mile mark."""

    def __init__(self, geometry: list[list[float]], total_miles: float):
        self.pts = geometry
        # Cumulative geometric distance at each vertex, scaled to total_miles.
        self.cum: list[float] = [0.0]
        for i in range(1, len(geometry)):
            a = GeoPoint("", geometry[i - 1][0], geometry[i - 1][1])
            b = GeoPoint("", geometry[i][0], geometry[i][1])
            self.cum.append(self.cum[-1] + routing._haversine_miles(a, b))
        geo_total = self.cum[-1] or 1.0
        scale = total_miles / geo_total if geo_total else 1.0
        self.cum = [c * scale for c in self.cum]

    def at(self, miles: float) -> tuple[float, float]:
        if miles <= 0 or len(self.pts) == 1:
            return self.pts[0][0], self.pts[0][1]
        if miles >= self.cum[-1]:
            return self.pts[-1][0], self.pts[-1][1]
        for i in range(1, len(self.cum)):
            if self.cum[i] >= miles:
                span = self.cum[i] - self.cum[i - 1] or 1.0
                frac = (miles - self.cum[i - 1]) / span
                lat = self.pts[i - 1][0] + (self.pts[i][0] - self.pts[i - 1][0]) * frac
                lng = self.pts[i - 1][1] + (self.pts[i][1] - self.pts[i - 1][1]) * frac
                return lat, lng
        return self.pts[-1][0], self.pts[-1][1]


def _serialize_segment(seg: Segment) -> dict:
    return {
        "status": seg.status.value,
        "start": _iso(seg.start),
        "end": _iso(seg.end),
        "location": seg.location,
        "remark": seg.remark,
    }


def _build_summary(segments: list[Segment], total_distance: float,
                   used_restart: bool) -> dict:
    def hrs(status: DutyStatus) -> float:
        return sum(s.hours for s in segments if s.status == status)

    driving = hrs(DutyStatus.DRIVING)
    on_duty_nd = hrs(DutyStatus.ON_DUTY_NOT_DRIVING)
    off = hrs(DutyStatus.OFF_DUTY)
    sleeper = hrs(DutyStatus.SLEEPER)

    return {
        "total_distance_miles": round(total_distance, 1),
        "total_driving_hours": round(driving, 2),
        "total_on_duty_hours": round(driving + on_duty_nd, 2),
        "total_off_duty_hours": round(off + sleeper, 2),
        "num_days": len({s.start.date() for s in segments}),
        "num_breaks": sum(1 for s in segments if s.remark == "30-minute break"),
        "num_rest_periods": sum(
            1 for s in segments if s.remark.startswith("10-hour reset")
        ),
        "num_fuel_stops": sum(1 for s in segments if s.remark == "Fuel stop"),
        "used_34h_restart": used_restart,
        "cycle_hours_added": round(driving + on_duty_nd, 2),
    }


def plan(*, current_location: str, pickup_location: str, dropoff_location: str,
         current_cycle_used_hours: float, start_datetime: str | None = None) -> dict:
    """Full pipeline. Raises ``routing.GeocodingError`` on bad locations."""
    origin = routing.geocode(current_location)
    pickup = routing.geocode(pickup_location)
    dropoff = routing.geocode(dropoff_location)

    routed1 = routing.route_leg(origin, pickup)
    routed2 = routing.route_leg(pickup, dropoff)

    start_dt = _resolve_start(start_datetime, origin)

    trip_input = TripInput(
        current_label=current_location,
        pickup_label=pickup_location,
        dropoff_label=dropoff_location,
        current_cycle_used_hours=current_cycle_used_hours,
        start_dt=start_dt,
        legs=[routed1.leg, routed2.leg],
    )
    segments = plan_trip(trip_input)

    # Combined polyline for the map + a locator for interpolated stop markers.
    # (leg2 geometry starts at pickup, so drop its duplicated first vertex.)
    full_geometry = routed1.geometry + routed2.geometry[1:]
    total_distance = routed1.leg.distance_miles + routed2.leg.distance_miles
    locator = _MileageLocator(full_geometry, total_distance)

    stops = [{
        "type": StopType.START.value,
        "label": current_location,
        "lat": origin.lat,
        "lng": origin.lng,
        "arrival": _iso(start_dt),
    }]
    endpoints = {StopType.PICKUP: pickup, StopType.DROPOFF: dropoff}
    for seg in segments:
        stop_type = _stop_type_for(seg.remark)
        if stop_type is None:
            continue
        if stop_type in endpoints:
            gp = endpoints[stop_type]
            lat, lng = gp.lat, gp.lng
            label = gp.label
        else:
            lat, lng = locator.at(seg.cum_miles_start)
            label = seg.remark
        stops.append({
            "type": stop_type.value,
            "label": label,
            "lat": lat,
            "lng": lng,
            "arrival": _iso(seg.start),
        })

    daily_logs = []
    for log in group_by_day(segments):
        daily_logs.append({
            "date": log.day.isoformat(),
            "segments": [_serialize_segment(s) for s in log.segments],
            "totals": {status.value: round(hrs, 3) for status, hrs in log.totals.items()},
            "miles": round(log.miles, 1),
        })

    used_restart = any(s.remark.startswith("34-hour restart") for s in segments)

    return {
        "timezone": _tz_label(start_dt),
        "start_datetime": _iso(start_dt),
        "summary": _build_summary(segments, total_distance, used_restart),
        "route": {
            "geometry": full_geometry,
            "legs": [_serialize_leg(r) for r in (routed1, routed2)],
            "stops": stops,
        },
        "segments": [_serialize_segment(s) for s in segments],
        "daily_logs": daily_logs,
    }


def _serialize_leg(routed: routing.RoutedLeg) -> dict:
    return {
        "from_label": routed.leg.from_label,
        "to_label": routed.leg.to_label,
        "distance_miles": round(routed.leg.distance_miles, 1),
        "duration_hours": round(routed.leg.duration_hours, 2),
        "geometry": routed.geometry,
    }


def _tz_label(dt: datetime) -> str:
    off = dt.utcoffset() or timedelta(0)
    total_min = int(off.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    total_min = abs(total_min)
    return f"UTC{sign}{total_min // 60:02d}:{total_min % 60:02d}"
