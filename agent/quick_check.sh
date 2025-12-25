#!/bin/bash
# -*- coding: utf-8 -*-
# בדיקה מהירה
# Quick check script

set -e

echo "🔍 Running quick checks..."

cd "$(dirname "$0")/.."

# Python syntax check
echo "✓ Checking Python syntax..."
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "*/__pycache__/*" -exec python -m py_compile {} \; 2>&1 | head -20

# Import check
echo "✓ Checking imports..."
python -c "from backend import app, calculator, scraper, config" 2>&1 || echo "⚠ Import check failed"

# Requirements check
echo "✓ Checking requirements..."
python -m pip check 2>&1 | head -10 || echo "⚠ Requirements check incomplete"

# Test count
echo "✓ Counting tests..."
python -m pytest tests/ --collect-only -q 2>&1 | tail -5 || echo "⚠ Test collection failed"

echo ""
echo "✅ Quick checks completed!"
echo "Run 'python agent/main_agent.py' for full analysis"

