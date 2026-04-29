"""
TradesBot — AI-powered back-office for tradespeople.
FastAPI application entry point.

Phase 5: Production-ready with metrics, security middleware, and /metrics endpoint.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from app.api.webhooks import router as webhook_router
from app.api.health import router as health_router
from app.api.data import router as data_router
from app.api.followups import router as followup_router
from app.api.voice import router as voice_router
from app.api.language import router as language_router
from app.api.media import router as media_router
from app.services.metrics import MetricsMiddleware, format_prometheus
from app.middleware.security import TwilioSignatureMiddleware, SecurityHeadersMiddleware
from app.utils.logger import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_logging()
    log = get_logger("app")
    log.info("tradesbot_starting", version="1.0.0", phase="5")
    yield
    log.info("tradesbot_shutting_down")


app = FastAPI(
    title="TradesBot",
    description="AI-powered WhatsApp back-office for tradespeople",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware (order matters — outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(TwilioSignatureMiddleware)

# Register routers
app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(data_router)
app.include_router(followup_router)
app.include_router(voice_router)
app.include_router(language_router)
app.include_router(media_router)


@app.get("/")
async def root():
    return {
        "app": "TradesBot",
        "version": "1.0.0",
        "phase": 5,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "endpoints": {
            "webhook": "/api/webhooks/twilio",
            "jobs": "/api/jobs",
            "quotes": "/api/quotes",
            "invoices": "/api/invoices",
            "followups": "/api/followups",
            "voice": "/api/voice/call",
            "language": "/api/language/detect",
            "conversations": "/api/conversations",
            "media": "/api/media/{path}",
        },
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return format_prometheus()
