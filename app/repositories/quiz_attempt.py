from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.quiz_attempt import QuizAttempt


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, QuizAttempt)

    async def get_average_score(
        self, user_id: UUID, company_id: UUID | None = None
    ) -> float:
        stmt = select(
            func.coalesce(func.sum(QuizAttempt.correct_answers_count), 0).label(
                "total_correct"
            ),
            func.coalesce(func.sum(QuizAttempt.total_questions_count), 0).label(
                "total_questions"
            ),
        ).where(QuizAttempt.user_id == user_id)

        if company_id:
            stmt = stmt.where(QuizAttempt.company_id == company_id)

        result = await self.db.execute(stmt)
        row = result.first()

        if row is None or row.total_questions == 0:
            return 0.0

        return round(row.total_correct / row.total_questions, 2)

    async def get_attempt_ids_for_export(
        self,
        user_id: UUID | None = None,
        company_id: UUID | None = None,
        quiz_id: UUID | None = None,
    ) -> list[UUID]:
        if not any([user_id, company_id, quiz_id]):
            raise ValueError("At least one filter must be provided")

        stmt = select(self.model.id)
        if user_id:
            stmt = stmt.where(self.model.user_id == user_id)
        if company_id:
            stmt = stmt.where(self.model.company_id == company_id)
        if quiz_id:
            stmt = stmt.where(self.model.quiz_id == quiz_id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
