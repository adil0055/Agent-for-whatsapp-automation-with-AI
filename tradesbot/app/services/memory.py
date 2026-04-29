"""
Conversation Memory — Redis-backed chat history for multi-turn conversations.
Each user gets a session with 24-hour TTL.
"""
import json
import redis.asyncio as aioredis
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("memory")
settings = get_settings()

SESSION_TTL = 86400  # 24 hours
MAX_HISTORY = 10     # Keep last 10 exchanges
PREFIX = "tradesbot:memory:"

_redis: aioredis.Redis = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_history(phone: str) -> list:
    """Get conversation history for a phone number."""
    r = await _get_redis()
    key = f"{PREFIX}{phone}"
    raw = await r.get(key)
    if raw:
        return json.loads(raw)
    return []


async def add_exchange(phone: str, user_msg: str, assistant_msg: str):
    """Add a user/assistant exchange to history."""
    r = await _get_redis()
    key = f"{PREFIX}{phone}"

    history = await get_history(phone)
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})

    # Keep only last N exchanges (N*2 messages)
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]

    await r.set(key, json.dumps(history), ex=SESSION_TTL)


async def clear_history(phone: str):
    """Clear conversation history for a phone number."""
    r = await _get_redis()
    await r.delete(f"{PREFIX}{phone}")
