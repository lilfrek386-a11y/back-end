import logging
import redis.asyncio as redis
from app.schemas.redis import RedisQuizAttemptDetail
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:

    def __init__(
        self, redis_client: redis.Redis, ttl_seconds: int = settings.redis.TTL_SECONDS
    ):
        self.redis = redis_client
        self.TTL_SECONDS = ttl_seconds

    async def save_quiz_attempt_details(self, details: RedisQuizAttemptDetail) -> None:
        key = f"quiz_attempt:{details.attempt_id}"

        json_data = details.model_dump_json()

        await self.redis.set(name=key, value=json_data, ex=self.TTL_SECONDS)
        logger.info(f"Saved quiz details to Redis. Key: {key}, TTL: 48h")
