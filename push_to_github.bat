@echo off
chcp 65001 >nul
echo ========================================
echo Pushing to GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Git status...
git status --short | findstr /V ".vscode .wdm venv __pycache__" | findstr /V ".git" | head -20

echo.
echo Adding files...
git add backend/ frontend/ tests/ infra/ agent/ docs/ .github/ *.py *.md *.txt *.bat *.yml Dockerfile docker-compose.yml .gitignore 2>nul

echo.
echo Committing...
git commit -m "Major improvements: Add automated agent, observability, tests, CI/CD, and authentication" 2>nul

if errorlevel 1 (
    echo No changes to commit or commit failed
) else (
    echo Commit successful!
)

echo.
echo Setting branch to main...
git branch -M main 2>nul

echo.
echo Adding remote (if not exists)...
git remote remove origin 2>nul
git remote add origin https://github.com/shakedr2/salary-tracker.git 2>nul

echo.
echo Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed. You may need to:
    echo 1. Set up GitHub credentials
    echo 2. Or use: git push -u origin main --force
) else (
    echo.
    echo ========================================
    echo Successfully pushed to GitHub!
    echo ========================================
)

pause

