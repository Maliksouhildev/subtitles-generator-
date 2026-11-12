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
    # Unified natural phrase without awkward fragmenting
    assert len(segs) == 1
    assert len(segs[0]["words"]) == 8
    assert segs[0]["text"] == "وكان الشرف للشركة Red Field أنها تدير test"
    assert segs[0]["start"] == 0.0
    assert segs[0]["end"] == 5.8


def test_calibrate_transcription_to_vad_timing_drift():
    from core.transcriber import calibrate_transcription_to_vad
    
    # Simulate the exact bug: AI compressed 18.88s of speech into 14.0s
    data = {
        "language": "ar-DZ",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 7.0,
                "text": "وكان شرف للشركة",
                "words": [
                    {"word": "وكان", "start": 0.0, "end": 2.0},
                    {"word": "شرف", "start": 2.0, "end": 4.5},
                    {"word": "للشركة", "start": 4.5, "end": 7.0}
                ]
            },
            {
                "id": 1,
                "start": 7.0,
                "end": 14.0,
                "text": "نهائيا",
                "words": [
                    {"word": "نهائيا", "start": 7.0, "end": 14.0}
                ]
            },
            {
                "id": 2,
                "start": 23.8,
                "end": 25.5,
                "text": "نزيد نعاودلك؟",
                "words": [
                    {"word": "نزيد", "start": 23.8, "end": 24.5},
                    {"word": "نعاودلك؟", "start": 24.5, "end": 25.5}
                ]
            }
        ]
    }
    
    speech_intervals = [(0.0, 18.88), (24.63, 25.44)]
    calibrated = calibrate_transcription_to_vad(data, speech_intervals)
    segs = calibrated["segments"]
    
    # The first cluster must now stretch all the way to 18.88s instead of cutting off at 14.0s
    assert segs[1]["end"] == 18.88
    assert segs[1]["words"][0]["end"] == 18.88
    
    # The second cluster must align with the second speech interval 24.63s - 25.44s
    assert segs[2]["start"] == 24.63
    assert segs[2]["end"] == 25.44
    assert segs[2]["words"][0]["start"] == 24.63
    assert segs[2]["words"][1]["end"] == 25.44




def test_bind_arabic_articles_to_latin():
    from core.transcriber import bind_arabic_articles_to_latin
    words = [
        {"word": "\u0627\u0644\u0640", "start": 1.0, "end": 1.2},
        {"word": "premier", "start": 1.2, "end": 1.6},
        {"word": "test", "start": 1.6, "end": 2.0},
        {"word": "\u0644\u0640", "start": 2.2, "end": 2.4},
        {"word": "Redfield", "start": 2.4, "end": 3.0},
        {"word": "\u0627\u0644", "start": 3.2, "end": 3.4},
        {"word": "premier test", "start": 3.4, "end": 4.0}
    ]
    bound = bind_arabic_articles_to_latin(words)
    assert len(bound) == 4
    assert bound[0]["word"] == "\u0627\u0644\u0640 premier"
    assert bound[0]["start"] == 1.0
    assert bound[0]["end"] == 1.6
    assert bound[1]["word"] == "test"
    assert bound[2]["word"] == "\u0644\u0640 Redfield"
    assert bound[2]["start"] == 2.2
    assert bound[2]["end"] == 3.0
    assert bound[3]["word"] == "\u0627\u0644 premier test"
    assert bound[3]["start"] == 3.2
    assert bound[3]["end"] == 4.0


def test_bind_darija_prefixes_multitoken():
    from core.transcriber import bind_arabic_articles_to_latin
    # Exactly replicating review issue: "دير ال premier test بهاد لا nouvelle"
    words = [
        {"word": "دير", "start": 0.0, "end": 0.4},
        {"word": "ال", "start": 0.4, "end": 0.7},
        {"word": "premier", "start": 0.7, "end": 1.2},
        {"word": "test", "start": 1.2, "end": 1.6},
        {"word": "بهاد", "start": 1.6, "end": 1.9},
        {"word": "لا", "start": 1.9, "end": 2.2},
        {"word": "nouvelle", "start": 2.2, "end": 2.8}
    ]
    bound = bind_arabic_articles_to_latin(words)
    # "ال" attaches to "premier", "بهاد" and "لا" attach to "nouvelle"
    assert len(bound) == 4
    assert bound[0]["word"] == "دير"
    assert bound[1]["word"] == "ال premier"
    assert bound[1]["start"] == 0.4
    assert bound[1]["end"] == 1.2
    assert bound[2]["word"] == "test"
    assert bound[3]["word"] == "بهاد لا nouvelle"
    assert bound[3]["start"] == 1.6
    assert bound[3]["end"] == 2.8


def test_split_fused_script_tokens():
    from core.transcriber import split_fused_script_tokens, GEMINI_MODELS
    # Prioritizes active transcribe models
    assert GEMINI_MODELS[0] in ("gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.1-flash-lite")
    assert "gemini-3.1-flash-lite" in GEMINI_MODELS

    words = [
        {"word": "komunه", "start": 6.42, "end": 6.84},
        {"word": "مع", "start": 6.84, "end": 8.78},
        {"word": "تشوف", "start": 8.78, "end": 9.5}
    ]
    split = split_fused_script_tokens(words)
    assert len(split) == 4
    assert split[0]["word"] == "komun"
    assert split[1]["word"] == "ه"
    assert split[2]["word"] == "مع"
    assert split[3]["word"] == "تشوف"


def test_sanitize_transcription_text_and_verb_prefixes():
    from core.transcriber import sanitize_transcription_text, bind_arabic_articles_to_latin, normalize_transcription_data

    # 1. Spelling normalization: strips trailing hamza from هكذاء
    raw_phrase = "سي بون، خلاص، هكذاء"
    clean_phrase = sanitize_transcription_text(raw_phrase)
    assert clean_phrase == "سي بون، خلاص، هكذا"

    # 2. Verb prefix binding with French verbs
    words = [
        {"word": "يـ", "start": 6.0, "end": 6.2},
        {"word": "percer", "start": 6.2, "end": 6.6},
        {"word": "داخل", "start": 6.6, "end": 6.9},
        {"word": "الـ", "start": 6.9, "end": 7.1},
        {"word": "PPF", "start": 7.1, "end": 7.5}
    ]
    bound = bind_arabic_articles_to_latin(words)
    assert len(bound) == 3
    assert bound[0]["word"] == "يـ percer"
    assert bound[1]["word"] == "داخل"
    assert bound[2]["word"] == "الـ PPF"

    # 3. Full normalize_transcription_data integration
    raw_data = {
        "text": "سي بون خلاص هكذاء",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "سي بون خلاص هكذاء",
                "words": [
                    {"word": "سي", "start": 0.0, "end": 0.4},
                    {"word": "بون", "start": 0.4, "end": 0.8},
                    {"word": "خلاص", "start": 0.8, "end": 1.4},
                    {"word": "هكذاء", "start": 1.4, "end": 2.0}
                ]
            }
        ]
    }
    norm = normalize_transcription_data(raw_data)
    assert norm["text"] == "سي بون خلاص هكذا"
    assert norm["segments"][0]["words"][2]["word"] == "هكذا"


def test_anti_hallucination_and_token_repair():
    from core.transcriber import sanitize_transcription_text

    text = "هل يؤثر على la visibilité تاع الـ d'alcool ولا كاش خطر"
    sanitized = sanitize_transcription_text(text)
    assert "visibilité" not in sanitized
    assert "d'alcool" not in sanitized
    assert "de colle" in sanitized or "aucun résidu de colle" in sanitized

    text2 = "هادي la nouvelle techn"
    sanitized2 = sanitize_transcription_text(text2)
    assert "technologie" in sanitized2

    text3 = "هذا هو le premi test"
    sanitized3 = sanitize_transcription_text(text3)
    assert "premier" in sanitized3


def test_hallucination_and_glossary_repairs():
    from core.transcriber import sanitize_transcription_text, normalize_transcription_data

    # 1. Phonetic sanitizer fixes
    assert sanitize_transcription_text("la visibilité") == "ولا كاش خطر"
    assert sanitize_transcription_text("la recette") == "النتيجة"
    assert sanitize_transcription_text("vryment") == "vraiment"
    assert sanitize_transcription_text("Redfilm") == "Redfield"
    assert sanitize_transcription_text("Red film") == "Redfield"

    # 2. Token sequence normalization repairs
    data = {
        "text": "la visibilité et la recette pour Redfilm avec vryment",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 4.0,
                "text": "la visibilité et la recette pour Redfilm avec vryment",
                "words": [
                    {"word": "la", "start": 0.0, "end": 0.3},
                    {"word": "visibilité", "start": 0.3, "end": 0.8},
                    {"word": "et", "start": 0.8, "end": 1.0},
                    {"word": "la", "start": 1.0, "end": 1.3},
                    {"word": "recette", "start": 1.3, "end": 1.8},
                    {"word": "pour", "start": 1.8, "end": 2.0},
                    {"word": "Red", "start": 2.0, "end": 2.5},
                    {"word": "film", "start": 2.5, "end": 3.0},
                    {"word": "avec", "start": 3.0, "end": 3.4},
                    {"word": "vryment", "start": 3.4, "end": 4.0}
                ]
            }
        ]
    }
    norm = normalize_transcription_data(data)
    words = norm["segments"][0]["words"]
    words_text = [w["word"] for w in words]
    assert "ولا كاش خطر" in words_text or ("ولا" in words_text and "كاش خطر" in words_text)
    assert "النتيجة" in words_text
    assert "Redfield" in words_text
    assert "vraiment" in words_text
    assert "visibilité" not in words_text
    assert "recette" not in words_text
    assert "vryment" not in words_text


def test_msa_bleed_and_parallel_clause_chunking():
    from core.transcriber import sanitize_transcription_text
    from core.ass_builder import ASSSubtitleBuilder

    # 1. Verify MSA bleed normalization
    assert sanitize_transcription_text("دير بهده التقنية") == "دير بهاد التقنية"
    assert sanitize_transcription_text("دير بهذه التقنية") == "دير بهاد التقنية"
    assert sanitize_transcription_text("فهده الخدمة") == "فهاد الخدمة"
    assert sanitize_transcription_text("فهذه الخدمة") == "فهاد الخدمة"
    assert sanitize_transcription_text("بهذا") == "بهاد"
    assert sanitize_transcription_text("فهذا") == "فهاد"

    # 2. Verify parallel coordinated clause chunking in ass_builder
    builder = ASSSubtitleBuilder(words_per_line=4)
    parallel_words = [
        {"word": "على", "start": 5.0, "end": 5.3},
        {"word": "المستوى", "start": 5.3, "end": 5.8},
        {"word": "الأفريقي", "start": 5.8, "end": 6.3},
        {"word": "والمستوى", "start": 6.3, "end": 6.8},
        {"word": "الوطني", "start": 6.8, "end": 7.3},
    ]
    chunks = builder.chunk_words(parallel_words)
    # The coordinated clause 'على المستوى الأفريقي والمستوى الوطني' must remain together
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}: {chunks}"
    assert len(chunks[0]) == 5
    assert [w["word"] for w in chunks[0]] == ["على", "المستوى", "الأفريقي", "والمستوى", "الوطني"]

    # 3. Script isolation: Latin loanwords (Redfield) are isolated from Arabic phrases
    bilingual_words = [
        {"word": "وكان", "start": 0.0, "end": 0.3},
        {"word": "الشرف", "start": 0.3, "end": 0.7},
        {"word": "لشركة", "start": 0.7, "end": 1.1},
        {"word": "Redfield", "start": 1.1, "end": 1.6},
    ]
    bi_chunks = builder.chunk_words(bilingual_words)
    assert len(bi_chunks) == 2, f"Expected 2 chunks for script isolation, got {len(bi_chunks)}: {bi_chunks}"
    assert [w["word"] for w in bi_chunks[0]] == ["وكان", "الشرف", "لشركة"]
    assert [w["word"] for w in bi_chunks[1]] == ["Redfield"]
