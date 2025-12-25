# -*- coding: utf-8 -*-
"""
Basic unit tests for SalaryCalculator.
"""
import pytest
from datetime import datetime, date, time as dt_time
from backend.calculator import SalaryCalculator, AttendanceRecord


def test_calculator_basic():
    """Test basic salary calculation."""
    calculator = SalaryCalculator()
    
    # Create sample attendance record
    records = [
        AttendanceRecord(
            date=date(2025, 12, 25),
            clock_in='09:00',
            clock_out='17:00',
            periods=[('09:00', '17:00')],
            raw={'date': '2025-12-25'}
        )
    ]
    
    report = calculator.calculate_salary(records)
    
    assert report is not None
    assert report.year == 2025
    assert report.month == 12
    assert len(report.days) == 1
    assert report.days[0].regular_hours == 8.0


def test_calculator_overtime():
    """Test overtime calculation."""
    calculator = SalaryCalculator()
    
    records = [
        AttendanceRecord(
            date=date(2025, 12, 25),
            clock_in='09:00',
            clock_out='20:00',
            periods=[('09:00', '20:00')],
            raw={'date': '2025-12-25'}
        )
    ]
    
    report = calculator.calculate_salary(records)
    
    assert report.days[0].overtime_125_hours > 0


if __name__ == '__main__':
    pytest.main([__file__])
