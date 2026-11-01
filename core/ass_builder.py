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
from typing import List, Dict, Any, Optional


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
        margin_v: int = 90,
        words_per_line: int = 3,
        animation_style: str = "karaoke_pop",  # "karaoke_pop", "word_reveal", "classic_line", "box_highlight"
        video_width: int = 1080,
        video_height: int = 1920
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
        self.margin_v = margin_v
        self.words_per_line = max(1, words_per_line)
        self.animation_style = animation_style
        self.video_width = video_width
        self.video_height = video_height

    def generate_header(self) -> str:
        """Generates the ASS script header and style block."""
        pri_ass = hex_to_ass_color(self.primary_color)
        sec_ass = hex_to_ass_color(self.highlight_color)
        out_ass = hex_to_ass_color(self.outline_color)
        sha_ass = hex_to_ass_color(self.shadow_color, alpha=120)

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
Style: Default,{self.font_name},{self.font_size},{pri_ass},{sec_ass},{out_ass},{sha_ass},-1,0,0,0,100,100,0,0,1,{self.outline_width},{self.shadow_depth},{self.alignment},30,30,{self.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def chunk_words(self, words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Splits a flat list of words into chunks of `words_per_line`."""
        if not words:
            return []
        chunks = []
        for i in range(0, len(words), self.words_per_line):
            chunk = words[i:i + self.words_per_line]
            chunks.append(chunk)
        return chunks

    def build_karaoke_pop_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """
        Builds word-by-word pop and highlight events.
        For each word in the chunk, during its active timestamp, it is highlighted and scaled up.
        """
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        pop_scale = "\\fscx115\\fscy115"
        norm_scale = "\\fscx100\\fscy100"

        for chunk in chunks:
            if not chunk:
                continue

            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]
            # Add a small padding at the end of the chunk if there's a pause
            chunk_end = max(chunk_end, chunk_start + 0.3)

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                # Active word ends when next word begins, or at chunk_end
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    w_end = active_word["end"]

                if w_end <= w_start:
                    w_end = w_start + 0.25

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                # Assemble line with active word styled
                formatted_words = []
                for j, w in enumerate(chunk):
                    word_text = w.get("word", "")
                    if j == i:
                        # Active highlighted & scaled word
                        formatted_words.append(f"{{{hl_tag}{pop_scale}}}{word_text}{{{pri_tag}{norm_scale}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}{norm_scale}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_word_reveal_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds progressive word reveal events where words appear one by one."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"

        for chunk in chunks:
            if not chunk:
                continue
            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    w_end = chunk[i + 1]["start"]
                else:
                    w_end = active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                # Words revealed so far (0..i)
                revealed = []
                for j in range(i + 1):
                    w_text = chunk[j].get("word", "")
                    if j == i:
                        revealed.append(f"{{{hl_tag}\\fscx112\\fscy112}}{w_text}{{{pri_tag}\\fscx100\\fscy100}}")
                    else:
                        revealed.append(f"{{{pri_tag}}}{w_text}")

                line_text = " ".join(revealed)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_classic_line_events(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Builds classic subtitle lines with smooth fade in/out transitions."""
        events = []
        fade_tag = "{\\fad(120,120)}"
        for seg in segments:
            start_str = format_ass_time(seg["start"])
            end_str = format_ass_time(seg["end"])
            text = seg.get("text", "").strip()
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{fade_tag}{text}")
        return events

    def build_box_highlight_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds box highlight style with extra border and accent color."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        box_tag = f"\\bord{self.outline_width + 2}\\3c{hex_to_ass_color(self.highlight_color)}"
        reset_box = f"\\bord{self.outline_width}\\3c{hex_to_ass_color(self.outline_color)}"

        for chunk in chunks:
            if not chunk:
                continue
            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                w_end = chunk[i + 1]["start"] if (i + 1 < len(chunk)) else active_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.25

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                formatted_words = []
                for j, w in enumerate(chunk):
                    word_text = w.get("word", "")
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}{box_tag}}}{word_text}{{{pri_tag}{reset_box}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}}}{word_text}")

                line_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def generate_ass(self, transcription_data: Dict[str, Any]) -> str:
        """
        Generates full ASS file content from transcription data.
        """
        segments = transcription_data.get("segments", [])

        # Extract all words sequentially
        all_words = []
        for seg in segments:
            all_words.extend(seg.get("words", []))

        chunks = self.chunk_words(all_words)

        header = self.generate_header()
        events = []

        if self.animation_style == "karaoke_pop":
            events = self.build_karaoke_pop_events(chunks)
        elif self.animation_style == "word_reveal":
            events = self.build_word_reveal_events(chunks)
        elif self.animation_style == "box_highlight":
            events = self.build_box_highlight_events(chunks)
        elif self.animation_style == "classic_line":
            events = self.build_classic_line_events(segments)
        else:
            events = self.build_karaoke_pop_events(chunks)

        # Fallback if no words were generated
        if not events and segments:
            events = self.build_classic_line_events(segments)

        return header + "\n".join(events) + "\n"
