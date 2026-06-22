from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.quiz import QuizService as QuizServiceClass
from app.utils.uow import UnitOfWork


def get_member_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> QuizServiceClass:
    return QuizServiceClass(uow)


type QuizService = Annotated[QuizServiceClass, Depends(get_member_service)]
