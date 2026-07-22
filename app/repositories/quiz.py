from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.answer_option import AnswerOption
from app.models.question import Question
from app.models.quiz import Quiz
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Quiz)

    async def get_quiz_with_details(self, quiz_id: UUID) -> Quiz | None:
        stmt = (
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions).selectinload(Question.answer_options))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_company(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[Quiz], int]:

        count_stmt = (
            select(func.count()).select_from(Quiz).where(Quiz.company_id == company_id)
        )
        total_count = await self.db.scalar(count_stmt)

        stmt = (
            select(Quiz).where(Quiz.company_id == company_id).offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total_count or 0

    async def create_quiz(self, data: dict, company_id: UUID) -> Quiz:
        questions_data = data.pop("questions", [])

        db_quiz = Quiz(**data, company_id=company_id)
        db_questions = []

        for q_dict in questions_data:
            options_data = q_dict.pop("answer_options", [])

            db_options = [AnswerOption(**opt_dict) for opt_dict in options_data]
            db_question = Question(**q_dict, answer_options=db_options)

            db_questions.append(db_question)

        db_quiz.questions = db_questions

        self.db.add(db_quiz)
        await self.db.flush()

        return await self.get_quiz_with_details(db_quiz.id)

    async def get_titles_by_ids(self, ids: set[UUID]) -> dict[UUID, str]:
        stmt = select(Quiz.id, Quiz.title).where(Quiz.id.in_(ids))
        result = await self.db.execute(stmt)
        return {row.id: row.title for row in result}
