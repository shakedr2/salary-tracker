# -*- coding: utf-8 -*-
"""
Salary calculation engine with improved type hints and error handling.

Rules:
- Regular: up to REGULAR_LIMIT hours @ RATE_REGULAR
- 125%: hours between REGULAR_LIMIT and LIMIT_125 @ RATE_125
- 150%: hours above LIMIT_125 @ RATE_150
- Weekend premium: any period that overlaps Friday 17:00 - Sunday 05:00 => all hours of that period/day at RATE_150
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Tuple, Optional, Any, Dict, Union
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
from .observability import get_structured_logger

logger = get_structured_logger("backend.calculator")


# Try to import models if present
try:
    from .models import AttendanceRecord, DaySalaryBreakdown, SalaryReport  # type: ignore
except ImportError:
    @dataclass
    class AttendanceRecord:
        """Attendance record data structure."""
        date: date
        clock_in: str
        clock_out: str
        periods: Optional[List[Tuple[str, str]]] = None

    @dataclass
    class DaySalaryBreakdown:
        """Daily salary breakdown."""
        date: date
        regular_hours: float
        overtime_125_hours: float
        overtime_150_hours: float
        day_total: float
        raw_periods: List[Tuple[str, str]] = field(default_factory=list)
        weekend_premium_applied: bool = False

    @dataclass
    class SalaryReport:
        """Complete salary report."""
        month: int
        year: int
        days: List[DaySalaryBreakdown]
        total: float = 0.0

        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary."""
            return {
                "year": self.year,
                "month": self.month,
                "total": self.total,
                "days": [asdict(d) for d in self.days],
            }


class CalculationError(Exception):
    """Exception raised during salary calculation."""
    pass


def _parse_time_str(s: str) -> Optional[dt_time]:
    """
    Parse time string to time object.
    
    Args:
        s: Time string in format "HH:MM" or "H:MM"
    
    Returns:
        time object or None if parsing fails
    """
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        parts = s.split(":")
        if len(parts) < 2:
            return None
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        if h < 0 or h > 23 or m < 0 or m > 59:
            logger.warning("Invalid time values", time_string=s, hour=h, minute=m)
            return None
        return dt_time(hour=h % 24, minute=m % 60)
    except (ValueError, IndexError) as e:
        logger.warning("Failed to parse time string", time_string=s, error=str(e))
        return None


def _period_duration_hours(start: dt_time, end: dt_time) -> float:
    """
    Calculate duration between two times in hours.
    
    Args:
        start: Start time
        end: End time
    
    Returns:
        Duration in hours (handles cross-midnight)
    """
    start_dt = datetime.combine(date.min, start)
    end_dt = datetime.combine(date.min, end)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return round((end_dt - start_dt).total_seconds() / 3600.0, 4)


def _find_weekend_window_for_date(d: date) -> Tuple[datetime, datetime]:
    """
    Find weekend premium window for a given date.
    
    Args:
        d: Date to check
    
    Returns:
        Tuple of (start_datetime, end_datetime) for weekend window
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
    """
    Check if a time period overlaps with weekend premium window.
    
    Args:
        d: Date of the period
        start_t: Start time
        end_t: End time
    
    Returns:
        True if period overlaps weekend window
    """
    try:
        start_win, end_win = _find_weekend_window_for_date(d)
        period_start = datetime.combine(d, start_t)
        period_end = datetime.combine(d, end_t)
        if period_end <= period_start:
            period_end += timedelta(days=1)
        return (period_start < end_win) and (period_end > start_win)
    except Exception as e:
        logger.warning("Error checking weekend overlap", date=str(d), error=str(e))
        return False


def _allocate_hours(total_hours: float) -> Tuple[float, float, float]:
    """
    Allocate hours into regular, 125%, and 150% categories.
    
    Args:
        total_hours: Total hours worked
    
    Returns:
        Tuple of (regular_hours, overtime_125_hours, overtime_150_hours)
    """
    if total_hours < 0:
        logger.warning("Negative hours detected", total_hours=total_hours)
        total_hours = 0.0
    
    regular = min(total_hours, float(REGULAR_LIMIT))
    remaining = max(0.0, total_hours - regular)
    overtime_125 = min(max(0.0, remaining), max(0.0, float(LIMIT_125 - REGULAR_LIMIT)))
    overtime_150 = max(0.0, total_hours - regular - overtime_125)
    
    return round(regular, 4), round(overtime_125, 4), round(overtime_150, 4)


class SalaryCalculator:
    """Salary calculator with improved error handling and logging."""
    
    def __init__(self) -> None:
        """Initialize calculator."""
        self.logger = get_structured_logger("backend.calculator")
    
    def calculate_salary(self, records: List[Any]) -> SalaryReport:
        """
        Calculate salary for attendance records.
        
        Args:
            records: List of attendance records (dicts or AttendanceRecord objects)
        
        Returns:
            SalaryReport with calculated salary
        
        Raises:
            CalculationError: If calculation fails
        """
        if not records:
            self.logger.warning("No records provided for calculation")
            raise CalculationError("No attendance records provided")
        
        try:
            # Determine month and year from first record
            first_date = self._extract_date(records[0])
            if not first_date:
                # Fallback to current month
                now = datetime.utcnow()
                target_month = now.month
                target_year = now.year
                self.logger.warning("Could not determine date from records, using current month")
            else:
                target_month = first_date.month
                target_year = first_date.year
            
            self.logger.info(
                "Starting salary calculation",
                month=target_month,
                year=target_year,
                records_count=len(records)
            )
            
            report = calculate_salary_for_month(target_year, target_month, records)
            
            self.logger.info(
                "Salary calculation completed",
                month=target_month,
                year=target_year,
                days_processed=len(report.days),
                total_salary=report.total
            )
            
            return report
            
        except Exception as e:
            self.logger.error(
                "Salary calculation failed",
                error=str(e),
                error_type=type(e).__name__,
                records_count=len(records)
            )
            raise CalculationError(f"Failed to calculate salary: {str(e)}") from e
    
    def _extract_date(self, record: Union[Dict[str, Any], AttendanceRecord]) -> Optional[date]:
        """Extract date from record."""
        if isinstance(record, dict):
            rec_date = record.get("date")
        elif hasattr(record, "date"):
            rec_date = getattr(record, "date")
        else:
            return None
        
        if isinstance(rec_date, date):
            return rec_date
        
        if isinstance(rec_date, str):
            try:
                return datetime.fromisoformat(rec_date).date()
            except ValueError:
                try:
                    return datetime.strptime(rec_date, "%d/%m/%Y").date()
                except ValueError:
                    return None
        
        return None


def calculate_salary_for_month(year: int, month: int, records: List[Any]) -> SalaryReport:
    """
    Calculate salary for a specific month.
    
    Args:
        year: Year
        month: Month (1-12)
        records: List of attendance records
    
    Returns:
        SalaryReport
    """
    days_breakdown: List[DaySalaryBreakdown] = []
    total_sum = 0.0

    for rec in records:
        try:
            # Extract date
            rec_date = None
            if isinstance(rec, dict):
                rec_date = rec.get("date")
            elif hasattr(rec, "date"):
                rec_date = getattr(rec, "date")
            else:
                logger.debug("Record without date skipped", record_type=type(rec).__name__)
                continue

            # Parse date if string
            if isinstance(rec_date, str):
                try:
                    rec_date_parsed = datetime.fromisoformat(rec_date).date()
                except ValueError:
                    try:
                        rec_date_parsed = datetime.strptime(rec_date, "%d/%m/%Y").date()
                    except ValueError:
                        logger.warning("Could not parse date", date_string=rec_date)
                        rec_date_parsed = None
                rec_date = rec_date_parsed

            # Gather periods
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
                    logger.debug("Skipping invalid period", start=start_s, end=end_s)
                    continue
                parsed_periods.append((start_s, end_s))
                dur = _period_duration_hours(start_t, end_t)
                total_hours_for_day += dur
                if rec_date and _period_overlaps_weekend(rec_date, start_t, end_t):
                    weekend_applied = True

            # If no periods but record has clock_in/clock_out fields separately
            if not parsed_periods:
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
            
        except Exception as e:
            logger.error("Error processing record", error=str(e), error_type=type(e).__name__)
            continue

    report = SalaryReport(month=month, year=year, days=days_breakdown, total=round(total_sum, 2))
    return report
