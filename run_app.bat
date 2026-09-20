@echo off
title NetraScreen - Diabetic Retinopathy Screener
cd /d "%~dp0"
echo ================================================================
echo    NetraScreen: AI Diabetic Retinopathy Screening Assistant
echo ================================================================
echo.
echo Activating virtual environment (.venv)...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate .venv. Please check your Python 3.11 setup.
    pause
    exit /b 1
)

echo Starting screening server on http://localhost:7860 ...
echo (Opening browser in 3 seconds...)
start "" "http://localhost:7860"

python app.py
pause
