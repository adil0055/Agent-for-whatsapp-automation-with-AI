"""
General Chat Agent — handles greetings, thanks, general questions, and fallback.
"""
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("general_agent")

GENERAL_PROMPT = """You are a friendly AI assistant for a {trade_type} business in India, communicating via WhatsApp.

You help the tradesperson manage their business. You can help with:
- 📋 Quotes — "Give me a quote for fixing a pipe leak"
- 📅 Scheduling — "Book a job for tomorrow at 9 AM"
- 🧾 Invoices — "Generate invoice for the last job"
- ❓ General questions about the business

Business context:
- Name: {user_name}
- Trade: {trade_type}
- Hourly Rate: ₹{hourly_rate}/hr

Rules:
- Be concise (WhatsApp messages should be short)
- Use emojis naturally
- Respond in the same language as the user
- If the user seems to want a quote/schedule/invoice, guide them to ask clearly
- Be warm and professional"""


async def handle_general(
    user_message: str,
    user_name: str = "Tradesperson",
    trade_type: str = "plumber",
    hourly_rate: float = 300.0,
    chat_history: list = None,
) -> str:
    """Handle general chat messages."""
    prompt = GENERAL_PROMPT.format(
        user_name=user_name,
        trade_type=trade_type,
        hourly_rate=hourly_rate,
    )

    response = await chat(prompt, user_message, chat_history)
    log.info("general_response", length=len(response))
    return response
