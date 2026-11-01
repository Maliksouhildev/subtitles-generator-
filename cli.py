"""
Command-Line Interface (CLI) for Darija Subtitles Generator.
Allows generating animated subtitles directly from the terminal.

Usage:
    python cli.py --input speech.mp3 --output video_subtitles.mp4 --bg green_screen
"""

import os
import argparse
import json
import logging
from pathlib import Path

from core.transcriber import transcribe
from core.ass_builder import ASSSubtitleBuilder
from core.srt_builder import generate_srt, generate_vtt
from core.video_engine import render_video, is_video_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cli")


def main():
    parser = argparse.ArgumentParser(
        description="DZ Subtitles AI: Automatic Algerian Arabic (Darija) animated subtitle generator"
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input audio or video file")
    parser.add_argument("-o", "--output", default="output.mp4", help="Path to output video file")
    parser.add_argument("--api-key", default=None, help="Gemini API Key (optional, defaults to GEMINI_API_KEY env)")
    parser.add_argument("--dialect", default="General Algerian", help="Algerian dialect focus (General Algerian, Algiers, Oran, Constantine)")
    parser.add_argument("--bg", default="green_screen", choices=["green_screen", "black", "blue", "original_video", "transparent", "custom"], help="Background mode")
    parser.add_argument("--custom-color", default="#1a1a24", help="Custom hex color for background")
    parser.add_argument("--font", default="Cairo", help="Arabic font (Cairo, Tajawal, Amiri, Almarai)")
    parser.add_argument("--font-size", type=int, default=56, help="Font size in pixels")
    parser.add_argument("--primary-color", default="#FFFFFF", help="Main subtitle text color hex")
    parser.add_argument("--highlight-color", default="#FFE600", help="Active spoken word highlight color hex")
    parser.add_argument("--style", default="karaoke_pop", choices=["karaoke_pop", "word_reveal", "box_highlight", "classic_line"], help="Animation style")
    parser.add_argument("--words-per-line", type=int, default=3, help="Words per line/chunk")
    parser.add_argument("--aspect-ratio", default="9:16", choices=["9:16", "16:9", "1:1"], help="Video aspect ratio")
    parser.add_argument("--force-local", action="store_true", help="Force local Faster-Whisper offline transcription")
    parser.add_argument("--export-subtitles", action="store_true", default=True, help="Also export .srt, .ass, and .json files")

    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return 1

    out_path = os.path.abspath(args.output)
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(out_path)[0]

    # Step 1: Transcribe
    logger.info(f"🎙️ Transcribing {input_path} in Algerian Darija...")
    transcription = transcribe(
        audio_path=input_path,
        api_key=args.api_key,
        dialect_hint=args.dialect,
        force_local=args.force_local
    )

    num_segs = len(transcription.get("segments", []))
    logger.info(f"✅ Transcription complete! Extracted {num_segs} segments.")

    # Step 2: Build Subtitles
    w, h = (1080, 1920) if args.aspect_ratio == "9:16" else ((1920, 1080) if args.aspect_ratio == "16:9" else (1080, 1080))
    builder = ASSSubtitleBuilder(
        font_name=args.font,
        font_size=args.font_size,
        primary_color=args.primary_color,
        highlight_color=args.highlight_color,
        words_per_line=args.words_per_line,
        animation_style=args.style,
        video_width=w,
        video_height=h
    )

    ass_content = builder.generate_ass(transcription)
    ass_path = f"{base_name}.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    if args.export_subtitles:
        srt_content = generate_srt(transcription, words_per_chunk=args.words_per_line)
        with open(f"{base_name}.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)

        vtt_content = generate_vtt(transcription, words_per_chunk=args.words_per_line)
        with open(f"{base_name}.vtt", "w", encoding="utf-8") as f:
            f.write(vtt_content)

        with open(f"{base_name}_transcript.json", "w", encoding="utf-8") as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 Exported subtitle files: {ass_path}, {base_name}.srt, {base_name}.vtt, {base_name}_transcript.json")

    # Step 3: Render Video
    bg_mode = args.bg
    if is_video_file(input_path) and bg_mode == "green_screen":
        logger.info("Detected video input! Defaulting background mode to 'original_video'.")
        bg_mode = "original_video"

    logger.info(f"🎬 Rendering video with FFmpeg (mode: {bg_mode}, ratio: {args.aspect_ratio})...")
    fonts_dir = str(Path(__file__).resolve().parent / "fonts")

    rendered_file = render_video(
        media_path=input_path,
        ass_path=ass_path,
        output_path=out_path,
        fonts_dir=fonts_dir,
        background_mode=bg_mode,
        custom_color_hex=args.custom_color,
        aspect_ratio=args.aspect_ratio
    )

    logger.info(f"🎉 Success! Generated video saved to: {rendered_file} ({os.path.getsize(rendered_file)} bytes)")
    return 0


if __name__ == "__main__":
    exit(main())
