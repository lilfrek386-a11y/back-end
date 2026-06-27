from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.answer_option import AnswerOption
from app.repositories.base import BaseRepository


class AnswerOptionRepository(BaseRepository[AnswerOption]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AnswerOption)

    async def get_texts_by_ids(self, ids: set[UUID]) -> dict[UUID, str]:
        stmt = select(AnswerOption.id, AnswerOption.text).where(
            AnswerOption.id.in_(ids)
        )
        result = await self.db.execute(stmt)
        return {row.id: row.text for row in result}
