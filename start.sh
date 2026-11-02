#!/usr/bin/env bash
set -e

echo "======================================================="
echo "    DZ Subtitles AI - Algerian Darija Generator"
echo "  Auto-transcribe & animate subtitles with Gemini AI"
echo "======================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/ or via your package manager."
    exit 1
fi

# 2. Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] FFmpeg is not installed!"
    echo "FFmpeg is required for video and audio rendering."
    echo "Install with:"
    echo "  macOS (Homebrew): brew install ffmpeg"
    echo "  Ubuntu/Debian:    sudo apt update && sudo apt install -y ffmpeg"
    echo "  Arch Linux:       sudo pacman -S ffmpeg"
    echo ""
fi

# 3. Install dependencies
echo "[1/3] Checking and installing Python dependencies..."
python3 -m pip install -r requirements.txt --quiet

# 4. Open browser in background
echo "[2/3] Launching Web UI at http://localhost:8000 ..."
if command -v open &> /dev/null; then
    (sleep 1 && open "http://localhost:8000") &
elif command -v xdg-open &> /dev/null; then
    (sleep 1 && xdg-open "http://localhost:8000") &
fi

# 5. Start server
echo "[3/3] Server running on http://localhost:8000"
echo "Press Ctrl+C to stop the server."
echo "======================================================="
python3 server.py
