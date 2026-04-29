"""
Message parser — determines message type from Twilio webhook payload
and builds a structured InboundMessage for the queue.
"""
from datetime import datetime, timezone
from app.models.schemas import InboundMessage, MessageType
from app.utils.logger import get_logger

log = get_logger("parser")


def parse_twilio_webhook(form_data: dict) -> InboundMessage:
    """
    Parse a Twilio WhatsApp webhook form POST into an InboundMessage.
    
    Twilio sends form-encoded data with fields:
      - MessageSid, From, To, Body
      - NumMedia, MediaUrl0, MediaContentType0 (if media attached)
    """
    message_sid = form_data.get("MessageSid", "")
    phone_from = form_data.get("From", "")
    phone_to = form_data.get("To", "")
    body = form_data.get("Body", "").strip()
    num_media = int(form_data.get("NumMedia", "0"))

    # Determine message type
    message_type = MessageType.TEXT
    media_url = None
    media_content_type = None

    if num_media > 0:
        media_url = form_data.get("MediaUrl0", "")
        media_content_type = form_data.get("MediaContentType0", "")

        if "audio" in media_content_type:
            message_type = MessageType.VOICE
        elif "image" in media_content_type:
            message_type = MessageType.IMAGE
        elif "application" in media_content_type or "pdf" in media_content_type:
            message_type = MessageType.DOCUMENT
        else:
            message_type = MessageType.OTHER

    # If there's body text AND media, treat as the media type (body is caption)
    if not body and num_media == 0:
        log.warning("empty_message", sid=message_sid, phone=phone_from)

    msg = InboundMessage(
        message_sid=message_sid,
        phone_from=phone_from,
        phone_to=phone_to,
        message_type=message_type,
        body=body or None,
        media_url=media_url,
        media_content_type=media_content_type,
        num_media=num_media,
        timestamp=datetime.now(timezone.utc),
    )

    log.info(
        "message_parsed",
        sid=message_sid,
        type=message_type.value,
        has_body=bool(body),
        has_media=num_media > 0,
    )
    return msg
