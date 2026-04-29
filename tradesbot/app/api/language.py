"""
Language management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from app.localization.profile import get_language_preference, set_language_preference
from app.localization.detector import detect_language
from app.utils.logger import get_logger

log = get_logger("api_language")
router = APIRouter(prefix="/api/language")

VALID_LANGUAGES = ["en", "hi", "ta", "ml"]


@router.get("/detect")
async def detect(text: str = Query(..., min_length=2)):
    """Detect language of input text."""
    result = await detect_language(text)
    return result


@router.get("/preference/{phone}")
async def get_preference(phone: str):
    """Get user's language preference."""
    pref = await get_language_preference(phone)
    return pref


@router.post("/preference/{phone}")
async def set_preference(phone: str, language: str = Query(...)):
    """Set user's language preference."""
    if language not in VALID_LANGUAGES:
        raise HTTPException(400, f"Supported languages: {VALID_LANGUAGES}")
    await set_language_preference(phone, language, auto_detected=False)
    return {"status": "ok", "language": language}
