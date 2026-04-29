"""
Orchestrator Agent — classifies user intent and routes to the correct agent.
Manages conversation memory via Redis.
"""
import json
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("orchestrator")

ORCHESTRATOR_PROMPT = """You are an AI assistant for a trades business (plumbing, electrical, carpentry, etc.) operating via WhatsApp in India.

Your ONLY job is to classify the user's intent into one of these categories:
- "quote" — user wants a price estimate, cost, or quotation for a job
- "schedule" — user wants to book, schedule, or arrange an appointment/job
- "invoice" — user wants to generate a bill, invoice, or payment document
- "job_status" — user asks about existing jobs, pending work, or status updates
- "marketing" — user wants to create a promotional image, ad, or marketing material
- "general" — greetings, thanks, questions, or anything else

Current tradesperson context:
- Name: {user_name}
- Trade: {trade_type}
- Hourly Rate: ₹{hourly_rate}/hr

Respond with ONLY a JSON object:
{{"intent": "<one of: quote, schedule, invoice, job_status, marketing, general>", "confidence": <0.0-1.0>, "summary": "<brief summary of what user wants>"}}

Do NOT include any other text. ONLY the JSON object."""


async def classify_intent(
    user_message: str,
    user_name: str = "Tradesperson",
    trade_type: str = "plumber",
    hourly_rate: float = 300.0,
) -> dict:
    """
    Classify user intent from their message.
    Returns: {"intent": str, "confidence": float, "summary": str}
    """
    prompt = ORCHESTRATOR_PROMPT.format(
        user_name=user_name,
        trade_type=trade_type,
        hourly_rate=hourly_rate,
    )

    raw = await chat(prompt, user_message)

    try:
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        result = json.loads(json_str)
        log.info("intent_classified", intent=result.get("intent"), confidence=result.get("confidence"))
        return result
    except (json.JSONDecodeError, IndexError):
        log.warning("intent_parse_failed", raw=raw[:200])
        return {"intent": "general", "confidence": 0.5, "summary": user_message}
