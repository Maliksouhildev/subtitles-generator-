"""
Darija Audio Transcriber using Google Gemini API with Faster-Whisper fallback.
Specialized for Algerian Arabic (الدارجة الجزائرية) dialect with word-level timestamps.
"""

import os
import re
import json
import base64
import logging
import tempfile
import subprocess
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger("darija_transcriber")
logging.basicConfig(level=logging.INFO)

# Gemini models with free-tier access ordered by speed, transcription accuracy & JSON mode support
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
]

DARIJA_SYSTEM_PROMPT = """
You are an expert transcriber specialized in Algerian Arabic (الدارجة الجزائرية - Darija).
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in authentic Algerian Darija written in clean ARABIC SCRIPT.

DIALECT & LINGUISTIC RULES:
1. Write in Arabic script (الخط العربي). Do NOT use Arabizi (Latin numbers like 3, 7, 9) unless it's a specific brand or English technical term.
2. Accurately capture authentic Algerian vocabulary, slang, and expressions:
   - "واش", "واشنو", "علاش", "كيفاش", "وقتاش", "وينتا", "راني", "راك", "راهو", "راهي", "حنا", "نتوما"
   - "برك", "بزاف", "شوية", "مليح", "قع", "كامل", "دير", "حاب", "باغي", "خلاص", "صحة", "خويا", "ختي", "كاش", "هكذا", "هاكا"
3. FRENCH & FOREIGN LOANWORD SPELLING (CRITICAL):
   - NEVER phonetically transliterate French, English, or foreign loanwords into Arabic letters (e.g. do NOT write 'برومي' for 'premier', do NOT write 'نوفيل' for 'nouvelle', do NOT write 'تيست' for 'test', do NOT write 'ريدفيلد' for 'Redfield', do NOT write 'دوزيام' for 'deuxième').
   - Always write established French, English, or foreign brand names, technical terms, and loanwords in their authentic standard LATIN script (e.g. "premier", "nouvelle", "test", "Redfield", "rendez-vous", "projet", "voiture", "normal", "c'est bon").
   - This ensures professional, native-grade bilingual subtitling.
4. Provide PRECISE TIMESTAMPS:
   - Every segment must have 'start' and 'end' in seconds (float).
   - Every word within a segment must have its exact spoken 'start' and 'end' timestamps in seconds.
   - Timestamps must correspond to the exact moment the speaker pronounces the word.

STRICT JSON OUTPUT FORMAT ONLY:
Return ONLY valid JSON matching this schema with NO markdown code fences, NO explanation, NO introduction:
{
  "language": "ar-DZ",
  "text": "Full transcript in Algerian Darija Arabic script",
  "segments": [
    {
      "id": 0,
      "start": 0.00,
      "end": 2.40,
      "text": "سلام عليكم خاوتنا واش راكم",
      "words": [
        {"word": "سلام", "start": 0.00, "end": 0.45},
        {"word": "عليكم", "start": 0.45, "end": 0.85},
        {"word": "خاوتنا", "start": 0.85, "end": 1.40},
        {"word": "واش", "start": 1.40, "end": 1.80},
        {"word": "راكم", "start": 1.80, "end": 2.40}
      ]
    }
  ]
}
"""

DARIJA_LATIN_SYSTEM_PROMPT = """
You are an expert transcriber specialized in Algerian Arabic Arabizi (الدارجة باللاتينية / Latin Darija).
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in authentic Algerian Darija written in LATIN SCRIPT with Arabizi numbers.

ARABIZI NUMERICAL CONVENTIONS:
- 3 for 'ع' (Ayn), e.g. 3likom, m3a, s3id
- 7 for 'ح' (Haa), e.g. 7aja, 7na, sa7a
- 9 for 'ق' (Qaf), e.g. 9al, 9olna, w9tach
- 5 for 'خ' (Khaa), e.g. 5oya, 5ir, 5las
- 2 for 'ء' (Hamza), e.g. rassi, ba2ess

DIALECT & VOCABULARY RULES:
1. Accurately transcribe spoken Algerian words: "wach", "wachno", "3lach", "kifech", "wa9tech", "rani", "rak", "raho", "rahi", "hna", "ntouma", "bzaf", "chwya", "mzyan", "mle7", "kamel", "sahbi", "khoya".
2. Write French loanwords in standard French spelling (e.g., "projet", "premier test", "normal", "c'est bon").
3. Provide PRECISE TIMESTAMPS:
   - Every segment must have 'start' and 'end' in seconds (float).
   - Every word within a segment must have its exact spoken 'start' and 'end' timestamps in seconds.

STRICT JSON OUTPUT FORMAT ONLY:
Return ONLY valid JSON matching this schema with NO markdown code fences, NO explanation, NO introduction:
{
  "language": "ar-DZ-Latn",
  "text": "Full transcript in Algerian Darija Arabizi",
  "segments": [
    {
      "id": 0,
      "start": 0.00,
      "end": 2.40,
      "text": "salam 3likom khawatna wach rakoum",
      "words": [
        {"word": "salam", "start": 0.00, "end": 0.45},
        {"word": "3likom", "start": 0.45, "end": 0.85},
        {"word": "khawatna", "start": 0.85, "end": 1.40},
        {"word": "wach", "start": 1.40, "end": 1.80},
        {"word": "rakoum", "start": 1.80, "end": 2.40}
      ]
    }
  ]
}
"""

FRENCH_SYSTEM_PROMPT = """
You are an expert transcriber specialized in the French language.
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in grammatically correct French.

RULES:
1. Write in correct standard French with proper accents, punctuation, and capitalization.
2. Provide PRECISE TIMESTAMPS:
   - Every segment must have 'start' and 'end' in seconds (float).
   - Every word within a segment must have its exact spoken 'start' and 'end' timestamps in seconds.
   - Timestamps must correspond to the exact moment the speaker pronounces the word.

STRICT JSON OUTPUT FORMAT ONLY:
Return ONLY valid JSON matching this schema with NO markdown code fences, NO explanation, NO introduction:
{
  "language": "fr",
  "text": "Full transcript in French",
  "segments": [
    {
      "id": 0,
      "start": 0.00,
      "end": 2.40,
      "text": "Bonjour à tous bienvenue",
      "words": [
        {"word": "Bonjour", "start": 0.00, "end": 0.50},
        {"word": "à", "start": 0.50, "end": 0.70},
        {"word": "tous", "start": 0.70, "end": 1.20},
        {"word": "bienvenue", "start": 1.20, "end": 2.40}
      ]
    }
  ]
}
"""

ENGLISH_SYSTEM_PROMPT = """
You are an expert transcriber specialized in English.
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in standard English.

RULES:
1. Write in correct English with proper punctuation and capitalization.
2. Provide PRECISE TIMESTAMPS:
   - Every segment must have 'start' and 'end' in seconds (float).
   - Every word within a segment must have its exact spoken 'start' and 'end' timestamps in seconds.
   - Timestamps must correspond to the exact moment the speaker pronounces the word.

STRICT JSON OUTPUT FORMAT ONLY:
Return ONLY valid JSON matching this schema with NO markdown code fences, NO explanation, NO introduction:
{
  "language": "en",
  "text": "Full transcript in English",
  "segments": [
    {
      "id": 0,
      "start": 0.00,
      "end": 2.40,
      "text": "Hello everyone and welcome",
      "words": [
        {"word": "Hello", "start": 0.00, "end": 0.50},
        {"word": "everyone", "start": 0.50, "end": 1.20},
        {"word": "and", "start": 1.20, "end": 1.50},
        {"word": "welcome", "start": 1.50, "end": 2.40}
      ]
    }
  ]
}
"""

ARABIC_STANDARD_SYSTEM_PROMPT = """
You are an expert transcriber specialized in Modern Standard Arabic (الفصحى).
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in clean Modern Standard Arabic script.

RULES:
1. Write in clean Arabic script with correct spelling.
2. Provide PRECISE TIMESTAMPS:
   - Every segment must have 'start' and 'end' in seconds (float).
   - Every word within a segment must have its exact spoken 'start' and 'end' timestamps in seconds.
   - Timestamps must correspond to the exact moment the speaker pronounces the word.

STRICT JSON OUTPUT FORMAT ONLY:
Return ONLY valid JSON matching this schema with NO markdown code fences, NO explanation, NO introduction:
{
  "language": "ar",
  "text": "Full transcript in Modern Standard Arabic",
  "segments": [
    {
      "id": 0,
      "start": 0.00,
      "end": 2.40,
      "text": "أهلا وسهلا بكم جميعا",
      "words": [
        {"word": "أهلا", "start": 0.00, "end": 0.50},
        {"word": "وسهلا", "start": 0.50, "end": 1.10},
        {"word": "بكم", "start": 1.10, "end": 1.60},
        {"word": "جميعا", "start": 1.60, "end": 2.40}
      ]
    }
  ]
}
"""


def get_system_prompt(dialect_hint: str = "General Algerian") -> str:
    """Selects the optimal transcription prompt based on the chosen language/dialect."""
    dh = (dialect_hint or "").strip().lower()
    if dh.startswith("french") or dh.startswith("français") or dh == "fr":
        return FRENCH_SYSTEM_PROMPT
    elif dh.startswith("english") or dh == "en":
        return ENGLISH_SYSTEM_PROMPT
    elif "latin" in dh or "arabizi" in dh:
        return DARIJA_LATIN_SYSTEM_PROMPT
    elif dh.startswith("arabic") or dh.startswith("modern standard") or dh.startswith("العربية"):
        return ARABIC_STANDARD_SYSTEM_PROMPT
    else:
        prompt = DARIJA_SYSTEM_PROMPT
        if dialect_hint and dialect_hint not in ("General Algerian", "Algerian Darija", "Algerian Darija (Arabic)", "ar-dz"):
            prompt += f"\nSpecific Regional Dialect Focus: {dialect_hint} (Algeria).\n"
        return prompt



def extract_audio(input_file: str, output_wav_or_mp3: Optional[str] = None) -> str:
    """
    Extracts and resamples audio from any video or audio file to 16kHz mono MP3.
    This guarantees lightweight payloads and maximum Gemini/Whisper accuracy.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if output_wav_or_mp3 is None:
        fd, output_wav_or_mp3 = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        output_wav_or_mp3
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg audio extraction failed: {e.stderr.decode('utf-8', errors='ignore')}")

    return output_wav_or_mp3


def get_audio_duration(file_path: str) -> float:
    """Returns the duration of an audio or video file in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"Failed to probe duration with ffprobe ({e}), defaulting to 10.0s")
        return 10.0


def detect_speech_intervals(audio_path: str, noise_thresh: str = "-28dB", min_silence: float = 0.65) -> Tuple[List[Tuple[float, float]], float]:
    """
    Detects active spoken intervals in audio using FFmpeg silencedetect.
    Returns list of (start_seconds, end_seconds) tuples of voice activity, and total duration.
    """
    dur = get_audio_duration(audio_path)
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-af", f"silencedetect=noise={noise_thresh}:d={min_silence}",
        "-f", "null", "-"
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        silences = []
        for line in res.stderr.splitlines():
            if "silence_start:" in line:
                m = re.search(r"silence_start:\s*([0-9.]+)", line)
                if m:
                    silences.append({"start": float(m.group(1))})
            elif "silence_end:" in line:
                m = re.search(r"silence_end:\s*([0-9.]+)", line)
                if m and silences and "end" not in silences[-1]:
                    silences[-1]["end"] = float(m.group(1))

        if not silences:
            return [(0.0, round(dur, 2))], dur

        speech = []
        curr = 0.0
        for s in silences:
            s_start = s["start"]
            s_end = s.get("end", dur)
            if s_start > curr + 0.2:
                speech.append((round(curr, 2), round(s_start, 2)))
            curr = s_end
        if curr < dur - 0.2:
            speech.append((round(curr, 2), round(dur, 2)))

        if not speech:
            speech = [(0.0, round(dur, 2))]

        return speech, dur
    except Exception as e:
        logger.warning(f"Failed to detect speech intervals via FFmpeg ({e}), fallback to full duration")
        return [(0.0, round(dur, 2))], dur


def calibrate_transcription_to_vad(transcription: Dict[str, Any], speech_intervals: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Aligns transcription word and segment timestamps to ground-truth acoustic voice activity intervals.
    Prevents AI hallucination/drift where speech words compress or end early.
    """
    if not speech_intervals:
        return transcription

    segments = transcription.get("segments", [])
    if not segments:
        return transcription

    # Cluster segments by pause gaps (> 1.2s pause indicates separate speech event)
    clusters = []
    current_cluster = []
    for seg in segments:
        if current_cluster:
            prev_end = current_cluster[-1]["end"]
            if seg["start"] - prev_end > 1.2:
                clusters.append(current_cluster)
                current_cluster = []
        current_cluster.append(seg)
    if current_cluster:
        clusters.append(current_cluster)

    for c_idx, cluster in enumerate(clusters):
        c_start = float(cluster[0]["start"])
        c_end = float(cluster[-1]["end"])
        c_dur = max(0.1, c_end - c_start)

        # Match to closest VAD interval by temporal overlap
        best_vad = None
        best_overlap = -1.0
        for vad_start, vad_end in speech_intervals:
            overlap = max(0.0, min(c_end, vad_end) - max(c_start, vad_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_vad = (vad_start, vad_end)

        # Fallback to index mapping if overlap is negligible
        if (not best_vad or best_overlap <= 0.1) and c_idx < len(speech_intervals):
            best_vad = speech_intervals[c_idx]

        if best_vad:
            vad_start, vad_end = best_vad
            vad_dur = vad_end - vad_start

            # Calibrate if there is drift > 0.35s
            if abs(c_dur - vad_dur) > 0.35 or abs(c_start - vad_start) > 0.35:
                scale = vad_dur / c_dur if c_dur > 0.1 else 1.0
                logger.info(f"VAD Calibration applied to cluster {c_idx}: AI [{c_start:.2f}s - {c_end:.2f}s] -> VAD [{vad_start:.2f}s - {vad_end:.2f}s] (scale={scale:.3f})")
                for seg in cluster:
                    seg["start"] = round(vad_start + (seg["start"] - c_start) * scale, 2)
                    seg["end"] = round(vad_start + (seg["end"] - c_start) * scale, 2)
                    for w in seg.get("words", []):
                        w["start"] = round(vad_start + (w["start"] - c_start) * scale, 2)
                        w["end"] = round(vad_start + (w["end"] - c_start) * scale, 2)

    return transcription


def clean_gemini_json(raw_text: str) -> Dict[str, Any]:
    """Cleans up markdown ticks or extra formatting from Gemini JSON responses."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Find boundaries of JSON object or array
    obj_start = text.find("{")
    arr_start = text.find("[")

    if arr_start != -1 and (obj_start == -1 or arr_start < obj_start):
        arr_end = text.rfind("]")
        if arr_end != -1:
            text = text[arr_start:arr_end + 1]
    elif obj_start != -1:
        obj_end = text.rfind("}")
        if obj_end != -1:
            text = text[obj_start:obj_end + 1]

    data = json.loads(text)
    if isinstance(data, list):
        data = {"segments": data}
    return data


def interpolate_word_timestamps(segment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ensures that a segment has word-level timestamps.
    If the AI model provided segment-level times but omitted or gave incomplete word timestamps,
    this calculates precise proportional timestamps based on word lengths and duration.
    If the user edited word text in the subtitle editor, updates the word text while preserving timing.
    """
    words_data = segment.get("words", [])
    text = segment.get("text", "").strip()
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    seg_start = float(segment.get("start", 0.0))
    seg_end = float(segment.get("end", seg_start + 2.0))
    duration = max(0.2, seg_end - seg_start)

    # If word timestamps already exist with matching word count, sync text and validate
    if words_data and len(words_data) == len(words):
        valid = True
        for w in words_data:
            if "start" not in w or "end" not in w:
                valid = False
                break
        if valid:
            updated_words = []
            for idx, w in enumerate(words_data):
                w_copy = dict(w)
                w_copy["word"] = words[idx]
                updated_words.append(w_copy)
            return updated_words

    # Otherwise interpolate based on character weight
    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        total_chars = len(words)

    result_words = []
    curr_time = seg_start
    for w in words:
        w_dur = (len(w) / total_chars) * duration
        w_start = round(curr_time, 2)
        w_end = round(curr_time + w_dur, 2)
        result_words.append({
            "word": w,
            "start": w_start,
            "end": w_end
        })
        curr_time += w_dur

    return result_words


ARABIC_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")


def classify_token_script(token: str, default: str = "arabic") -> str:
    """
    Classifies a word token into 'latin' (French/English) or 'arabic' (Darija/Arabic script).
    Neutral tokens (numbers, punctuation) inherit the active script context.
    """
    has_latin = bool(LATIN_REGEX.search(token))
    has_arabic = bool(ARABIC_REGEX.search(token))
    if has_latin and not has_arabic:
        return "latin"
    elif has_arabic and not has_latin:
        return "arabic"
    elif has_arabic and has_latin:
        return "arabic"
    else:
        return default


ARABIC_PREFIX_ARTICLE_REGEX = re.compile(r'^(?:و?الـ?|و?ال-|و?ال|لـ?|ل-|للـ?|لل-|فـ?|ف-|بـ?|ب-|لا)$')


def bind_arabic_articles_to_latin(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Binds orphaned Arabic definite articles (e.g. 'ال', 'الـ', 'لـ', 'لا') to subsequent Latin loanwords
    (e.g. 'premier test', 'nouvelle'), treating them as a single highlighted token.
    Prevents awkward isolated article pop on screen and preserves natural bilingual phrasing.
    """
    if not words:
        return []
    bound: List[Dict[str, Any]] = []
    i = 0
    while i < len(words):
        w = words[i]
        text_val = str(w.get("word", "")).strip()
        if ARABIC_PREFIX_ARTICLE_REGEX.match(text_val) and i + 1 < len(words):
            next_w = words[i + 1]
            next_text = str(next_w.get("word", "")).strip()
            if LATIN_REGEX.search(next_text):
                joint_word = f"{text_val} {next_text}"
                bound.append({
                    "word": joint_word,
                    "start": w.get("start", 0.0),
                    "end": next_w.get("end", next_w.get("start", 0.0) + 0.3)
                })
                i += 2
                continue
        bound.append(w)
        i += 1
    return bound


def normalize_transcription_data(data: Dict[str, Any], total_duration: float = 0.0) -> Dict[str, Any]:
    """
    Ensures consistent segments, IDs, and word-level timestamps.
    Keeps natural mixed-language phrases intact so French loanwords flow seamlessly with Arabic text.
    Binds orphaned Arabic articles to subsequent Latin words into unified highlighted tokens.
    """
    segments = data.get("segments", [])
    normalized_segments = []
    seg_counter = 0

    for seg in segments:
        words = interpolate_word_timestamps(seg)
        words = bind_arabic_articles_to_latin(words)
        if not words:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 2.0))
            text = seg.get("text", "").strip()
            normalized_segments.append({
                "id": seg_counter,
                "start": round(start, 2),
                "end": round(end, 2),
                "text": text,
                "words": []
            })
            seg_counter += 1
            continue

        seg_start = float(words[0]["start"])
        seg_end = float(words[-1]["end"])
        seg_text = seg.get("text", "").strip() or " ".join(w["word"] for w in words)
        normalized_segments.append({
            "id": seg_counter,
            "start": round(seg_start, 2),
            "end": round(seg_end, 2),
            "text": seg_text,
            "words": words
        })
        seg_counter += 1

    full_text = data.get("text", "")
    if not full_text and normalized_segments:
        full_text = " ".join(s["text"] for s in normalized_segments)

    res = {
        "language": data.get("language", "ar-DZ"),
        "text": full_text,
        "segments": normalized_segments
    }
    if "speech_intervals" in data:
        res["speech_intervals"] = data["speech_intervals"]
    return res


def transcribe_with_gemini(
    audio_path: str,
    api_key: Optional[str] = None,
    dialect_hint: str = "General Algerian",
    preferred_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes Algerian Darija audio using Google Gemini API with free token access.
    Tries models in order of capability until successful.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Please provide an API key or set GEMINI_API_KEY.")
    key_masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
    logger.info(f"Authenticating with user Gemini API Key: {key_masked}")

    # 1. Downsample to 16kHz mono MP3
    processed_audio = extract_audio(audio_path)
    intervals, audio_duration = detect_speech_intervals(processed_audio, min_silence=0.65)

    with open(processed_audio, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Clean up temp downsampled file
    try:
        os.remove(processed_audio)
    except Exception:
        pass

    prompt = get_system_prompt(dialect_hint)
    timing_hint = f"\nCRITICAL ACOUSTIC WAVEFORM TIMINGS:\n- Exact Total Duration: {audio_duration:.2f} seconds.\n"
    if intervals:
        int_strs = [f"[{start:.2f}s - {end:.2f}s]" for start, end in intervals]
        timing_hint += f"- Ground-Truth Active Spoken Intervals: {', '.join(int_strs)}\n"
        timing_hint += "You MUST map your transcribed words to accurately cover these spoken intervals without compressing or ending early.\n"
    prompt += timing_hint

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "audio/mp3",
                            "data": audio_b64
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    # Model cascade
    models_to_try = [preferred_model] if preferred_model else []
    for m in GEMINI_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        logger.info(f"Attempting Gemini transcription with model: {model_name}...")
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                resp_json = response.json()
                candidates = resp_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        raw_text = parts[0].get("text", "")
                        parsed_data = clean_gemini_json(raw_text)
                        normalized = normalize_transcription_data(parsed_data, audio_duration)
                        calibrated = calibrate_transcription_to_vad(normalized, intervals)
                        calibrated["speech_intervals"] = intervals
                        logger.info(f"Successfully transcribed audio with {model_name}: {len(calibrated['segments'])} segments (VAD calibrated)")
                        return calibrated
            else:
                err_body = response.text[:200]
                logger.warning(f"Model {model_name} returned HTTP {response.status_code}: {err_body}")
                last_error = f"HTTP {response.status_code}: {err_body}"
        except Exception as e:
            logger.warning(f"Model {model_name} request failed: {e}")
            last_error = str(e)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def transcribe_with_faster_whisper(audio_path: str, dialect_hint: str = "General Algerian") -> Dict[str, Any]:
    """
    Offline fallback using Faster-Whisper with word-level timestamps.
    Automatically used if Gemini is unavailable or offline.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper is not installed. Install it or use Gemini API.")

    dh = (dialect_hint or "").strip().lower()
    if dh.startswith("french") or dh.startswith("français") or dh == "fr":
        whisper_lang = "fr"
        whisper_prompt = "Transcription en français avec horodatage précis par mot."
    elif dh.startswith("english") or dh == "en":
        whisper_lang = "en"
        whisper_prompt = "English transcription with accurate word-level timestamps."
    elif dh.startswith("arabic") or dh.startswith("modern standard") or dh.startswith("العربية"):
        whisper_lang = "ar"
        whisper_prompt = "اللغة العربية الفصحى: أهلا وسهلا بكم جميعا."
    else:
        whisper_lang = "ar"
        whisper_prompt = "الدارجة الجزائرية: سلام خويا واش راك لاباس راني مليح يعطيك الصحة برك بزاف دير هاكا"

    logger.info(f"Starting local Faster-Whisper transcription for {whisper_lang}...")
    processed_audio = extract_audio(audio_path)
    audio_duration = get_audio_duration(processed_audio)

    # Use small or base model for fast execution on CPU
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(
        processed_audio,
        language=whisper_lang,
        initial_prompt=whisper_prompt,
        word_timestamps=True
    )

    segments = []
    for i, seg in enumerate(segments_gen):
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 2),
                    "end": round(w.end, 2)
                })
        else:
            words = interpolate_word_timestamps({"text": seg.text, "start": seg.start, "end": seg.end})

        segments.append({
            "id": i,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": words
        })

    try:
        os.remove(processed_audio)
    except Exception:
        pass

    return normalize_transcription_data({"language": whisper_lang, "segments": segments}, audio_duration)


def transcribe(
    audio_path: str,
    api_key: Optional[str] = None,
    dialect_hint: str = "General Algerian",
    force_local: bool = False
) -> Dict[str, Any]:
    """
    Unified entry point for Algerian Darija transcription.
    Tries Gemini AI first, falls back to Faster-Whisper if requested or if Gemini fails.
    """
    if force_local:
        return transcribe_with_faster_whisper(audio_path, dialect_hint=dialect_hint)

    try:
        return transcribe_with_gemini(audio_path, api_key=api_key, dialect_hint=dialect_hint)
    except Exception as e:
        logger.warning(f"Gemini transcription failed ({e}), falling back to local Faster-Whisper...")
        try:
            return transcribe_with_faster_whisper(audio_path, dialect_hint=dialect_hint)
        except Exception as e2:
            raise RuntimeError(f"Both Gemini AI and local Whisper transcription failed: Gemini error: {e} | Whisper error: {e2}")
