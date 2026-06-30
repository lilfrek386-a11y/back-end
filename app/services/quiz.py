import logging
from uuid import UUID

from fastapi import BackgroundTasks

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
    QuizzesResponseList,
    QuizListResponse,
)
from app.services.notification import send_quiz_notifications_bg
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    QuizNotFoundException,
)
from app.services.utils import check_company_admin_or_owner
from app.models.quiz import Quiz

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_quiz(
        self,
        user_id: UUID,
        company_id: UUID,
        quiz_data: QuizCreate,
        background_tasks: BackgroundTasks | None = None,
    ) -> QuizResponse:
        logger.info(
            f"Attempting to create new quiz: {quiz_data.title} in company {company_id}"
        )
        async with self.uow:
            await check_company_admin_or_owner(self.uow, company_id, user_id)

            db_quiz_data = quiz_data.model_dump()
            new_quiz = await self.uow.quizzes.create_quiz(
                data=db_quiz_data, company_id=company_id
            )

            if background_tasks is not None:
                background_tasks.add_task(
                    send_quiz_notifications_bg,
                    company_id=company_id,
                    quiz_title=new_quiz.title,
                    creator_id=user_id,
                )

            logger.info(f"Successfully created quiz: {quiz_data.title}")
            return QuizResponse.model_validate(new_quiz)

    async def get_quiz_by_id(self, quiz_id: UUID) -> QuizResponse:
        async with self.uow:
            quiz = await self.uow.quizzes.get_quiz_with_details(quiz_id)
            if not quiz:
                raise QuizNotFoundException()
            return QuizResponse.model_validate(quiz)

    async def get_all_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> QuizzesResponseList:
        async with self.uow:
            company = await self.uow.companies.get_one(company_id)
            if not company:
                raise CompanyNotFoundException()

            quizzes, total_count = await self.uow.quizzes.get_all_by_company(
                company_id, skip, limit
            )
            quizzes_list = [QuizListResponse.model_validate(q) for q in quizzes]

            return QuizzesResponseList(quizzes=quizzes_list, total_count=total_count)

    async def update_quiz(
        self, user_id: UUID, quiz_id: UUID, quiz_data: QuizUpdate
    ) -> QuizResponse:
        logger.info(f"Attempting to update quiz ID: {quiz_id}")
        async with self.uow:
            quiz = await self._get_quiz_and_check_permissions(quiz_id, user_id)

            update_dict = quiz_data.model_dump(exclude_unset=True)
            await self.uow.quizzes.update(quiz, update_dict)

            updated_quiz = await self.uow.quizzes.get_quiz_with_details(quiz.id)

            logger.info(f"Successfully updated quiz ID: {quiz_id}")

            return QuizResponse.model_validate(updated_quiz)

    async def delete_quiz(self, user_id: UUID, quiz_id: UUID) -> None:
        logger.info(f"Attempting to delete quiz ID: {quiz_id}")
        async with self.uow:
            quiz = await self._get_quiz_and_check_permissions(quiz_id, user_id)
            await self.uow.quizzes.delete(quiz)
            logger.info(f"Successfully deleted quiz ID: {quiz_id}")

    async def _get_quiz_and_check_permissions(
        self, quiz_id: UUID, user_id: UUID
    ) -> Quiz:
        if self.uow.session is None:
            raise RuntimeError("Must be called within an active UoW context")

        quiz = await self.uow.quizzes.get_one(quiz_id)
        if not quiz:
            raise QuizNotFoundException()

        await check_company_admin_or_owner(self.uow, quiz.company_id, user_id)

        return quiz
