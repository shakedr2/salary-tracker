#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
קובץ הפעלה מהירה
"""
import sys
import os

# הוסף את התיקייה הנוכחית ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app, config

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 YLM Salary Tracker")
    print("=" * 50)
    print(f"📊 Server: http://localhost:{config.FLASK_PORT}")
    print(f"💰 User: {config.YLM_USERNAME}")
    print("=" * 50)
    print("\nלחץ Ctrl+C לעצירה\n")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
