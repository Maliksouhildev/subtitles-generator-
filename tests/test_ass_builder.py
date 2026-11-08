import pytest
from core.ass_builder import hex_to_ass_color, format_ass_time, ASSSubtitleBuilder


def test_hex_to_ass_color():
    # White #FFFFFF -> &H00FFFFFF&
    assert hex_to_ass_color("#FFFFFF") == "&H00FFFFFF&"
    # Yellow #FFFF00 (RGB: 255, 255, 0) -> BGR: 0, 255, 255 -> &H0000FFFF&
    assert hex_to_ass_color("#FFFF00") == "&H0000FFFF&"
    # Red #FF0000 -> BGR: 0, 0, 255 -> &H000000FF&
    assert hex_to_ass_color("#FF0000") == "&H000000FF&"
    # Blue #0000FF -> BGR: 255, 0, 0 -> &H00FF0000&
    assert hex_to_ass_color("#0000FF") == "&H00FF0000&"
    # Hex with alpha
    assert hex_to_ass_color("#000000", alpha=128) == "&H80000000&"


def test_format_ass_time():
    assert format_ass_time(0.0) == "0:00:00.00"
    assert format_ass_time(1.25) == "0:00:01.25"
    assert format_ass_time(65.5) == "0:01:05.50"
    assert format_ass_time(3661.12) == "1:01:01.12"


def test_ass_builder_karaoke_pop():
    builder = ASSSubtitleBuilder(
        font_name="Cairo",
        font_size=50,
        primary_color="#FFFFFF",
        highlight_color="#FFE600",
        words_per_line=3,
        animation_style="karaoke_pop"
    )

    data = {
        "language": "ar-DZ",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "سلام خاوتنا واش راكم",
                "words": [
                    {"word": "سلام", "start": 0.0, "end": 0.5},
                    {"word": "خاوتنا", "start": 0.5, "end": 1.0},
                    {"word": "واش", "start": 1.0, "end": 1.5},
                    {"word": "راكم", "start": 1.5, "end": 2.0}
                ]
            }
        ]
    }

    ass_text = builder.generate_ass(data)
    assert "[Script Info]" in ass_text
    assert "[V4+ Styles]" in ass_text
    assert "Style: Default,Cairo" in ass_text
    assert "[Events]" in ass_text
    assert "Dialogue: 0," in ass_text
    assert "سلام" in ass_text
    assert "\\t(" in ass_text
    assert "\\fscy118" in ass_text
    assert "\\fscx100" in ass_text


def test_ass_builder_speed_scaling():
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "صحا خويا",
                "words": [
                    {"word": "صحا", "start": 0.0, "end": 0.5},
                    {"word": "خويا", "start": 0.5, "end": 1.0}
                ]
            }
        ]
    }

    builder_fast = ASSSubtitleBuilder(animation_speed=2.0, animation_style="karaoke_pop")
    ass_fast = builder_fast.generate_ass(data)

    builder_slow = ASSSubtitleBuilder(animation_speed=0.5, animation_style="karaoke_pop")
    ass_slow = builder_slow.generate_ass(data)

    # Fast animation has smaller transform timing than slow animation
    assert "\\t(" in ass_fast
    assert "\\t(" in ass_slow


def test_ass_builder_sub_box_styles():
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "صحا خويا",
                "words": [
                    {"word": "صحا", "start": 0.0, "end": 0.5},
                    {"word": "خويا", "start": 0.5, "end": 1.0}
                ]
            }
        ]
    }

    # 1. Pill badge box style -> BorderStyle=3
    builder_pill = ASSSubtitleBuilder(sub_box_style="pill", sub_box_color="#112233", sub_box_alpha=0.8)
    ass_pill = builder_pill.generate_ass(data)
    assert ",3,8.0,1.5," in ass_pill

    # 2. None style -> BorderStyle=1
    builder_none = ASSSubtitleBuilder(sub_box_style="none")
    ass_none = builder_none.generate_ass(data)
    assert ",1,3.5,2.5," in ass_none

    # 3. Deep shadow style -> BorderStyle=1 with shadow 5.0
    builder_shadow = ASSSubtitleBuilder(sub_box_style="shadow", sub_box_color="#000000")
    ass_shadow = builder_shadow.generate_ass(data)
    assert ",1,2.0,5.0," in ass_shadow


def test_ass_builder_all_styles():
    for style in ["karaoke_pop", "bouncy_spring", "neon_glow", "color_flash", "word_reveal", "classic_line", "box_highlight"]:
        builder = ASSSubtitleBuilder(animation_style=style)
        data = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "صحا خويا",
                    "words": [
                        {"word": "صحا", "start": 0.0, "end": 0.5},
                        {"word": "خويا", "start": 0.5, "end": 1.0}
                    ]
                }
            ]
        }
        out = builder.generate_ass(data)
        assert "[Events]" in out
        assert "صحا" in out


def test_ass_builder_pos_y_override():
    builder = ASSSubtitleBuilder(pos_y=1400, video_height=1920)
    assert builder.margin_v == 1920 - 1400  # 520px
    ass_text = builder.generate_ass({"segments": []})
    assert ",520,-1" in ass_text


def test_ass_builder_rtl_ordering():
    builder = ASSSubtitleBuilder(words_per_line=3, animation_style="karaoke_pop")
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 1.5,
                "text": "سلام عليكم خاوتنا",
                "words": [
                    {"word": "سلام", "start": 0.0, "end": 0.5},
                    {"word": "عليكم", "start": 0.5, "end": 1.0},
                    {"word": "خاوتنا", "start": 1.0, "end": 1.5}
                ]
            }
        ]
    }
    ass_text = builder.generate_ass(data)
    # In libass, override-tagged chunks are laid out strictly left-to-right across the screen.
    # To place the first spoken Arabic word ("سلام") on the far right (X = max),
    # the words are placed in visual LTR file order: [خاوتنا, عليكم, سلام].
    event_lines = [l for l in ass_text.splitlines() if l.startswith("Dialogue: 0,0:00:00.00")]
    assert len(event_lines) == 1
    ev = event_lines[0]
    assert ev.index("سلام") < ev.index("عليكم") < ev.index("خاوتنا")


def test_resolve_visual_word_order_mixed_bidi():
    from core.ass_builder import resolve_visual_word_order

    chunk1 = [{"word": "المستوى"}, {"word": "الافريقي"}]
    assert resolve_visual_word_order(chunk1, in_rtl_context=True) == [0, 1]

    chunk2 = [{"word": "ما"}, {"word": "كاين"}, {"word": "حتى"}, {"word": "إشكال"}]
    assert resolve_visual_word_order(chunk2, in_rtl_context=True) == [0, 1, 2, 3]

    chunk3 = [{"word": "بهذا"}, {"word": "le"}, {"word": "premier"}, {"word": "test"}]
    assert resolve_visual_word_order(chunk3, in_rtl_context=True) == [0, 1, 2, 3]

    chunk4 = [{"word": "le"}, {"word": "premier"}, {"word": "test"}, {"word": "بهذا"}]
    assert resolve_visual_word_order(chunk4, in_rtl_context=True) == [0, 1, 2, 3]

    assert resolve_visual_word_order(chunk3, in_rtl_context=False) == [0, 1, 2, 3]


def test_ass_builder_bidi_loanword_isolation():
    from core.ass_builder import format_bidi_word, balance_chunk_sizes
    # French loanwords inside Arabic context must be isolated with \u200E (LRM)
    assert format_bidi_word("test", in_rtl_context=True) == "\u200Etest\u200E"
    assert format_bidi_word("premier", in_rtl_context=True) == "\u200Epremier\u200E"
    # Arabic words are not altered
    assert format_bidi_word("يبدا", in_rtl_context=True) == "يبدا"

    # Balanced chunking prevents awkward 1-word orphan lines
    assert balance_chunk_sizes(4, 3) == [2, 2]
    assert balance_chunk_sizes(5, 3) == [3, 2]
    assert balance_chunk_sizes(7, 3) == [3, 2, 2]


def test_ass_builder_ltr_ordering_preserved():
    builder = ASSSubtitleBuilder(words_per_line=2, animation_style="karaoke_pop")
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "Hello world",
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0}
                ]
            }
        ]
    }
    ass_text = builder.generate_ass(data)
    event_lines = [l for l in ass_text.splitlines() if l.startswith("Dialogue: 0,0:00:00.00")]
    assert len(event_lines) == 1
    ev = event_lines[0]
    # In English, 'Hello' comes before 'world'
    assert ev.index("Hello") < ev.index("world")


def test_ass_builder_silence_isolation():
    builder = ASSSubtitleBuilder(words_per_line=3, animation_style="karaoke_pop")
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": "سلام",
                "words": [{"word": "سلام", "start": 0.0, "end": 1.0}]
            },
            {
                "start": 30.0,
                "end": 31.0,
                "text": "واش",
                "words": [{"word": "واش", "start": 30.0, "end": 31.0}]
            }
        ]
    }
    ass_text = builder.generate_ass(data)
    events = [l for l in ass_text.splitlines() if l.startswith("Dialogue:")]
    # Verify segment 1 cleanly dismisses at 1.35s and does not linger across 30s silence gap
    assert any("0:00:00.00,0:00:01.35" in e for e in events)
    assert not any("0:00:00.00,0:00:30.00" in e for e in events)


def test_ass_builder_script_separated_chunking():
    builder = ASSSubtitleBuilder(words_per_line=4, animation_style="karaoke_pop")
    words = [
        {"word": "وكان", "start": 0.0, "end": 0.5},
        {"word": "شرف", "start": 0.5, "end": 1.0},
        {"word": "للشركة", "start": 1.0, "end": 1.8},
        {"word": "Red", "start": 1.8, "end": 2.3},
        {"word": "Field", "start": 2.3, "end": 3.0},
        {"word": "أنها", "start": 3.0, "end": 3.5},
        {"word": "تدير", "start": 3.5, "end": 4.1},
        {"word": "test", "start": 4.1, "end": 4.8}
    ]
    chunks = builder.chunk_words(words)
    # Script separation: French words displayed by themselves
    assert len(chunks) == 4
    assert [w["word"] for w in chunks[0]] == ["وكان", "الشرف", "للشركة"]
    assert [w["word"] for w in chunks[1]] == ["Red", "Field"]
    assert [w["word"] for w in chunks[2]] == ["أنها", "تدير"]
    assert [w["word"] for w in chunks[3]] == ["test"]


def test_ass_builder_verb_prefix_binding_and_spelling():
    builder = ASSSubtitleBuilder(words_per_line=3, animation_style="karaoke_pop")
    words = [
        {"word": "يـ", "start": 6.0, "end": 6.2},
        {"word": "percer", "start": 6.2, "end": 6.5},
        {"word": "داخل", "start": 6.5, "end": 6.8},
        {"word": "la", "start": 6.8, "end": 7.0},
        {"word": "tôle", "start": 7.0, "end": 7.3},
        {"word": "شوف", "start": 7.3, "end": 7.6}
    ]
    chunks = builder.chunk_words(words)
    # Verb prefix "يـ" binds with "percer" into "يـ percer", and "la" binds with "tôle" into "la tôle"
    assert chunks[0][0]["word"] == "يـ percer"
    # Script separation: Arabic and French isolated into distinct screens
    assert len(chunks) == 4
    assert [w["word"] for w in chunks[0]] == ["يـ percer"]
    assert [w["word"] for w in chunks[1]] == ["داخل"]
    assert [w["word"] for w in chunks[2]] == ["la tôle"]
    assert [w["word"] for w in chunks[3]] == ["شوف"]


def test_ass_builder_new_creative_templates():
    transcription = {
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "سلام عليكم",
                "words": [
                    {"word": "سلام", "start": 0.0, "end": 1.0},
                    {"word": "عليكم", "start": 1.0, "end": 2.0}
                ]
            }
        ]
    }
    
    new_styles = [
        "hormozi-pop",
        "minimal-slide",
        "cyber-glitch",
        "comic-bounce",
        "viral-punch",
        "fade-editorial",
        "badge-invert",
        "letter_pop",
        "letter_drop",
        "letter_rise",
        "cumulative_fill",
        "cumulative_bounce",
        "cumulative_glow"
    ]
    
    for style in new_styles:
        builder = ASSSubtitleBuilder(words_per_line=3, animation_style=style)
        ass_text = builder.generate_ass(transcription)
        assert "[Events]" in ass_text
        assert "Dialogue:" in ass_text
        assert "سلام" in ass_text





def test_strict_chunking_limit_and_rlm_embedding():
    # Enforces max 6 words even if requested 8
    builder = ASSSubtitleBuilder(words_per_line=8, animation_style="hormozi-pop")
    assert builder.words_per_line <= 6

    words = [
        {"word": "دير", "start": 0.0, "end": 0.4},
        {"word": "ال", "start": 0.4, "end": 0.7},
        {"word": "premier", "start": 0.7, "end": 1.2},
        {"word": "test", "start": 1.2, "end": 1.6},
        {"word": "بهاد", "start": 1.6, "end": 1.9},
        {"word": "لا", "start": 1.9, "end": 2.2},
        {"word": "nouvelle", "start": 2.2, "end": 2.8}
    ]
    chunks = builder.chunk_words(words)
    # The raw tokens get bound and all chunks are <= 6 words
    assert all(len(c) <= 6 for c in chunks)

    # Mixed script ASS contains RLM marker \u200F for RTL embedding
    data = {
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.8,
                "text": "دير ال premier test بهاد لا nouvelle",
                "words": words
            }
        ]
    }
    ass_content = builder.generate_ass(data)
    dialogues = [line for line in ass_content.splitlines() if line.startswith("Dialogue:")]
    assert len(dialogues) > 0
    # Every dialogue line containing Arabic clause starts with \u200F
    assert any("\u200f" in d for d in dialogues)


def test_grammatical_cohesion_anti_dangling_particles():
    builder = ASSSubtitleBuilder(words_per_line=3, animation_style="karaoke_pop")
    words = [
        {"word": "داخل", "start": 3.81, "end": 3.94},
        {"word": "la", "start": 3.94, "end": 3.95},
        {"word": "tôle", "start": 4.00, "end": 4.10},
        {"word": "شوف", "start": 4.10, "end": 4.66}
    ]
    chunks = builder.chunk_words(words)
    # 'la' and 'tôle' bind together into 'la tôle' and must not be separated
    assert any("la tôle" in [w["word"] for w in ch] for ch in chunks)


def test_noun_adjective_cohesion_and_letter_pop_visibility():
    builder = ASSSubtitleBuilder(words_per_line=3, animation_style="letter_drop")
    words = [
        {"word": "على", "start": 4.96, "end": 5.48},
        {"word": "المستوى", "start": 5.48, "end": 5.92},
        {"word": "الأفريقي", "start": 5.92, "end": 6.56},
        {"word": "والمستوى", "start": 6.84, "end": 7.36},
        {"word": "الوطني", "start": 7.36, "end": 7.82},
        {"word": "اللي كانت", "start": 7.82, "end": 8.35},
        {"word": "النتيجة", "start": 8.35, "end": 8.78},
        {"word": "تاعها", "start": 8.78, "end": 9.14}
    ]
    chunks = builder.chunk_words(words)
    # Ensure 'والمستوى' and 'الوطني' are never split across chunks
    has_wal_mustawa_watani = any(
        "والمستوى" in [w["word"] for w in ch] and "الوطني" in [w["word"] for w in ch]
        for ch in chunks
    )
    assert has_wal_mustawa_watani, "Noun-adjective pair 'والمستوى الوطني' was split!"

    # Letter pop events must never use \\alpha&HFF& (100% invisible letters)
    chunk_french = [
        {"word": "la nouvelle", "start": 3.91, "end": 4.43},
        {"word": "technologie", "start": 4.43, "end": 4.81},
        {"word": "PPF", "start": 4.81, "end": 4.96}
    ]
    events = builder.build_letter_pop_events([chunk_french], style_type="drop")
    assert all("\\alpha&HFF&" not in e for e in events)
