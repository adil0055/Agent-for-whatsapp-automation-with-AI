"""
Twilio WhatsApp Webhook — receives inbound messages, parses them,
and enqueues for async processing by the worker.
"""
from fastapi import APIRouter, Request, Response
from app.services.parser import parse_twilio_webhook
from app.services.queue_service import enqueue_message
from app.utils.logger import get_logger

log = get_logger("webhook")
router = APIRouter(prefix="/api")


@router.post("/webhooks/twilio")
async def twilio_webhook(request: Request):
    """
    Receive inbound WhatsApp messages from Twilio.
    
    Twilio sends a form-encoded POST with message details.
    We parse it, enqueue for async processing, and return 200 immediately
    (Twilio requires a fast response to avoid retries).
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    log.info(
        "webhook_received",
        sid=form_dict.get("MessageSid"),
        from_=form_dict.get("From"),
        type=form_dict.get("MediaContentType0", "text"),
    )

    try:
        # Parse the Twilio payload into our internal schema
        message = parse_twilio_webhook(form_dict)

        # Push to Redis queue for async processing
        await enqueue_message(message)

        log.info("webhook_processed", sid=message.message_sid, type=message.message_type.value)

    except Exception as e:
        log.error("webhook_error", error=str(e), form_data=form_dict)
        # Still return 200 to prevent Twilio retries
        # The error is logged and can be investigated

    # Return empty TwiML response (no auto-reply from webhook; worker handles replies)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="text/xml",
    )


@router.get("/webhooks/twilio")
async def twilio_webhook_verify(request: Request):
    """Handle GET requests (Twilio health checks / verification)."""
    return {"status": "webhook_active", "path": "/api/webhooks/twilio"}
