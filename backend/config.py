#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
קובץ הגדרות למערכת
"""
import os


class Config:
    """הגדרות כלליות"""

    # פרטי התחברות YLM
    YLM_USERNAME = "209368927"
    YLM_PASSWORD = "209368927"
    YLM_URL = "https://ins.ylm.co.il"

    # הגדרות שכר
    HOURLY_RATE = 75
    RATE_REGULAR = 75
    RATE_OVERTIME_125 = 93.75  # 75 * 1.25
    RATE_OVERTIME_150 = 112.5  # 75 * 1.5

    # הגדרות סופש (שישי 17:00 - שבת 05:00)
    WEEKEND_START_DAY = 4  # שישי (0=ראשון)
    WEEKEND_START_HOUR = 17  # 17:00
    WEEKEND_END_DAY = 5  # שבת
    WEEKEND_END_HOUR = 5  # 05:00

    # הגדרות שעות נוספות
    REGULAR_HOURS_LIMIT = 8  # 8 שעות רגילות
    OVERTIME_125_LIMIT = 2  # 2 שעות ב-125%

    # הגדרות Selenium
    SELENIUM_HEADLESS = True
    SELENIUM_TIMEOUT = 15

    # הגדרות Flask
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    FLASK_DEBUG = True

    # נתיבי קבצים
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    SALARY_DATA_FILE = os.path.join(DATA_DIR, 'salary_data.json')
