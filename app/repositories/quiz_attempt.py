from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Quiz, User, CompanyMember
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

    # Analytics: user-specific

    async def get_user_quiz_averages(
        self,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[tuple[UUID, str, float]]:

        stmt = (
            select(
                QuizAttempt.quiz_id,
                Quiz.title,
                func.coalesce(func.sum(QuizAttempt.correct_answers_count), 0).label(
                    "total_correct"
                ),
                func.coalesce(func.sum(QuizAttempt.total_questions_count), 0).label(
                    "total_questions"
                ),
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(QuizAttempt.user_id == user_id)
            .group_by(QuizAttempt.quiz_id, Quiz.title)
        )

        if date_from is not None:
            stmt = stmt.where(QuizAttempt.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(QuizAttempt.created_at <= date_to)

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            (
                row.quiz_id,
                row.title,
                (
                    round(row.total_correct / row.total_questions, 2)
                    if row.total_questions
                    else 0.0
                ),
            )
            for row in rows
        ]

    async def get_user_last_attempts(
        self, user_id: UUID
    ) -> list[tuple[UUID, str, datetime]]:

        stmt = (
            select(
                QuizAttempt.quiz_id,
                Quiz.title,
                func.max(QuizAttempt.created_at).label("last_attempt_at"),
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(QuizAttempt.user_id == user_id)
            .group_by(QuizAttempt.quiz_id, Quiz.title)
        )

        result = await self.db.execute(stmt)
        return [(row.quiz_id, row.title, row.last_attempt_at) for row in result]

    # Analytics: company-specific

    async def get_company_members_weekly_scores(
        self, company_id: UUID
    ) -> list[tuple[UUID, str, datetime, float]]:

        week_start = func.date_trunc("week", QuizAttempt.created_at).label("week_start")

        stmt = (
            select(
                QuizAttempt.user_id,
                User.email,
                week_start,
                func.coalesce(func.sum(QuizAttempt.correct_answers_count), 0).label(
                    "total_correct"
                ),
                func.coalesce(func.sum(QuizAttempt.total_questions_count), 0).label(
                    "total_questions"
                ),
            )
            .join(User, User.id == QuizAttempt.user_id)
            .where(QuizAttempt.company_id == company_id)
            .group_by(QuizAttempt.user_id, User.email, week_start)
            .order_by(QuizAttempt.user_id, week_start)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            (
                row.user_id,
                row.email,
                row.week_start,
                (
                    round(row.total_correct / row.total_questions, 2)
                    if row.total_questions
                    else 0.0
                ),
            )
            for row in rows
        ]

    async def get_user_quiz_weekly_scores(
        self, company_id: UUID, user_id: UUID
    ) -> list[tuple[UUID, str, datetime, float]]:

        week_start = func.date_trunc("week", QuizAttempt.created_at).label("week_start")

        stmt = (
            select(
                QuizAttempt.quiz_id,
                Quiz.title,
                week_start,
                func.coalesce(func.sum(QuizAttempt.correct_answers_count), 0).label(
                    "total_correct"
                ),
                func.coalesce(func.sum(QuizAttempt.total_questions_count), 0).label(
                    "total_questions"
                ),
            )
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .where(
                QuizAttempt.company_id == company_id,
                QuizAttempt.user_id == user_id,
            )
            .group_by(QuizAttempt.quiz_id, Quiz.title, week_start)
            .order_by(QuizAttempt.quiz_id, week_start)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            (
                row.quiz_id,
                row.title,
                row.week_start,
                (
                    round(row.total_correct / row.total_questions, 2)
                    if row.total_questions
                    else 0.0
                ),
            )
            for row in rows
        ]

    async def get_company_last_attempts(
        self, company_id: UUID
    ) -> list[tuple[UUID, str, datetime | None]]:

        stmt = (
            select(
                CompanyMember.user_id,
                User.email,
                func.max(QuizAttempt.created_at).label("last_attempt_at"),
            )
            .join(User, User.id == CompanyMember.user_id)
            .outerjoin(
                QuizAttempt,
                (QuizAttempt.user_id == CompanyMember.user_id)
                & (QuizAttempt.company_id == CompanyMember.company_id),
            )
            .where(CompanyMember.company_id == company_id)
            .group_by(CompanyMember.user_id, User.email)
        )

        result = await self.db.execute(stmt)
        return [(row.user_id, row.email, row.last_attempt_at) for row in result]
