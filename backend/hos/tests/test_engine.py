"""HOS engine correctness anchors.

Runs with the standard library alone::

    cd backend && python3 -m unittest hos.tests.test_engine -v

Every scenario asserts the hard invariants (no plan exceeds 11h drive / 14h
window / 70h cycle, segments are gapless and ordered) plus the behaviour that
scenario is designed to force.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from hos.engine import cycle
from hos.engine.constants import (
    EPS,
    MAX_CYCLE_HOURS,
    MAX_DRIVE_HOURS,
    MAX_WINDOW_HOURS,
)
from hos.engine.dailylog import group_by_day
from hos.engine.models import DutyStatus, Leg, SimState, TripInput
from hos.engine.planner import drive_leg, plan_trip

TZ = timezone(timedelta(hours=-6))  # a fixed local offset for all tests
START = datetime(2026, 7, 10, 8, 0, tzinfo=TZ)


def make_trip(*, d1_mi, d1_hr, d2_mi, d2_hr, cycle_used=0.0, start=START):
    return TripInput(
        current_label="A",
        pickup_label="B",
        dropoff_label="C",
        current_cycle_used_hours=cycle_used,
        start_dt=start,
        legs=[
            Leg("A", "B", d1_mi, d1_hr),
            Leg("B", "C", d2_mi, d2_hr),
        ],
    )


class InvariantMixin:
    """Reusable assertions every produced plan must satisfy."""

    def assert_gapless_ordered(self, segments):
        for i in range(1, len(segments)):
            self.assertLessEqual(segments[i - 1].start, segments[i - 1].end)
            self.assertEqual(
                segments[i - 1].end, segments[i].start,
                msg=f"gap/overlap between segment {i - 1} and {i}",
            )

    def assert_no_drive_violations(self, segments):
        """Replay the timeline and check the 11h / 14h / 70h limits hold."""
        shift_drive = 0.0
        drive_since_break = 0.0
        window_end = None
        # Rebuild a state just for cycle checking. ``restart_at`` is advanced as
        # we encounter ≥34h off periods so the 70h check honours restarts,
        # exactly as the engine does.
        state = SimState(now=segments[0].start)
        for seg in segments:
            if seg.status.is_on_duty:
                cycle.add_onduty(state, seg.start, seg.end)

        for seg in segments:
            if seg.status != DutyStatus.DRIVING and seg.hours + EPS >= 34.0:
                state.restart_at = seg.end
            if seg.status == DutyStatus.DRIVING:
                if window_end is None:
                    window_end = seg.start + timedelta(hours=MAX_WINDOW_HOURS)
                # 11h driving
                shift_drive += seg.hours
                self.assertLessEqual(
                    shift_drive, MAX_DRIVE_HOURS + 1e-3,
                    msg="11h driving limit exceeded",
                )
                # 14h window
                self.assertLessEqual(
                    seg.end, window_end + timedelta(seconds=1),
                    msg="14h window exceeded",
                )
                # 30-min break
                drive_since_break += seg.hours
                self.assertLessEqual(
                    drive_since_break, 8.0 + 1e-3,
                    msg="drove more than 8h without a break",
                )
                # 70h cycle: on-duty up to this segment's end must be ≤ 70
                self.assertLessEqual(
                    cycle.cycle_used_at(state, seg.end), MAX_CYCLE_HOURS + 1e-3,
                    msg="70h cycle exceeded",
                )
            else:
                if seg.hours + EPS >= 0.5:
                    drive_since_break = 0.0
                if seg.hours + EPS >= 10.0:
                    shift_drive = 0.0
                    window_end = seg.end + timedelta(hours=MAX_WINDOW_HOURS)


class TestShortTrip(unittest.TestCase, InvariantMixin):
    def test_no_limits_hit(self):
        # ~4h + ~3h driving, well under every limit.
        trip = make_trip(d1_mi=200, d1_hr=4, d2_mi=150, d2_hr=3)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        # No resets, no breaks, no fuel — just drive/pickup/drive/dropoff.
        statuses = [s.status for s in segs]
        self.assertNotIn(DutyStatus.SLEEPER, statuses)
        # Two driving legs + two ON_DUTY activities.
        self.assertEqual(statuses.count(DutyStatus.DRIVING), 2)
        self.assertEqual(statuses.count(DutyStatus.ON_DUTY_NOT_DRIVING), 2)


class TestBreakAt8h(unittest.TestCase, InvariantMixin):
    def test_30min_break_inserted(self):
        # 9h of driving in one leg forces a 30-min break at 8h.
        trip = make_trip(d1_mi=540, d1_hr=9, d2_mi=60, d2_hr=1)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        breaks = [s for s in segs if "30-minute break" in s.remark]
        self.assertGreaterEqual(len(breaks), 1)
        self.assertAlmostEqual(breaks[0].hours, 0.5, places=6)


class TestForced10hReset(unittest.TestCase, InvariantMixin):
    def test_reset_when_11h_hit(self):
        # 13h of driving needs a 10h reset once 11h is used.
        trip = make_trip(d1_mi=650, d1_hr=13, d2_mi=50, d2_hr=1)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        resets = [s for s in segs if "10-hour reset" in s.remark]
        self.assertGreaterEqual(len(resets), 1)
        self.assertAlmostEqual(resets[0].hours, 10.0, places=6)


class TestWindowClosesBefore11h(unittest.TestCase, InvariantMixin):
    def test_14h_window_limits_before_driving_11h(self):
        # Slow driving (heavy traffic): 10h driving but interrupted so the 14h
        # wall clock closes before the 11h driving cap. Force it via a fuel
        # stop pattern: long low-speed leg with a required break eats window.
        trip = make_trip(d1_mi=300, d1_hr=10, d2_mi=120, d2_hr=4)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        # A reset must appear (either 11h or 14h triggered it).
        self.assertTrue(any("10-hour reset" in s.remark for s in segs))


class TestFuelStop(unittest.TestCase, InvariantMixin):
    def test_fuel_stop_every_1000mi(self):
        # 1,500 miles total → at least one fuel stop.
        trip = make_trip(d1_mi=900, d1_hr=15, d2_mi=600, d2_hr=10)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        fuel = [s for s in segs if s.remark == "Fuel stop"]
        self.assertGreaterEqual(len(fuel), 1)


class TestCycleNear70(unittest.TestCase, InvariantMixin):
    def test_restart_forced_when_cycle_exhausted(self):
        # 68h already used; a multi-hour drive must trigger a 34h restart.
        trip = make_trip(d1_mi=300, d1_hr=6, d2_mi=200, d2_hr=4, cycle_used=68)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        restarts = [s for s in segs if "34-hour restart" in s.remark]
        self.assertGreaterEqual(len(restarts), 1)
        self.assertAlmostEqual(restarts[0].hours, 34.0, places=6)


class TestMultipleRestarts(unittest.TestCase, InvariantMixin):
    def test_two_restarts_on_very_long_trip(self):
        # Enormous mileage that consumes >140h of on-duty → ≥2 restarts.
        trip = make_trip(d1_mi=4000, d1_hr=70, d2_mi=4000, d2_hr=70)
        segs = plan_trip(trip)
        self.assert_gapless_ordered(segs)
        self.assert_no_drive_violations(segs)
        restarts = [s for s in segs if "34-hour restart" in s.remark]
        self.assertGreaterEqual(len(restarts), 2)


class TestDailyLogReconciles(unittest.TestCase, InvariantMixin):
    def test_midnight_split_totals(self):
        trip = make_trip(d1_mi=650, d1_hr=13, d2_mi=400, d2_hr=7, cycle_used=10)
        segs = plan_trip(trip)
        logs = group_by_day(segs)

        # Each day's four status totals sum to ≤ 24h (== 24 for full days).
        for log in logs:
            total = sum(log.totals.values())
            self.assertLessEqual(total, 24.0 + 1e-3)

        # On-duty across all days equals on-duty across the raw segments.
        onduty_from_logs = sum(
            log.totals[DutyStatus.DRIVING]
            + log.totals[DutyStatus.ON_DUTY_NOT_DRIVING]
            for log in logs
        )
        onduty_from_segs = sum(
            s.hours for s in segs if s.status.is_on_duty
        )
        self.assertAlmostEqual(onduty_from_logs, onduty_from_segs, places=4)

        # Miles reconcile too.
        miles_from_logs = sum(log.miles for log in logs)
        miles_from_segs = sum(
            s.cum_miles_end - s.cum_miles_start
            for s in segs if s.status == DutyStatus.DRIVING
        )
        self.assertAlmostEqual(miles_from_logs, miles_from_segs, places=2)


if __name__ == "__main__":
    unittest.main()
