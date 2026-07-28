from typing import Annotated
from uuid import UUID
from fastapi import Depends, Form
from app.services.quiz_import import QuizImportService as QuizImportServiceClass
from app.utils.uow import UnitOfWork
from app.dependencies.uow import get_uow


class QuizImportForm:
    def __init__(
        self,
        title: str = Form(..., min_length=1, max_length=255),
        description: str = Form(..., min_length=1),
        quiz_id: UUID | None = Form(None),
    ):
        self.title = title
        self.description = description
        self.quiz_id = quiz_id


def get_quiz_import_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> QuizImportServiceClass:
    return QuizImportServiceClass(uow)


type QuizImportService = Annotated[
    QuizImportServiceClass, Depends(get_quiz_import_service)
]

type QuizImportFormData = Annotated[QuizImportForm, Depends()]
