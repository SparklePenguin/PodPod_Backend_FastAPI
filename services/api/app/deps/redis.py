from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    global _redis_client
    if not _redis_client:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield _redis_client
    finally:
        pass
