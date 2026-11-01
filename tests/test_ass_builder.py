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
    assert "\\fscx115\\fscy115" in ass_text


def test_ass_builder_all_styles():
    for style in ["karaoke_pop", "word_reveal", "classic_line", "box_highlight"]:
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
    # The first event (when 'سلام' is spoken at 0.0) should render 'خاوتنا' first and 'سلام' last
    # so that libass LTR layout places 'خاوتنا' on the left and 'سلام' on the right
    event_lines = [l for l in ass_text.splitlines() if l.startswith("Dialogue: 0,0:00:00.00")]
    assert len(event_lines) == 1
    ev = event_lines[0]
    # Word 'خاوتنا' appears before 'سلام' in the ASS line text for correct visual RTL
    assert ev.index("خاوتنا") < ev.index("سلام")


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
    # Verify segment 1 ends at 1.0s and does not stretch until 30.0s
    assert any("0:00:00.00,0:00:01.00" in e for e in events)
    assert not any("0:00:00.00,0:00:30.00" in e for e in events)

