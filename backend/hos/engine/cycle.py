"""Rolling 70-hour / 8-day cycle accounting.

On-duty time is tracked as a list of (start, end) intervals on ``SimState`` so
the rolling window and the 34h restart can both be computed precisely, without
losing intra-day timing to per-day aggregation.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .constants import CYCLE_WINDOW_DAYS, MAX_CYCLE_HOURS
from .models import SimState


def _overlap_hours(a_start: datetime, a_end: datetime,
                   b_start: datetime, b_end: datetime) -> float:
    """Hours of overlap between intervals [a_start, a_end] and [b_start, b_end]."""
    lo = max(a_start, b_start)
    hi = min(a_end, b_end)
    if hi <= lo:
        return 0.0
    return (hi - lo).total_seconds() / 3600.0


def cycle_used_at(state: SimState, when: datetime) -> float:
    """On-duty hours counting against the 70h limit as of ``when``.

    = seed (if still in-window and not cleared by a restart)
      + on-duty intervals overlapping [lower_bound, when]

    ``lower_bound`` is the later of the 8-day rolling window start (local
    midnight of ``when.date() - 7 days``) and the most recent 34h restart.
    """
    window_start_day = (when - timedelta(days=CYCLE_WINDOW_DAYS - 1)).date()
    lower = datetime.combine(window_start_day, datetime.min.time(), tzinfo=when.tzinfo)
    if state.restart_at is not None and state.restart_at > lower:
        lower = state.restart_at

    total = 0.0

    # Seed: the driver's pre-trip cycle hours, attributed entirely to the trip
    # start instant (conservative — see README simplification note).
    if (
        state.seed_hours > 0
        and state.seed_at is not None
        and lower <= state.seed_at <= when
    ):
        total += state.seed_hours

    for s, e in state.onduty_intervals:
        total += _overlap_hours(s, e, lower, when)

    return total


def cycle_available_at(state: SimState, when: datetime) -> float:
    """Hours of on-duty driving still allowed before the 70h limit bites."""
    return MAX_CYCLE_HOURS - cycle_used_at(state, when)


def add_onduty(state: SimState, start: datetime, end: datetime) -> None:
    """Record an on-duty interval (driving or on-duty-not-driving)."""
    if end > start:
        state.onduty_intervals.append((start, end))
