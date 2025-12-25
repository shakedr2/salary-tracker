# -*- coding: utf-8 -*-
"""
Flask API Server - משרת API עבור YLM Salary Tracker.

מספק endpoints:
- /api/refresh: מפעיל את ה-scraper ומחשב שכר
- /api/salary: מחזיר את נתוני השכר המחושבים
- /api/health: endpoint לבדיקת בריאות השרת
"""
import json
import logging
import os
import tempfile
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import (
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
    CORS_ORIGINS,
    SALARY_JSON_PATH,
)
from .scraper import YLMScraper
from .calculator import SalaryCalculator

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# CORS - מאפשר גישה מכתובות מורשות בלבד
allowed_origins = [o.strip() for o in CORS_ORIGINS.split(',')]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def atomic_write_json(data: dict, filepath: str) -> None:
    """כתיבה אטומית של JSON - מונע קורפשן של הקובץ."""
    dir_name = os.path.dirname(filepath)
    with tempfile.NamedTemporaryFile(
        mode='w', dir=dir_name, delete=False, suffix='.tmp'
    ) as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        temp_name = tf.name
    os.replace(temp_name, filepath)
    logger.info(f"Atomic write completed: {filepath}")


@app.route('/')
def index():
    """משרת את דף ה-HTML הראשי."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint לבדיקת בריאות השרת."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route('/api/salary', methods=['GET'])
def get_salary():
    """מחזיר את נתוני השכר האחרונים (אם קיימים)."""
    try:
        if not os.path.exists(SALARY_JSON_PATH):
            return jsonify({"error": "No salary data found. Please refresh first."}), 404
        
        with open(SALARY_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error reading salary data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/refresh', methods=['POST'])
def refresh_salary():
    """מפעיל את ה-scraper ומחשב שכר."""
    try:
        logger.info("Starting scrape and calculation...")
        
        # רצת scraper
        scraper = YLMScraper()
        attendance_records = scraper.scrape_attendance()
        
        if not attendance_records:
            return jsonify({"error": "No attendance records found"}), 404
        
        # חישוב שכר
        calculator = SalaryCalculator()
        salary_report = calculator.calculate_salary(attendance_records)
        
        # הכנת response
        response_data = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "report": {
                "month": salary_report.month,
                "year": salary_report.year,
                "days_worked": len(salary_report.days),
                "total_salary": sum(d.day_total for d in salary_report.days),
                "days_breakdown": [
                    {
                        "date": str(d.date),
                        "regular_hours": d.regular_hours,
                        "overtime_125_hours": d.overtime_125_hours,
                        "overtime_150_hours": d.overtime_150_hours,
                        "weekend_premium_applied": d.weekend_premium_applied,
                        "day_total": d.day_total,
                    }
                    for d in salary_report.days
                ],
            },
        }
        
        # שמירה אטומית
        atomic_write_json(response_data, SALARY_JSON_PATH)
        
        logger.info("Scrape and calculation completed successfully")
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error during refresh: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
