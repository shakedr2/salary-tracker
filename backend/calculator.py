#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מנוע חישוב שכר
"""
from datetime import datetime
from typing import List, Dict
import logging

from .config import Config
from .models import AttendanceRecord, DaySalaryBreakdown, SalaryReport

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SalaryCalculator:
    """מחשבון שכר"""

    def __init__(self):
        self.config = Config()

    def _parse_time(self, time_str: str) -> float:
        """המרת מחרוזת זמן לשעות"""
        time_str = time_str.strip().replace(" ", "")
        if ":" not in time_str:
            return 0.0

        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours + minutes / 60
        except:
            return 0.0

    def _is_weekend_shift(self, date_str: str, entry_time: str) -> bool:
        """
        בדיקה אם המשמרת בסופש
        שישי מ-17:00 עד שבת 05:00 = 150% על כל השעות
        """
        try:
            day, month, year = map(int, date_str.split("/"))
            date = datetime(year, month, day)
            day_of_week = date.weekday()

            entry_hour = self._parse_time(entry_time)

            if day_of_week == self.config.WEEKEND_START_DAY:
                if entry_hour >= self.config.WEEKEND_START_HOUR:
                    return True

            if day_of_week == self.config.WEEKEND_END_DAY:
                if entry_hour < self.config.WEEKEND_END_HOUR:
                    return True

        except Exception as e:
            logger.warning(f"⚠️ Failed to check weekend: {e}")

        return False

    def _calculate_day_salary(self, total_hours: float, is_weekend: bool = False) -> Dict[str, float]:
        """
        חישוב שכר ליום אחד

        כללים:
        - סופש: כל השעות ב-150%
        - יום רגיל:
          * 8 שעות ראשונות: 75₪
          * שעות 9-10: 93.75₪ (125%)
          * שעה 11+: 112.5₪ (150%)
        """
        if is_weekend:
            return {
                "regular": 0.0,
                "overtime_125": 0.0,
                "overtime_150": total_hours,
                "salary": total_hours * self.config.RATE_OVERTIME_150
            }

        regular_hours = min(self.config.REGULAR_HOURS_LIMIT, total_hours)
        remaining = max(0, total_hours - self.config.REGULAR_HOURS_LIMIT)

        overtime_125 = min(self.config.OVERTIME_125_LIMIT, remaining)
        remaining = max(0, remaining - self.config.OVERTIME_125_LIMIT)

        overtime_150 = remaining

        salary = (
                regular_hours * self.config.RATE_REGULAR +
                overtime_125 * self.config.RATE_OVERTIME_125 +
                overtime_150 * self.config.RATE_OVERTIME_150
        )

        return {
            "regular": regular_hours,
            "overtime_125": overtime_125,
            "overtime_150": overtime_150,
            "salary": salary
        }

    def calculate(self, attendance_data: List[AttendanceRecord]) -> SalaryReport:
        """חישוב שכר כולל"""
        logger.info("💰 Calculating salary...")

        total_salary = 0.0
        total_regular = 0.0
        total_125 = 0.0
        total_150 = 0.0
        breakdown = []

        for record in attendance_data:
            total_hours = self._parse_time(record.total_hours)
            is_weekend = self._is_weekend_shift(record.date, record.entry)

            day_calc = self._calculate_day_salary(total_hours, is_weekend)

            total_salary += day_calc["salary"]
            total_regular += day_calc["regular"]
            total_125 += day_calc["overtime_125"]
            total_150 += day_calc["overtime_150"]

            weekend_tag = " 🎉 (סופש)" if is_weekend else ""
            logger.info(f"  {record.date}: {day_calc['salary']:.2f} ₪{weekend_tag}")

            day_breakdown = DaySalaryBreakdown(
                date=record.date,
                day=record.day,
                site=record.site,
                entry=record.entry,
                exit=record.exit,
                hours=total_hours,
                regular_hours=day_calc["regular"],
                overtime_125_hours=day_calc["overtime_125"],
                overtime_150_hours=day_calc["overtime_150"],
                salary=day_calc["salary"],
                is_weekend=is_weekend
            )
            breakdown.append(day_breakdown.to_dict())

        report = SalaryReport(
            total_salary=round(total_salary, 2),
            total_hours=round(total_regular + total_125 + total_150, 2),
            regular_hours=round(total_regular, 2),
            overtime_125_hours=round(total_125, 2),
            overtime_150_hours=round(total_150, 2),
            breakdown=breakdown,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"\n{'=' * 50}")
        logger.info(f"💵 סה\"כ שכר ברוטו: {report.total_salary:.2f} ₪")
        logger.info(f"⏱️ סה\"כ שעות: {report.total_hours:.2f}")
        logger.info(f"   • רגילות (75₪): {report.regular_hours:.2f}")
        logger.info(f"   • נוספות 125%: {report.overtime_125_hours:.2f}")
        logger.info(f"   • נוספות 150%: {report.overtime_150_hours:.2f}")
        logger.info(f"{'=' * 50}\n")

        return report
