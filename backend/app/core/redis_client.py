"""Redis client configuration."""
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_redis() -> Redis:
    """Get Redis client instance."""
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    return redis


async def check_redis_health() -> bool:
    """Check if Redis is reachable."""
    try:
        redis = await get_redis()
        await redis.ping()
        await redis.close()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False
