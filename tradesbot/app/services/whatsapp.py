"""
WhatsApp messaging service via Twilio.
Handles sending text, media, and document messages.
"""
from twilio.rest import Client
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("whatsapp")
settings = get_settings()

_client: Client = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        log.info("twilio_client_initialized")
    return _client


def send_text(to: str, body: str) -> str:
    """
    Send a text message via WhatsApp.
    
    Args:
        to: Recipient phone in format 'whatsapp:+91XXXXXXXXXX'
        body: Message text
    
    Returns:
        Message SID
    """
    client = _get_client()
    from_number = f"whatsapp:{settings.twilio_whatsapp_number}"

    msg = client.messages.create(
        from_=from_number,
        to=to,
        body=body,
    )
    log.info("message_sent", to=to, sid=msg.sid, status=msg.status)
    return msg.sid


def send_media(to: str, body: str, media_url: str) -> str:
    """
    Send a message with a media attachment (image, PDF, etc.).
    """
    client = _get_client()
    from_number = f"whatsapp:{settings.twilio_whatsapp_number}"

    msg = client.messages.create(
        from_=from_number,
        to=to,
        body=body,
        media_url=[media_url],
    )
    log.info("media_sent", to=to, sid=msg.sid, media=media_url)
    return msg.sid
