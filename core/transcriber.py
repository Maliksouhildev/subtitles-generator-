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

# Gemini models with free-tier access ordered by speed & transcription accuracy
GEMINI_MODELS = [
    "gemini-3.5-transcribe",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash"
]

DARIJA_SYSTEM_PROMPT = """
You are an expert transcriber specialized in Algerian Arabic (الدارجة الجزائرية - Darija).
Your task is to listen to the provided audio and generate an accurate, word-by-word transcription in authentic Algerian Darija written in clean ARABIC SCRIPT.

DIALECT & LINGUISTIC RULES:
1. Write in Arabic script (الخط العربي). Do NOT use Arabizi (Latin numbers like 3, 7, 9) unless it's a specific brand or English technical term.
2. Accurately capture authentic Algerian vocabulary, slang, and expressions:
   - "واش", "واشنو", "علاش", "كيفاش", "وقتاش", "وينتا", "راني", "راك", "راهو", "راهي", "حنا", "نتوما"
   - "برك", "بزاف", "شوية", "مليح", "قع", "كامل", "دير", "حاب", "باغي", "خلاص", "صحة", "خويا", "ختي", "كاش", "هكذا", "هاكا"
   - French loanwords naturally used in Algeria written phonetically in Arabic (e.g., بورطابل, طوموبيل, ميرسي, بلاصة, نورمال, الخ).
3. Provide PRECISE TIMESTAMPS:
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

    # Sometimes Gemini might wrap or have leading comments
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx + 1]

    data = json.loads(text)
    return data


def interpolate_word_timestamps(segment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ensures that a segment has word-level timestamps.
    If the AI model provided segment-level times but omitted or gave incomplete word timestamps,
    this calculates precise proportional timestamps based on word lengths and duration.
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

    # If valid word timestamps already exist for all words, validate and return
    if words_data and len(words_data) == len(words):
        valid = True
        for w in words_data:
            if "start" not in w or "end" not in w or not w.get("word"):
                valid = False
                break
        if valid:
            return words_data

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


def normalize_transcription_data(data: Dict[str, Any], total_duration: float = 0.0) -> Dict[str, Any]:
    """Ensures consistent segments, IDs, and word-level timestamps."""
    segments = data.get("segments", [])
    normalized_segments = []

    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start + 2.0))
        text = seg.get("text", "").strip()

        words = interpolate_word_timestamps(seg)
        if words and not text:
            text = " ".join(w["word"] for w in words)

        normalized_segments.append({
            "id": i,
            "start": round(start, 2),
            "end": round(end, 2),
            "text": text,
            "words": words
        })

    full_text = data.get("text", "")
    if not full_text and normalized_segments:
        full_text = " ".join(s["text"] for s in normalized_segments)

    return {
        "language": data.get("language", "ar-DZ"),
        "text": full_text,
        "segments": normalized_segments
    }


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

    # 1. Downsample to 16kHz mono MP3
    processed_audio = extract_audio(audio_path)
    audio_duration = get_audio_duration(processed_audio)

    with open(processed_audio, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Clean up temp downsampled file
    try:
        os.remove(processed_audio)
    except Exception:
        pass

    prompt = DARIJA_SYSTEM_PROMPT
    if dialect_hint and dialect_hint != "General Algerian":
        prompt += f"\nSpecific Regional Dialect Focus: {dialect_hint} (Algeria).\n"

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
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                resp_json = response.json()
                candidates = resp_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        raw_text = parts[0].get("text", "")
                        parsed_data = clean_gemini_json(raw_text)
                        normalized = normalize_transcription_data(parsed_data, audio_duration)
                        logger.info(f"Successfully transcribed audio with {model_name}: {len(normalized['segments'])} segments")
                        return normalized
            else:
                err_body = response.text[:200]
                logger.warning(f"Model {model_name} returned HTTP {response.status_code}: {err_body}")
                last_error = f"HTTP {response.status_code}: {err_body}"
        except Exception as e:
            logger.warning(f"Model {model_name} request failed: {e}")
            last_error = str(e)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def transcribe_with_faster_whisper(audio_path: str) -> Dict[str, Any]:
    """
    Offline fallback using Faster-Whisper with word-level timestamps.
    Automatically used if Gemini is unavailable or offline.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper is not installed. Install it or use Gemini API.")

    logger.info("Starting local Faster-Whisper transcription for Darija...")
    processed_audio = extract_audio(audio_path)
    audio_duration = get_audio_duration(processed_audio)

    # Use small or base model for fast execution on CPU
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(
        processed_audio,
        language="ar",
        initial_prompt="الدارجة الجزائرية: سلام خويا واش راك لاباس راني مليح يعطيك الصحة برك بزاف دير هاكا",
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

    return normalize_transcription_data({"language": "ar-DZ", "segments": segments}, audio_duration)


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
        return transcribe_with_faster_whisper(audio_path)

    try:
        return transcribe_with_gemini(audio_path, api_key=api_key, dialect_hint=dialect_hint)
    except Exception as e:
        logger.warning(f"Gemini transcription failed ({e}), falling back to local Faster-Whisper...")
        try:
            return transcribe_with_faster_whisper(audio_path)
        except Exception as e2:
            raise RuntimeError(f"Both Gemini AI and local Whisper transcription failed: Gemini error: {e} | Whisper error: {e2}")
