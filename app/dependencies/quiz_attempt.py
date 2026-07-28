from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.quiz_attempt import QuizAttemptService as QuizAttemptServiceClass
from app.utils.uow import UnitOfWork
from app.dependencies.redis import RedisService


def get_quiz_attempt_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    redis: RedisService,
) -> QuizAttemptServiceClass:
    return QuizAttemptServiceClass(uow, redis)


type QuizAttemptService = Annotated[
    QuizAttemptServiceClass, Depends(get_quiz_attempt_service)
]
