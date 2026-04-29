"""
OCR Service — extracts text from images using Groq's vision model.
Uses Groq's Llama Vision for OCR instead of Tesseract (no GPU needed, better accuracy).
"""
import base64
import tempfile
from pathlib import Path
from groq import Groq
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("ocr")
settings = get_settings()

_groq: Groq = None


def _get_groq() -> Groq:
    global _groq
    if _groq is None:
        _groq = Groq(api_key=settings.groq_api_key)
    return _groq


async def extract_text_from_image(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Extract text from an image using Groq's vision model.
    Returns structured data with raw text and any detected invoice/receipt data.
    """
    groq = _get_groq()

    # Encode image to base64
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    media_type = content_type or "image/jpeg"

    try:
        response = groq.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract ALL text from this image. If it's an invoice, receipt, or business document, also extract structured data.

Respond with JSON:
{
  "raw_text": "all text found in the image",
  "document_type": "invoice/receipt/form/other/none",
  "structured_data": {
    "vendor_name": "if found",
    "date": "if found",
    "items": [{"description": "item", "amount": 0}],
    "total": 0,
    "tax": 0,
    "grand_total": 0
  },
  "language": "detected language",
  "confidence": 0.0-1.0
}

If no text is found, return {"raw_text": "", "document_type": "none", "confidence": 0}."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024,
            temperature=0.1,
        )

        raw = response.choices[0].message.content

        # Parse JSON response
        import json
        try:
            if "```json" in raw:
                json_str = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                json_str = raw.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw.strip()

            result = json.loads(json_str)
            log.info("ocr_complete", doc_type=result.get("document_type"), confidence=result.get("confidence"))
            return result

        except (json.JSONDecodeError, IndexError):
            log.warning("ocr_json_failed", raw=raw[:200])
            return {"raw_text": raw, "document_type": "other", "confidence": 0.5}

    except Exception as e:
        log.error("ocr_failed", error=str(e))
        return {"raw_text": "", "document_type": "none", "confidence": 0, "error": str(e)}


def format_ocr_whatsapp(ocr_result: dict) -> str:
    """Format OCR results as a WhatsApp message."""
    if not ocr_result.get("raw_text"):
        return "📷 I couldn't find any text in this image. Please try with a clearer photo."

    doc_type = ocr_result.get("document_type", "other")
    confidence = ocr_result.get("confidence", 0)

    lines = [
        f"📄 *Document Scanned* ({doc_type.title()})",
        f"Confidence: {'🟢' if confidence > 0.8 else '🟡' if confidence > 0.5 else '🔴'} {confidence:.0%}",
        "",
    ]

    if doc_type in ("invoice", "receipt") and ocr_result.get("structured_data"):
        data = ocr_result["structured_data"]
        if data.get("vendor_name"):
            lines.append(f"🏢 {data['vendor_name']}")
        if data.get("date"):
            lines.append(f"📅 {data['date']}")

        items = data.get("items", [])
        if items:
            lines.append("\n📌 *Items:*")
            for i, item in enumerate(items, 1):
                desc = item.get("description", "Item")
                amt = item.get("amount", 0)
                lines.append(f"  {i}. {desc} — ₹{amt:,.0f}" if amt else f"  {i}. {desc}")

        if data.get("grand_total"):
            lines.append(f"\n🏷️ *Total: ₹{data['grand_total']:,.0f}*")
    else:
        text_preview = ocr_result["raw_text"][:500]
        lines.append(f"📝 *Extracted Text:*\n{text_preview}")

    return "\n".join(lines)
