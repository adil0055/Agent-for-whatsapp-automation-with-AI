"""
Security middleware for TradesBot.
- Twilio webhook signature validation
- Request logging
- Rate limiting headers
"""
import hmac
import hashlib
import base64
from urllib.parse import urlencode
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("security")
settings = get_settings()


def validate_twilio_signature(url: str, params: dict, signature: str, auth_token: str) -> bool:
    """
    Validate Twilio webhook signature per:
    https://www.twilio.com/docs/usage/security#validating-requests
    """
    # Sort POST params and append to URL
    s = url
    if params:
        for key in sorted(params.keys()):
            s += key + params[key]

    # HMAC-SHA1
    mac = hmac.new(auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1)
    computed = base64.b64encode(mac.digest()).decode("utf-8")

    return hmac.compare_digest(computed, signature)


class TwilioSignatureMiddleware(BaseHTTPMiddleware):
    """
    Validates Twilio X-Twilio-Signature header on webhook endpoints.
    Enabled only in production (ENVIRONMENT=production).
    """

    async def dispatch(self, request: Request, call_next):
        # Only validate webhook paths in production
        if (
            settings.app_env == "production"
            and request.url.path.startswith("/api/webhooks/")
            and request.method == "POST"
        ):
            signature = request.headers.get("X-Twilio-Signature", "")
            if not signature:
                log.warning("missing_twilio_signature", path=request.url.path)
                raise HTTPException(status_code=403, detail="Missing Twilio signature")

            # Read form data
            body = await request.body()
            form_data = dict(
                item.split("=", 1)
                for item in body.decode().split("&")
                if "=" in item
            )

            # Reconstruct the full URL
            url = str(request.url)

            if not validate_twilio_signature(url, form_data, signature, settings.twilio_auth_token):
                log.warning("invalid_twilio_signature", path=request.url.path)
                raise HTTPException(status_code=403, detail="Invalid signature")

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
