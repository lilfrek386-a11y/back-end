from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.quiz_attempt import QuizAttemptService as QuizAttemptServiceClass
from app.utils.uow import UnitOfWork


def get_quiz_attempt_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> QuizAttemptServiceClass:
    return QuizAttemptServiceClass(uow)


type QuizAttemptService = Annotated[
    QuizAttemptServiceClass, Depends(get_quiz_attempt_service)
]
