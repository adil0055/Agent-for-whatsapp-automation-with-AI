"""
Voice call API endpoints — TwiML handlers and call management.
"""
from fastapi import APIRouter, Request, Response, Query
from twilio.twiml.voice_response import VoiceResponse
from app.services.consent import request_consent, check_consent
from app.services.voice_call import make_followup_call
from app.utils.logger import get_logger

log = get_logger("api_voice")
router = APIRouter(prefix="/api/voice")


@router.post("/call")
async def initiate_call(
    customer_phone: str = Query(...),
    message: str = Query(...),
    language: str = Query("en"),
    user_id: str = Query(...),
):
    """Initiate an outbound WhatsApp voice call."""
    result = await make_followup_call(customer_phone, message, language)
    return result


@router.post("/consent/request")
async def request_call_consent(
    user_id: str = Query(...),
    customer_phone: str = Query(...),
):
    """Send a consent request to a customer before calling."""
    status = await request_consent(user_id, customer_phone)
    return {"status": status}


@router.get("/consent/check")
async def check_call_consent(customer_phone: str = Query(...)):
    """Check consent status for a customer."""
    consent = await check_consent(customer_phone)
    return consent or {"status": "no_consent"}


@router.post("/twiml")
async def voice_twiml(request: Request, audio_url: str = Query(None)):
    """TwiML endpoint for call scripts."""
    response = VoiceResponse()
    if audio_url:
        response.play(audio_url)
    else:
        response.say("Hello, this is a follow-up call regarding your service request. Thank you.", voice="Polly.Aditi")
    response.gather(
        input="speech dtmf",
        action="/api/voice/response",
        language="hi-IN",
        timeout=5,
    )
    response.say("Thank you. Goodbye.", voice="Polly.Aditi")
    return Response(content=str(response), media_type="text/xml")


@router.post("/response")
async def voice_response(request: Request):
    """Handle customer's response during a call (speech/DTMF)."""
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    digits = form.get("Digits", "")

    log.info("call_response", speech=speech_result, digits=digits)

    response = VoiceResponse()
    response.say("Thank you for your response. We will follow up shortly. Goodbye.", voice="Polly.Aditi")
    return Response(content=str(response), media_type="text/xml")
