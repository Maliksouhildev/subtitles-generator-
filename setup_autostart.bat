@echo off
title DZ Subtitles AI - Auto-Start Setup
cd /d "%~dp0"
echo =======================================================
echo     DZ Subtitles AI - Auto-Start on Windows Boot
echo =======================================================
echo.
echo Configuring auto-run when your PC turns on...
python -c "from core.autostart import set_autostart; res = set_autostart(True); print(res.get('message', 'Done!'))"
echo.
echo =======================================================
echo Auto-start has been enabled!
echo DZ Subtitles AI will now run automatically on PC boot.
echo You can toggle this anytime in the web app under Automation Settings.
echo =======================================================
echo.
pause
