# -*- coding: utf-8 -*-
"""
קובץ הגדרות מרכזי של הפרויקט (Config).
טוען משתני סביבה מ-.env ומגדיר קבועים לשימוש בכל המודולים.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# טען .env אם קיים
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=str(ENV_PATH))

# נתיב לקבצים (נתוני cache וכו')
DATA_DIR = os.getenv("DATA_DIR", os.path.join(str(BASE_DIR), "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# YLM credentials - אין לקודד סיסמאות בקוד
YLM_USERNAME = os.getenv("YLM_USERNAME")
YLM_PASSWORD = os.getenv("YLM_PASSWORD")


def get_credentials():
    """
    מחזיר קרדנצ'לים ומוודא שהם קיימים.
    זורק ValueError אם לא הוגדרו - ה-scraper צריך לקרוא לפונקציה זו.
    """
    if not YLM_USERNAME or not YLM_PASSWORD:
        raise ValueError(
            "Missing YLM credentials: set YLM_USERNAME and YLM_PASSWORD in .env"
        )
    return YLM_USERNAME, YLM_PASSWORD


# שיעורי שכר
RATE_REGULAR = float(os.getenv("RATE_REGULAR", "75.0"))  # ₪ לשעה רגילה
RATE_125 = float(os.getenv("RATE_125", str(RATE_REGULAR * 1.25)))  # 125%
RATE_150 = float(os.getenv("RATE_150", str(RATE_REGULAR * 1.5)))  # 150%

# גבולות שעות (בשעות)
REGULAR_LIMIT = int(os.getenv("REGULAR_LIMIT", "8"))  # עד 8 שעות רגילות
LIMIT_125 = int(os.getenv("LIMIT_125", "10"))  # 8-10 => 125%, מעל 10 => 150%

# פרמיית סוף שבוע: תקופה ספציפית (שישי 17:00 עד ראשון 05:00)
# שינוי לפי בקשתך: סופ"ש מוגדר מ-שישי 17:00 עד ראשון 05:00 (כולל כל השבת).
WEEKEND_PREMIUM_START = {"weekday": 4, "hour": 17, "minute": 0}  # Friday 17:00 (weekday=4)
WEEKEND_PREMIUM_END = {"weekday": 6, "hour": 5, "minute": 0}  # Sunday 05:00 (weekday=6)

# Selenium / Scraper settings
SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() in (
    "1",
    "true",
    "yes",
)
SELENIUM_TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "15"))
SCRAPER_RETRIES = int(os.getenv("SCRAPER_RETRIES", "3"))
SCRAPER_RETRY_BACKOFF = float(os.getenv("SCRAPER_RETRY_BACKOFF", "1.5"))

# Flask / deployment
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

# CORS - ברירת מחדל מוגבלת; ניתן להעביר כמה origins מופרדים בפסיק
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5000")

# קבצים שבהם נשמרים נתונים
SALARY_JSON_PATH = os.path.join(DATA_DIR, "salary_data.json")
