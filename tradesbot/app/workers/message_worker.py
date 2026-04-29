"""
Message Worker — long-running process that dequeues messages from Redis
and processes them through the AI agent pipeline.

Phase 4: Full multilingual support with language detection and localized prompts.
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy import text
from app.config import get_settings
from app.models.schemas import InboundMessage, MessageType, ConversationLog
from app.models.database import async_session
from app.services.queue_service import dequeue_message
from app.services.whatsapp import send_text, send_media
from app.services.gemini_image import generate_marketing_image
from app.services.media import (
    download_twilio_media,
    upload_to_storage,
    get_extension_for_content_type,
)
from app.services.asr import transcribe_audio
from app.agents.orchestrator import classify_intent
from app.agents.quote_agent import generate_quote, format_quote_whatsapp
from app.agents.schedule_agent import handle_schedule
from app.agents.invoice_agent import generate_invoice_data, format_invoice_whatsapp
from app.agents.general_agent import handle_general
from app.agents.marketing_agent import generate_marketing_prompt
from app.services.pdf_generator import generate_invoice_pdf
from app.services.ocr import extract_text_from_image, format_ocr_whatsapp
from app.services.memory import get_history, add_exchange
from app.services.consent import grant_consent, revoke_consent
from app.services.followup_scheduler import scheduler_loop as followup_loop
from app.localization.detector import detect_language
from app.localization.profile import resolve_language, set_language_preference
from app.localization.prompts import build_localized_prompt
from app.localization.messages import get_message
from app.utils.logger import setup_logging, get_logger

setup_logging()
log = get_logger("worker")
settings = get_settings()


# ── Database helpers ────────────────────────────────────────

async def log_conversation(conv: ConversationLog):
    """Insert a conversation record into the database."""
    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO conversations
                    (phone_from, phone_to, direction, message_type, message_sid,
                     content, transcript, media_url, media_stored_url, metadata)
                VALUES
                    (:phone_from, :phone_to, :direction, :message_type, :message_sid,
                     :content, :transcript, :media_url, :media_stored_url, :metadata)
            """),
            {
                "phone_from": conv.phone_from,
                "phone_to": conv.phone_to,
                "direction": conv.direction.value,
                "message_type": conv.message_type.value,
                "message_sid": conv.message_sid,
                "content": conv.content,
                "transcript": conv.transcript,
                "media_url": conv.media_url,
                "media_stored_url": conv.media_stored_url,
                "metadata": json.dumps(conv.metadata),
            },
        )
        await session.commit()


async def get_user_context(phone: str) -> dict:
    """Fetch tradesperson profile from DB."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT name, trade_type, hourly_rate, gstin, language_preference FROM users WHERE phone_number = :phone"),
            {"phone": phone.replace("whatsapp:", "")},
        )
        row = result.fetchone()
        if row:
            return {
                "user_name": row[0] or "Tradesperson",
                "trade_type": row[1] or "plumber",
                "hourly_rate": float(row[2]) if row[2] else 300.0,
                "gstin": row[3] or "N/A",
                "language": row[4] or "en",
            }
    return {"user_name": "Tradesperson", "trade_type": "plumber", "hourly_rate": 300.0, "gstin": "N/A", "language": "en"}


async def save_job(user_phone: str, description: str, scheduled_at: str = None, location: str = None) -> str:
    """Create a job record in the DB and return the job ID."""
    phone = user_phone.replace("whatsapp:", "")
    async with async_session() as session:
        # Get user_id first
        user_result = await session.execute(
            text("SELECT id FROM users WHERE phone_number = :phone"),
            {"phone": phone},
        )
        user_row = user_result.fetchone()
        if not user_row:
            return None
        user_id = str(user_row[0])

        # Convert scheduled_at string to datetime
        sched_dt = None
        if scheduled_at:
            try:
                from datetime import datetime as dt
                for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        sched_dt = dt.strptime(scheduled_at, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                log.warning("date_parse_failed", raw=scheduled_at)

        status = "scheduled" if sched_dt else "pending"
        result = await session.execute(
            text("""
                INSERT INTO jobs (user_id, description, status, scheduled_at, location, notes)
                VALUES (:uid, :desc, :status, :sched, :loc, :notes)
                RETURNING id
            """),
            {"uid": user_id, "desc": description, "status": status, "sched": sched_dt, "loc": location, "notes": ""},
        )
        row = result.fetchone()
        await session.commit()
        return str(row[0]) if row else None


async def save_quote(user_phone: str, quote_data: dict) -> str:
    """Save a quote to the DB and return quote ID."""
    phone = user_phone.replace("whatsapp:", "")
    async with async_session() as session:
        # Get user_id first
        user_result = await session.execute(
            text("SELECT id FROM users WHERE phone_number = :phone"),
            {"phone": phone},
        )
        user_row = user_result.fetchone()
        if not user_row:
            return None
        user_id = str(user_row[0])

        from datetime import timedelta
        validity_days = int(quote_data.get("validity_days", 7))
        valid_until = (datetime.now() + timedelta(days=validity_days)).date()

        result = await session.execute(
            text("""
                INSERT INTO quotes (user_id, items, labor_total, material_total, subtotal,
                    gst_rate, gst_amount, grand_total, notes, valid_until)
                VALUES (:uid, :items, :labor, :material, :subtotal,
                    :gst_rate, :gst_amount, :grand_total, :notes, :valid_until)
                RETURNING id
            """),
            {
                "uid": user_id,
                "items": json.dumps(quote_data.get("items", [])),
                "labor": quote_data.get("labor_total", 0),
                "material": quote_data.get("material_total", 0),
                "subtotal": quote_data.get("subtotal", 0),
                "gst_rate": quote_data.get("gst_rate", 18),
                "gst_amount": quote_data.get("gst_amount", 0),
                "grand_total": quote_data.get("grand_total", 0),
                "notes": quote_data.get("notes", ""),
                "valid_until": valid_until,
            },
        )
        row = result.fetchone()
        await session.commit()
        return str(row[0]) if row else None


async def get_next_invoice_number() -> str:
    """Get the next sequential invoice number."""
    async with async_session() as session:
        result = await session.execute(text("SELECT nextval('invoice_seq')"))
        seq = result.scalar()
        await session.commit()
        return f"INV-{datetime.now().year}-{seq:04d}"


# ── Message Handlers ────────────────────────────────────────

async def process_text_with_ai(msg: InboundMessage, text_content: str):
    """Route text through the AI orchestrator and respond."""
    user_ctx = await get_user_context(msg.phone_from)

    # Log inbound
    await log_conversation(ConversationLog(
        phone_from=msg.phone_from, phone_to=msg.phone_to,
        direction="inbound", message_type=MessageType.TEXT,
        message_sid=msg.message_sid, content=text_content,
    ))

    # Classify intent
    intent_result = await classify_intent(
        text_content,
        user_name=user_ctx["user_name"],
        trade_type=user_ctx["trade_type"],
        hourly_rate=user_ctx["hourly_rate"],
    )

    intent = intent_result.get("intent", "general")
    log.info("intent_routed", intent=intent, message=text_content[:80])

    reply = ""

    # Handle language selection (1/2/3/4)
    text_stripped = text_content.strip()
    if text_stripped in ("1", "2", "3", "4"):
        lang_map = {"1": "en", "2": "hi", "3": "ta", "4": "ml"}
        chosen_lang = lang_map[text_stripped]
        await set_language_preference(msg.phone_from, chosen_lang, auto_detected=False)
        reply = get_message("language_set", chosen_lang)
        send_text(to=msg.phone_from, body=reply)
        await log_conversation(ConversationLog(
            phone_from=msg.phone_to, phone_to=msg.phone_from,
            direction="outbound", message_type=MessageType.TEXT,
            content=reply, metadata={"action": "language_set", "language": chosen_lang},
        ))
        return

    # Detect language
    lang_result = await detect_language(text_content)
    detected_lang = lang_result.get("primary_language", "en")
    is_code_mixed = lang_result.get("is_code_mixed", False)
    user_lang = await resolve_language(msg.phone_from, detected_lang, is_code_mixed)
    log.info("language_resolved", detected=detected_lang, resolved=user_lang, code_mixed=is_code_mixed)

    # Check for consent/opt-out keywords first
    text_lower = text_content.strip().lower()
    if text_lower in ("yes", "y", "ha", "haan", "ok"):
        granted = await grant_consent(msg.phone_from)
        if granted:
            reply = "✅ Thank you! Your consent has been recorded. We may now call you regarding your service requests."
            send_text(to=msg.phone_from, body=reply)
            await log_conversation(ConversationLog(
                phone_from=msg.phone_to, phone_to=msg.phone_from,
                direction="outbound", message_type=MessageType.TEXT,
                content=reply, metadata={"action": "consent_granted"},
            ))
            return

    if text_lower in ("stop", "no", "nahi", "unsubscribe"):
        await revoke_consent(msg.phone_from)
        reply = "🛑 You have been opted out. We will not call you. Reply anytime to resume service."
        send_text(to=msg.phone_from, body=reply)
        await log_conversation(ConversationLog(
            phone_from=msg.phone_to, phone_to=msg.phone_from,
            direction="outbound", message_type=MessageType.TEXT,
            content=reply, metadata={"action": "consent_revoked"},
        ))
        return

    # Classify intent
    if intent == "quote":
        quote_data = await generate_quote(
            text_content,
            trade_type=user_ctx["trade_type"],
            hourly_rate=user_ctx["hourly_rate"],
            gstin=user_ctx["gstin"],
        )
        quote_id = await save_quote(msg.phone_from, quote_data)
        qnum = f"Q-{datetime.now().strftime('%Y%m%d')}-{quote_id[:4] if quote_id else '0000'}"
        reply = format_quote_whatsapp(quote_data, qnum)

    elif intent == "schedule":
        sched_data = await handle_schedule(
            text_content, trade_type=user_ctx["trade_type"],
        )
        if sched_data.get("action") == "book" and sched_data.get("preferred_date"):
            sched_at = sched_data.get("preferred_date")
            if sched_data.get("preferred_time"):
                sched_at += f" {sched_data['preferred_time']}"
            job_id = await save_job(
                msg.phone_from,
                sched_data.get("job_description", text_content),
                scheduled_at=sched_at,
                location=sched_data.get("location"),
            )
            reply = sched_data.get("response_message", "✅ Job booked!")
            if job_id:
                reply += f"\n\n📋 Job ID: {job_id[:8]}"
        else:
            reply = sched_data.get("response_message", "I'd like to help schedule a job. Could you provide more details?")

    elif intent == "invoice":
        inv_data = await generate_invoice_data(
            text_content,
            business_name=user_ctx["user_name"],
            trade_type=user_ctx["trade_type"],
            hourly_rate=user_ctx["hourly_rate"],
            gstin=user_ctx["gstin"],
        )
        inv_number = await get_next_invoice_number()
        reply = format_invoice_whatsapp(inv_data, inv_number)

        # Generate PDF
        try:
            pdf_url = generate_invoice_pdf(
                inv_number, inv_data,
                business_name=user_ctx["user_name"],
                gstin=user_ctx["gstin"],
            )
            reply += f"\n\n📄 PDF invoice generated and saved."
        except Exception as e:
            log.error("pdf_generation_failed", error=str(e))

    elif intent == "job_status":
        # Query recent jobs
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT description, status, scheduled_at FROM jobs
                    WHERE user_id = (SELECT id FROM users WHERE phone_number = :phone)
                    ORDER BY created_at DESC LIMIT 5
                """),
                {"phone": msg.phone_from.replace("whatsapp:", "")},
            )
            jobs = result.fetchall()

        if jobs:
            lines = ["📋 *Your Recent Jobs:*\n"]
            for j in jobs:
                status_emoji = {"pending": "🟡", "scheduled": "🔵", "completed": "🟢", "cancelled": "🔴"}.get(j[1], "⚪")
                sched = f" — {j[2].strftime('%b %d, %H:%M')}" if j[2] else ""
                lines.append(f"{status_emoji} {j[0]} ({j[1]}){sched}")
            reply = "\n".join(lines)
        else:
            reply = "📋 No jobs found yet. Tell me about a job you'd like to schedule!"

    elif intent == "marketing":
        # Step 1: Generate marketing prompt via LLM
        mkt = await generate_marketing_prompt(
            text_content,
            business_name=user_ctx["user_name"],
            trade_type=user_ctx["trade_type"],
            contact_number=msg.phone_from.replace("whatsapp:", ""),
        )

        # Step 2: Generate actual image using Gemini (free tier)
        image_bytes = await generate_marketing_image(
            trade_type=user_ctx["trade_type"],
            business_name=user_ctx["user_name"],
            description=text_content,
            contact=msg.phone_from.replace("whatsapp:", ""),
        )

        if image_bytes:
            # Upload image to MinIO and get public URL
            import uuid
            image_filename = f"marketing/{uuid.uuid4().hex}.png"
            image_url = upload_to_storage(image_bytes, image_filename, "image/png")

            if image_url:
                # Send image via WhatsApp with caption
                caption = mkt.get('caption', f'🎨 Marketing poster for {user_ctx["user_name"]}')
                send_media(to=msg.phone_from, body=caption, media_url=image_url)
                reply = (
                    f"🎨 *Marketing Image Generated!*\n\n"
                    f"📝 *Caption:* {caption}\n\n"
                    f"📌 *Text overlay:*\n"
                    + "\n".join(f"  • {t}" for t in mkt.get('overlay_text', []))
                    + f"\n\n✅ Image sent! Share it on WhatsApp Status or social media."
                )
            else:
                reply = (
                    f"🎨 Image generated but upload failed.\n\n"
                    f"📝 *Caption:* {mkt.get('caption', '')}\n"
                    f"💡 Try again in a moment."
                )
        else:
            # Fallback to text-only prompt if Gemini fails
            reply = (
                f"🎨 *Marketing Prompt Generated!*\n\n"
                f"📝 *Caption:* {mkt.get('caption', '')}\n\n"
                f"📌 *Text overlay:*\n"
                + "\n".join(f"  • {t}" for t in mkt.get('overlay_text', []))
                + f"\n\n💡 _Image generation temporarily unavailable. "
                f"Use this prompt with any AI image tool:_\n\n"
                f"`{mkt.get('image_prompt', '')[:300]}`"
            )

    else:  # general
        reply = await handle_general(
            text_content,
            user_name=user_ctx["user_name"],
            trade_type=user_ctx["trade_type"],
            hourly_rate=user_ctx["hourly_rate"],
        )

    # Send reply via WhatsApp
    send_text(to=msg.phone_from, body=reply)

    # Save to conversation memory
    await add_exchange(msg.phone_from, text_content, reply)

    # Log outbound
    await log_conversation(ConversationLog(
        phone_from=msg.phone_to, phone_to=msg.phone_from,
        direction="outbound", message_type=MessageType.TEXT,
        content=reply, metadata={"intent": intent},
    ))


async def handle_voice_message(msg: InboundMessage):
    """Handle a voice message — download, transcribe, then route through AI."""
    log.info("processing_voice", sid=msg.message_sid)

    audio_bytes, content_type = await download_twilio_media(msg.media_url)
    ext = get_extension_for_content_type(content_type)
    stored_url = upload_to_storage(audio_bytes, filename=f"{msg.message_sid}{ext}", content_type=content_type)

    asr_result = await transcribe_audio(audio_bytes, content_type)

    await log_conversation(ConversationLog(
        phone_from=msg.phone_from, phone_to=msg.phone_to,
        direction="inbound", message_type=MessageType.VOICE,
        message_sid=msg.message_sid, content=msg.body,
        transcript=asr_result.transcript, media_url=msg.media_url,
        media_stored_url=stored_url,
        metadata={"asr_language": asr_result.language, "asr_duration": asr_result.duration_seconds},
    ))

    # Send transcription acknowledgment
    lang_label = asr_result.language or "auto"
    send_text(to=msg.phone_from, body=f"🎤 I heard ({lang_label}): \"{asr_result.transcript}\"\n\n⏳ Processing...")

    # Now route the transcript through the AI pipeline
    await process_text_with_ai(msg, asr_result.transcript)


async def handle_image_message(msg: InboundMessage):
    """Handle image — store, run OCR, and return results."""
    file_bytes, content_type = await download_twilio_media(msg.media_url)
    ext = get_extension_for_content_type(content_type)
    stored_url = upload_to_storage(file_bytes, filename=f"{msg.message_sid}{ext}", content_type=content_type)

    await log_conversation(ConversationLog(
        phone_from=msg.phone_from, phone_to=msg.phone_to,
        direction="inbound", message_type=MessageType.IMAGE,
        message_sid=msg.message_sid, content=msg.body,
        media_url=msg.media_url, media_stored_url=stored_url,
    ))

    # Run OCR on the image
    send_text(to=msg.phone_from, body="📷 Image received! Analyzing... ⏳")
    try:
        ocr_result = await extract_text_from_image(file_bytes, content_type)
        reply = format_ocr_whatsapp(ocr_result)
    except Exception as e:
        log.error("ocr_failed", error=str(e))
        reply = "📷 Image saved! Could not extract text at this time."

    send_text(to=msg.phone_from, body=reply)


async def handle_document_message(msg: InboundMessage):
    """Handle document — store and acknowledge."""
    doc_bytes, content_type = await download_twilio_media(msg.media_url)
    ext = get_extension_for_content_type(content_type)
    stored_url = upload_to_storage(doc_bytes, filename=f"{msg.message_sid}{ext}", content_type=content_type)

    await log_conversation(ConversationLog(
        phone_from=msg.phone_from, phone_to=msg.phone_to,
        direction="inbound", message_type=MessageType.DOCUMENT,
        message_sid=msg.message_sid, content=msg.body,
        media_url=msg.media_url, media_stored_url=stored_url,
    ))

    reply = "📄 Document received and saved!"
    send_text(to=msg.phone_from, body=reply)


# ── Message Router ──────────────────────────────────────────

async def process_message(msg: InboundMessage):
    """Route a message to the correct handler based on type."""
    try:
        if msg.message_type == MessageType.TEXT:
            await process_text_with_ai(msg, msg.body or "")
        elif msg.message_type == MessageType.VOICE:
            await handle_voice_message(msg)
        elif msg.message_type == MessageType.IMAGE:
            await handle_image_message(msg)
        elif msg.message_type == MessageType.DOCUMENT:
            await handle_document_message(msg)
        else:
            send_text(to=msg.phone_from, body="⚠️ Unsupported message type.")
    except Exception as e:
        log.error("message_processing_failed", error=str(e), sid=msg.message_sid, exc_info=True)
        try:
            send_text(to=msg.phone_from, body="⚠️ Sorry, something went wrong. Please try again.")
        except Exception:
            pass


# ── Worker Main Loop ────────────────────────────────────────

async def worker_loop():
    """Continuously dequeue and process messages."""
    log.info("worker_started", version="phase4", queue="tradesbot:inbound_messages")

    while True:
        try:
            msg = await dequeue_message(timeout=5)
            if msg is None:
                continue

            log.info("processing_message", sid=msg.message_sid, type=msg.message_type.value)
            await process_message(msg)
            log.info("message_processed", sid=msg.message_sid)

        except Exception as e:
            log.error("worker_error", error=str(e), exc_info=True)
            await asyncio.sleep(1)


async def run_all():
    """Run message worker + follow-up scheduler concurrently."""
    await asyncio.gather(
        worker_loop(),
        followup_loop(),
    )


def main():
    """Entry point for the worker process."""
    asyncio.run(run_all())


if __name__ == "__main__":
    main()
