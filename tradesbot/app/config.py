"""
Configuration module — loads all settings from environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Twilio ──────────────────────────────────────────────
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str = "+14155238886"

    # ── Groq (ASR + LLM) ───────────────────────────────────
    groq_api_key: str

    # ── Gemini (Image Generation) ──────────────────────────
    gemini_api_key: str = ""

    # ── Database ────────────────────────────────────────────
    database_url: str

    # ── Redis ───────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── MinIO ───────────────────────────────────────────────
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "tradesbot-media"
    minio_secure: bool = False

    # ── App ─────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "DEBUG"
    webhook_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
