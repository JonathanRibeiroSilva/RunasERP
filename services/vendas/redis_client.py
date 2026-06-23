"""
Cliente Redis compartilhado.
"""
import redis.asyncio as redis
from config import settings


async def get_redis() -> redis.Redis:
    """Retorna cliente Redis."""
    return redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )


# Cliente singleton (não é async, use get_redis() para operações)
redis_client = None


async def init_redis():
    """Inicializa cliente Redis (se necessário no futuro)."""
    global redis_client
    redis_client = await get_redis()
    return redis_client


async def close_redis():
    """Fecha conexão Redis (se necessário no futuro)."""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
