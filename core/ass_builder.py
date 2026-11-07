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


def classify_token_script(token: str, default: str = "arabic") -> str:
    """
    Classifies a word token into 'latin' (French/English) or 'arabic' (Darija/Arabic script).
    Tokens containing Latin letters (including loanwords with bound prefixes like 'الـ PPF', 'يـ percer')
    are classified as 'latin' to keep loanwords homogeneous and isolated. Pure Arabic words are 'arabic'.
    Neutral tokens (numbers, punctuation) inherit the active script context.
    """
    has_latin = bool(LATIN_REGEX.search(token))
    has_arabic = bool(ARABIC_REGEX.search(token))
    if has_latin:
        return "latin"
    elif has_arabic:
        return "arabic"
    else:
        return default


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
    r'[\u0648]?[\u064a\u062a\u0646][\u0640\-]+|'                                  # يـ, تـ, نـ (Darija imperfective verb prefixes e.g. يـ percer)
    r'[\u0648]?\u0645\u0627[\u0640\-]*|'                                          # ما, وما
    r'[\u0648]?\u064a\u0627[\u0640\-]*|'                                          # يا, ويا
    r'[\u0648]?\u0647\u0627[\u0640\-]*|'                                          # ها, وها
    r'[\u0628\u0641]?\u0647\u0627\u062f[\u0640\-]*'                               # بهاد, فهاد, هاد
    r')$'
)


def is_prefix_token(token: str, next_token: Optional[str] = None) -> bool:
    """Checks if a token is an orphaned Arabic article/particle/verb prefix."""
    t = str(token).strip()
    clean = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', t)
    if not clean:
        return False
    if bool(ARABIC_PREFIX_ARTICLE_REGEX.match(clean)) or t.endswith(("-", "ـ")):
        return True
    if clean in ("ي", "ت", "ن") and next_token and bool(LATIN_REGEX.search(str(next_token))):
        return True
    return False


def calculate_word_end_time(
    w_start: float,
    natural_end: float,
    next_chunk_start: Optional[float],
    min_hold_duration: float = 0.70,
    silence_threshold: float = 0.50,
    max_duration: float = 2.5
) -> float:
    """
    Calculates display end time for the final word in a chunk.
    - Strictly enforces max_duration rule: no subtitle stays on screen longer than 2.5s.
    - If there is a silence gap (> silence_threshold) before the next chunk,
      dismisses the subtitle cleanly at natural_end + 0.35s (does not linger over silence).
    - If speech continues promptly, bridges smoothly to next_chunk_start - 0.05s
      or maintains min_hold_duration.
    """
    if next_chunk_start is not None:
        gap = next_chunk_start - natural_end
        if gap > silence_threshold:
            chosen_end = max(w_start + 0.30, natural_end + 0.35)
        else:
            min_hold = w_start + min_hold_duration
            chosen_end = min(next_chunk_start - 0.05, max(natural_end, min_hold))
    else:
        min_hold = w_start + min_hold_duration
        chosen_end = max(natural_end, min_hold)

    return min(w_start + max_duration, max(w_start + 0.25, chosen_end))


def split_fused_script_tokens(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Splits hybrid tokens containing both Arabic and Latin characters into distinct
    tokens with accurate proportional timestamps.
    E.g. 'بهاد la' -> 'بهاد' (Arabic) + 'la' (Latin)
         'الـ premier' -> 'الـ' (Arabic) + 'premier' (Latin)
    """
    if not words:
        return []
    result: List[Dict[str, Any]] = []
    latin_then_arabic = re.compile(r'^([a-zA-Z0-9_\-]+)([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF].*)$')
    arabic_then_latin = re.compile(r'^([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s\-\u0640]+?)\s*([a-zA-Z].*)$')

    for w in words:
        text = str(w.get("word", "")).strip()
        dur = max(0.1, float(w.get("end", float(w.get("start", 0.0)) + 0.3)) - float(w.get("start", 0.0)))
        s = float(w.get("start", 0.0))
        e = float(w.get("end", s + 0.3))

        m1 = latin_then_arabic.match(text)
        if m1 and not text.endswith(("-", "ـ")):
            p1, p2 = m1.group(1).strip(), m1.group(2).strip()
            split_ratio = len(p1) / max(1, len(p1) + len(p2))
            mid = round(s + dur * split_ratio, 2)
            if p1:
                result.append({"word": p1, "start": s, "end": mid})
            if p2:
                result.append({"word": p2, "start": mid, "end": e})
            continue

        m2 = arabic_then_latin.match(text)
        if m2 and not text.endswith(("-", "ـ")):
            p1, p2 = m2.group(1).strip(), m2.group(2).strip()
            split_ratio = len(p1) / max(1, len(p1) + len(p2))
            mid = round(s + dur * split_ratio, 2)
            if p1:
                result.append({"word": p1, "start": s, "end": mid})
            if p2:
                result.append({"word": p2, "start": mid, "end": e})
            continue

        result.append(w)
    return result


def bind_arabic_articles_to_latin(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Binds orphaned Arabic definite articles (e.g. 'ال', 'الـ', 'لـ', 'لا', 'بهاد')
    and imperfective verb prefixes (e.g. 'يـ', 'تـ', 'نـ') to subsequent Latin loanwords
    (e.g. 'PPF', 'percer', 'premier', 'nouvelle'), treating them as a single highlighted token.
    Prevents awkward isolated article pop on screen and preserves natural bilingual phrasing.
    Supports chained prefixes (e.g. 'و' + 'لا' + 'nouvelle').
    Also merges isolated punctuation tokens and common French multi-word expressions ('par rapport').
    """
    if not words:
        return []
    bound: List[Dict[str, Any]] = []
    i = 0
    while i < len(words):
        w = words[i]
        text_val = str(w.get("word", "")).strip()

        # Merge isolated punctuation into previous word
        if text_val in (",", "،", ".", "!", "?", "؛", ":") and bound:
            prev = bound[-1]
            prev["word"] = f"{prev.get('word', '')}{text_val}"
            prev["end"] = max(float(prev.get("end", 0.0)), float(w.get("end", prev.get("end", 0.0))))
            i += 1
            continue

        next_w_val = words[i + 1].get("word", "") if i + 1 < len(words) else None

        # Bind multi-word French loan expressions: e.g. "par" + "rapport"
        if text_val.lower() == "par" and next_w_val and str(next_w_val).strip().lower().startswith("rapport"):
            next_w = words[i + 1]
            bound.append({
                "word": f"{text_val} {str(next_w.get('word', '')).strip()}",
                "start": w.get("start", 0.0),
                "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
            })
            i += 2
            continue

        # Bind French/Darija expressions: e.g. "c'est" + "bon", "سي" + "بون"
        if text_val.lower() in ("c'est", "سي") and next_w_val and str(next_w_val).strip().lower().startswith(("bon", "بون")):
            next_w = words[i + 1]
            bound.append({
                "word": f"{text_val} {str(next_w.get('word', '')).strip()}",
                "start": w.get("start", 0.0),
                "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
            })
            i += 2
            continue

        # Bind French article to Latin loanword: e.g. "la" + "différence" -> "la différence", "la" + "tôle" -> "la tôle"
        clean_tv = re.sub(r'^[^\w]+|[^\w]+$', '', text_val).lower()
        if clean_tv in ("la", "le", "les", "un", "une", "des", "du") and next_w_val and bool(LATIN_REGEX.search(str(next_w_val))):
            next_w = words[i + 1]
            bound.append({
                "word": f"{text_val} {str(next_w.get('word', '')).strip()}",
                "start": w.get("start", 0.0),
                "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
            })
            i += 2
            continue

        # Bind Arabic-only clitics (e.g. 'و' + 'السيارة', 'في' + 'الدار') - strictly Arabic only, never across to Latin!
        if is_prefix_token(text_val, next_w_val) and i + 1 < len(words) and not bool(LATIN_REGEX.search(str(next_w_val or ""))):
            chain = [w]
            j = i + 1
            while j < len(words):
                future_w = words[j + 1].get("word", "") if j + 1 < len(words) else None
                if is_prefix_token(words[j].get("word", ""), future_w) and not bool(LATIN_REGEX.search(str(future_w or ""))):
                    chain.append(words[j])
                    j += 1
                else:
                    break

            if j < len(words) and not bool(LATIN_REGEX.search(str(words[j].get("word", "")))):
                target_word = words[j]
                joint_text = " ".join(str(item.get("word", "")).strip() for item in chain) + " " + str(target_word.get("word", "")).strip()
                bound.append({
                    "word": joint_text.strip(),
                    "start": chain[0].get("start", 0.0),
                    "end": target_word.get("end", target_word.get("start", 0.0) + 0.3)
                })
                i = j + 1
                continue
            elif not bool(LATIN_REGEX.search(str(words[i + 1].get("word", "")))):
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


def format_bidi_word(word: str, in_rtl_context: bool = True) -> str:
    """
    Wraps Latin/French loanwords in Unicode Left-to-Right Isolates to prevent BiDi collisions
    with adjacent Arabic text in FriBidi / libass.
    For mixed tokens (e.g. 'الـ premier'), wraps only the Latin portion to keep the Arabic prefix in natural RTL.
    """
    if not in_rtl_context:
        return word
    has_latin = bool(LATIN_REGEX.search(word))
    has_arabic = bool(ARABIC_REGEX.search(word))
    if has_latin and has_arabic:
        return re.sub(r'([a-zA-Z0-9_\-]+)', lambda m: f"\u200E{m.group(1)}\u200E", word)
    elif has_latin:
        return f"\u200E{word}\u200E"
    return word


def resolve_visual_word_order(chunk: List[Dict[str, Any]], in_rtl_context: bool = True) -> List[int]:
    """
    With libass Encoding: -1 (FRIBIDI_PAR_ON), FriBidi automatically handles BiDi text layout
    preserving natural Right-to-Left Arabic reading order and Left-to-Right loanwords.
    Words maintain their authentic chronological speech order [0, 1, 2, ...].
    """
    return list(range(len(chunk)))


def balance_chunk_sizes(total_words: int, target_size: int = 4) -> List[int]:
    """
    Calculates balanced chunk sizes enforcing a strict 3-to-4 word limit
    for single-line short-form vertical video aesthetic.
    A chunk never exceeds 4 words.
    """
    effective_target = min(4, max(2, target_size))
    if total_words <= effective_target:
        return [total_words]
    num_chunks = max(1, math.ceil(total_words / effective_target))
    base_size = total_words // num_chunks
    remainder = total_words % num_chunks
    sizes = [base_size + (1 if k < remainder else 0) for k in range(num_chunks)]
    while any(s > 4 for s in sizes):
        num_chunks += 1
        base_size = total_words // num_chunks
        remainder = total_words % num_chunks
        sizes = [base_size + (1 if k < remainder else 0) for k in range(num_chunks)]
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


FONT_FAMILY_MAP = {
    "Cairo": "Cairo",
    "Tajawal": "Tajawal",
    "Lalezar": "Lalezar",
    "Amiri": "Amiri",
    "Almarai": "Almarai",
    "Changa": "Changa",
    "El Messiri": "El Messiri",
    "Readex Pro": "Readex Pro",
    "Rubik": "Rubik",
    "IBM Plex Sans Arabic": "IBM Plex Sans Arabic",
    "Reem Kufi": "Reem Kufi",
    "Alexandria": "Alexandria",
    "Baloo Bhaijaan 2": "Baloo Bhaijaan 2",
    "Aref Ruqaa": "Aref Ruqaa",
    "Marhey": "Marhey",
    "Noto Sans Arabic": "Noto Sans Arabic",
    "Noto Kufi Arabic": "Noto Kufi Arabic",
    "Lemonada": "Lemonada",
    "Mada": "Mada",
    "Harmattan": "Harmattan",
    "Montserrat": "Montserrat",
    "Anton": "Anton",
    "Bebas Neue": "Bebas Neue",
    "Outfit": "Outfit",
    "Poppins": "Poppins",
}

NON_TERMINAL_PARTICLES = {
    "و", "ف", "ب", "ل", "في", "على", "من", "عن", "مع", "إلى", "الى",
    "ما", "لا", "لي", "اللي", "دي", "دو", "يا", "ها", "بهاد", "فهاد", "هاد",
    "بهذا", "هذا", "هادي", "يعني", "كيما", "باش", "باشما", "علاش", "كيفاش", "وين", "وقتاش",
    "بلي", "كي", "غير", "حتى", "ما كاين", "ماكاين", "ما كاش", "ماكاش", "ما كانش",
    "la", "le", "les", "un", "une", "des", "du", "de", "d'", "et", "ou",
    "en", "au", "aux", "par", "pour", "avec", "dans", "sur"
}

def is_non_terminal_token(token: str) -> bool:
    clean = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', str(token).strip().lower())
    if clean in NON_TERMINAL_PARTICLES or str(token).strip().endswith(("-", "ـ")):
        return True
    if clean.startswith(("و", "ف")) and len(clean) > 1 and clean[1:] in NON_TERMINAL_PARTICLES:
        return True
    return False

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
        shadow_depth: float = 2.5,
        alignment: int = 2,  # 2: Bottom Center, 5: Middle Center, 8: Top Center
        margin_v: int = 960,  # Center of the screen (960px on 1920h)
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
        self.font_name = FONT_FAMILY_MAP.get(font_name, font_name)
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
        self.words_per_line = min(4, max(2, words_per_line))
        self.animation_style = animation_style
        self.video_width = video_width
        self.video_height = video_height
        self.animation_speed = max(0.3, min(3.0, float(animation_speed)))
        self.sub_box_style = sub_box_style or "none"
        self.sub_box_color = sub_box_color or "#000000"
        self.sub_box_alpha = max(0.0, min(1.0, float(sub_box_alpha)))
        self.is_arabic_mode = True

    def is_chunk_rtl(self, chunk: List[Dict[str, Any]]) -> bool:
        """
        Determines whether the subtitle chunk should render in Right-to-Left (RTL) base direction.
        In Algerian Darija subtitling, any chunk containing Arabic script, Arabic prefixes,
        or mixed Arabic/French loanwords ALWAYS has RTL base paragraph direction (\u200F).
        Only 100% purely Latin chunks with zero Arabic characters or context default to LTR.
        """
        has_arabic = any(bool(ARABIC_REGEX.search(str(w.get("word", "")))) for w in chunk)
        if has_arabic:
            return True
        return getattr(self, "is_arabic_mode", True)

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
            outline_val = max(1.5, min(6.0, float(self.outline_width)))
            # Clean, high-legibility mobile shadow with soft ambient blur
            sha_ass = hex_to_ass_color(self.shadow_color, alpha=35)
            shadow_val = max(0.0, min(5.0, float(self.shadow_depth)))

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
Style: Default,{self.font_name},{self.font_size},{pri_ass},{sec_ass},{out_ass},{sha_ass},-1,0,0,0,100,100,0,0,{border_style},{outline_val},{shadow_val},{self.alignment},30,30,{self.margin_v},-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header

    def chunk_words(self, words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Splits words into balanced, single-line bilingual subtitle chunks:
        - Strictly isolates French loanwords from Algerian Darija: forced chunk breaks before & after Latin strings.
        - Enforces strict 3 to 4 words maximum per chunk (maintains clean, single-line vertical short aesthetic).
        - Hard silence boundary: never crosses pauses > 0.50s (completely prevents future subtitle desync drift).
        """
        if not words:
            return []

        # 0. Normalization: restore dropped definite articles in key idioms ('وكان شرف' -> 'وكان الشرف')
        for widx in range(len(words) - 1):
            w1_txt = str(words[widx].get("word", "")).strip()
            w2_txt = str(words[widx + 1].get("word", "")).strip()
            if w1_txt in ("وكان", "كان") and w2_txt == "شرف":
                words[widx + 1]["word"] = "الشرف"

        # 1. Split fused Arabic/Latin tokens (e.g. 'بهاد la' -> 'بهاد' + 'la')
        words = split_fused_script_tokens(words)

        # 2. Bind internal French articles ('le premier', 'la nouvelle', 'par rapport')
        words = bind_arabic_articles_to_latin(words)
        if not words:
            return []

        target_size = min(4, max(2, self.words_per_line))

        # 3. Form script-isolated chunks with hard pause boundaries
        raw_chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = []
        current_script: Optional[str] = None

        for w in words:
            w_text = str(w.get("word", "")).strip()
            if not w_text:
                continue

            w_script = "latin" if bool(LATIN_REGEX.search(w_text)) else "arabic"

            pause_gap = 0.0
            if current_chunk:
                prev_w = current_chunk[-1]
                prev_end = float(prev_w.get("end", float(prev_w.get("start", 0.0)) + 0.3))
                pause_gap = float(w.get("start", 0.0)) - prev_end

            prev_text = str(current_chunk[-1].get("word", "")).strip() if current_chunk else ""
            prev_clean = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', prev_text.lower())
            has_major_stop = any(prev_text.endswith(p) for p in (".", "!", "?", "،", ","))

            # Never break after a negative existential copula before 'حتى' or noun
            is_inseparable = (prev_clean in ("ما كاين", "ماكاين", "ما كاش", "ماكاش", "ما كانش") and w_text.startswith("حتى")) or (prev_clean == "حتى" and not is_non_terminal_token(w_text))

            should_break = False
            if current_chunk:
                # Forced break before and after Latin loan strings to eliminate BiDi layout collisions
                if w_script != current_script:
                    should_break = True
                # Hard silence boundary: never cross pause > 0.50s
                elif pause_gap > 0.50:
                    should_break = True
                elif is_inseparable:
                    should_break = False
                # Strict 3-4 words max per chunk
                elif len(current_chunk) >= target_size:
                    should_break = True
                # Break before non-terminal particles when chunk already has >= 2 words to preserve natural phrasing
                elif len(current_chunk) >= 2 and is_non_terminal_token(w_text):
                    should_break = True
                # Punctuation boundary when chunk has >= 2 words
                elif has_major_stop and len(current_chunk) >= 2:
                    should_break = True

            if should_break and current_chunk:
                raw_chunks.append(current_chunk)
                current_chunk = []

            current_chunk.append(w)
            current_script = w_script

        if current_chunk:
            raw_chunks.append(current_chunk)

        # 4. Anti-orphan pass: only merge tiny 1-word fragments if SAME script, gap <= 0.40s, and combined <= 4 words
        merged_chunks: List[List[Dict[str, Any]]] = []
        for c in raw_chunks:
            if not c:
                continue
            if merged_chunks:
                prev_c = merged_chunks[-1]
                prev_script = "latin" if bool(LATIN_REGEX.search(str(prev_c[-1].get("word", "")))) else "arabic"
                curr_script = "latin" if bool(LATIN_REGEX.search(str(c[0].get("word", "")))) else "arabic"
                prev_end = float(prev_c[-1].get("end", float(prev_c[-1].get("start", 0.0)) + 0.3))
                gap = float(c[0].get("start", 0.0)) - prev_end

                if prev_script == curr_script and gap <= 0.40 and len(prev_c) + len(c) <= target_size and (len(c) == 1 or len(prev_c) == 1):
                    prev_c.extend(c)
                    continue

            merged_chunks.append(c)

        return merged_chunks

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

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

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
                    f"\\t(0,{t1},0.45,\\fscx120\\fscy120)"
                    f"\\t({t1},{t2},1.6,\\fscx108\\fscy108)"
                    f"\\t({t2},{t3},0.8,\\fscx114\\fscy114)"
                    f"\\t({t3},{t4},1.3,\\fscx100\\fscy100)"
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
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
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

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.45), int(110 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.85), int(220 / spd)))

                reveal_tag = (
                    f"\\alpha&HFF&\\blur1.8\\fscx100\\fscy90"
                    f"\\t(0,{t1},0.6,\\alpha&H00&\\fscx100\\fscy115)"
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
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
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

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.4), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.8), int(200 / spd)))

                box_tag = (
                    f"\\bord{self.outline_width}\\3c{out_ass}\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\bord{self.outline_width + 0.8}\\3c{hl_ass}\\fscx100\\fscy114)"
                    f"\\t({t1},{t2},1.3,\\bord{self.outline_width}\\3c{hl_ass}\\fscx100\\fscy106)"
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
                        formatted_words.append(f"{{{hl_tag}\\blur0.8{box_tag}}}{word_text}{{{pri_tag}{reset_box}}}")
                    else:
                        formatted_words.append(f"{{{pri_tag}\\blur1.8{reset_box}}}{word_text}")

                line_text = " ".join(formatted_words)
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_bouncy_spring_events(self, chunks: List[List[Dict[str, Any]]]) -> List[str]:
        """Builds energetic bouncy spring animation with fluid elastic bounce physics."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        norm_tag = "\\fscx100\\fscy100"

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(120, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.3), int(90 / spd)))
                t2 = max(t1 + 25, min(int(dur_ms * 0.6), int(180 / spd)))
                t3 = max(t2 + 25, min(int(dur_ms * 0.85), int(260 / spd)))
                t4 = max(t3 + 20, min(dur_ms, int(330 / spd)))

                bounce_tag = (
                    f"\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.45,\\fscx124\\fscy124)"
                    f"\\t({t1},{t2},1.6,\\fscx96\\fscy96)"
                    f"\\t({t2},{t3},0.8,\\fscx112\\fscy112)"
                    f"\\t({t3},{t4},1.3,\\fscx100\\fscy100)"
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
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
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

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(35, min(int(dur_ms * 0.4), int(120 / spd)))
                t2 = max(t1 + 35, min(int(dur_ms * 0.8), int(240 / spd)))

                neon_tag = (
                    f"\\bord{self.outline_width}\\3c{out_ass}\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\bord{self.outline_width + 4}\\3c{hl_ass}\\blur4.5\\fscx100\\fscy116)"
                    f"\\t({t1},{t2},1.3,\\bord{self.outline_width + 2.5}\\3c{hl_ass}\\blur2.5\\fscx100\\fscy108)"
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
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
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

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.35), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.75), int(200 / spd)))

                flash_tag = (
                    f"\\c{hl_ass}\\blur1.8\\fscx100\\fscy100"
                    f"\\t(0,{t1},0.6,\\c&H00FFFF00&\\blur2.2\\fscx100\\fscy118)"
                    f"\\t({t1},{t2},1.4,\\c{hl_ass}\\blur1.8\\fscx100\\fscy106)"
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
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_letter_pop_events(self, chunks: List[List[Dict[str, Any]]], style_type: str = "pop") -> List[str]:
        """Builds kinetic letter-by-letter popping subtitles with spring dynamics."""
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        out_ass = hex_to_ass_color(self.outline_color)

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.35), int(80 / spd)))
                t2 = max(t1 + 25, min(int(dur_ms * 0.7), int(160 / spd)))

                if style_type == "drop":
                    pop_tag = (
                        f"\\fscx85\\fscy85"
                        f"\\t(0,{t1},0.5,\\fscx120\\fscy120)"
                        f"\\t({t1},{t2},1.4,\\fscx100\\fscy100)"
                    )
                elif style_type == "rise":
                    pop_tag = (
                        f"\\fscx90\\fscy90"
                        f"\\t(0,{t1},0.6,\\fscx120\\fscy120)"
                        f"\\t({t1},{t2},1.3,\\fscx100\\fscy100)"
                    )
                else:
                    pop_tag = (
                        f"\\fscx60\\fscy60"
                        f"\\t(0,{t1},0.5,\\fscx125\\fscy125)"
                        f"\\t({t1},{t2},1.4,\\fscx100\\fscy100)"
                    )

                reset_tag = "\\fscx100\\fscy100"
                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)
                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j == i:
                        formatted_words.append(f"{{{hl_tag}\\blur0.8{pop_tag}}}{word_text}{{{pri_tag}{reset_tag}}}")
                    elif j < i:
                        formatted_words.append(f"{{{pri_tag}\\blur0.8{reset_tag}}}{word_text}")
                    else:
                        formatted_words.append(f"{{{pri_tag}\\alpha&H88&\\blur0.8{reset_tag}}}{word_text}")

                line_text = " ".join(formatted_words)
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def build_cumulative_fill_events(self, chunks: List[List[Dict[str, Any]]], style_type: str = "pop") -> List[str]:
        """
        Builds cumulative word fill animations: words transition to highlight color
        as spoken and remain permanently highlighted for the rest of the sentence.
        """
        events = []
        pri_tag = f"\\c{hex_to_ass_color(self.primary_color)}"
        hl_tag = f"\\c{hex_to_ass_color(self.highlight_color)}"
        spd = self.animation_speed
        norm_tag = "\\fscx100\\fscy100"

        for chunk_idx, chunk in enumerate(chunks):
            if not chunk:
                continue

            chunk_is_rtl = self.is_chunk_rtl(chunk)
            next_chunk_start = chunks[chunk_idx + 1][0]["start"] if chunk_idx + 1 < len(chunks) else None

            for i, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if i + 1 < len(chunk):
                    next_start = float(chunk[i + 1]["start"])
                    nat_end = float(active_word.get("end", w_start + 0.3))
                    if next_start - nat_end > 0.50:
                        w_end = nat_end + 0.25
                    else:
                        w_end = next_start
                else:
                    w_end = calculate_word_end_time(w_start, active_word["end"], next_chunk_start, min_hold_duration=0.70, silence_threshold=0.50)

                if w_end <= w_start:
                    w_end = w_start + 0.30

                dur_ms = max(100, int((w_end - w_start) * 1000))
                t1 = max(30, min(int(dur_ms * 0.4), int(100 / spd)))
                t2 = max(t1 + 30, min(int(dur_ms * 0.8), int(200 / spd)))

                if style_type == "glow":
                    active_tag = (
                        f"\\t(0,{t1},0.6,\\fscx116\\fscy116\\blur3.5)"
                        f"\\t({t1},{t2},1.3,\\fscx104\\fscy104\\blur1.8)"
                    )
                elif style_type == "bounce":
                    active_tag = (
                        f"\\t(0,{t1},0.5,\\fscx122\\fscy122)"
                        f"\\t({t1},{t2},1.4,\\fscx104\\fscy104)"
                    )
                else:
                    active_tag = (
                        f"\\t(0,{t1},0.6,\\fscx118\\fscy118)"
                        f"\\t({t1},{t2},1.3,\\fscx100\\fscy100)"
                    )

                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                display_indices = resolve_visual_word_order(chunk, in_rtl_context=chunk_is_rtl)
                formatted_words = []
                for j in display_indices:
                    w = chunk[j]
                    word_text = format_bidi_word(w.get("word", ""), in_rtl_context=chunk_is_rtl)
                    if j < i:
                        # Previously spoken in this sentence: REMAINS in highlight color!
                        formatted_words.append(f"{{{hl_tag}\\blur0.8{norm_tag}}}{word_text}")
                    elif j == i:
                        # Currently being spoken: POP and turn to highlight color!
                        formatted_words.append(f"{{{hl_tag}\\blur0.8{active_tag}}}{word_text}{{{pri_tag}{norm_tag}}}")
                    else:
                        # Not yet spoken in this sentence: remains primary (unspoken) color
                        formatted_words.append(f"{{{pri_tag}\\blur0.8{norm_tag}}}{word_text}")

                line_text = " ".join(formatted_words)
                if chunk_is_rtl:
                    line_text = f"\u200F{line_text}"
                else:
                    line_text = f"\u200E{line_text}"
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        return events

    def generate_ass(self, transcription_data: Dict[str, Any]) -> str:
        """
        Generates full ASS file content from transcription data.
        Chunks words per segment to preserve natural pauses and prevent subtitle drift.
        """
        segments = transcription_data.get("segments", [])
        has_arabic = any(bool(ARABIC_REGEX.search(str(seg.get("text", "")))) for seg in segments)
        lang = str(transcription_data.get("language", "")).lower()
        self.is_arabic_mode = has_arabic or lang.startswith("ar") or "algerian" in lang

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

        anim = (self.animation_style or "karaoke_pop").lower().replace("-", "_")

        if anim in ("karaoke_pop", "hormozi_pop"):
            events = self.build_karaoke_pop_events(chunks)
        elif anim in ("bouncy_spring", "comic_bounce"):
            events = self.build_bouncy_spring_events(chunks)
        elif anim in ("neon_glow", "cyber_glitch", "cyber_pulse"):
            events = self.build_neon_glow_events(chunks)
        elif anim in ("minimal_slide", "smooth_slide"):
            events = self.build_word_reveal_events(chunks)
        elif anim in ("viral_punch", "typewriter_pop"):
            events = self.build_karaoke_pop_events(chunks)
        elif anim in ("letter_pop", "letter_bounce", "letter_snap"):
            events = self.build_letter_pop_events(chunks, style_type="pop")
        elif anim in ("letter_drop", "gravity_drop"):
            events = self.build_letter_pop_events(chunks, style_type="drop")
        elif anim in ("letter_rise", "wave_rise"):
            events = self.build_letter_pop_events(chunks, style_type="rise")
        elif anim in ("cumulative_fill", "cumulative_pop", "hormozi_fill", "word_fill"):
            events = self.build_cumulative_fill_events(chunks, style_type="pop")
        elif anim in ("cumulative_bounce", "bounce_stay"):
            events = self.build_cumulative_fill_events(chunks, style_type="bounce")
        elif anim in ("cumulative_glow", "neon_lock"):
            events = self.build_cumulative_fill_events(chunks, style_type="glow")
        elif anim in ("box_highlight", "badge_invert"):
            events = self.build_box_highlight_events(chunks)
        elif anim == "color_flash":
            events = self.build_color_flash_events(chunks)
        elif anim == "word_reveal":
            events = self.build_word_reveal_events(chunks)
        elif anim in ("classic_line", "classic_fade", "fade_editorial", "fade_highlight"):
            events = self.build_classic_line_events(segments)
        else:
            events = self.build_karaoke_pop_events(chunks)

        # Fallback if no words were generated
        if not events and segments:
            events = self.build_classic_line_events(segments)

        return header + "\n".join(events) + "\n"

