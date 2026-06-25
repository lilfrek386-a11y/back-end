from typing import Annotated
import redis.asyncio as redis
from fastapi import Depends
from app.core.config import settings

redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized.")
    return redis_client


async def init_redis() -> None:
    global redis_client
    redis_client = redis.Redis(
        host=settings.redis.HOST, port=settings.redis.PORT, decode_responses=True
    )


async def close_redis() -> None:
    if redis_client:
        await redis_client.aclose()


type RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
