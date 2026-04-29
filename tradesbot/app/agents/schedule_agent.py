"""
Schedule Agent — handles job booking via conversational flow.
"""
import json
from datetime import datetime
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("schedule_agent")

SCHEDULE_PROMPT = """You are a scheduling assistant for a {trade_type} business in India, communicating via WhatsApp.

Help the tradesperson book jobs with customers. From the user's message, extract scheduling details.

Current date and time: {current_date}

Respond with ONLY a JSON object:
{{
  "action": "book/query/confirm/unclear",
  "customer_name": "name if mentioned or null",
  "customer_phone": "phone if mentioned or null",
  "job_description": "what needs to be done",
  "preferred_date": "YYYY-MM-DD or null",
  "preferred_time": "HH:MM or null",
  "location": "address if mentioned or null",
  "missing_info": ["list of info still needed"],
  "response_message": "friendly WhatsApp message to send back"
}}

Rules:
- If date/time is relative ("tomorrow", "next Friday"), convert to actual date
- If critical info is missing, ask for it in response_message
- Time format: 24-hour
- If all info present, set action to "book" and confirm in response_message
- Be concise and friendly
- Respond in the same language as the user's message

User message: {user_message}"""


async def handle_schedule(
    user_message: str,
    trade_type: str = "plumber",
    current_date: str = None,
) -> dict:
    """Process a scheduling request and return structured data + response."""
    if not current_date:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")

    prompt = SCHEDULE_PROMPT.format(
        trade_type=trade_type,
        current_date=current_date,
        user_message=user_message,
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
        log.info("schedule_parsed", action=result.get("action"), date=result.get("preferred_date"))
        return result
    except (json.JSONDecodeError, IndexError):
        log.warning("schedule_parse_failed", raw=raw[:200])
        return {
            "action": "unclear",
            "response_message": raw if len(raw) < 500 else "I'd be happy to help you schedule a job! Could you tell me:\n1. What work needs to be done?\n2. When would you like it?\n3. Customer name and address?",
        }
