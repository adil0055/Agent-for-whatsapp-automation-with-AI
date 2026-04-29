"""
Language Profile Manager — persists and retrieves user language preferences.
"""
from sqlalchemy import text
from app.models.database import async_session
from app.utils.logger import get_logger

log = get_logger("lang_profile")


async def get_language_preference(phone: str) -> dict:
    """Get user's language preference from DB."""
    clean_phone = phone.replace("whatsapp:", "")
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT language_preference, language_auto_detected, language_confirmed
                FROM users WHERE phone_number = :phone
            """),
            {"phone": clean_phone},
        )
        row = result.fetchone()

    if row:
        return {
            "language": row[0] or "en",
            "auto_detected": row[1],
            "confirmed": row[2] or False,
        }
    return {"language": "en", "auto_detected": None, "confirmed": False}


async def set_language_preference(phone: str, language: str, auto_detected: bool = False):
    """Save user's language preference."""
    clean_phone = phone.replace("whatsapp:", "")
    async with async_session() as session:
        if auto_detected:
            await session.execute(
                text("""
                    UPDATE users SET language_auto_detected = :lang, language_preference = :lang
                    WHERE phone_number = :phone
                """),
                {"lang": language, "phone": clean_phone},
            )
        else:
            await session.execute(
                text("""
                    UPDATE users SET language_preference = :lang, language_confirmed = TRUE
                    WHERE phone_number = :phone
                """),
                {"lang": language, "phone": clean_phone},
            )
        await session.commit()
    log.info("language_set", phone=clean_phone, language=language, auto=auto_detected)


async def resolve_language(phone: str, detected_lang: str, is_code_mixed: bool) -> str:
    """
    Resolve which language to use for responses.
    Priority: confirmed preference > auto-detected > current detection
    """
    pref = await get_language_preference(phone)

    if pref["confirmed"]:
        return pref["language"]

    # Auto-update if detected language differs
    if detected_lang != pref.get("auto_detected"):
        await set_language_preference(phone, detected_lang, auto_detected=True)

    return detected_lang
