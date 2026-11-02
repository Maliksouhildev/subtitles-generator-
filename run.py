#!/usr/bin/env python3
"""
Universal 1-Click Python Launcher for Darija Subtitles Generator.
Runs on Windows, macOS, and Linux without Docker or complex setup.
Usage: python run.py
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading

def check_and_install_dependencies():
    """Ensure all required dependencies are installed automatically."""
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        return

    try:
        import fastapi
        import uvicorn
        import requests
        import pydantic
    except ImportError:
        print("[*] Installing required lightweight packages from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"])

def check_ffmpeg():
    """Check if ffmpeg is available in system PATH."""
    import shutil
    if not shutil.which("ffmpeg"):
        print("[WARNING] FFmpeg is not detected in your PATH.")
        print("          Video burning requires FFmpeg. Download from https://ffmpeg.org/download.html")

def open_browser_delayed(url="http://localhost:8000"):
    """Open default browser once server is running."""
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    print("=" * 65)
    print("        DARIJA SUBTITLES GENERATOR - 1-CLICK LAUNCHER")
    print("=" * 65)

    check_and_install_dependencies()
    check_ffmpeg()

    print("[*] Starting local server on http://localhost:8000 ...")
    print("[*] Opening your web browser automatically...")
    print("[*] Press CTRL+C to stop the server anytime.")
    print("=" * 65)

    threading.Thread(target=open_browser_delayed, daemon=True).start()

    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
