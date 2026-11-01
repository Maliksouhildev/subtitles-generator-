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


def is_arabic_text(text: str) -> bool:
    """Checks if text contains Arabic characters."""
    return bool(ARABIC_REGEX.search(text))


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
        font_name: str = "Cairo",
        font_size: int = 56,
        primary_color: str = "#FFFFFF",
        highlight_color: str = "#FFE600",
        outline_color: str = "#000000",
        shadow_color: str = "#000000",
        outline_width: float = 3.5,
        shadow_depth: float = 2.0,
        alignment: int = 2,  # 2: Bottom Center, 5: Middle Center, 8: Top Center
        margin_v: int = 420,  # Safe Zone above Shorts/Reels/TikTok native bottom UI
        words_per_line: int = 3,
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
            sha_ass = hex_to_ass_color(self.shadow_color, alpha=120)
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
        """Splits words into chunks of `words_per_line`, breaking on significant pauses."""
        if not words:
            return []
        chunks = []
        current_chunk = []
        for w in words:
            if current_chunk:
                prev_w = current_chunk[-1]
                # Break chunk if pause between words > 1.2s or chunk reaches words_per_line
                pause_gap = w.get("start", 0.0) - prev_w.get("end", 0.0)
                if pause_gap > 1.2 or len(current_chunk) >= self.words_per_line:
                    chunks.append(current_chunk)
                    current_chunk = []
            current_chunk.append(w)
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def build_karaoke_pop_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """
        Builds word-by-word pop and highlight events with dynamic easing.
        For Arabic / RTL text, words are arranged visually in RTL order (first spoken word on the right).
        """
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        norm_scale = "\\fscx100\\fscy100"

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    w_end = active_word["end"]

                if w_end <= w_start:
                    w_end = w_start + 0.25

                dur_ms = max(100, int((w_end - w_start) * 1000))
                # Dynamic ease in and settle timings
                t_pop = max(35, min(int(dur_ms * 0.45), int(120 / spd)))
                t_settle = max(t_pop + 30, min(int(dur_ms * 0.8), int(220 / spd)))

                # Dynamic spring ease with accel=0.6 (fast expansion) and accel=1.4 (smooth settlement)
                active_pop_transform = (
                    f"\\fscx100\\fscy100"
                    f"\\t(0,{t_pop},0.6,\\fscx125\\fscy125)"
                    f"\\t({t_pop},{t_settle},1.4,\\fscx112\\fscy112)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = list(reversed(range(len(chunk)))) if chunk_is_rtl else list(range(len(chunk)))

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = w.get("word", "")
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

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    w_end = active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.45), int(110 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.85), int(220 / spd)))

                reveal_tag = (
                    f"\\alpha&HFF&\\fscx95\\fscy95"
                    f"\\t(0,{t1},0.6,\\alpha&H00&\\fscx115\\fscy115)"
                    f"\\t({t1},{t2},1.4,\\fscx100\\fscy100)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                revealed_indices = list(reversed(range(i + 1))) if chunk_is_rtl else list(range(i + 1))

                revealed = []
                for j in revealed_indices:
                    w_text = chunk[j].get("word", "")
                    if j == i:
                        formatted = f"{{{hl_tag}{reveal_tag}}}{w_text}{{{pri_tag}\\fscx100\\fscy100}}"
                        revealed.append(formatted)
                    else:
                        revealed.append(f"{{{pri_tag}}}{w_text}")

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
            fade_tag = f"{{\\fad({fade_ms},{fade_ms})}}"
            start_str = format_ass_time(start)
            end_str = format_ass_time(end)
            text = seg.get("text", "").strip()
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{fade_tag}{text}")
        return events

    def build_box_highlight_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds box highlight style with fluid border expansion and accent badge."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        hl_ass = hex_to_ass_color(self.highlight_color)
        out_ass = hex_to_ass_color(self.outline_color)

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                w_end = chunk[i + 1]["start"] if (i + 1 < len(chunk)) else active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

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

                display_indices = list(reversed(range(len(chunk)))) if chunk_is_rtl else list(range(len(chunk)))

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = w.get("word", "")
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{box_tag}}}{word_text}{{{pri_tag}{reset_box}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}{reset_box}}}{word_text}")

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

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                w_end = chunk[i + 1]["start"] if (i + 1 < len(chunk)) else active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                dur_ms = max(120, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.3), int(90 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.6), int(180 / spd)))
                t3 = max(t2 + 30, min(int(dur_ms * 0.9), int(270 / spd)))

                bounce_tag = (
                    f"\\fscx100\\fscy100\\frz0"
                    f"\\t(0,{t1},0.5,\\fscy132\\fscx110\\frz-2)"
                    f"\\t({t1},{t2},1.5,\\fscy96\\fscx104\\frz1)"
                    f"\\t({t2},{t3},0.8,\\fscy104\\fscx102\\frz0)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = list(reversed(range(len(chunk)))) if chunk_is_rtl else list(range(len(chunk)))

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = w.get("word", "")
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{bounce_tag}}}{word_text}{{{pri_tag}{norm_tag}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}{norm_tag}}}{word_text}")

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

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                w_end = chunk[i + 1]["start"] if (i + 1 < len(chunk)) else active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.4), int(120 / spd)))
                t2 = max(t1 + 35, min(int(dur_ms * 0.8), int(240 / spd)))

                neon_tag = (
                    f"\\bord{self.outline_width}\\3c{out_ass}\\blur0\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\bord{self.outline_width + 4}\\3c{hl_ass}\\blur4\\fscx114\\fscy114)"
                    f"\\t({t1},{t2},1.3,\\bord{self.outline_width + 2.5}\\3c{hl_ass}\\blur2.5\\fscx108\\fscy108)"
                )
                reset_neon = f"\\bord{self.outline_width}\\3c{out_ass}\\blur0\\fscx100\\fscy100"

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = list(reversed(range(len(chunk)))) if chunk_is_rtl else list(range(len(chunk)))

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = w.get("word", "")
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
        norm_tag = f"{pri_tag}\\fscx100\\fscy100"

        for chunk in chunks:
            if not chunk:
                continue

            chunk_is_rtl = any(is_arabic_text(w.get("word", "")) for w in chunk)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                w_end = chunk[i + 1]["start"] if (i + 1 < len(chunk)) else active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.35), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.75), int(200 / spd)))

                flash_tag = (
                    f"\\c{hl_ass}\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\c&H00FFFF00&\\fscx120\\fscy120)"
                    f"\\t({t1},{t2},1.4,\\c{hl_ass}\\fscx108\\fscy108)"
                )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = list(reversed(range(len(chunk)))) if chunk_is_rtl else list(range(len(chunk)))

                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = w.get("word", "")
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

