from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, User)

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_emails_by_ids(self, ids: set[UUID]) -> dict[UUID, str]:
        stmt = select(User.id, User.email).where(User.id.in_(ids))
        result = await self.db.execute(stmt)
        return {row.id: row.email for row in result}
