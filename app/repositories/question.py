from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.question import Question
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Question)

    async def get_texts_by_ids(self, ids: set[UUID]) -> dict[UUID, str]:
        stmt = select(Question.id, Question.title).where(Question.id.in_(ids))
        result = await self.db.execute(stmt)
        return {row.id: row.title for row in result}
