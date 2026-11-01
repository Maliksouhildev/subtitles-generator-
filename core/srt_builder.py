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
    Chunks words per segment to respect sentence boundaries and pauses.
    """
    segments = transcription_data.get("segments", [])
    srt_lines = []
    counter = 1

    for seg in segments:
        words = seg.get("words", [])
        if words and len(words) > 1:
            for i in range(0, len(words), words_per_chunk):
                chunk = words[i:i + words_per_chunk]
                start_str = format_srt_time(chunk[0]["start"])
                end_str = format_srt_time(chunk[-1]["end"])
                text = " ".join(w.get("word", "") for w in chunk)

                srt_lines.append(f"{counter}\n{start_str} --> {end_str}\n{text}\n")
                counter += 1
        else:
            start_str = format_srt_time(seg.get("start", 0.0))
            end_str = format_srt_time(seg.get("end", 2.0))
            text = seg.get("text", "").strip()

            srt_lines.append(f"{counter}\n{start_str} --> {end_str}\n{text}\n")
            counter += 1

    return "\n".join(srt_lines)


def generate_vtt(transcription_data: Dict[str, Any], words_per_chunk: int = 4) -> str:
    """
    Generates WebVTT (.vtt) format subtitle content.
    Chunks words per segment to respect sentence boundaries and pauses.
    """
    segments = transcription_data.get("segments", [])
    vtt_lines = ["WEBVTT\n"]

    for seg in segments:
        words = seg.get("words", [])
        if words and len(words) > 1:
            for i in range(0, len(words), words_per_chunk):
                chunk = words[i:i + words_per_chunk]
                start_str = format_vtt_time(chunk[0]["start"])
                end_str = format_vtt_time(chunk[-1]["end"])
                text = " ".join(w.get("word", "") for w in chunk)

                vtt_lines.append(f"{start_str} --> {end_str}\n{text}\n")
        else:
            start_str = format_vtt_time(seg.get("start", 0.0))
            end_str = format_vtt_time(seg.get("end", 2.0))
            text = seg.get("text", "").strip()
            vtt_lines.append(f"{start_str} --> {end_str}\n{text}\n")

    return "\n".join(vtt_lines)

