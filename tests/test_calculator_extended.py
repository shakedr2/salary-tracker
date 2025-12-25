# -*- coding: utf-8 -*-
"""
Extended unit tests for SalaryCalculator - Edge cases and comprehensive testing.
"""
import pytest
from datetime import date, time as dt_time
from backend.calculator import (
    SalaryCalculator,
    AttendanceRecord,
    _parse_time_str,
    _period_duration_hours,
    _allocate_hours,
    _period_overlaps_weekend,
    CalculationError
)
from backend.config import RATE_REGULAR, RATE_125, RATE_150, REGULAR_LIMIT, LIMIT_125


class TestTimeParsing:
    """Test time parsing functions."""
    
    def test_parse_valid_time(self):
        """Test parsing valid time strings."""
        assert _parse_time_str("09:00") == dt_time(9, 0)
        assert _parse_time_str("17:30") == dt_time(17, 30)
        assert _parse_time_str("23:59") == dt_time(23, 59)
    
    def test_parse_invalid_time(self):
        """Test parsing invalid time strings."""
        assert _parse_time_str("") is None
        assert _parse_time_str("invalid") is None
        assert _parse_time_str("25:00") is None  # Invalid hour
        assert _parse_time_str("12:60") is None  # Invalid minute
    
    def test_parse_edge_cases(self):
        """Test edge cases in time parsing."""
        assert _parse_time_str("9:5") == dt_time(9, 5)  # Single digit minute
        assert _parse_time_str("  09:00  ") == dt_time(9, 0)  # Whitespace


class TestPeriodDuration:
    """Test period duration calculation."""
    
    def test_normal_period(self):
        """Test normal period (same day)."""
        assert _period_duration_hours(dt_time(9, 0), dt_time(17, 0)) == 8.0
        assert _period_duration_hours(dt_time(8, 30), dt_time(16, 30)) == 8.0
    
    def test_cross_midnight(self):
        """Test period crossing midnight."""
        # 22:00 to 06:00 = 8 hours
        assert _period_duration_hours(dt_time(22, 0), dt_time(6, 0)) == 8.0
        # 23:00 to 01:00 = 2 hours
        assert _period_duration_hours(dt_time(23, 0), dt_time(1, 0)) == 2.0


class TestHourAllocation:
    """Test hour allocation logic."""
    
    def test_regular_hours_only(self):
        """Test allocation for regular hours only."""
        regular, ot125, ot150 = _allocate_hours(8.0)
        assert regular == 8.0
        assert ot125 == 0.0
        assert ot150 == 0.0
    
    def test_with_overtime_125(self):
        """Test allocation with 125% overtime."""
        regular, ot125, ot150 = _allocate_hours(9.0)
        assert regular == REGULAR_LIMIT
        assert ot125 == 1.0
        assert ot150 == 0.0
    
    def test_with_overtime_150(self):
        """Test allocation with 150% overtime."""
        regular, ot125, ot150 = _allocate_hours(12.0)
        assert regular == REGULAR_LIMIT
        assert ot125 == (LIMIT_125 - REGULAR_LIMIT)
        assert ot150 > 0.0
    
    def test_negative_hours(self):
        """Test handling of negative hours."""
        regular, ot125, ot150 = _allocate_hours(-5.0)
        assert regular == 0.0
        assert ot125 == 0.0
        assert ot150 == 0.0


class TestWeekendOverlap:
    """Test weekend premium overlap detection."""
    
    def test_friday_evening(self):
        """Test Friday evening (should overlap)."""
        # Friday 18:00-20:00 should overlap
        friday = date(2025, 1, 3)  # Friday
        assert _period_overlaps_weekend(friday, dt_time(18, 0), dt_time(20, 0)) is True
    
    def test_saturday(self):
        """Test Saturday (should overlap)."""
        saturday = date(2025, 1, 4)  # Saturday
        assert _period_overlaps_weekend(saturday, dt_time(10, 0), dt_time(18, 0)) is True
    
    def test_sunday_morning(self):
        """Test Sunday morning (should overlap)."""
        sunday = date(2025, 1, 5)  # Sunday
        assert _period_overlaps_weekend(sunday, dt_time(2, 0), dt_time(4, 0)) is True
    
    def test_monday(self):
        """Test Monday (should not overlap)."""
        monday = date(2025, 1, 6)  # Monday
        assert _period_overlaps_weekend(monday, dt_time(9, 0), dt_time(17, 0)) is False


class TestSalaryCalculator:
    """Test SalaryCalculator class."""
    
    def test_empty_records(self):
        """Test calculation with empty records."""
        calculator = SalaryCalculator()
        with pytest.raises(CalculationError):
            calculator.calculate_salary([])
    
    def test_basic_calculation(self):
        """Test basic salary calculation."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": [("09:00", "17:00")]
            }
        ]
        report = calculator.calculate_salary(records)
        assert report is not None
        assert report.days[0].regular_hours == 8.0
        assert report.days[0].day_total == 8.0 * RATE_REGULAR
    
    def test_overtime_calculation(self):
        """Test overtime calculation."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": [("09:00", "20:00")]  # 11 hours
            }
        ]
        report = calculator.calculate_salary(records)
        day = report.days[0]
        assert day.regular_hours == REGULAR_LIMIT
        assert day.overtime_125_hours > 0
        assert day.overtime_150_hours > 0
        assert day.day_total > 8.0 * RATE_REGULAR
    
    def test_weekend_premium(self):
        """Test weekend premium application."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-04",  # Saturday
                "periods": [("10:00", "18:00")]
            }
        ]
        report = calculator.calculate_salary(records)
        day = report.days[0]
        assert day.weekend_premium_applied is True
        # All hours should be at 150% rate
        assert day.overtime_150_hours == 8.0
        assert day.day_total == 8.0 * RATE_150
    
    def test_multiple_periods(self):
        """Test calculation with multiple periods in one day."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": [("09:00", "12:00"), ("13:00", "17:00")]  # 7 hours total
            }
        ]
        report = calculator.calculate_salary(records)
        day = report.days[0]
        assert day.regular_hours == 7.0
        total_hours = day.regular_hours + day.overtime_125_hours + day.overtime_150_hours
        assert total_hours == 7.0
    
    def test_cross_midnight_period(self):
        """Test period that crosses midnight."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": [("22:00", "06:00")]  # 8 hours crossing midnight
            }
        ]
        report = calculator.calculate_salary(records)
        day = report.days[0]
        assert day.regular_hours == 8.0
    
    def test_invalid_time_format(self):
        """Test handling of invalid time formats."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": [("invalid", "17:00")]
            }
        ]
        report = calculator.calculate_salary(records)
        # Should skip invalid periods
        day = report.days[0]
        assert day.day_total == 0.0
    
    def test_multiple_days(self):
        """Test calculation for multiple days."""
        calculator = SalaryCalculator()
        records = [
            {"date": "2025-01-15", "periods": [("09:00", "17:00")]},
            {"date": "2025-01-16", "periods": [("09:00", "17:00")]},
            {"date": "2025-01-17", "periods": [("09:00", "17:00")]},
        ]
        report = calculator.calculate_salary(records)
        assert len(report.days) == 3
        assert report.total == 3 * 8.0 * RATE_REGULAR
    
    def test_edge_case_zero_hours(self):
        """Test edge case with zero hours."""
        calculator = SalaryCalculator()
        records = [
            {
                "date": "2025-01-15",
                "periods": []
            }
        ]
        report = calculator.calculate_salary(records)
        day = report.days[0]
        assert day.day_total == 0.0
        assert day.regular_hours == 0.0


if __name__ == '__main__':
    pytest.main([__file__, "-v"])

