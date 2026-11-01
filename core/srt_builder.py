"""
Standard Subtitle Exporters: SRT, VTT, and JSON.
"""

from typing import Dict, Any, List


def format_srt_time(seconds: float) -> str:
    """Converts seconds to SRT timecode format: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_vtt_time(seconds: float) -> str:
    """Converts seconds to WebVTT timecode format: HH:MM:SS.mmm"""
    srt_str = format_srt_time(seconds)
    return srt_str.replace(",", ".")


def generate_srt(transcription_data: Dict[str, Any], words_per_chunk: int = 4) -> str:
    """
    Generates standard SubRip (.srt) subtitles.
    If word timestamps are available, chunks words into natural short lines.
    """
    segments = transcription_data.get("segments", [])
    srt_lines = []
    counter = 1

    all_words = []
    for seg in segments:
        all_words.extend(seg.get("words", []))

    if all_words and len(all_words) > len(segments):
        # Chunk words for short-form video pacing
        for i in range(0, len(all_words), words_per_chunk):
            chunk = all_words[i:i + words_per_chunk]
            start_str = format_srt_time(chunk[0]["start"])
            end_str = format_srt_time(chunk[-1]["end"])
            text = " ".join(w["word"] for w in chunk)

            srt_lines.append(f"{counter}\n{start_str} --> {end_str}\n{text}\n")
            counter += 1
    else:
        # Fall back to segments
        for seg in segments:
            start_str = format_srt_time(seg["start"])
            end_str = format_srt_time(seg["end"])
            text = seg.get("text", "").strip()

            srt_lines.append(f"{counter}\n{start_str} --> {end_str}\n{text}\n")
            counter += 1

    return "\n".join(srt_lines)


def generate_vtt(transcription_data: Dict[str, Any], words_per_chunk: int = 4) -> str:
    """Generates WebVTT (.vtt) format subtitle content."""
    segments = transcription_data.get("segments", [])
    vtt_lines = ["WEBVTT\n"]

    all_words = []
    for seg in segments:
        all_words.extend(seg.get("words", []))

    if all_words and len(all_words) > len(segments):
        for i in range(0, len(all_words), words_per_chunk):
            chunk = all_words[i:i + words_per_chunk]
            start_str = format_vtt_time(chunk[0]["start"])
            end_str = format_vtt_time(chunk[-1]["end"])
            text = " ".join(w["word"] for w in chunk)

            vtt_lines.append(f"{start_str} --> {end_str}\n{text}\n")
    else:
        for seg in segments:
            start_str = format_vtt_time(seg["start"])
            end_str = format_vtt_time(seg["end"])
            text = seg.get("text", "").strip()
            vtt_lines.append(f"{start_str} --> {end_str}\n{text}\n")

    return "\n".join(vtt_lines)
