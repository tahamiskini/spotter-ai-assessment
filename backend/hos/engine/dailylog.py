"""Turn a flat segment timeline into per-day ELD log sheets.

Segments are split at the driver's local midnight so every segment belongs to
exactly one calendar day, then grouped by day with per-status hour totals and
driven miles. The per-day on-duty total must reconcile with the segments'
on-duty time (asserted by the engine tests).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .models import DutyStatus, Segment


@dataclass
class DailyLog:
    day: date
    segments: list[Segment] = field(default_factory=list)
    totals: dict[DutyStatus, float] = field(default_factory=dict)
    miles: float = 0.0


def _next_midnight(dt: datetime) -> datetime:
    nxt = (dt + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return nxt


def split_at_midnight(segments: list[Segment]) -> list[Segment]:
    """Split any segment spanning local midnight into per-day pieces.

    Cumulative miles are interpolated at the split point so each piece carries
    its own share of driven distance.
    """
    out: list[Segment] = []
    for seg in segments:
        start = seg.start
        while True:
            boundary = _next_midnight(start)
            if seg.end <= boundary:
                piece_end = seg.end
                done = True
            else:
                piece_end = boundary
                done = False

            frac = (
                (piece_end - start).total_seconds()
                / (seg.end - seg.start).total_seconds()
                if seg.end > seg.start else 1.0
            )
            span_miles = seg.cum_miles_end - seg.cum_miles_start
            cum_from = seg.cum_miles_start + span_miles * (
                (start - seg.start).total_seconds()
                / (seg.end - seg.start).total_seconds()
                if seg.end > seg.start else 0.0
            )
            cum_to = seg.cum_miles_start + span_miles * (
                (piece_end - seg.start).total_seconds()
                / (seg.end - seg.start).total_seconds()
                if seg.end > seg.start else 1.0
            )
            out.append(Segment(
                status=seg.status,
                start=start,
                end=piece_end,
                location=seg.location,
                remark=seg.remark,
                cum_miles_start=cum_from,
                cum_miles_end=cum_to,
            ))
            if done:
                break
            start = piece_end
    return out


def day_totals(segments: list[Segment]) -> dict[DutyStatus, float]:
    """Per-status hour totals for one day's (already-split) segments."""
    totals = {status: 0.0 for status in DutyStatus}
    for seg in segments:
        totals[seg.status] += seg.hours
    return totals


def group_by_day(segments: list[Segment]) -> list[DailyLog]:
    """Split at midnight and group into ordered daily logs with totals + miles."""
    pieces = split_at_midnight(segments)

    by_day: dict[date, list[Segment]] = {}
    for seg in pieces:
        by_day.setdefault(seg.start.date(), []).append(seg)

    logs: list[DailyLog] = []
    for day in sorted(by_day):
        day_segments = by_day[day]
        miles = sum(
            s.cum_miles_end - s.cum_miles_start
            for s in day_segments
            if s.status == DutyStatus.DRIVING
        )
        logs.append(DailyLog(
            day=day,
            segments=day_segments,
            totals=day_totals(day_segments),
            miles=miles,
        ))
    return logs
