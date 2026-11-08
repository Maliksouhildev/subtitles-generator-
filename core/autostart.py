"""
Cross-platform Auto-Start on Boot Manager.
Supports Windows (Startup Folder + Registry HKCU), Linux (XDG Autostart), and macOS (LaunchAgents).
Enables seamless toggling directly from the web interface.
"""
import os
import sys
import logging
from typing import Dict, Any

logger = logging.getLogger("dz_subtitles.autostart")

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_NAME = "DZSubtitlesAI"


def ensure_launcher_scripts():
    """Ensures start.bat and start_background.vbs exist in repo root."""
    vbs_path = os.path.join(REPO_DIR, "start_background.vbs")
    if not os.path.exists(vbs_path):
        vbs_content = (
            "' Silent background launcher for DZ Subtitles AI\n"
            "Set WshShell = CreateObject(\"WScript.Shell\")\n"
            "Set fso = CreateObject(\"Scripting.FileSystemObject\")\n"
            "strPath = fso.GetParentFolderName(WScript.ScriptFullName)\n"
            "WshShell.CurrentDirectory = strPath\n"
            "WshShell.Run \"python server.py\", 0, False\n"
        )
        try:
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_content)
        except Exception as e:
            logger.warning(f"Could not create start_background.vbs: {e}")

    bat_path = os.path.join(REPO_DIR, "start.bat")
    if not os.path.exists(bat_path):
        bat_content = (
            "@echo off\r\n"
            "title DZ Subtitles AI Server\r\n"
            "cd /d \"%~dp0\"\r\n"
            "echo Starting DZ Subtitles AI...\r\n"
            "start \"\" http://localhost:8000\r\n"
            "python server.py\r\n"
            "pause\r\n"
        )
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
        except Exception as e:
            logger.warning(f"Could not create start.bat: {e}")


def get_windows_startup_path() -> str:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        appdata = os.path.expanduser("~\\AppData\\Roaming")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", f"{APP_NAME}.bat")


def get_autostart_status() -> Dict[str, Any]:
    """Checks whether auto-start on boot is currently enabled."""
    is_windows = sys.platform.startswith("win")
    is_linux = sys.platform.startswith("linux")
    is_mac = sys.platform.startswith("darwin")

    enabled = False
    details = []

    if is_windows:
        startup_bat = get_windows_startup_path()
        if os.path.exists(startup_bat):
            enabled = True
            details.append("Startup folder")

        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_NAME)
                enabled = True
                details.append("Registry Run")
            except FileNotFoundError:
                pass
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass

    elif is_linux:
        desktop_file = os.path.expanduser(f"~/.config/autostart/{APP_NAME.lower()}.desktop")
        if os.path.exists(desktop_file):
            enabled = True
            details.append("XDG Autostart")

    elif is_mac:
        plist_file = os.path.expanduser(f"~/Library/LaunchAgents/com.{APP_NAME.lower()}.plist")
        if os.path.exists(plist_file):
            enabled = True
            details.append("LaunchAgent")

    return {
        "supported": True,
        "enabled": enabled,
        "platform": sys.platform,
        "details": ", ".join(details) if details else "None"
    }


def set_autostart(enable: bool) -> Dict[str, Any]:
    """Enables or disables auto-start on boot."""
    ensure_launcher_scripts()
    is_windows = sys.platform.startswith("win")
    is_linux = sys.platform.startswith("linux")
    is_mac = sys.platform.startswith("darwin")

    if is_windows:
        startup_bat = get_windows_startup_path()
        vbs_path = os.path.join(REPO_DIR, "start_background.vbs")

        if enable:
            # 1. Write to Startup folder (.bat)
            try:
                os.makedirs(os.path.dirname(startup_bat), exist_ok=True)
                bat_script = (
                    f"@echo off\r\n"
                    f"cd /d \"{REPO_DIR}\"\r\n"
                    f"wscript.exe \"{vbs_path}\"\r\n"
                )
                with open(startup_bat, "w", encoding="utf-8") as f:
                    f.write(bat_script)
                logger.info(f"Created startup script: {startup_bat}")
            except Exception as e:
                logger.error(f"Failed to write startup script: {e}")

            # 2. Add Registry entry
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                cmd_value = f'wscript.exe "{vbs_path}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd_value)
                winreg.CloseKey(key)
                logger.info("Added Windows registry run entry")
            except Exception as e:
                logger.warning(f"Could not write registry run entry: {e}")

            return {
                "success": True,
                "enabled": True,
                "message": "Auto-start enabled! DZ Subtitles AI will now automatically run when Windows boots up."
            }
        else:
            # 1. Remove from Startup folder
            if os.path.exists(startup_bat):
                try:
                    os.remove(startup_bat)
                    logger.info(f"Removed startup script: {startup_bat}")
                except Exception as e:
                    logger.error(f"Failed to remove startup script: {e}")

            # 2. Remove Registry entry
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Removed Windows registry run entry")
                except FileNotFoundError:
                    pass
                winreg.CloseKey(key)
            except Exception as e:
                logger.warning(f"Could not remove registry run entry: {e}")

            return {
                "success": True,
                "enabled": False,
                "message": "Auto-start disabled. The app will only run when you start it manually."
            }

    elif is_linux:
        desktop_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = os.path.join(desktop_dir, f"{APP_NAME.lower()}.desktop")
        if enable:
            os.makedirs(desktop_dir, exist_ok=True)
            content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                f"Name={APP_NAME}\n"
                f"Exec={sys.executable} {os.path.join(REPO_DIR, 'server.py')}\n"
                f"Path={REPO_DIR}\n"
                "Hidden=false\n"
                "NoDisplay=false\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "enabled": True, "message": "Auto-start enabled for Linux desktop session."}
        else:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return {"success": True, "enabled": False, "message": "Auto-start disabled."}

    elif is_mac:
        launch_dir = os.path.expanduser("~/Library/LaunchAgents")
        plist_file = os.path.join(launch_dir, f"com.{APP_NAME.lower()}.plist")
        if enable:
            os.makedirs(launch_dir, exist_ok=True)
            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.join(REPO_DIR, 'server.py')}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{REPO_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            with open(plist_file, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "enabled": True, "message": "Auto-start enabled for macOS user session."}
        else:
            if os.path.exists(plist_file):
                os.remove(plist_file)
            return {"success": True, "enabled": False, "message": "Auto-start disabled."}

    return {"success": False, "enabled": False, "message": f"Unsupported platform: {sys.platform}"}
