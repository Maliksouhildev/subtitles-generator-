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

ARABIC_PREFIX_ARTICLE_REGEX = re.compile(
    r'^(?:'
    r'[\u0648\u0641\u0628\u0643]?[\u0622\u0623\u0625\u0627]?\u0644[\u0640\-]*|'  # ال, وال, بال, فال, كال, أَل, إل, آل with optional tatweel/hyphen
    r'[\u0648\u0641\u0628]?\u0644\u0644[\u0640\-]*|'                              # لل, ولل, فلل, بلل
    r'[\u0648\u0641\u0628]?\u0644[\u0640\-]+|'                                    # لـ, ولـ, فلـ, بلـ
    r'[\u0648]?\u0644\u0627[\u0640\-]*|'                                          # لا, ولا (French 'la' particle / Arabic neg/art)
    r'[\u0648]?\u0644\u0648[\u0640\-]*|'                                          # لو, ولو (French 'le')
    r'[\u0648]?\u0644\u064a[\u0640\-]*|'                                          # لي, ولي (French 'les' / Darija li)
    r'[\u0648]?\u0627\u0644\u0644\u064a[\u0640\-]*|'                              # اللي, واللي (Darija relative pronoun)
    r'[\u0648]?\u062f\u064a[\u0640\-]*|'                                          # دي, ودي (French 'des')
    r'[\u0648]?\u062f\u0648[\u0640\-]*|'                                          # دو, ودو (French 'du')
    r'[\u0648]?\u062f[\u0640\-]+|'                                                # دـ, ودـ (Darija genitive d-)
    r'[\u0648]?[\u0628\u0641\u0643][\u0640\-]+|'                                  # بـ, فـ, كـ
    r'[\u0648]?\u0645\u0627[\u0640\-]*|'                                          # ما, وما
    r'[\u0648]?\u064a\u0627[\u0640\-]*|'                                          # يا, ويا
    r'[\u0648]?\u0647\u0627[\u0640\-]*|'                                          # ها, وها
    r'[\u0628\u0641]?\u0647\u0627\u062f[\u0640\-]*'                               # بهاد, فهاد, هاد
    r')$'
)


def is_prefix_token(token: str) -> bool:
    """Checks if a token is an orphaned Arabic article/particle prefix."""
    clean = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', str(token).strip())
    if not clean:
        return False
    return bool(ARABIC_PREFIX_ARTICLE_REGEX.match(clean)) or token.strip().endswith(("-", "ـ"))


def bind_arabic_articles_to_latin(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not words:
        return []
    bound: List[Dict[str, Any]] = []
    i = 0
    while i < len(words):
        w = words[i]
        text_val = str(w.get("word", "")).strip()
        if is_prefix_token(text_val) and i + 1 < len(words):
            chain = [w]
            j = i + 1
            while j < len(words) and is_prefix_token(words[j].get("word", "")):
                chain.append(words[j])
                j += 1
            if j < len(words):
                target_word = words[j]
                joint_text = " ".join(str(item.get("word", "")).strip() for item in chain) + " " + str(target_word.get("word", "")).strip()
                bound.append({
                    "word": joint_text.strip(),
                    "start": chain[0].get("start", 0.0),
                    "end": target_word.get("end", target_word.get("start", 0.0) + 0.3)
                })
                i = j + 1
                continue
            else:
                next_w = words[i + 1]
                joint_text = f"{text_val} {str(next_w.get('word', '')).strip()}"
                bound.append({
                    "word": joint_text,
                    "start": w.get("start", 0.0),
                    "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
                })
                i += 2
                continue
        bound.append(w)
        i += 1
    return bound



NON_TERMINAL_PARTICLES = {
    "و", "ف", "ب", "ل", "في", "على", "من", "عن", "مع", "إلى", "الى",
    "ما", "لا", "لي", "اللي", "دي", "دو", "يا", "ها", "بهاد", "فهاد", "هاد",
    "la", "le", "les", "un", "une", "des", "du", "de", "d'", "et", "ou",
    "en", "au", "aux", "par", "pour", "avec", "dans", "sur"
}

def is_non_terminal_token(token: str) -> bool:
    clean = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', str(token).strip().lower())
    return clean in NON_TERMINAL_PARTICLES or token.strip().endswith(("-", "ـ"))


def chunk_words_by_script(words: List[Dict[str, Any]], words_per_chunk: int = 4) -> List[List[Dict[str, Any]]]:
    """
    Chunks words respecting speech pauses, keeping Arabic phrases and Latin loanwords unified
    and avoiding stranding non-terminal particles at the end of chunks.
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
    w_target = min(4, max(2, words_per_chunk))
    for block in pause_blocks:
        block_chunks = []
        for i in range(0, len(block), w_target):
            block_chunks.append(list(block[i:i + w_target]))

        # Grammatical cohesion
        for c_i in range(len(block_chunks) - 1):
            curr_c = block_chunks[c_i]
            next_c = block_chunks[c_i + 1]
            if curr_c and is_non_terminal_token(curr_c[-1].get("word", "")):
                if len(curr_c) > 2:
                    moved = curr_c.pop()
                    next_c.insert(0, moved)
                elif len(curr_c) < 4 and next_c:
                    moved = next_c.pop(0)
                    curr_c.append(moved)

        for c in block_chunks:
            if c:
                chunks.append(c)

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

