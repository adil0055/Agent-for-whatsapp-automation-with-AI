"""
Pydantic models for request/response validation and internal data transfer.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Enums ────────────────────────────────────────────────────

class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    OTHER = "other"


class Direction(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ── Queue Job Schema ─────────────────────────────────────────

class InboundMessage(BaseModel):
    """Schema for messages pushed to the Redis queue."""
    message_sid: str
    phone_from: str
    phone_to: str
    message_type: MessageType
    body: Optional[str] = None
    media_url: Optional[str] = None
    media_content_type: Optional[str] = None
    num_media: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Conversation Log ─────────────────────────────────────────

class ConversationLog(BaseModel):
    """Schema for logging a conversation entry to the database."""
    phone_from: str
    phone_to: str
    direction: Direction
    message_type: MessageType
    message_sid: Optional[str] = None
    content: Optional[str] = None
    transcript: Optional[str] = None
    media_url: Optional[str] = None
    media_stored_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


# ── ASR Result ───────────────────────────────────────────────

class ASRResult(BaseModel):
    """Result from the ASR (speech-to-text) service."""
    transcript: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None


# ── API Responses ────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    services: dict = Field(default_factory=dict)
