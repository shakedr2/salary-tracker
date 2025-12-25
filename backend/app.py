# -*- coding: utf-8 -*-
"""
Flask API Server - משרת API עבור YLM Salary Tracker.

מספק endpoints:
- /api/refresh: מפעיל את ה-scraper ומחשב שכר
- /api/salary: מחזיר את נתוני השכר המחושבים
- /api/health: endpoint לבדיקת בריאות השרת
- /api/metrics: מחזיר מטריקות של האפליקציה
"""
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Union
from flask import Flask, jsonify, send_from_directory, request, Response
from flask_cors import CORS

from .config import (
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
    CORS_ORIGINS,
    SALARY_JSON_PATH,
)
from .scraper import YLMScraper, ScraperError
from .calculator import SalaryCalculator
from .observability import (
    get_structured_logger,
    get_metrics,
    time_operation,
    monitor_performance
)

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# CORS - מאפשר גישה מכתובות מורשות בלבד
allowed_origins = [o.strip() for o in CORS_ORIGINS.split(',')]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Structured logger for CloudWatch
logger = get_structured_logger(__name__)
metrics = get_metrics()


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
def index() -> Union[Response, Tuple[Response, int]]:
    """משרת את דף ה-HTML הראשי."""
    if app.static_folder:
        return send_from_directory(app.static_folder, 'index.html')
    return jsonify({"error": "Static folder not configured"}), 500


@app.route('/api/health', methods=['GET'])
def health() -> Tuple[Union[Response, Dict[str, Any]], int]:
    """Endpoint לבדיקת בריאות השרת."""
    try:
        metrics.record_api_request("/api/health", success=True)
        metrics.update_health("healthy")
        
        health_data = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": metrics.metrics["health"]["uptime_seconds"],
            "version": "1.0.0"
        }
        
        logger.info("Health check", endpoint="/api/health", status="ok")
        return jsonify(health_data), 200
    except Exception as e:
        logger.error("Health check failed", endpoint="/api/health", error=str(e))
        metrics.record_api_request("/api/health", success=False)
        metrics.update_health("unhealthy")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/salary', methods=['GET'])
@monitor_performance("get_salary")
def get_salary() -> Tuple[Union[Response, Dict[str, Any]], int]:
    """מחזיר את נתוני השכר האחרונים (אם קיימים)."""
    try:
        logger.info("Salary data request", endpoint="/api/salary")
        
        if not os.path.exists(SALARY_JSON_PATH):
            logger.warning("Salary data not found", endpoint="/api/salary")
            metrics.record_api_request("/api/salary", success=False)
            return jsonify({
                "error": "No salary data found. Please refresh first.",
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        with open(SALARY_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metrics.record_api_request("/api/salary", success=True)
        logger.info("Salary data retrieved", endpoint="/api/salary", records_count=len(data.get("report", {}).get("days_breakdown", [])))
        return jsonify(data), 200
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in salary data", endpoint="/api/salary", error=str(e))
        metrics.record_api_request("/api/salary", success=False)
        return jsonify({
            "error": "Corrupted salary data file",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    except Exception as e:
        logger.error("Error reading salary data", endpoint="/api/salary", error=str(e), error_type=type(e).__name__)
        metrics.record_api_request("/api/salary", success=False)
        return jsonify({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/refresh', methods=['POST'])
@monitor_performance("refresh_salary")
def refresh_salary() -> Tuple[Union[Response, Dict[str, Any]], int]:
    """מפעיל את ה-scraper ומחשב שכר."""
    scrape_start_time = time.time()
    
    try:
        logger.info("Starting salary refresh", endpoint="/api/refresh")
        
        # רצת scraper
        with time_operation("scraping", logger):
            scraper = YLMScraper()
            attendance_records = scraper.scrape_attendance()
        
        scrape_duration = time.time() - scrape_start_time
        
        if not attendance_records:
            logger.warning("No attendance records found", endpoint="/api/refresh")
            metrics.record_scraping(scrape_duration, 0, success=False)
            metrics.record_api_request("/api/refresh", success=False)
            return jsonify({
                "error": "No attendance records found",
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        metrics.record_scraping(scrape_duration, len(attendance_records), success=True)
        logger.info("Scraping completed", endpoint="/api/refresh", records_count=len(attendance_records))
        
        # חישוב שכר
        with time_operation("calculation", logger):
            calculator = SalaryCalculator()
            # Type cast for type checker - attendance_records is List[Dict[str, Any]]
            salary_report = calculator.calculate_salary(attendance_records)  # type: ignore
        
        total_salary = sum(d.day_total for d in salary_report.days)
        metrics.record_calculation(len(salary_report.days), total_salary)
        
        # הכנת response
        response_data = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "report": {
                "month": salary_report.month,
                "year": salary_report.year,
                "days_worked": len(salary_report.days),
                "total_salary": total_salary,
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
        
        logger.info(
            "Salary refresh completed",
            endpoint="/api/refresh",
            days_processed=len(salary_report.days),
            total_salary=total_salary
        )
        metrics.record_api_request("/api/refresh", success=True)
        return jsonify(response_data), 200
    
    except ScraperError as e:
        scrape_duration = time.time() - scrape_start_time
        logger.error(
            "Scraper error during refresh",
            endpoint="/api/refresh",
            error=str(e),
            error_type="ScraperError"
        )
        metrics.record_scraping(scrape_duration, 0, success=False)
        metrics.record_api_request("/api/refresh", success=False)
        return jsonify({
            "error": f"Scraping failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    except Exception as e:
        scrape_duration = time.time() - scrape_start_time
        logger.error(
            "Error during refresh",
            endpoint="/api/refresh",
            error=str(e),
            error_type=type(e).__name__
        )
        metrics.record_scraping(scrape_duration, 0, success=False)
        metrics.record_api_request("/api/refresh", success=False)
        return jsonify({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics_endpoint() -> Tuple[Union[Response, Dict[str, Any]], int]:
    """מחזיר מטריקות של האפליקציה."""
    try:
        metrics_data = metrics.get_metrics()
        logger.info("Metrics requested", endpoint="/api/metrics")
        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error("Error getting metrics", endpoint="/api/metrics", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error: Any) -> Tuple[Union[Response, Dict[str, Any]], int]:
    """Handle 404 errors."""
    logger.warning("404 Not Found", path=request.path, method=request.method)
    return jsonify({
        "error": "Endpoint not found",
        "path": request.path,
        "timestamp": datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error: Any) -> Tuple[Union[Response, Dict[str, Any]], int]:
    """Handle 500 errors."""
    logger.error("Internal server error", error=str(error))
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }), 500


if __name__ == '__main__':
    logger.info("Starting Flask application", host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
