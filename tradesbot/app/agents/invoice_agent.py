"""
Invoice Agent — generates GST-compliant invoices and PDF documents.
"""
import json
from datetime import datetime, timedelta
from app.services.llm import chat
from app.utils.logger import get_logger

log = get_logger("invoice_agent")

INVOICE_PROMPT = """You are an invoicing assistant for a {trade_type} business in India.

Generate a GST-compliant invoice based on the provided job/quote details.

Business details:
- Name: {business_name}
- GSTIN: {gstin}
- Trade: {trade_type}
- Hourly rate: ₹{hourly_rate}/hr

Respond with ONLY a JSON object:
{{
  "customer_name": "customer name",
  "items": [
    {{"description": "item name", "hsn_sac": "9954", "quantity": 1, "unit": "hrs/pcs/job", "unit_price": 0.00, "total": 0.00}}
  ],
  "subtotal": 0.00,
  "cgst_rate": 9,
  "cgst_amount": 0.00,
  "sgst_rate": 9,
  "sgst_amount": 0.00,
  "grand_total": 0.00,
  "payment_terms": "Due within 15 days",
  "notes": ""
}}

Rules:
- Use HSN/SAC code 9954 for construction/repair services
- Split GST into CGST (9%) + SGST (9%) for same-state
- Calculate all amounts correctly
- Include all items from the job description

Job/Quote details: {job_details}"""


async def generate_invoice_data(
    job_details: str,
    business_name: str = "Tradesperson",
    trade_type: str = "plumber",
    hourly_rate: float = 300.0,
    gstin: str = "N/A",
) -> dict:
    """Generate structured invoice data from job details."""
    prompt = INVOICE_PROMPT.format(
        trade_type=trade_type,
        business_name=business_name,
        gstin=gstin,
        hourly_rate=hourly_rate,
        job_details=job_details,
    )

    raw = await chat(prompt, job_details)

    try:
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        data = json.loads(json_str)
        log.info("invoice_generated", total=data.get("grand_total"))
        return data
    except (json.JSONDecodeError, IndexError):
        log.error("invoice_parse_failed", raw=raw[:300])
        return {"error": "Failed to generate invoice", "raw_response": raw}


def format_invoice_whatsapp(invoice_data: dict, invoice_number: str) -> str:
    """Format invoice data as a WhatsApp message."""
    if "error" in invoice_data:
        return f"⚠️ Could not generate invoice. Please provide more details about the completed job."

    items = invoice_data.get("items", [])
    customer = invoice_data.get("customer_name", "Customer")

    lines = [
        f"🧾 *Invoice #{invoice_number}*",
        "━━━━━━━━━━━━━━━━━━",
        f"📅 Date: {datetime.now().strftime('%d %b %Y')}",
        f"👤 Customer: {customer}",
        "",
        "📌 *Items:*",
    ]

    for i, item in enumerate(items, 1):
        desc = item.get("description", "Service")
        total = item.get("total", 0)
        lines.append(f"  {i}. {desc} — ₹{total:,.0f}")

    subtotal = invoice_data.get("subtotal", 0)
    cgst = invoice_data.get("cgst_amount", 0)
    sgst = invoice_data.get("sgst_amount", 0)
    grand_total = invoice_data.get("grand_total", 0)

    lines.extend([
        "",
        f"💰 Subtotal: ₹{subtotal:,.0f}",
        f"📊 CGST (9%): ₹{cgst:,.0f}",
        f"📊 SGST (9%): ₹{sgst:,.0f}",
        "━━━━━━━━━━━━━━━━━━",
        f"🏷️ *Total: ₹{grand_total:,.0f}*",
        "",
        f"📝 {invoice_data.get('payment_terms', 'Due within 15 days')}",
        "",
        "💳 Pay via UPI / Bank Transfer / Cash",
    ])

    return "\n".join(lines)
