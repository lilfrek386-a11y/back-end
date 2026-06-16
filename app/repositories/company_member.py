from uuid import UUID
from collections.abc import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_member import CompanyMember
from app.repositories.base import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMember]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, CompanyMember)

    async def get_by_company_and_user(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMember | None:
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_company_members(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[CompanyMember], int]:
        count_stmt = (
            select(func.count())
            .select_from(CompanyMember)
            .where(CompanyMember.company_id == company_id)
        )
        total = await self.db.scalar(count_stmt)

        stmt = (
            select(CompanyMember)
            .where(CompanyMember.company_id == company_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total or 0
