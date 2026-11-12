"""
Arabic contextual letter shaping module for kinetic letter-by-letter subtitle animations.
Decomposes words into contextual presentation glyphs (isolated, initial, medial, final)
and Lam-Alef ligatures so that individual letters can be animated with spring physics
while preserving flawless cursive connectivity.
"""
import re
from typing import List

ARABIC_GLYPHS = {
    '\u0621': {'iso': '\uFE80'},
    '\u0622': {'iso': '\uFE81', 'fin': '\uFE82'},
    '\u0623': {'iso': '\uFE83', 'fin': '\uFE84'},
    '\u0624': {'iso': '\uFE85', 'fin': '\uFE86'},
    '\u0625': {'iso': '\uFE87', 'fin': '\uFE88'},
    '\u0626': {'iso': '\uFE89', 'fin': '\uFE8A', 'ini': '\uFE8B', 'med': '\uFE8C'},
    '\u0627': {'iso': '\uFE8D', 'fin': '\uFE8E'},
    '\u0628': {'iso': '\uFE8F', 'fin': '\uFE90', 'ini': '\uFE91', 'med': '\uFE92'},
    '\u0629': {'iso': '\uFE93', 'fin': '\uFE94'},
    '\u062A': {'iso': '\uFE95', 'fin': '\uFE96', 'ini': '\uFE97', 'med': '\uFE98'},
    '\u062B': {'iso': '\uFE99', 'fin': '\uFE9A', 'ini': '\uFE9B', 'med': '\uFE9C'},
    '\u062C': {'iso': '\uFE9D', 'fin': '\uFE9E', 'ini': '\uFE9F', 'med': '\uFEA0'},
    '\u062D': {'iso': '\uFEA1', 'fin': '\uFEA2', 'ini': '\uFEA3', 'med': '\uFEA4'},
    '\u062E': {'iso': '\uFEA5', 'fin': '\uFEA6', 'ini': '\uFEA7', 'med': '\uFEA8'},
    '\u062F': {'iso': '\uFEA9', 'fin': '\uFEAA'},
    '\u0630': {'iso': '\uFEAB', 'fin': '\uFEAC'},
    '\u0631': {'iso': '\uFEAD', 'fin': '\uFEAE'},
    '\u0632': {'iso': '\uFEAF', 'fin': '\uFEB0'},
    '\u0633': {'iso': '\uFEB1', 'fin': '\uFEB2', 'ini': '\uFEB3', 'med': '\uFEB4'},
    '\u0634': {'iso': '\uFEB5', 'fin': '\uFEB6', 'ini': '\uFEB7', 'med': '\uFEB8'},
    '\u0635': {'iso': '\uFEB9', 'fin': '\uFEBA', 'ini': '\uFEBB', 'med': '\uFEBC'},
    '\u0636': {'iso': '\uFEBD', 'fin': '\uFEBE', 'ini': '\uFEBF', 'med': '\uFEC0'},
    '\u0637': {'iso': '\uFEC1', 'fin': '\uFEC2', 'ini': '\uFEC3', 'med': '\uFEC4'},
    '\u0638': {'iso': '\uFEC5', 'fin': '\uFEC6', 'ini': '\uFEC7', 'med': '\uFEC8'},
    '\u0639': {'iso': '\uFEC9', 'fin': '\uFECA', 'ini': '\uFECB', 'med': '\uFECC'},
    '\u063A': {'iso': '\uFECD', 'fin': '\uFECE', 'ini': '\uFECF', 'med': '\uFED0'},
    '\u0640': {'iso': '\u0640', 'fin': '\u0640', 'ini': '\u0640', 'med': '\u0640'},
    '\u0641': {'iso': '\uFED1', 'fin': '\uFED2', 'ini': '\uFED3', 'med': '\uFED4'},
    '\u0642': {'iso': '\uFED5', 'fin': '\uFED6', 'ini': '\uFED7', 'med': '\uFED8'},
    '\u0643': {'iso': '\uFED9', 'fin': '\uFEDA', 'ini': '\uFEDB', 'med': '\uFEDC'},
    '\u0644': {'iso': '\uFEDD', 'fin': '\uFEDE', 'ini': '\uFEDF', 'med': '\uFEE0'},
    '\u0645': {'iso': '\uFEE1', 'fin': '\uFEE2', 'ini': '\uFEE3', 'med': '\uFEE4'},
    '\u0646': {'iso': '\uFEE5', 'fin': '\uFEE6', 'ini': '\uFEE7', 'med': '\uFEE8'},
    '\u0647': {'iso': '\uFEE9', 'fin': '\uFEEA', 'ini': '\uFEEB', 'med': '\uFEEC'},
    '\u0648': {'iso': '\uFEED', 'fin': '\uFEEE'},
    '\u0649': {'iso': '\uFEEF', 'fin': '\uFEF0', 'ini': '\uFEF3', 'med': '\uFEF4'},
    '\u064A': {'iso': '\uFEF1', 'fin': '\uFEF2', 'ini': '\uFEF3', 'med': '\uFEF4'},
    '\u0671': {'iso': '\uFB50', 'fin': '\uFB51'},
    '\u06A4': {'iso': '\uFB6A', 'fin': '\uFB6B', 'ini': '\uFB6C', 'med': '\uFB6D'},
    '\u06AD': {'iso': '\uFBD3', 'fin': '\uFBD4', 'ini': '\uFBD5', 'med': '\uFBD6'},
    '\u067E': {'iso': '\uFB56', 'fin': '\uFB57', 'ini': '\uFB58', 'med': '\uFB59'},
    '\u0686': {'iso': '\uFB7A', 'fin': '\uFB7B', 'ini': '\uFB7C', 'med': '\uFB7D'},
    '\u06AF': {'iso': '\uFB92', 'fin': '\uFB93', 'ini': '\uFB94', 'med': '\uFB95'},
    '\u0698': {'iso': '\uFB8A', 'fin': '\uFB8B'},
}

LA_LIGATURES = {
    '\u0622': {'iso': '\uFEF5', 'fin': '\uFEF6'},
    '\u0623': {'iso': '\uFEF7', 'fin': '\uFEF8'},
    '\u0625': {'iso': '\uFEF9', 'fin': '\uFEFA'},
    '\u0627': {'iso': '\uFEFB', 'fin': '\uFEFC'},
    '\u0671': {'iso': '\uFEFB', 'fin': '\uFEFC'},
}

DIACRITIC_REGEX = re.compile(r'[\u064B-\u065F\u0670]')
ARABIC_CHAR_REGEX = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')


def is_arabic_text(text: str) -> bool:
    """Returns True if text contains Arabic characters."""
    return bool(ARABIC_CHAR_REGEX.search(text))


def shape_arabic_word_to_letters(word: str) -> List[str]:
    """
    Decomposes an Arabic word into contextual cursive presentation glyphs
    (isolated, initial, medial, final) and Lam-Alef ligatures.
    Matches browser preview shaping exactly.
    """
    if not word:
        return []

    raw_chars = list(word)
    base_chars: List[str] = []
    diacritics: List[str] = []

    for ch in raw_chars:
        if DIACRITIC_REGEX.match(ch):
            if diacritics:
                diacritics[-1] += ch
        else:
            base_chars.append(ch)
            diacritics.append('')

    shaped: List[str] = []
    i = 0
    while i < len(base_chars):
        ch = base_chars[i]
        prev_ch = base_chars[i - 1] if i > 0 else None
        next_ch = base_chars[i + 1] if i + 1 < len(base_chars) else None

        # Lam-Alef ligatures
        if ch == '\u0644' and next_ch and next_ch in LA_LIGATURES:
            prev_entry = ARABIC_GLYPHS.get(prev_ch) if prev_ch else None
            connects_prev = bool(prev_entry and (prev_entry.get('ini') or prev_entry.get('med')))
            lig = LA_LIGATURES[next_ch]
            lig_glyph = (lig['fin'] if connects_prev else lig['iso']) + diacritics[i] + diacritics[i + 1]
            shaped.append(lig_glyph)
            i += 2
            continue

        entry = ARABIC_GLYPHS.get(ch)
        if not entry:
            shaped.append(ch + diacritics[i])
            i += 1
            continue

        prev_entry = ARABIC_GLYPHS.get(prev_ch) if prev_ch else None
        next_entry = ARABIC_GLYPHS.get(next_ch) if next_ch else None

        connects_prev = bool(prev_entry and (prev_entry.get('ini') or prev_entry.get('med')) and (entry.get('fin') or entry.get('med')))
        connects_next = bool(next_entry and (entry.get('ini') or entry.get('med')) and (next_entry.get('fin') or next_entry.get('med')))

        glyph = entry.get('iso', ch)
        if connects_prev and connects_next and entry.get('med'):
            glyph = entry['med']
        elif connects_prev and entry.get('fin'):
            glyph = entry['fin']
        elif connects_next and entry.get('ini'):
            glyph = entry['ini']

        shaped.append(glyph + diacritics[i])
        i += 1

    return shaped


def decompose_arabic_word_zwj(word: str) -> List[str]:
    """
    Decomposes an Arabic word into sequential character tokens preserving cursive connectivity
    via standard Arabic characters and Zero-Width Joiner (ZWJ, \\u200D).
    This allows libass and DirectWrite to shape Arabic natively via OpenType GSUB tables
    without using deprecated Unicode Presentation Forms B (which cause Arial fallback in Tajawal/Cairo/Almarai).
    """
    if not word:
        return []

    zwj = '\u200D'
    raw_chars = list(word)
    base_chars: List[str] = []
    diacritics: List[str] = []

    for ch in raw_chars:
        if DIACRITIC_REGEX.match(ch):
            if diacritics:
                diacritics[-1] += ch
        else:
            base_chars.append(ch)
            diacritics.append('')

    tokens: List[str] = []
    i = 0
    while i < len(base_chars):
        ch = base_chars[i]
        prev_ch = base_chars[i - 1] if i > 0 else None
        next_ch = base_chars[i + 1] if i + 1 < len(base_chars) else None

        # Check Lam-Alef ligature
        if ch == '\u0644' and next_ch and next_ch in LA_LIGATURES:
            prev_entry = ARABIC_GLYPHS.get(prev_ch) if prev_ch else None
            connects_prev = bool(prev_entry and (prev_entry.get('ini') or prev_entry.get('med')))
            tok = (zwj if connects_prev else '') + ch + next_ch + diacritics[i] + diacritics[i + 1]
            tokens.append(tok)
            i += 2
            continue

        entry = ARABIC_GLYPHS.get(ch)
        if not entry:
            tokens.append(ch + diacritics[i])
            i += 1
            continue

        prev_entry = ARABIC_GLYPHS.get(prev_ch) if prev_ch else None
        next_entry = ARABIC_GLYPHS.get(next_ch) if next_ch else None

        connects_prev = bool(prev_entry and (prev_entry.get('ini') or prev_entry.get('med')) and (entry.get('fin') or entry.get('med')))
        connects_next = bool(next_entry and (entry.get('ini') or entry.get('med')) and (next_entry.get('fin') or next_entry.get('med')))

        tok = ''
        if connects_prev:
            tok += zwj
        tok += ch + diacritics[i]
        if connects_next:
            tok += zwj
        tokens.append(tok)
        i += 1

    return tokens
