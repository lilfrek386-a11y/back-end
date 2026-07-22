from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.company import Company


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Company)

    async def get_company_by_name(self, name: str) -> Company | None:
        stmt = select(self.model).where(self.model.name == name)

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_name_and_owner(self, name: str, owner_id: UUID) -> Company | None:
        stmt = select(self.model).where(
            self.model.name == name, self.model.owner_id == owner_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
