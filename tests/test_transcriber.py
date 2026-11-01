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
