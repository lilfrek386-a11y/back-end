from typing import Annotated
from fastapi import Depends
from app.services.redis import RedisService as RedisServiceClass
from app.core.redis import RedisDep


def get_redis_service(
    redis: RedisDep,
) -> RedisServiceClass:
    return RedisServiceClass(redis)


type RedisService = Annotated[RedisServiceClass, Depends(get_redis_service)]
