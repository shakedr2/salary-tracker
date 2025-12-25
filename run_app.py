#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט הפעלה מהיר
Quick startup script
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app
from backend.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 YLM Salary Tracker")
    print("=" * 50)
    print(f"📊 Server starting on: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"💡 Make sure to fill in YLM_USERNAME and YLM_PASSWORD in .env file")
    print("=" * 50)
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

