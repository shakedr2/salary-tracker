@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 YLM Salary Tracker
echo ========================================
echo.

cd /d "%~dp0"
python run_app.py

pause

