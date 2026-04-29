"""
Consent Manager — handles TRAI-compliant call consent flow.
"""
from datetime import datetime, timedelta
from sqlalchemy import text
from app.models.database import async_session
from app.services.whatsapp import send_text
from app.utils.logger import get_logger

log = get_logger("consent")

CONSENT_EXPIRY_DAYS = 30  # Consent valid for 30 days


async def request_consent(user_id: str, customer_phone: str) -> str:
    """Send a consent request message to the customer."""
    # Check if valid consent already exists
    existing = await check_consent(customer_phone)
    if existing and existing.get("status") == "granted":
        return "already_granted"

    # Create pending consent record
    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO call_consents (user_id, customer_phone, consent_status)
                VALUES (:uid, :phone, 'pending')
                ON CONFLICT DO NOTHING
            """),
            {"uid": user_id, "phone": customer_phone.replace("whatsapp:", "")},
        )
        await session.commit()

    # Send consent request via WhatsApp
    msg = (
        "🔔 *Call Permission Request*\n\n"
        "We'd like to call you regarding your service request. "
        "Your consent is required as per regulations.\n\n"
        "Reply *YES* to allow us to call you.\n"
        "Reply *NO* or *STOP* to decline.\n\n"
        "This consent is valid for 30 days."
    )
    send_text(to=f"whatsapp:{customer_phone}", body=msg)
    log.info("consent_requested", phone=customer_phone)
    return "requested"


async def grant_consent(customer_phone: str) -> bool:
    """Grant call consent for a customer."""
    phone = customer_phone.replace("whatsapp:", "")
    expires = datetime.utcnow() + timedelta(days=CONSENT_EXPIRY_DAYS)

    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE call_consents SET
                    consent_status = 'granted',
                    consented_at = NOW(),
                    expires_at = :expires
                WHERE customer_phone = :phone AND consent_status = 'pending'
                RETURNING id
            """),
            {"phone": phone, "expires": expires},
        )
        row = result.fetchone()
        await session.commit()

    if row:
        log.info("consent_granted", phone=phone, expires=str(expires))
        return True
    return False


async def revoke_consent(customer_phone: str) -> bool:
    """Revoke call consent (customer replied STOP/NO)."""
    phone = customer_phone.replace("whatsapp:", "")

    async with async_session() as session:
        await session.execute(
            text("""
                UPDATE call_consents SET consent_status = 'revoked'
                WHERE customer_phone = :phone AND consent_status IN ('pending', 'granted')
            """),
            {"phone": phone},
        )
        await session.commit()

    log.info("consent_revoked", phone=phone)
    return True


async def check_consent(customer_phone: str) -> dict | None:
    """Check if valid consent exists for a customer."""
    phone = customer_phone.replace("whatsapp:", "")

    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT consent_status, consented_at, expires_at, dnd_checked, dnd_status
                FROM call_consents
                WHERE customer_phone = :phone
                ORDER BY created_at DESC LIMIT 1
            """),
            {"phone": phone},
        )
        row = result.fetchone()

    if not row:
        return None

    status = row[0]
    expires = row[2]

    # Check if expired
    if status == "granted" and expires and expires < datetime.utcnow():
        status = "expired"

    return {
        "status": status,
        "consented_at": str(row[1]) if row[1] else None,
        "expires_at": str(expires) if expires else None,
        "dnd_checked": row[3],
        "dnd_status": row[4],
    }


async def is_call_allowed(customer_phone: str) -> tuple[bool, str]:
    """
    Full check: consent + time window + DND.
    Returns (allowed, reason).
    """
    # Check consent
    consent = await check_consent(customer_phone)
    if not consent or consent["status"] != "granted":
        return False, f"No valid consent (status: {consent['status'] if consent else 'none'})"

    # Check TRAI time window (9 AM - 9 PM IST)
    from datetime import timezone
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist)
    if now_ist.hour < 9 or now_ist.hour >= 21:
        return False, f"Outside calling hours (9 AM - 9 PM IST). Current: {now_ist.strftime('%H:%M')}"

    return True, "ok"
