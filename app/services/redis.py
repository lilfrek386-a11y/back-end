import logging
from uuid import UUID

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

    async def get_quiz_attempts_details(
        self, attempt_ids: list[UUID]
    ) -> list[RedisQuizAttemptDetail]:
        if not attempt_ids:
            return []

        keys = [f"quiz_attempt:{attempt_id}" for attempt_id in attempt_ids]

        raw_data_list = await self.redis.mget(keys)

        results = []
        for raw_data in raw_data_list:
            if raw_data:
                details = RedisQuizAttemptDetail.model_validate_json(raw_data)
                results.append(details)

        return results
