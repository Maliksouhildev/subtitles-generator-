"""
Video Composition and Subtitle Burning Engine using FFmpeg.
Supports:
- Audio input: generates Green Screen, Black Screen, Blue Screen, Custom Color, or Transparent Alpha video
- Video input: burns animated subtitles directly into original video
- Aspect ratios: 9:16 (Shorts/Reels), 16:9 (YouTube), 1:1 (Square)
- Automatic font loading via libass fontsdir
"""

import os
import shutil
import tempfile
import logging
import subprocess
from typing import Optional, Tuple, Dict, Any

from core.transcriber import get_audio_duration

logger = logging.getLogger("video_engine")

ACTIVE_RENDER_PROCESSES: Dict[str, subprocess.Popen] = {}
CANCELLED_TASKS: set = set()

def cancel_render(task_id: str) -> bool:
    """Terminates any running FFmpeg render process associated with task_id."""
    if not task_id:
        return False
    CANCELLED_TASKS.add(task_id)
    proc = ACTIVE_RENDER_PROCESSES.get(task_id)
    if proc:
        try:
            proc.terminate()
            proc.kill()
            logger.info(f"Terminated active FFmpeg render process for task {task_id}")
            return True
        except Exception as e:
            logger.warning(f"Error terminating process for task {task_id}: {e}")
    return False

ASPECT_RATIOS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080)
}

BACKGROUND_COLORS = {
    "green_screen": "0x00FF00",
    "black": "0x000000",
    "blue": "0x0000FF",
    "white": "0xFFFFFF",
    "dark_gray": "0x1A1A1A"
}


def is_video_file(file_path: str) -> bool:
    """Checks if a media file contains a valid video stream."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout.strip() == "video"
    except Exception:
        return False


def get_video_dimensions(file_path: str) -> Tuple[int, int]:
    """Returns (width, height) of a video file."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        file_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        parts = res.stdout.strip().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception as e:
        logger.warning(f"Could not read video dimensions ({e}), defaulting to 1080x1920")
    return 1080, 1920


def render_video(
    media_path: str,
    ass_path: str,
    output_path: str,
    fonts_dir: Optional[str] = None,
    background_mode: str = "green_screen",  # "original_video", "green_screen", "black", "blue", "transparent", "custom"
    custom_color_hex: Optional[str] = None,
    aspect_ratio: str = "9:16",
    fps: int = 30,
    task_id: Optional[str] = None
) -> str:
    """
    Renders video with animated subtitles burned in using FFmpeg libass.
    Guarantees cross-platform path safety by executing inside an isolated temp staging directory.
    """
    if not os.path.exists(media_path):
        raise FileNotFoundError(f"Media file not found: {media_path}")
    if not os.path.exists(ass_path):
        raise FileNotFoundError(f"ASS subtitle file not found: {ass_path}")

    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output) or ".", exist_ok=True)

    is_video = is_video_file(media_path)
    duration = get_audio_duration(media_path)

    # Resolve fonts directory
    if fonts_dir is None:
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
    abs_fonts = os.path.abspath(fonts_dir)

    # Create temporary isolated staging folder to eliminate Windows path escaping issues in FFmpeg
    stage_dir = tempfile.mkdtemp(prefix="darija_render_")
    try:
        staged_ass = os.path.join(stage_dir, "subtitles.ass")
        shutil.copy(ass_path, staged_ass)

        staged_fonts = os.path.join(stage_dir, "fonts")
        if os.path.exists(abs_fonts):
            if os.path.exists(staged_fonts):
                shutil.rmtree(staged_fonts)
            shutil.copytree(abs_fonts, staged_fonts)
        else:
            os.makedirs(staged_fonts, exist_ok=True)

        # Decide whether to burn into video or generate background for audio
        if is_video and background_mode in ("original_video", "video"):
            logger.info(f"Burning subtitles onto existing video: {media_path}")
            staged_media = os.path.join(stage_dir, "input_media" + os.path.splitext(media_path)[1])
            shutil.copy(media_path, staged_media)

            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-i", os.path.basename(staged_media),
                "-vf", "ass=filename=subtitles.ass:fontsdir=fonts",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "fastdecode",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "out.mp4"
            ]
        else:
            # Audio input (or user selected solid background instead of original video)
            logger.info(f"Generating synthetic background video for audio: {media_path} (mode={background_mode})")
            width, height = ASPECT_RATIOS.get(aspect_ratio, (1080, 1920))

            staged_audio = os.path.join(stage_dir, "input_audio" + os.path.splitext(media_path)[1])
            shutil.copy(media_path, staged_audio)

            if background_mode == "transparent":
                # Render transparent VP9 WebM (or ProRes MOV)
                out_filename = "out.webm" if abs_output.endswith(".webm") else "out.mov"
                if out_filename.endswith(".webm"):
                    cmd = [
                        "ffmpeg", "-y",
                        "-threads", "0",
                        "-f", "lavfi", "-i", f"color=c=black@0.0:s={width}x{height}:d={duration}:r={fps}",
                        "-i", os.path.basename(staged_audio),
                        "-vf", "ass=filename=subtitles.ass:fontsdir=fonts",
                        "-c:v", "libvpx-vp9",
                        "-deadline", "realtime",
                        "-cpu-used", "8",
                        "-row-mt", "1",
                        "-pix_fmt", "yuva420p",
                        "-c:a", "libopus",
                        "-b:a", "128k",
                        "-shortest",
                        out_filename
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-y",
                        "-threads", "0",
                        "-f", "lavfi", "-i", f"color=c=black@0.0:s={width}x{height}:d={duration}:r={fps}",
                        "-i", os.path.basename(staged_audio),
                        "-vf", "ass=filename=subtitles.ass:fontsdir=fonts",
                        "-c:v", "prores_ks",
                        "-profile:v", "4",
                        "-pix_fmt", "yuva444p10le",
                        "-c:a", "pcm_s16le",
                        "-shortest",
                        out_filename
                    ]
            else:
                # Solid color background (Green screen, Black, Blue, Custom) - optimized with ultrafast
                if background_mode == "custom" and custom_color_hex:
                    hex_clean = custom_color_hex.lstrip("#")
                    bg_color_spec = f"0x{hex_clean}"
                else:
                    bg_color_spec = BACKGROUND_COLORS.get(background_mode, "0x00FF00")

                cmd = [
                    "ffmpeg", "-y",
                    "-threads", "0",
                    "-f", "lavfi", "-i", f"color=c={bg_color_spec}:s={width}x{height}:d={duration}:r={fps}",
                    "-i", os.path.basename(staged_audio),
                    "-vf", "ass=filename=subtitles.ass:fontsdir=fonts",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-tune", "fastdecode",
                    "-crf", "20",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    "out.mp4"
                ]

        logger.info(f"Executing FFmpeg render in stage dir: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, cwd=stage_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if task_id:
            ACTIVE_RENDER_PROCESSES[task_id] = proc
        try:
            stdout, stderr = proc.communicate()
        finally:
            if task_id and task_id in ACTIVE_RENDER_PROCESSES:
                ACTIVE_RENDER_PROCESSES.pop(task_id, None)

        if task_id and task_id in CANCELLED_TASKS:
            CANCELLED_TASKS.discard(task_id)
            raise RuntimeError(f"Rendering cancelled by user for task {task_id}")

        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="ignore")
            logger.error(f"FFmpeg render failed: {err}")
            raise RuntimeError(f"FFmpeg rendering error: {err}")

        # Find produced file and copy to destination
        produced_file = None
        for cand in ["out.mp4", "out.webm", "out.mov"]:
            p = os.path.join(stage_dir, cand)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                produced_file = p
                break

        if not produced_file:
            raise RuntimeError("FFmpeg completed with 0 but no output file was created.")

        shutil.copy(produced_file, abs_output)
        logger.info(f"Render completed successfully: {abs_output} ({os.path.getsize(abs_output)} bytes)")
        return abs_output

    finally:
        # Cleanup staging directory
        try:
            shutil.rmtree(stage_dir, ignore_errors=True)
        except Exception:
            pass
