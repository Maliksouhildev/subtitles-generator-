@echo off
title DZ Subtitles AI - Algerian Darija Generator
color 0B

echo =======================================================
echo     DZ Subtitles AI - Algerian Darija Generator
echo   Auto-transcribe ^& animate subtitles with Gemini AI
echo =======================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo.
    echo 1. Download Python 3.10+ from: https://www.python.org/downloads/
    echo 2. IMPORTANT: Check the box "Add python.exe to PATH" during installation!
    echo 3. Re-run start.bat once installed.
    echo.
    pause
    exit /b 1
)

:: 2. Check FFmpeg installation (attempt automated install if missing)
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg was not detected in your PATH!
    echo FFmpeg is required for burning animated subtitles and processing video/audio.
    echo.
    where winget >nul 2>nul
    if %errorlevel% equ 0 (
        echo Attempting automatic installation via Windows Package Manager (winget)...
        winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
        echo.
        echo [NOTE] If FFmpeg was just installed, please close this window and double-click start.bat again!
    ) else (
        echo Please download FFmpeg from: https://ffmpeg.org/download.html or install via winget.
    )
    echo.
)

:: 3. Install required Python packages
echo [1/3] Checking and installing Python dependencies...
python -m pip install -r requirements.txt --quiet

:: 4. Launch browser automatically
echo [2/3] Launching Web UI at http://localhost:8000 ...
start "" "http://localhost:8000"

:: 5. Start web server
echo [3/3] Server running on http://localhost:8000
echo - Open your browser to http://localhost:8000 if it did not open automatically.
echo - Enter your free Gemini API Key in the settings panel (saved automatically!).
echo - Press Ctrl+C in this window anytime to stop the server.
echo =======================================================
echo.
python server.py

pause
