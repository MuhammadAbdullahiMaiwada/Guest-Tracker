@echo off
echo ============================================
echo   Guest Tracker - Setup
echo ============================================

echo.
echo [1/3] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment. Is Python installed?
    pause
    exit /b 1
)

echo [2/3] Activating and installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/3] Starting app...
echo.
echo Default admin credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo Open http://localhost:5000 in your browser.
echo.
python app.py

pause
