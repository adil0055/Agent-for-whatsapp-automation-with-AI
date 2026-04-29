"""
Redis-based message queue for decoupling webhook receipt from processing.
"""
import json
import redis.asyncio as aioredis
from app.config import get_settings
from app.models.schemas import InboundMessage
from app.utils.logger import get_logger

log = get_logger("queue")
settings = get_settings()

QUEUE_NAME = "tradesbot:inbound_messages"

_redis: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        log.info("redis_connected", url=settings.redis_url)
    return _redis


async def enqueue_message(message: InboundMessage) -> int:
    """
    Push an inbound message onto the processing queue.
    Returns the new queue length.
    """
    r = await get_redis()
    payload = message.model_dump_json()
    length = await r.lpush(QUEUE_NAME, payload)
    log.info("message_enqueued", sid=message.message_sid, queue_len=length)
    return length


async def dequeue_message(timeout: int = 5) -> InboundMessage | None:
    """
    Pop the next message from the queue. Blocks up to `timeout` seconds.
    Returns None if queue is empty after timeout.
    """
    r = await get_redis()
    result = await r.brpop(QUEUE_NAME, timeout=timeout)
    if result is None:
        return None

    _, payload = result
    msg = InboundMessage.model_validate_json(payload)
    log.info("message_dequeued", sid=msg.message_sid, type=msg.message_type)
    return msg


async def get_queue_length() -> int:
    r = await get_redis()
    return await r.llen(QUEUE_NAME)
