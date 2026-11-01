#!/usr/bin/env bash
set -e

echo "======================================================="
echo "    DZ Subtitles AI - Algerian Darija Generator"
echo "  Auto-transcribe & animate subtitles with Gemini AI"
echo "======================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    exit 1
fi

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] FFmpeg is not installed! Install with: sudo apt install ffmpeg (Ubuntu) or brew install ffmpeg (macOS)"
fi

echo "[1/3] Installing dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo "[2/3] Starting web server..."
python3 server.py
