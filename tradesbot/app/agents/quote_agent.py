"""
Quote Agent — generates itemized service quotes using LLM.
"""
import json
from datetime import datetime, timedelta
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("quote_agent")

QUOTE_PROMPT = """You are a quoting assistant for a {trade_type} business in India.

Given a job description, produce an itemized quote.

Tradesperson rates:
- Hourly labor rate: ₹{hourly_rate}/hr
- GSTIN: {gstin}

Rules:
- Estimate realistic quantities based on common {trade_type} jobs in India
- Use reasonable India-market material prices
- Always include GST at 18%
- Be transparent: mark estimates with "~" (approx)

Respond with ONLY a JSON object in this exact format:
{{
  "title": "Short job title",
  "items": [
    {{"description": "item name", "type": "labor/material", "quantity": 1, "unit": "hrs/pcs/job", "unit_price": 0.00, "total": 0.00}}
  ],
  "labor_total": 0.00,
  "material_total": 0.00,
  "subtotal": 0.00,
  "gst_rate": 18,
  "gst_amount": 0.00,
  "grand_total": 0.00,
  "estimated_duration": "2 hours",
  "notes": "any relevant notes",
  "validity_days": 7
}}

Job Description: {job_description}"""


async def generate_quote(
    job_description: str,
    trade_type: str = "plumber",
    hourly_rate: float = 300.0,
    gstin: str = "N/A",
) -> dict:
    """Generate an itemized quote from a job description."""
    prompt = QUOTE_PROMPT.format(
        trade_type=trade_type,
        hourly_rate=hourly_rate,
        gstin=gstin,
        job_description=job_description,
    )

    raw = await chat(prompt, job_description)

    try:
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        quote_data = json.loads(json_str)
        log.info("quote_generated", title=quote_data.get("title"), total=quote_data.get("grand_total"))
        return quote_data
    except (json.JSONDecodeError, IndexError):
        log.error("quote_parse_failed", raw=raw[:300])
        return {"error": "Failed to generate quote", "raw_response": raw}


def format_quote_whatsapp(quote_data: dict, quote_number: str = None) -> str:
    """Format a quote dict into a WhatsApp-friendly message."""
    if "error" in quote_data:
        return f"⚠️ Sorry, I couldn't generate a quote. Here's what I understood:\n{quote_data.get('raw_response', '')[:500]}"

    qnum = quote_number or f"Q-{datetime.now().strftime('%Y%m%d-%H%M')}"
    title = quote_data.get("title", "Service Quote")
    items = quote_data.get("items", [])

    lines = [
        f"📋 *Quote #{qnum}*",
        "━━━━━━━━━━━━━━━━━━",
        f"🔧 *{title}*",
        "",
        "📌 *Items:*",
    ]

    for i, item in enumerate(items, 1):
        desc = item.get("description", "Item")
        qty = item.get("quantity", 1)
        unit = item.get("unit", "")
        total = item.get("total", 0)
        item_type = "🛠️" if item.get("type") == "labor" else "📦"
        lines.append(f"  {i}. {item_type} {desc} ({qty} {unit}) — ₹{total:,.0f}")

    subtotal = quote_data.get("subtotal", 0)
    gst_rate = quote_data.get("gst_rate", 18)
    gst_amount = quote_data.get("gst_amount", 0)
    grand_total = quote_data.get("grand_total", 0)
    validity = quote_data.get("validity_days", 7)
    valid_until = (datetime.now() + timedelta(days=validity)).strftime("%b %d, %Y")

    lines.extend([
        "",
        f"💰 Subtotal: ₹{subtotal:,.0f}",
        f"📊 GST ({gst_rate}%): ₹{gst_amount:,.0f}",
        "━━━━━━━━━━━━━━━━━━",
        f"🏷️ *Total: ₹{grand_total:,.0f}*",
        "",
        f"⏳ Valid until: {valid_until}",
    ])

    if quote_data.get("notes"):
        lines.append(f"📝 {quote_data['notes']}")

    lines.append("\nReply ✅ to accept or ❌ to discuss changes.")

    return "\n".join(lines)
