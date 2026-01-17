"""Redis 클라이언트 관리 및 의존성 주입"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """Redis 클라이언트 반환 (일반 함수에서 직접 사용)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )
    return _redis_client


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Redis 의존성 주입용 (FastAPI Depends에서 사용)"""
    client = await get_redis_client()
    try:
        yield client
    finally:
        pass


async def close_redis():
    """Redis 연결 종료"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
