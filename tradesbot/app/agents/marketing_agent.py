"""
Marketing Agent — generates image prompts and text overlays for promotional materials.
"""
import json
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("marketing_agent")

MARKETING_PROMPT = """You are a marketing assistant for a {trade_type} business in India.

The tradesperson wants to create a professional marketing image for WhatsApp/social media.

Based on their request, generate a detailed image prompt and text overlays.

User request: {user_request}
Business name: {business_name}
Contact: {contact_number}

Rules:
- Create professional, clean, modern visuals
- Include relevant text for overlays (business name, offer, contact)
- Use bright colors suitable for WhatsApp sharing
- Culturally appropriate for Indian audience

Respond with ONLY a JSON:
{{
  "image_prompt": "detailed prompt for AI image generation (describe the visual scene, style, colors, composition - do NOT include text in the image prompt)",
  "overlay_text": ["Line 1 - Business/Service", "Line 2 - Offer/Price", "Line 3 - Contact"],
  "caption": "Short WhatsApp caption to send with the image",
  "style": "professional/vibrant/minimal"
}}"""


async def generate_marketing_prompt(
    user_request: str,
    business_name: str = "Tradesperson",
    trade_type: str = "plumber",
    contact_number: str = "",
) -> dict:
    """Generate marketing image prompt and overlay text."""
    prompt = MARKETING_PROMPT.format(
        trade_type=trade_type,
        user_request=user_request,
        business_name=business_name,
        contact_number=contact_number,
    )

    raw = await chat(prompt, user_request)

    try:
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        result = json.loads(json_str)
        log.info("marketing_prompt_generated", style=result.get("style"))
        return result
    except (json.JSONDecodeError, IndexError):
        log.warning("marketing_parse_failed", raw=raw[:200])
        return {
            "image_prompt": f"Professional marketing poster for {trade_type} services, modern design, vibrant colors",
            "overlay_text": [business_name, user_request, contact_number],
            "caption": f"🔧 {user_request} — Contact us today!",
            "style": "professional",
        }
