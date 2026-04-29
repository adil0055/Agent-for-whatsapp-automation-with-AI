"""
Follow-up Agent — generates polite, escalating reminder messages.
"""
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("followup_agent")

FOLLOWUP_PROMPT = """You are a polite follow-up assistant for a {trade_type} business in India.

Generate a professional, friendly reminder message for a customer via WhatsApp.

Context:
- Tradesperson: {user_name} ({trade_type})
- Customer: {customer_name}
- Type: {follow_up_type} (quote_pending / invoice_unpaid)
- Amount: ₹{amount}
- Reference: {reference_id}
- Days since sent: {days_elapsed}
- Reminder #: {reminder_count} of {max_reminders}

Tone guidelines:
- Reminder 1: gentle, informative
- Reminder 2: slightly more direct
- Reminder 3: firm but polite, mention deadline
- Never aggressive or threatening

Rules:
- Use emojis naturally
- Include the amount
- End with a clear call-to-action
- Be concise (WhatsApp message)
- Respond in {language}

Output: ONLY the reminder message text (no JSON, no wrapper)."""


async def generate_reminder(
    user_name: str,
    trade_type: str,
    customer_name: str,
    follow_up_type: str,
    amount: float,
    reference_id: str,
    days_elapsed: int,
    reminder_count: int,
    max_reminders: int = 3,
    language: str = "en",
) -> str:
    """Generate a follow-up reminder message."""
    prompt = FOLLOWUP_PROMPT.format(
        user_name=user_name,
        trade_type=trade_type,
        customer_name=customer_name,
        follow_up_type=follow_up_type,
        amount=amount,
        reference_id=reference_id,
        days_elapsed=days_elapsed,
        reminder_count=reminder_count,
        max_reminders=max_reminders,
        language=language,
    )

    message = await chat(prompt, f"Generate reminder #{reminder_count} for {follow_up_type}")
    log.info("reminder_generated", type=follow_up_type, count=reminder_count, length=len(message))
    return message
