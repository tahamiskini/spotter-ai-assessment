"""The HOS scheduling engine.

``plan_trip`` turns a routed :class:`TripInput` into a gapless, ordered list of
duty-status :class:`Segment` objects that never violate the 11h / 14h / 30-min
break / 70h rules, inserting 10h resets, 34h restarts, and fuel stops as needed.

The design follows a chunked drive loop (see ``drive_leg``): at every step we
first resolve any blocking limit in strict priority order, then drive the
largest chunk that cannot cross any remaining limit.
"""

from __future__ import annotations

from datetime import timedelta

from . import cycle
from .constants import (
    BREAK_HOURS,
    DRIVE_BEFORE_BREAK_HOURS,
    DROPOFF_HOURS,
    EPS,
    FUEL_INTERVAL_MILES,
    FUEL_STOP_HOURS,
    MAX_DRIVE_HOURS,
    MIN_BREAK_QUALIFYING_HOURS,
    PICKUP_HOURS,
    RESET_HOURS,
    RESTART_HOURS,
)
from .models import DutyStatus, Leg, Segment, SimState, TripInput

# Defensive cap so a logic error can never produce an unbounded loop.
_MAX_ITERATIONS = 100_000


def _emit(state: SimState, status: DutyStatus, hours: float, location: str,
          remark: str, miles: float = 0.0) -> Segment:
    """Append a contiguous segment starting at ``state.now`` and advance the clock."""
    start = state.now
    end = start + timedelta(hours=hours)
    seg = Segment(
        status=status,
        start=start,
        end=end,
        location=location,
        remark=remark,
        cum_miles_start=state.total_miles,
        cum_miles_end=state.total_miles + miles,
    )
    state.segments.append(seg)
    state.now = end
    return seg


def insert_rest(state: SimState, hours: float, status: DutyStatus,
                location: str, remark: str) -> None:
    """Insert a non-driving rest and apply its reset semantics.

    * any ≥30-min non-driving resets the 30-min break clock;
    * ≥10h additionally resets shift driving + the 14h window;
    * ≥34h additionally clears the cycle (restart).
    """
    _emit(state, status, hours, location, remark)

    if hours + EPS >= MIN_BREAK_QUALIFYING_HOURS:
        state.drive_since_break = 0.0
    if hours + EPS >= RESET_HOURS:
        state.start_shift()  # resets shift_drive, drive_since_break, window_end
    if hours + EPS >= RESTART_HOURS:
        # ``now`` is already the end of the 34h off period.
        state.restart_at = state.now


def do_activity(state: SimState, hours: float, location: str, remark: str) -> None:
    """On-duty (not driving) work — pickup/dropoff/fuel. Counts toward the cycle."""
    start = state.now
    _emit(state, DutyStatus.ON_DUTY_NOT_DRIVING, hours, location, remark)
    cycle.add_onduty(state, start, state.now)
    # A ≥30-min on-duty stop also satisfies the pending 30-min break.
    if hours + EPS >= MIN_BREAK_QUALIFYING_HOURS:
        state.drive_since_break = 0.0


def _window_remaining(state: SimState) -> float:
    assert state.window_end is not None
    return (state.window_end - state.now).total_seconds() / 3600.0


def drive_leg(state: SimState, leg: Leg) -> None:
    """Consume ``leg.duration_hours`` of driving, inserting rests/breaks/fuel."""
    speed = leg.speed_mph
    remaining = leg.duration_hours
    location = f"en route to {leg.to_label}"
    guard = 0

    while remaining > EPS:
        guard += 1
        if guard > _MAX_ITERATIONS:  # pragma: no cover - safety net
            raise RuntimeError("drive_leg exceeded iteration cap")

        # --- STEP A: resolve blocking limits in strict priority order --------
        # 1. 70h cycle exhausted → only a 34h restart can fix it.
        if cycle.cycle_available_at(state, state.now) <= EPS:
            insert_rest(state, RESTART_HOURS, DutyStatus.OFF_DUTY, location,
                        "34-hour restart (70h cycle reached)")
            continue
        # 2. 11h driving OR 14h window exhausted → 10h reset.
        if (state.shift_drive >= MAX_DRIVE_HOURS - EPS
                or _window_remaining(state) <= EPS):
            insert_rest(state, RESET_HOURS, DutyStatus.SLEEPER, location,
                        "10-hour reset (shift limit reached)")
            continue
        # 3. 1,000-mile fuel mark reached → refuel (also satisfies a pending
        #    break, so it is resolved before the 30-min break below).
        if state.miles_since_fuel >= FUEL_INTERVAL_MILES - EPS:
            do_activity(state, FUEL_STOP_HOURS, location, "Fuel stop")
            state.miles_since_fuel = max(0.0, state.miles_since_fuel - FUEL_INTERVAL_MILES)
            continue
        # 4. 8h cumulative driving → 30-min break.
        if state.drive_since_break >= DRIVE_BEFORE_BREAK_HOURS - EPS:
            insert_rest(state, BREAK_HOURS, DutyStatus.OFF_DUTY, location,
                        "30-minute break")
            continue

        # --- STEP B: largest chunk that crosses no remaining limit -----------
        # Each term is > 0 here (STEP A cleared every zero-limit), so the chunk
        # makes real progress and the loop always terminates.
        drive_left = MAX_DRIVE_HOURS - state.shift_drive
        window_left = _window_remaining(state)
        break_left = DRIVE_BEFORE_BREAK_HOURS - state.drive_since_break
        cycle_left = cycle.cycle_available_at(state, state.now)
        fuel_left_hours = (
            (FUEL_INTERVAL_MILES - state.miles_since_fuel) / speed
            if speed > 0 else float("inf")
        )
        chunk = min(remaining, drive_left, window_left, break_left,
                    cycle_left, fuel_left_hours)
        if chunk <= EPS:  # pragma: no cover - STEP A guarantees progress
            break

        # --- STEP C: emit DRIVING, advance clock, update counters ------------
        miles = chunk * speed
        start = state.now
        _emit(state, DutyStatus.DRIVING, chunk, location, "Driving", miles=miles)
        cycle.add_onduty(state, start, state.now)
        state.shift_drive += chunk
        state.drive_since_break += chunk
        state.miles_since_fuel += miles
        state.total_miles += miles
        remaining -= chunk


def plan_trip(trip: TripInput) -> list[Segment]:
    """Simulate the whole trip: current→pickup (load) →dropoff (unload)."""
    if len(trip.legs) != 2:
        raise ValueError("plan_trip expects exactly two legs (→pickup, →dropoff)")

    state = SimState(
        now=trip.start_dt,
        seed_hours=max(0.0, trip.current_cycle_used_hours),
        seed_at=trip.start_dt,
    )
    state.start_shift()

    leg_to_pickup, leg_to_dropoff = trip.legs

    drive_leg(state, leg_to_pickup)
    do_activity(state, PICKUP_HOURS, trip.pickup_label, "Pickup / loading")

    drive_leg(state, leg_to_dropoff)
    do_activity(state, DROPOFF_HOURS, trip.dropoff_label, "Dropoff / unloading")

    return state.segments
