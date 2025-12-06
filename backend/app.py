#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import logging

from .config import Config
from .scraper import YLMScraper
from .calculator import SalaryCalculator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

config = Config()

# יצירת תיקיית data אם לא קיימת
os.makedirs(config.DATA_DIR, exist_ok=True)


@app.route('/')
def index():
    """דף הבית"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/salary')
def get_salary():
    """קבלת נתוני שכר"""
    try:
        # בדוק אם יש נתונים שמורים
        if os.path.exists(config.SALARY_DATA_FILE):
            with open(config.SALARY_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({"error": "No data available. Please refresh first."}), 404

    except Exception as e:
        logger.error(f"Error reading salary data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """רענון נתונים מהמערכת"""
    try:
        logger.info("🔄 Starting data refresh...")

        # הרץ scraper
        scraper = YLMScraper()
        attendance_data = scraper.run()

        if not attendance_data:
            return jsonify({"error": "Failed to scrape data"}), 500

        # חשב שכר
        calculator = SalaryCalculator()
        salary_report = calculator.calculate(attendance_data)

        # שמור לקובץ
        with open(config.SALARY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(salary_report.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info("✅ Data refreshed successfully")
        return jsonify(salary_report.to_dict())

    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health():
    """בדיקת תקינות"""
    return jsonify({"status": "healthy", "message": "API is running"})


if __name__ == '__main__':
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
