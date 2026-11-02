@echo off
setlocal enabledelayedexpansion
title Darija Subtitles Generator
color 0b

echo ===============================================================================
echo                DARIJA SUBTITLES GENERATOR - 1-CLICK LAUNCHER
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not found in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and install dependencies
echo [*] Checking and installing required packages...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [!] Pip install returned a warning, continuing startup...
)

:: 3. Check FFmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg was not detected in PATH.
    echo For video rendering, please ensure FFmpeg is installed or download it from:
    echo https://ffmpeg.org/download.html
    echo.
)

:: 4. Launch browser after 1.5 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: 5. Start Server
echo [*] Starting server on http://localhost:8000 ...
echo [*] Ready! Opening your web browser automatically.
echo [*] Press CTRL+C in this window anytime to stop the server.
echo ===============================================================================
echo.

python server.py

pause
