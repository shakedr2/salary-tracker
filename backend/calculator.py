# -*- coding: utf-8 -*-
"""
Salary calculation engine.

Rules:
- Regular: up to REGULAR_LIMIT hours @ RATE_REGULAR
- 125%: hours between REGULAR_LIMIT and LIMIT_125 @ RATE_125
- 150%: hours above LIMIT_125 @ RATE_150
- Weekend premium: any period that overlaps Friday 17:00 - Sunday 05:00 => all hours of that period/day at RATE_150
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Tuple, Optional, Any, Dict
from datetime import datetime, date, time as dt_time, timedelta

from .config import (
    RATE_REGULAR,
    RATE_125,
    RATE_150,
    REGULAR_LIMIT,
    LIMIT_125,
    WEEKEND_PREMIUM_START,
    WEEKEND_PREMIUM_END,
)

logger = logging.getLogger("backend.calculator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# Try to import models if present
try:
    from .models import AttendanceRecord, DaySalaryBreakdown, SalaryReport  # type: ignore
except Exception:
    @dataclass
    class AttendanceRecord:
        date: date
        clock_in: str
        clock_out: str
        periods: Optional[List[Tuple[str, str]]] = None

    @dataclass
    class DaySalaryBreakdown:
        date: date
        regular_hours: float
        overtime_125_hours: float
        overtime_150_hours: float
        day_total: float
        raw_periods: List[Tuple[str, str]] = field(default_factory=list)
        weekend_premium_applied: bool = False

    @dataclass
    class SalaryReport:
        month: int
        year: int
        days: List[DaySalaryBreakdown]
        total: float = 0.0

        def to_dict(self) -> Dict[str, Any]:
            return {
                "year": self.year,
                "month": self.month,
                "total": self.total,
                "days": [asdict(d) for d in self.days],
            }


def _parse_time_str(s: str) -> Optional[dt_time]:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        parts = s.split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return dt_time(hour=h % 24, minute=m % 60)
    except Exception:
        return None


def _period_duration_hours(start: dt_time, end: dt_time) -> float:
    start_dt = datetime.combine(date.min, start)
    end_dt = datetime.combine(date.min, end)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return (end_dt - start_dt).total_seconds() / 3600.0


def _find_weekend_window_for_date(d: date) -> Tuple[datetime, datetime]:
    """
    Given any date, compute the weekend premium window (start_datetime, end_datetime)
    based on WEEKEND_PREMIUM_START and WEEKEND_PREMIUM_END config.
    The start anchor is the most recent weekday matching WEEKEND_PREMIUM_START['weekday'].
    """
    start_cfg = WEEKEND_PREMIUM_START
    end_cfg = WEEKEND_PREMIUM_END

    s_wd = start_cfg.get("weekday", 4)
    s_h = start_cfg.get("hour", 17)
    s_m = start_cfg.get("minute", 0)

    e_wd = end_cfg.get("weekday", 6)
    e_h = end_cfg.get("hour", 5)
    e_m = end_cfg.get("minute", 0)

    days_since_start = (d.weekday() - s_wd) % 7
    start_anchor = d - timedelta(days=days_since_start)
    start_window = datetime.combine(start_anchor, dt_time(s_h, s_m))

    days_until_end = (e_wd - s_wd) % 7
    end_anchor = start_anchor + timedelta(days=days_until_end)
    end_window = datetime.combine(end_anchor, dt_time(e_h, e_m))

    return start_window, end_window


def _period_overlaps_weekend(d: date, start_t: dt_time, end_t: dt_time) -> bool:
    try:
        start_win, end_win = _find_weekend_window_for_date(d)
        period_start = datetime.combine(d, start_t)
        period_end = datetime.combine(d, end_t)
        if period_end <= period_start:
            period_end += timedelta(days=1)
        return (period_start < end_win) and (period_end > start_win)
    except Exception:
        return False


def _allocate_hours(total_hours: float) -> Tuple[float, float, float]:
    regular = min(total_hours, REGULAR_LIMIT)
    remaining = max(0.0, total_hours - regular)
    overtime_125 = min(max(0.0, remaining), max(0.0, LIMIT_125 - REGULAR_LIMIT))
    overtime_150 = max(0.0, total_hours - regular - overtime_125)
    return round(regular, 4), round(overtime_125, 4), round(overtime_150, 4)


def calculate_salary_for_month(year: int, month: int, records: List[Any]) -> "SalaryReport":
    days_breakdown: List[DaySalaryBreakdown] = []
    total_sum = 0.0

    for rec in records:
        # extract date
        rec_date = None
        if isinstance(rec, dict):
            rec_date = rec.get("date")
        elif hasattr(rec, "date"):
            rec_date = getattr(rec, "date")
        else:
            logger.debug("Record without date skipped: %s", rec)
            continue

        # parse date if string
        if isinstance(rec_date, str):
            try:
                rec_date_parsed = datetime.fromisoformat(rec_date).date()
            except Exception:
                try:
                    rec_date_parsed = datetime.strptime(rec_date, "%d/%m/%Y").date()
                except Exception:
                    # leave as None to store raw
                    rec_date_parsed = None
            rec_date = rec_date_parsed

        # gather periods
        periods: List[Tuple[str, str]] = []
        if isinstance(rec, dict):
            if "periods" in rec and rec.get("periods"):
                periods = rec.get("periods", [])
            elif "clock_in" in rec and "clock_out" in rec:
                periods = [(rec.get("clock_in"), rec.get("clock_out"))]
        else:
            if hasattr(rec, "periods") and getattr(rec, "periods"):
                periods = getattr(rec, "periods")  # type: ignore
            elif hasattr(rec, "clock_in") and hasattr(rec, "clock_out"):
                periods = [(getattr(rec, "clock_in"), getattr(rec, "clock_out"))]

        parsed_periods: List[Tuple[str, str]] = []
        total_hours_for_day = 0.0
        weekend_applied = False

        for start_s, end_s in periods:
            start_t = _parse_time_str(start_s) if start_s else None
            end_t = _parse_time_str(end_s) if end_s else None
            if not start_t or not end_t:
                continue
            parsed_periods.append((start_s, end_s))
            dur = _period_duration_hours(start_t, end_t)
            total_hours_for_day += dur
            if rec_date and _period_overlaps_weekend(rec_date, start_t, end_t):
                weekend_applied = True

        # if no periods but record has clock_in/clock_out fields separately
        if not parsed_periods:
            # attempt to extract clock_in/clock_out if present as strings
            if isinstance(rec, dict) and "clock_in" in rec and "clock_out" in rec:
                si = rec.get("clock_in")
                so = rec.get("clock_out")
                st = _parse_time_str(si)
                et = _parse_time_str(so)
                if st and et:
                    parsed_periods.append((si, so))
                    dur = _period_duration_hours(st, et)
                    total_hours_for_day += dur
                    if rec_date and _period_overlaps_weekend(rec_date, st, et):
                        weekend_applied = True

        if total_hours_for_day <= 0:
            day_break = DaySalaryBreakdown(
                date=rec_date if isinstance(rec_date, date) else (datetime.utcnow().date() if rec_date is None else rec_date),
                regular_hours=0.0,
                overtime_125_hours=0.0,
                overtime_150_hours=0.0,
                day_total=0.0,
                raw_periods=parsed_periods,
                weekend_premium_applied=weekend_applied,
            )
            days_breakdown.append(day_break)
            continue

        if weekend_applied:
            day_total = round(total_hours_for_day * RATE_150, 2)
            regular_h, ot125_h, ot150_h = 0.0, 0.0, round(total_hours_for_day, 4)
        else:
            regular_h, ot125_h, ot150_h = _allocate_hours(total_hours_for_day)
            day_total = round(regular_h * RATE_REGULAR + ot125_h * RATE_125 + ot150_h * RATE_150, 2)

        total_sum += day_total
        day_break = DaySalaryBreakdown(
            date=rec_date if isinstance(rec_date, date) else (datetime.utcnow().date() if rec_date is None else rec_date),
            regular_hours=regular_h,
            overtime_125_hours=ot125_h,
            overtime_150_hours=ot150_h,
            day_total=day_total,
            raw_periods=parsed_periods,
            weekend_premium_applied=weekend_applied,
        )
        days_breakdown.append(day_break)

    report = SalaryReport(month=month, year=year, days=days_breakdown, total=round(total_sum, 2))
    return report
