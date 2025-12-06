#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מודלים לנתונים
"""
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class AttendanceRecord:
    """רשומת נוכחות יומית"""
    day: str
    date: str
    site: str
    entry: str
    exit: str
    total_hours: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DaySalaryBreakdown:
    """פירוט שכר יומי"""
    date: str
    day: str
    site: str
    entry: str
    exit: str
    hours: float
    regular_hours: float
    overtime_125_hours: float
    overtime_150_hours: float
    salary: float
    is_weekend: bool

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SalaryReport:
    """דוח שכר מלא"""
    total_salary: float
    total_hours: float
    regular_hours: float
    overtime_125_hours: float
    overtime_150_hours: float
    breakdown: List[Dict]
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            "total_salary": self.total_salary,
            "total_hours": self.total_hours,
            "regular_hours": self.regular_hours,
            "overtime_125_hours": self.overtime_125_hours,
            "overtime_150_hours": self.overtime_150_hours,
            "breakdown": self.breakdown,
            "timestamp": self.timestamp
        }
