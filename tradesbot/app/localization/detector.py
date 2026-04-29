"""
Language Detection Service — detects language and code-mixing
using Groq LLM for high accuracy on Indic languages.
"""
import json
import re
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("lang_detect")

# Quick heuristic patterns for common scripts
SCRIPT_PATTERNS = {
    "hi": re.compile(r'[\u0900-\u097F]'),   # Devanagari
    "ta": re.compile(r'[\u0B80-\u0BFF]'),   # Tamil
    "ml": re.compile(r'[\u0D00-\u0D7F]'),   # Malayalam
    "kn": re.compile(r'[\u0C80-\u0CFF]'),   # Kannada
    "te": re.compile(r'[\u0C00-\u0C7F]'),   # Telugu
}

DETECTION_PROMPT = """Detect the language of this message. Consider code-mixing (e.g., Hinglish = Hindi+English).

Respond with ONLY a JSON object:
{{"primary_language": "en/hi/ta/ml", "confidence": 0.0-1.0, "is_code_mixed": true/false, "code_mix_languages": ["lang1", "lang2"]}}

Message: {message}"""


def detect_script(text: str) -> str | None:
    """Fast heuristic: detect Indic scripts by Unicode range."""
    for lang, pattern in SCRIPT_PATTERNS.items():
        if pattern.search(text):
            return lang
    return None


async def detect_language(text: str) -> dict:
    """
    Detect language with code-mixing support.
    Uses script detection first (fast), falls back to LLM for romanized text.
    """
    if not text or len(text.strip()) < 2:
        return {"primary_language": "en", "confidence": 0.5, "is_code_mixed": False}

    # Fast path: check for Indic scripts
    script_lang = detect_script(text)
    if script_lang:
        # Check if there's also Latin text (code-mixing)
        has_latin = bool(re.search(r'[a-zA-Z]{2,}', text))
        return {
            "primary_language": script_lang,
            "confidence": 0.95,
            "is_code_mixed": has_latin,
            "code_mix_languages": [script_lang, "en"] if has_latin else [script_lang],
        }

    # Check if it's pure English (all Latin, common English words)
    if re.match(r'^[a-zA-Z0-9\s.,!?\'"-]+$', text):
        # Could be English or romanized Indic — check common Indic words
        indic_markers = {
            "hi": ["hai", "hain", "kya", "nahi", "mujhe", "chahiye", "kaise", "aur", "mein", "yeh", "woh", "karo", "bhai", "ji"],
            "ta": ["enakku", "venum", "aagum", "illa", "sollu", "enna", "epdi", "vanakkam", "nandri"],
            "ml": ["enikku", "venam", "aanu", "illa", "parayoo", "enth", "engane", "namaskaram"],
        }

        text_lower = text.lower()
        for lang, markers in indic_markers.items():
            matches = sum(1 for m in markers if m in text_lower)
            if matches >= 2:
                return {
                    "primary_language": lang,
                    "confidence": 0.8,
                    "is_code_mixed": True,
                    "code_mix_languages": [lang, "en"],
                }

        # Likely pure English
        return {"primary_language": "en", "confidence": 0.9, "is_code_mixed": False}

    # Fallback: use LLM for ambiguous cases
    try:
        raw = await chat(DETECTION_PROMPT.format(message=text[:200]), text[:200])
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        result = json.loads(json_str)
        log.info("language_detected", lang=result.get("primary_language"), code_mixed=result.get("is_code_mixed"))
        return result
    except Exception:
        return {"primary_language": "en", "confidence": 0.5, "is_code_mixed": False}
