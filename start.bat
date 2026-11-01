@echo off
title DZ Subtitles AI - Algerian Darija Generator
color 0B

echo =======================================================
echo     DZ Subtitles AI - Algerian Darija Generator
echo   Auto-transcribe ^& animate subtitles with Gemini AI
echo =======================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg was not detected in PATH!
    echo FFmpeg is required for video and audio rendering.
    echo Please download FFmpeg from https://ffmpeg.org/download.html and add it to PATH.
    echo.
)

echo [1/3] Checking dependencies...
python -m pip install -r requirements.txt --quiet

echo [2/3] Starting web server on http://localhost:8000 ...
start "" "http://localhost:8000"

echo [3/3] Server running! Press Ctrl+C to stop.
python server.py

pause
