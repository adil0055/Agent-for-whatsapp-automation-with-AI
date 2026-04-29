"""
End-to-End Integration Tests for TradesBot.
Tests all 8 core flows defined in Phase 5.
"""
import asyncio
import json
import pytest
import httpx
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

BASE_URL = "http://localhost:8000"
TEST_PHONE = "whatsapp:+919999900000"
BOT_PHONE = "whatsapp:+14155238886"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        yield c


# ── Helpers ──────────────────────────────────────────────────

def twilio_payload(body: str, sid: str = None, num_media: int = 0):
    """Create a Twilio-like webhook payload."""
    return {
        "MessageSid": sid or f"SM_TEST_{datetime.now().timestamp():.0f}",
        "From": TEST_PHONE,
        "To": BOT_PHONE,
        "Body": body,
        "NumMedia": str(num_media),
    }


# ── Flow 1: Text Scheduling ─────────────────────────────────

@pytest.mark.asyncio
async def test_flow_1_text_scheduling(client: httpx.AsyncClient):
    """Send 'need plumber Friday 9AM' → confirm → verify DB."""
    r = await client.post(
        "/api/webhooks/twilio",
        data=twilio_payload("I need a plumber visit on Friday at 9 AM at my house in Koramangala"),
    )
    assert r.status_code == 200

    # Wait for worker to process
    await asyncio.sleep(8)

    # Verify job created in DB
    jobs = await client.get("/api/jobs")
    assert jobs.status_code == 200
    data = jobs.json()
    assert len(data) >= 1


# ── Flow 2: Quote Generation ────────────────────────────────

@pytest.mark.asyncio
async def test_flow_2_quote_generation(client: httpx.AsyncClient):
    """Send request about pipe leak → receive itemized quote."""
    r = await client.post(
        "/api/webhooks/twilio",
        data=twilio_payload("How much will it cost to fix a leaking kitchen faucet?"),
    )
    assert r.status_code == 200

    await asyncio.sleep(8)

    quotes = await client.get("/api/quotes")
    assert quotes.status_code == 200
    data = quotes.json()
    assert len(data) >= 1
    latest = data[-1]
    assert latest.get("grand_total", 0) > 0
    assert latest.get("status") == "draft"


# ── Flow 3: Invoice Generation ──────────────────────────────

@pytest.mark.asyncio
async def test_flow_3_invoice_generation(client: httpx.AsyncClient):
    """Request invoice → verify invoice created."""
    r = await client.post(
        "/api/webhooks/twilio",
        data=twilio_payload("Generate an invoice for bathroom tap repair, 2 hours of work for Mr. Kumar"),
    )
    assert r.status_code == 200

    await asyncio.sleep(8)

    invoices = await client.get("/api/invoices")
    assert invoices.status_code == 200
    data = invoices.json()
    assert len(data) >= 1


# ── Flow 4: Follow-up Reminder ──────────────────────────────

@pytest.mark.asyncio
async def test_flow_4_followup_trigger(client: httpx.AsyncClient):
    """Trigger follow-up check endpoint."""
    r = await client.post("/api/followups/trigger")
    assert r.status_code == 200
    data = r.json()
    assert "processed" in data


# ── Flow 5: Consent Management ──────────────────────────────

@pytest.mark.asyncio
async def test_flow_5_consent_flow(client: httpx.AsyncClient):
    """Grant consent via API, verify."""
    # Grant consent
    r_grant = await client.post(
        "/api/voice/consent/request",
        params={"phone": "+919999900000"},
    )
    assert r_grant.status_code == 200

    # Check consent status
    r_check = await client.get(
        "/api/voice/consent/check",
        params={"phone": "+919999900000"},
    )
    assert r_check.status_code == 200


# ── Flow 6: Marketing Prompt ────────────────────────────────

@pytest.mark.asyncio
async def test_flow_6_marketing(client: httpx.AsyncClient):
    """Request promo → marketing prompt generated."""
    r = await client.post(
        "/api/webhooks/twilio",
        data=twilio_payload("Create a festive Diwali promo for my electrical services"),
    )
    assert r.status_code == 200

    await asyncio.sleep(8)

    # Verify through conversation log
    convs = await client.get("/api/conversations")
    assert convs.status_code == 200
    data = convs.json()
    found = any("Marketing" in str(c.get("content_preview", "")) for c in data)
    assert found, "Marketing response not found in conversations"


# ── Flow 7: Language Detection ───────────────────────────────

@pytest.mark.asyncio
async def test_flow_7_language_detection(client: httpx.AsyncClient):
    """Send text in different languages → correct detection."""
    # English
    r1 = await client.get("/api/language/detect", params={"text": "I need a plumber tomorrow"})
    assert r1.status_code == 200
    assert r1.json()["primary_language"] == "en"

    # Hindi (Devanagari)
    r2 = await client.get("/api/language/detect", params={"text": "मुझे कल प्लंबर चाहिए"})
    assert r2.status_code == 200
    assert r2.json()["primary_language"] == "hi"

    # Hinglish (code-mixed)
    r3 = await client.get("/api/language/detect", params={"text": "Mujhe ek plumber chahiye kal subah"})
    assert r3.status_code == 200
    assert r3.json()["primary_language"] == "hi"
    assert r3.json()["is_code_mixed"] is True


# ── Flow 8: Multi-Language Response ──────────────────────────

@pytest.mark.asyncio
async def test_flow_8_multilang_response(client: httpx.AsyncClient):
    """Send Tamil message → verify processed."""
    r = await client.post(
        "/api/webhooks/twilio",
        data=twilio_payload("எனக்கு நாளை காலை ஒரு plumber வேண்டும்"),
    )
    assert r.status_code == 200

    await asyncio.sleep(8)

    convs = await client.get("/api/conversations")
    assert convs.status_code == 200


# ── API Health Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(client: httpx.AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: httpx.AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["phase"] == 4
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_openapi_docs(client: httpx.AsyncClient):
    r = await client.get("/docs")
    assert r.status_code == 200
