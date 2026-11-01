import pytest
from core.srt_builder import format_srt_time, format_vtt_time, generate_srt, generate_vtt


def test_srt_time_formatting():
    assert format_srt_time(0.0) == "00:00:00,000"
    assert format_srt_time(1.5) == "00:00:01,500"
    assert format_srt_time(65.123) == "00:01:05,123"
    assert format_vtt_time(65.123) == "00:01:05.123"


def test_generate_srt():
    data = {
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "واش راك خونا",
                "words": [
                    {"word": "واش", "start": 0.0, "end": 0.6},
                    {"word": "راك", "start": 0.6, "end": 1.2},
                    {"word": "خونا", "start": 1.2, "end": 2.0}
                ]
            }
        ]
    }
    srt = generate_srt(data, words_per_chunk=3)
    assert "1" in srt
    assert "00:00:00,000 --> 00:00:02,000" in srt
    assert "واش راك خونا" in srt


def test_generate_vtt():
    data = {
        "segments": [
            {"start": 1.0, "end": 3.0, "text": "راني مليح الحمد لله"}
        ]
    }
    vtt = generate_vtt(data)
    assert "WEBVTT" in vtt
    assert "00:00:01.000 --> 00:00:03.000" in vtt
    assert "راني مليح الحمد لله" in vtt


def test_srt_silence_isolation():
    data = {
        "segments": [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "سلام",
                "words": [{"word": "سلام", "start": 0.0, "end": 2.0}]
            },
            {
                "start": 40.0,
                "end": 42.0,
                "text": "واش",
                "words": [{"word": "واش", "start": 40.0, "end": 42.0}]
            }
        ]
    }
    srt = generate_srt(data, words_per_chunk=3)
    # Ensure no cue spans across the 40s silence
    assert "00:00:00,000 --> 00:00:02,000" in srt
    assert "00:00:40,000 --> 00:00:42,000" in srt
    assert "00:00:00,000 --> 00:00:42,000" not in srt

