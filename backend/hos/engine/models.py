"""Pure-Python data structures for the HOS engine.

No Django imports here — this module (and everything under ``engine/``) must be
importable and unit-testable with the standard library alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .constants import MAX_WINDOW_HOURS


class DutyStatus(str, Enum):
    """The four FMCSA duty statuses — the rows of an ELD daily-log grid."""

    OFF_DUTY = "OFF_DUTY"
    SLEEPER = "SLEEPER"
    DRIVING = "DRIVING"
    ON_DUTY_NOT_DRIVING = "ON_DUTY_NOT_DRIVING"

    @property
    def is_on_duty(self) -> bool:
        """On-duty time counts toward the 70h cycle (driving + on-duty ND)."""
        return self in (DutyStatus.DRIVING, DutyStatus.ON_DUTY_NOT_DRIVING)


class StopType(str, Enum):
    START = "start"
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    FUEL = "fuel"
    BREAK = "break"
    REST = "rest"
    RESTART = "restart"


@dataclass
class Segment:
    """A single continuous duty-status block on the timeline."""

    status: DutyStatus
    start: datetime
    end: datetime
    location: str
    remark: str
    # Cumulative trip miles at the segment's start/end (drives accrue miles;
    # non-driving segments keep start == end). Used only for map placement.
    cum_miles_start: float = 0.0
    cum_miles_end: float = 0.0

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0


@dataclass
class Leg:
    """One routed leg (e.g. current→pickup) with a constant assumed speed."""

    from_label: str
    to_label: str
    distance_miles: float
    duration_hours: float

    @property
    def speed_mph(self) -> float:
        # Time is authoritative; speed only exists to account for fuel miles.
        # duration is validated > 0 at the routing layer; guard kept for safety.
        if self.duration_hours <= 0:
            return 0.0
        return self.distance_miles / self.duration_hours


@dataclass
class TripInput:
    current_label: str
    pickup_label: str
    dropoff_label: str
    current_cycle_used_hours: float
    start_dt: datetime
    # The two routed legs: current→pickup, pickup→dropoff.
    legs: list[Leg] = field(default_factory=list)


@dataclass
class SimState:
    """Five independent HOS clocks plus fuel/mileage bookkeeping.

    All datetimes are timezone-aware and share the trip's local offset, so
    ``.date()`` gives the driver's local calendar day.
    """

    now: datetime

    # 11h driving clock — hours driven in the current shift.
    shift_drive: float = 0.0
    # 14h window — wall-clock deadline; driving is illegal past this instant.
    window_end: datetime | None = None
    # 30-min break clock — cumulative driving since the last ≥30-min break.
    drive_since_break: float = 0.0

    # Rolling 70h/8-day cycle bookkeeping.
    onduty_intervals: list[tuple[datetime, datetime]] = field(default_factory=list)
    seed_hours: float = 0.0            # current_cycle_used_hours
    seed_at: datetime | None = None    # attributed entirely to the start instant
    restart_at: datetime | None = None  # a 34h restart clears everything before this

    # Fuel.
    miles_since_fuel: float = 0.0
    total_miles: float = 0.0

    # Output.
    segments: list[Segment] = field(default_factory=list)

    def start_shift(self) -> None:
        """Begin a fresh 14h window and reset the shift-scoped clocks.

        Called at trip start and after any ≥10h reset / 34h restart.
        """
        self.window_end = self.now + timedelta(hours=MAX_WINDOW_HOURS)
        self.shift_drive = 0.0
        self.drive_since_break = 0.0
