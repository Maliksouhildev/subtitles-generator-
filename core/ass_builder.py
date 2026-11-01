"""
Advanced SubStation Alpha (.ass) Subtitle Generator with Word-by-Word Animations.
Features:
- TikTok / Reels / Shorts style word-by-word karaoke pop animation
- Right-to-Left (RTL) Arabic text shaping
- Custom font families (Cairo, Tajawal, Amiri, Almarai)
- Full color customization (Primary text, active word highlight, outline, shadow)
- Screen position control (Bottom, Middle, Top)
- Pacing control (Words per line / chunk)
"""

import math
import re
from typing import List, Dict, Any, Optional

ARABIC_REGEX = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
LATIN_REGEX = re.compile(r'[a-zA-Z]')


def is_arabic_text(text: str) -> bool:
    """Checks if text contains Arabic characters."""
    return bool(ARABIC_REGEX.search(text))


def format_bidi_word(word: str, in_rtl_context: bool = True) -> str:
    """
    Wraps Latin/French loanwords in Unicode Left-to-Right Isolates to prevent BiDi collisions
    with adjacent Arabic text in FriBidi / libass.
    """
    if in_rtl_context and LATIN_REGEX.search(word):
        # \u200E (Left-to-Right Mark) forces FriBidi to treat the Latin token as an atomic LTR unit
        return f"\u200E{word}\u200E"
    return word


def resolve_visual_word_order(chunk: List[Dict[str, Any]], in_rtl_context: bool = True) -> List[int]:
    """
    Resolves physical Left-to-Right visual word indices for rendering in libass.

    Mechanics:
    - In an LTR context (e.g. English/French speech):
      Physical layout order matches chronological speech order [0, 1, 2, ...].
    - In an RTL context (Arabic speech / Algerian Darija):
      Libass lays out override-tagged chunks from Left to Right across the screen.
      To ensure the first spoken Arabic word is placed on the far RIGHT and subsequent
      words flow leftward, Arabic word sequences must be ordered in reverse.
      However, continuous Latin loanword runs (e.g. ['le', 'premier', 'test']) MUST retain
      their internal Left-to-Right word order so they are not read backward!
    """
    if not in_rtl_context or len(chunk) <= 1:
        return list(range(len(chunk)))

    runs = []
    current_run = []
    current_is_latin = None

    for idx, w in enumerate(chunk):
        text = w.get("word", "") if isinstance(w, dict) else str(w)
        is_latin = bool(LATIN_REGEX.search(text))
        if current_is_latin is None or is_latin == current_is_latin:
            current_run.append(idx)
            current_is_latin = is_latin
        else:
            runs.append((current_is_latin, current_run))
            current_run = [idx]
            current_is_latin = is_latin
    if current_run:
        runs.append((current_is_latin, current_run))

    # In an RTL context:
    # Runs are placed from Right to Left on screen:
    # Run 0 is on the far right, Run N-1 on the far left.
    # Because libass places runs on screen sequentially from Left to Right:
    # The visual file order is: Run N-1, ..., Run 0.
    visual_indices: List[int] = []
    for is_latin, run in reversed(runs):
        if is_latin:
            # Latin run is read LTR internally: keep original chronological order
            visual_indices.extend(run)
        else:
            # Arabic run is read RTL internally: reverse so earlier spoken word is on the right
            visual_indices.extend(reversed(run))

    return visual_indices


def balance_chunk_sizes(total_words: int, target_size: int) -> List[int]:
    """
    Calculates balanced chunk sizes preventing awkward 1-word orphan lines.
    For example: 4 words with target=3 splits into [2, 2], not [3, 1].
    """
    if total_words <= target_size:
        return [total_words]
    num_chunks = math.ceil(total_words / target_size)
    if total_words % target_size == 1 and num_chunks > 1:
        base_size = total_words // num_chunks
        remainder = total_words % num_chunks
        return [base_size + (1 if k < remainder else 0) for k in range(num_chunks)]
    sizes = []
    remaining = total_words
    while remaining > 0:
        if remaining == target_size + 1:
            half = remaining // 2
            sizes.append(remaining - half)
            sizes.append(half)
            break
        take = min(target_size, remaining)
        sizes.append(take)
        remaining -= take
    return sizes


def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """
    Converts a standard hex color string (#RRGGBB or RRGGBB) to ASS color format (&HAABBGGRR&).
    ASS colors are stored in Blue-Green-Red (BGR) order with hexadecimal alpha (00 = opaque, FF = transparent).
    """
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        hex_clean = "FFFFFF"  # default white

    r = hex_clean[0:2]
    g = hex_clean[2:4]
    b = hex_clean[4:6]
    a = f"{alpha:02X}"

    # ASS order: &H[Alpha][Blue][Green][Red]&
    return f"&H{a}{b}{g}{r}&"


def format_ass_time(seconds: float) -> str:
    """Converts seconds (e.g. 125.45) to ASS timecode H:MM:SS.cs (e.g. 0:02:05.45)."""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


class ASSSubtitleBuilder:
    def __init__(
        self,
        font_name: str = "Lalezar",
        font_size: int = 56,
        primary_color: str = "#FFFFFF",
        highlight_color: str = "#FFE600",
        outline_color: str = "#000000",
        shadow_color: str = "#000000",
        outline_width: float = 2.4,
        shadow_depth: float = 2.2,
        alignment: int = 2,  # 2: Bottom Center, 5: Middle Center, 8: Top Center
        margin_v: int = 420,  # Safe Zone above Shorts/Reels/TikTok native bottom UI
        words_per_line: int = 4,
        animation_style: str = "karaoke_pop",  # "karaoke_pop", "bouncy_spring", "neon_glow", "color_flash", "box_highlight", "word_reveal", "classic_line"
        video_width: int = 1080,
        video_height: int = 1920,
        pos_y: Optional[int] = None,
        animation_speed: float = 1.0,
        sub_box_style: str = "none",  # "none", "pill", "box", "shadow"
        sub_box_color: str = "#000000",
        sub_box_alpha: float = 0.85
    ):
        self.font_name = font_name
        self.font_size = font_size
        self.primary_color = primary_color
        self.highlight_color = highlight_color
        self.outline_color = outline_color
        self.shadow_color = shadow_color
        self.outline_width = outline_width
        self.shadow_depth = shadow_depth
        self.alignment = alignment
        # If explicit pos_y was provided, calculate margin_v from bottom (for alignment=2)
        if pos_y is not None:
            self.margin_v = max(30, video_height - pos_y)
        else:
            self.margin_v = margin_v
        self.words_per_line = max(1, words_per_line)
        self.animation_style = animation_style
        self.video_width = video_width
        self.video_height = video_height
        self.animation_speed = max(0.3, min(3.0, float(animation_speed)))
        self.sub_box_style = sub_box_style or "none"
        self.sub_box_color = sub_box_color or "#000000"
        self.sub_box_alpha = max(0.0, min(1.0, float(sub_box_alpha)))

    def generate_header(self) -> str:
        """Generates the ASS script header and style block."""
        pri_ass = hex_to_ass_color(self.primary_color)
        sec_ass = hex_to_ass_color(self.highlight_color)

        if self.sub_box_style in ("pill", "box"):
            # ASS BorderStyle 3 produces an opaque/translucent bounding box around subtitle text
            border_style = 3
            alpha_int = max(0, min(255, int(round((1.0 - self.sub_box_alpha) * 255))))
            out_ass = hex_to_ass_color(self.sub_box_color, alpha=alpha_int)
            outline_val = 8.0
            sha_ass = hex_to_ass_color("#000000", alpha=180)
            shadow_val = 1.5
        elif self.sub_box_style == "shadow":
            border_style = 1
            out_ass = hex_to_ass_color(self.outline_color)
            outline_val = 2.0
            alpha_int = max(0, min(255, int(round((1.0 - self.sub_box_alpha) * 255))))
            sha_ass = hex_to_ass_color(self.sub_box_color, alpha=alpha_int)
            shadow_val = 5.0
        else:
            border_style = 1
            out_ass = hex_to_ass_color(self.outline_color)
            outline_val = self.outline_width
            # Soft feathered broadcast drop shadow
            sha_ass = hex_to_ass_color(self.shadow_color, alpha=150)
            shadow_val = self.shadow_depth

        header = f"""[Script Info]
Title: Darija Subtitles Generator
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {self.video_width}
PlayResY: {self.video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.font_name},{self.font_size},{pri_ass},{sec_ass},{out_ass},{sha_ass},-1,0,0,0,100,100,0,0,{border_style},{outline_val},{shadow_val},{self.alignment},30,30,{self.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def chunk_words(self, words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Splits words into balanced chunks based on `words_per_line` and significant pauses.
        Anti-orphan balancing: Never leaves a solitary 1-word chunk isolated in the center.
        """
        if not words:
            return []

        # Group words by natural speech pauses > 0.9s
        pause_blocks = []
        current_block = []
        for w in words:
            if current_block:
                prev_w = current_block[-1]
                pause_gap = w.get("start", 0.0) - prev_w.get("end", 0.0)
                if pause_gap > 0.9:
                    pause_blocks.append(current_block)
                    current_block = []
            current_block.append(w)
        if current_block:
            pause_blocks.append(current_block)

        chunks = []
        for block in pause_blocks:
            sizes = balance_chunk_sizes(len(block), self.words_per_line)
            idx = 0
            for sz in sizes:
                chunks.append(block[idx:idx + sz])
                idx += sz
        return chunks

    def build_karaoke_pop_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """
        Builds word-by-word pop and highlight events with Remotion-calibrated 4-stage spring physics.
        Resolves physical Left-to-Right layout order so Arabic words flow authentic RTL and French loanwords LTR.
        """
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        norm_scale = "\\blur1.8\\fscx100\\fscy100"

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    # Hold the completed phrase on screen for minimum 0.85s so viewer can absorb sentence context
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.85
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(120, int((w_end - w_start) * 1000))

                # Remotion-calibrated 4-stage harmonic spring: overshoot -> recoil -> micro-bounce -> settle
                t1 = max(35, min(int(dur_ms * 0.32), int(95 / spd)))
                t2 = max(t1 + 25, min(int(dur_ms * 0.62), int(185 / spd)))
                t3 = max(t2 + 25, min(int(dur_ms * 0.85), int(260 / spd)))
                t4 = max(t3 + 20, min(dur_ms, int(330 / spd)))

                active_pop_transform = (
                    f"\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.45,\\fscx130\\fscy130)"
                    f"\\t({t1},{t2},1.6,\\fscx107\\fscy107)"
                    f"\\t({t2},{t3},0.8,\\fscx115\\fscy115)"
                    f"\\t({t3},{t4},1.3,\\fscx110\\fscy110)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                # Resolve physical Left-to-Right layout order for libass:
                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{active_pop_transform}}}{word_text}{{{pri_tag}{norm_scale}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}{norm_scale}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_word_reveal_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds progressive word reveal events with smooth opacity fade-in and scale pop."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.85
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.45), int(110 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.85), int(220 / spd)))

                reveal_tag = (
                    f"\\alpha&HFF&\\blur1.8\\fscx95\\fscy95"
                    f"\\t(0,{t1},0.6,\\alpha&H00&\\fscx115\\fscy115)"
                    f"\\t({t1},{t2},1.4,\\fscx100\\fscy100)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                # Resolve physical Left-to-Right layout order for currently revealed words
                sub_chunk = chunk[:i + 1]
                sub_indices = resolve_visual_word_order(sub_chunk, in_rtl_context=chunk_is_rtl)

                revealed = []
                for j in sub_indices:
                    w_text = format_bidi_word(sub_chunk[j].get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted = f"{{{hl_tag}{reveal_tag}}}{w_text}{{{pri_tag}\\blur1.8\\fscx100\\fscy100}}"
                        revealed.append(formatted)
                    else:
                        revealed.append(f"{{{pri_tag}\\blur1.8}}{w_text}")

                line_text = " ".join(revealed)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_classic_line_events(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Builds classic subtitle lines with smooth dynamic fade in/out transitions."""
        events = []
        spd = self.animation_speed
        for seg in segments:
            start = seg.get("start", 0.0)
            end = seg.get("end", start + 2.0)
            dur_ms = max(50, int((end - start) * 1000))
            fade_ms = max(20, min(160, int((dur_ms * 0.15) / spd)))
            fade_tag = f"{{\\fad({fade_ms},{fade_ms})\\blur1.8}}"
            start_str = format_ass_time(start)
            end_str = format_ass_time(end)
            raw_text = seg.get("text", "").strip()
            tokens = raw_text.split()
            has_arabic = any(is_arabic_text(t) for t in tokens)
            visual_indices = resolve_visual_word_order(tokens, in_rtl_context=has_arabic)
            formatted_tokens = [format_bidi_word(tokens[idx], in_rtl_context=has_arabic) for idx in visual_indices]
            line_text = " ".join(formatted_tokens)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{fade_tag}{line_text}")
        return events

    def build_box_highlight_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds box highlight style with fluid border expansion and accent badge."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        hl_ass = hex_to_ass_color(self.highlight_color)
        out_ass = hex_to_ass_color(self.outline_color)

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.65
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.4), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.8), int(200 / spd)))

                box_tag = (
                    f"\\bord{self.outline_width}\\3c{out_ass}\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\bord{self.outline_width + 2.5}\\3c{hl_ass}\\fscx112\\fscy112)"
                    f"\\t({t1},{t2},1.3,\\bord{self.outline_width + 2}\\3c{hl_ass}\\fscx106\\fscy106)"
                )
                reset_box = f"\\bord{self.outline_width}\\3c{out_ass}\\fscx100\\fscy100"

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}\\blur1.8{box_tag}}}{word_text}{{{pri_tag}{reset_box}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}\\blur1.8{reset_box}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_bouncy_spring_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds energetic bouncy spring animation with fluid elastic bounce physics."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        norm_tag = "\\fscx100\\fscy100\\frz0"

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.85
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(120, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.3), int(90 / spd)))
                t2 = max(t1 + 25, min(int(dur_ms * 0.6), int(180 / spd)))
                t3 = max(t2 + 25, min(int(dur_ms * 0.85), int(260 / spd)))
                t4 = max(t3 + 20, min(dur_ms, int(330 / spd)))

                bounce_tag = (
                    f"\\blur1.8\\fscx100\\fscy100\\frz0"
                    f"\\t(0,{t1},0.45,\\fscy134\\fscx112\\frz-2.5)"
                    f"\\t({t1},{t2},1.6,\\fscy94\\fscx105\\frz1.5)"
                    f"\\t({t2},{t3},0.8,\\fscy108\\fscx102\\frz-0.8)"
                    f"\\t({t3},{t4},1.3,\\fscy102\\fscx100\\frz0)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{bounce_tag}}}{word_text}{{{pri_tag}{norm_tag}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}\\blur1.8{norm_tag}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_neon_glow_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds intense luminous neon halo outline with smooth opening and closing glow ease."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        hl_ass = hex_to_ass_color(self.highlight_color)
        out_ass = hex_to_ass_color(self.outline_color)
        spd = self.animation_speed

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.85
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.4), int(120 / spd)))
                t2 = max(t1 + 35, min(int(dur_ms * 0.8), int(240 / spd)))

                neon_tag = (
                    f"\\bord{self.outline_width}\\3c{out_ass}\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\bord{self.outline_width + 4}\\3c{hl_ass}\\blur4.5\\fscx114\\fscy114)"
                    f"\\t({t1},{t2},1.3,\\bord{self.outline_width + 2.5}\\3c{hl_ass}\\blur2.5\\fscx108\\fscy108)"
                )
                reset_neon = f"\\bord{self.outline_width}\\3c{out_ass}\\blur1.8\\fscx100\\fscy100"

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{neon_tag}}}{word_text}{{{pri_tag}{reset_neon}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}{reset_neon}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_color_flash_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds high-contrast dynamic color flash with fluid chromatic pulse."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_ass = hex_to_ass_color(self.highlight_color)
        spd = self.animation_speed
        norm_tag = f"{pri_tag}\\blur1.8\\fscx100\\fscy100"

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    natural_end = active_word["end"]
                    min_hold = w_start + 0.85
                    w_end = min(next_chunk_start - 0.05, max(natural_end, min_hold)) if next_chunk_start else max(natural_end, min_hold)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.35), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.75), int(200 / spd)))

                flash_tag = (
                    f"\\c{hl_ass}\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\c&H00FFFF00&\\blur2.2\\fscx120\\fscy120)"
                    f"\\t({t1},{t2},1.4,\\c{hl_ass}\\blur1.8\\fscx108\\fscy108)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{flash_tag}}}{word_text}{{{norm_tag}}}")
                    else:
                        formatted_words.append(f"{{{norm_tag}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def generate_ass(self, transcription_data: Dict[str, Any]) -> str:
        """
        Generates full ASS file content from transcription data.
        Chunks words per segment to preserve natural pauses and prevent subtitle drift.
        """
        segments = transcription_data.get("segments", [])

        # Extract words per segment to respect pauses between sentences
        chunks = []
        for seg in segments:
            seg_words = seg.get("words", [])
            if not seg_words and seg.get("text"):
                ws = seg["text"].split()
                dur = (seg.get("end", 0.0) - seg.get("start", 0.0)) / max(1, len(ws))
                cur = seg.get("start", 0.0)
                seg_words = [{"word": w, "start": cur + idx * dur, "end": cur + (idx + 1) * dur} for idx, w in enumerate(ws)]
            if seg_words:
                chunks.extend(self.chunk_words(seg_words))

        header = self.generate_header()
        events = []

        if self.animation_style == "karaoke_pop":
            events = self.build_karaoke_pop_events(chunks)
        elif self.animation_style == "bouncy_spring":
            events = self.build_bouncy_spring_events(chunks)
        elif self.animation_style == "neon_glow":
            events = self.build_neon_glow_events(chunks)
        elif self.animation_style == "color_flash":
            events = self.build_color_flash_events(chunks)
        elif self.animation_style == "word_reveal":
            events = self.build_word_reveal_events(chunks)
        elif self.animation_style == "box_highlight":
            events = self.build_box_highlight_events(chunks)
        elif self.animation_style == "classic_line" or self.animation_style == "classic_fade":
            events = self.build_classic_line_events(segments)
        else:
            events = self.build_karaoke_pop_events(chunks)

        # Fallback if no words were generated
        if not events and segments:
            events = self.build_classic_line_events(segments)

        return header + "\n".join(events) + "\n"

