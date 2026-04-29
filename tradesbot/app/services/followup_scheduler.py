"""
Follow-up Scheduler — APScheduler-based service that checks for
pending follow-ups and sends reminders via WhatsApp.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from app.models.database import async_session
from app.services.whatsapp import send_text
from app.agents.followup_agent import generate_reminder
from app.utils.logger import get_logger

log = get_logger("scheduler")

# Follow-up rules configuration
FOLLOW_UP_RULES = {
    "quote": {
        "delay_days": 3,
        "max_reminders": 3,
        "interval_days": 2,
        "escalation": "owner_notify",
    },
    "invoice": {
        "delay_days": 7,
        "max_reminders": 5,
        "interval_days": 3,
        "escalation": "owner_notify",
    },
}


async def create_follow_up(user_id: str, reference_type: str, reference_id: str, customer_id: str = None):
    """Create a follow-up entry when a quote/invoice is sent."""
    rules = FOLLOW_UP_RULES.get(reference_type, FOLLOW_UP_RULES["quote"])
    next_reminder = datetime.utcnow() + timedelta(days=rules["delay_days"])

    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO follow_ups (user_id, customer_id, reference_type, reference_id,
                    max_reminders, next_reminder_at)
                VALUES (:uid, :cid, :ref_type, :ref_id, :max_rem, :next_at)
            """),
            {
                "uid": user_id, "cid": customer_id,
                "ref_type": reference_type, "ref_id": reference_id,
                "max_rem": rules["max_reminders"], "next_at": next_reminder,
            },
        )
        await session.commit()
    log.info("followup_created", ref_type=reference_type, ref_id=reference_id, next_at=str(next_reminder))


async def check_and_send_reminders():
    """Check for due follow-ups and send reminder messages."""
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT f.id, f.reference_type, f.reference_id, f.reminder_count, f.max_reminders,
                       f.user_id, u.name as user_name, u.trade_type, u.phone_number,
                       u.language_preference
                FROM follow_ups f
                JOIN users u ON f.user_id = u.id
                WHERE f.status = 'pending'
                  AND f.next_reminder_at <= NOW()
                ORDER BY f.next_reminder_at ASC
                LIMIT 20
            """),
        )
        due = result.fetchall()

    if not due:
        return 0

    sent_count = 0
    for row in due:
        fu_id, ref_type, ref_id, count, max_rem, user_id, user_name, trade_type, phone, lang = row

        # Get reference details (amount)
        amount = 0
        async with async_session() as session:
            if ref_type == "quote":
                r = await session.execute(text("SELECT grand_total FROM quotes WHERE id = :id"), {"id": ref_id})
            else:
                r = await session.execute(text("SELECT grand_total FROM invoices WHERE id = :id"), {"id": ref_id})
            amt_row = r.fetchone()
            if amt_row:
                amount = float(amt_row[0] or 0)

        if count >= max_rem:
            # Escalate
            async with async_session() as session:
                await session.execute(
                    text("UPDATE follow_ups SET status = 'escalated', escalated = TRUE, updated_at = NOW() WHERE id = :id"),
                    {"id": fu_id},
                )
                await session.commit()
            send_text(
                to=f"whatsapp:{phone}",
                body=f"⚠️ Follow-up for {ref_type} #{str(ref_id)[:8]} has been escalated after {max_rem} reminders with no response."
            )
            log.info("followup_escalated", fu_id=str(fu_id), ref_type=ref_type)
            continue

        # Generate and send reminder
        try:
            new_count = count + 1
            reminder_msg = await generate_reminder(
                user_name=user_name or "Tradesperson",
                trade_type=trade_type or "plumber",
                customer_name="Customer",
                follow_up_type=f"{ref_type}_pending" if ref_type == "quote" else f"{ref_type}_unpaid",
                amount=amount,
                reference_id=str(ref_id)[:8],
                days_elapsed=(new_count * FOLLOW_UP_RULES.get(ref_type, {}).get("interval_days", 2)),
                reminder_count=new_count,
                max_reminders=max_rem,
                language=lang or "en",
            )

            send_text(to=f"whatsapp:{phone}", body=reminder_msg)

            rules = FOLLOW_UP_RULES.get(ref_type, FOLLOW_UP_RULES["quote"])
            next_at = datetime.utcnow() + timedelta(days=rules["interval_days"])

            async with async_session() as session:
                await session.execute(
                    text("""
                        UPDATE follow_ups SET
                            reminder_count = :count, last_reminded_at = NOW(),
                            next_reminder_at = :next_at, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {"count": new_count, "next_at": next_at, "id": fu_id},
                )
                await session.commit()

            sent_count += 1
            log.info("reminder_sent", fu_id=str(fu_id), count=new_count, ref_type=ref_type)

        except Exception as e:
            log.error("reminder_failed", fu_id=str(fu_id), error=str(e))

    return sent_count


async def cancel_follow_up(reference_type: str, reference_id: str):
    """Cancel follow-up when customer responds (e.g., accepts quote)."""
    async with async_session() as session:
        await session.execute(
            text("""
                UPDATE follow_ups SET status = 'responded', updated_at = NOW()
                WHERE reference_type = :ref_type AND reference_id = :ref_id AND status = 'pending'
            """),
            {"ref_type": reference_type, "ref_id": reference_id},
        )
        await session.commit()
    log.info("followup_cancelled", ref_type=reference_type, ref_id=reference_id)


async def scheduler_loop():
    """Run the follow-up check every 15 minutes."""
    log.info("followup_scheduler_started")
    while True:
        try:
            count = await check_and_send_reminders()
            if count > 0:
                log.info("reminders_batch_sent", count=count)
        except Exception as e:
            log.error("scheduler_error", error=str(e))
        await asyncio.sleep(900)  # 15 minutes
