"""
Voice Call Service — makes outbound calls via Twilio with TTS.
Uses Twilio's built-in <Say> TTS for now (Phase 4 will add Indic-TTS).
"""
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from app.config import get_settings
from app.services.consent import is_call_allowed
from app.utils.logger import get_logger

log = get_logger("voice_call")
settings = get_settings()


async def make_followup_call(
    customer_phone: str,
    message: str,
    language: str = "en",
) -> dict:
    """
    Make a WhatsApp voice call with TTS message.
    Checks consent and TRAI compliance before calling.
    """
    # Check if call is allowed
    allowed, reason = await is_call_allowed(customer_phone)
    if not allowed:
        log.warning("call_blocked", phone=customer_phone, reason=reason)
        return {"status": "blocked", "reason": reason}

    # Map language to Twilio voice
    voice_map = {
        "en": "Polly.Aditi",      # Indian English
        "hi": "Polly.Aditi",      # Hindi
        "ta": "Polly.Aditi",      # Tamil (fallback)
        "ml": "Polly.Aditi",      # Malayalam (fallback)
    }
    voice = voice_map.get(language, "Polly.Aditi")

    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

        # Create TwiML for the call
        from_number = f"whatsapp:{settings.twilio_whatsapp_number}"
        to_number = f"whatsapp:{customer_phone}"

        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=f'<Response><Say voice="{voice}" language="{language}-IN">{message}</Say></Response>',
        )

        log.info("call_initiated", sid=call.sid, to=customer_phone, language=language)
        return {"status": "initiated", "call_sid": call.sid}

    except Exception as e:
        log.error("call_failed", phone=customer_phone, error=str(e))
        return {"status": "failed", "error": str(e)}
