import logging
from uuid import UUID

from fastapi import UploadFile

from app.utils.uow import UnitOfWork
from app.core.exceptions import QuizNotFoundException
from app.services.utils import check_company_admin_or_owner
from app.services.quiz_import_parser import parse_quiz_excel
from app.schemas.quiz_import import QuizImportResult, ImportedQuestion

logger = logging.getLogger(__name__)


class QuizImportService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def import_quiz(
        self,
        user_id: UUID,
        company_id: UUID,
        file: UploadFile,
        title: str,
        description: str,
        quiz_id: UUID | None = None,
    ) -> QuizImportResult:
        questions_data = await parse_quiz_excel(file)

        async with self.uow:
            await check_company_admin_or_owner(self.uow, company_id, user_id)

            existing_quiz = None
            if quiz_id:
                existing_quiz = await self.uow.quizzes.get_one(quiz_id)
                if existing_quiz and existing_quiz.company_id != company_id:
                    raise QuizNotFoundException()

            if existing_quiz:
                await self.uow.quizzes.replace_questions_from_import(
                    existing_quiz, questions_data
                )
                await self.uow.quizzes.update(
                    existing_quiz, {"title": title, "description": description}
                )
                quiz_id_result = existing_quiz.id
                created = False
                logger.info(f"Updated quiz {quiz_id_result} via Excel import")
            else:
                questions_as_dicts = self._questions_to_dicts(questions_data)
                new_quiz = await self.uow.quizzes.create_quiz(
                    data={
                        "title": title,
                        "description": description,
                        "questions": questions_as_dicts,
                    },
                    company_id=company_id,
                )
                quiz_id_result = new_quiz.id
                created = True
                logger.info(f"Created new quiz {quiz_id_result} via Excel import")

        return QuizImportResult(
            quiz_id=quiz_id_result,
            created=created,
            questions_imported=len(questions_data),
        )

    @staticmethod
    def _questions_to_dicts(questions_data: list[ImportedQuestion]) -> list[dict]:
        return [
            {
                "title": q.title,
                "answer_options": [
                    {"text": opt.text, "is_correct": opt.is_correct}
                    for opt in q.answer_options
                ],
            }
            for q in questions_data
        ]
