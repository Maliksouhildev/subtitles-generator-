import pytest
from core.transcriber import clean_gemini_json, interpolate_word_timestamps, normalize_transcription_data


def test_clean_gemini_json():
    # Markdown wrapped json
    raw = '```json\n{"text": "مرحبا", "segments": []}\n```'
    parsed = clean_gemini_json(raw)
    assert parsed["text"] == "مرحبا"

    # Json with extra whitespace and leading text
    raw2 = 'Sure, here is the result: {"text": "صحا"}'
    parsed2 = clean_gemini_json(raw2)
    assert parsed2["text"] == "صحا"


def test_interpolate_word_timestamps():
    # Segment without words
    seg = {
        "text": "واش راك خويا",
        "start": 1.0,
        "end": 4.0
    }
    words = interpolate_word_timestamps(seg)
    assert len(words) == 3
    assert words[0]["word"] == "واش"
    assert words[0]["start"] == 1.0
    assert words[2]["word"] == "خويا"
    assert words[2]["end"] == 4.0


def test_normalize_transcription_data():
    raw_data = {
        "language": "ar-DZ",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "الحمد لله",
            }
        ]
    }
    normalized = normalize_transcription_data(raw_data, total_duration=2.0)
    assert normalized["language"] == "ar-DZ"
    assert len(normalized["segments"]) == 1
    assert len(normalized["segments"][0]["words"]) == 2
    assert normalized["text"] == "الحمد لله"


def test_clean_gemini_json_array():
    raw_array = '[{"id": 0, "start": 0.0, "end": 1.0, "text": "سلام"}]'
    parsed = clean_gemini_json(raw_array)
    assert "segments" in parsed
    assert len(parsed["segments"]) == 1


def test_interpolate_word_timestamps_user_edit():
    # User edited a word in the text while keeping original count
    seg = {
        "text": "واش راكم",  # edited from 'واش راك'
        "start": 0.0,
        "end": 2.0,
        "words": [
            {"word": "واش", "start": 0.0, "end": 0.9},
            {"word": "راك", "start": 0.9, "end": 2.0}
        ]
    }
    words = interpolate_word_timestamps(seg)
    assert len(words) == 2
    assert words[1]["word"] == "راكم"
    assert words[1]["start"] == 0.9
    assert words[1]["end"] == 2.0


def test_get_system_prompt_languages():
    from core.transcriber import get_system_prompt, FRENCH_SYSTEM_PROMPT, ENGLISH_SYSTEM_PROMPT, ARABIC_STANDARD_SYSTEM_PROMPT, DARIJA_SYSTEM_PROMPT, DARIJA_LATIN_SYSTEM_PROMPT
    assert get_system_prompt("French") == FRENCH_SYSTEM_PROMPT
    assert get_system_prompt("English") == ENGLISH_SYSTEM_PROMPT
    assert get_system_prompt("Modern Standard Arabic") == ARABIC_STANDARD_SYSTEM_PROMPT
    assert get_system_prompt("Algerian Darija Latin") == DARIJA_LATIN_SYSTEM_PROMPT
    assert get_system_prompt("General Algerian") == DARIJA_SYSTEM_PROMPT
    assert "Algerian" in get_system_prompt("General Algerian")


def test_normalize_transcription_script_separation():
    raw_mixed = {
        "language": "ar-DZ",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 6.0,
                "text": "وكان شرف للشركة Red Field أنها تدير test",
                "words": [
                    {"word": "وكان", "start": 0.0, "end": 0.6},
                    {"word": "شرف", "start": 0.6, "end": 1.2},
                    {"word": "للشركة", "start": 1.2, "end": 2.0},
                    {"word": "Red", "start": 2.0, "end": 2.6},
                    {"word": "Field", "start": 2.6, "end": 3.4},
                    {"word": "أنها", "start": 3.4, "end": 4.1},
                    {"word": "تدير", "start": 4.1, "end": 4.9},
                    {"word": "test", "start": 4.9, "end": 5.8}
                ]
            }
        ]
    }
    normalized = normalize_transcription_data(raw_mixed)
    segs = normalized["segments"]
    assert len(segs) == 4
    # Segment 1: Pure Arabic
    assert segs[0]["text"] == "وكان شرف للشركة"
    assert segs[0]["start"] == 0.0
    assert segs[0]["end"] == 2.0
    # Segment 2: Pure French loanwords
    assert segs[1]["text"] == "Red Field"
    assert segs[1]["start"] == 2.0
    assert segs[1]["end"] == 3.4
    # Segment 3: Pure Arabic
    assert segs[2]["text"] == "أنها تدير"
    assert segs[2]["start"] == 3.4
    assert segs[2]["end"] == 4.9
    # Segment 4: Pure French loanword
    assert segs[3]["text"] == "test"
    assert segs[3]["start"] == 4.9
    assert segs[3]["end"] == 5.8



