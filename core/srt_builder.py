"""
Standard Subtitle Exporters: SRT, VTT, and JSON.
"""

import re
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


ARABIC_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")

ARABIC_PREFIX_ARTICLE_REGEX = re.compile(r"^(?:و?الـ?|و?ال-|و?ال|لـ?|ل-|للـ?|لل-|فـ?|ف-|بـ?|ب-|لا)$")


def bind_arabic_articles_to_latin(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not words:
        return []
    bound: List[Dict[str, Any]] = []
    i = 0
    while i < len(words):
        w = words[i]
        text_val = str(w.get("word", "")).strip()
        if ARABIC_PREFIX_ARTICLE_REGEX.match(text_val) and i + 1 < len(words):
            next_w = words[i + 1]
            next_text = str(next_w.get("word", "")).strip()
            if LATIN_REGEX.search(next_text):
                joint_word = f"{text_val} {next_text}"
                bound.append({
                    "word": joint_word,
                    "start": w.get("start", 0.0),
                    "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
                })
                i += 2
                continue
        bound.append(w)
        i += 1
    return bound



def chunk_words_by_script(words: List[Dict[str, Any]], words_per_chunk: int = 4) -> List[List[Dict[str, Any]]]:
    """
    Chunks words respecting speech pauses, keeping Arabic phrases and Latin loanwords unified.
    """
    if not words:
        return []
    words = bind_arabic_articles_to_latin(words)

    pause_blocks = []
    current_block = []
    for w in words:
        if current_block:
            prev = current_block[-1]
            if w.get("start", 0.0) - prev.get("end", 0.0) > 0.9:
                pause_blocks.append(current_block)
                current_block = []
        current_block.append(w)
    if current_block:
        pause_blocks.append(current_block)

    chunks = []
    for block in pause_blocks:
        for i in range(0, len(block), words_per_chunk):
            chunks.append(block[i:i + words_per_chunk])
    return chunks


def generate_srt(transcription_data: Dict[str, Any], words_per_chunk: int = 4) -> str:
    """
    Generates standard SubRip (.srt) subtitles.
    Chunks words per segment respecting sentence boundaries, pauses, and script boundaries.
    """
    segments = transcription_data.get("segments", [])
    srt_lines = []
    counter = 1

    for seg in segments:
        words = seg.get("words", [])
        if words and len(words) > 1:
            chunks = chunk_words_by_script(words, words_per_chunk)
            for chunk in chunks:
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
    Chunks words per segment respecting sentence boundaries, pauses, and script boundaries.
    """
    segments = transcription_data.get("segments", [])
    vtt_lines = ["WEBVTT\n"]

    for seg in segments:
        words = seg.get("words", [])
        if words and len(words) > 1:
            chunks = chunk_words_by_script(words, words_per_chunk)
            for chunk in chunks:
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

