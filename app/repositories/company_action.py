from uuid import UUID
from collections.abc import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_action import CompanyAction, ActionType
from app.repositories.base import BaseRepository


class CompanyActionRepository(BaseRepository[CompanyAction]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, CompanyAction)

    async def get_by_company_and_user(
        self, company_id: UUID, user_id: UUID, action_type: ActionType
    ) -> CompanyAction | None:
        stmt = select(CompanyAction).where(
            CompanyAction.company_id == company_id,
            CompanyAction.user_id == user_id,
            CompanyAction.action_type == action_type,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_invitations(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[CompanyAction], int]:
        return await self._get_filtered(
            skip,
            limit,
            CompanyAction.user_id == user_id,
            CompanyAction.action_type == ActionType.INVITATION,
        )

    async def get_user_requests(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[CompanyAction], int]:
        return await self._get_filtered(
            skip,
            limit,
            CompanyAction.user_id == user_id,
            CompanyAction.action_type == ActionType.REQUEST,
        )

    async def get_company_invitations(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[CompanyAction], int]:
        return await self._get_filtered(
            skip,
            limit,
            CompanyAction.company_id == company_id,
            CompanyAction.action_type == ActionType.INVITATION,
        )

    async def get_company_requests(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[CompanyAction], int]:
        return await self._get_filtered(
            skip,
            limit,
            CompanyAction.company_id == company_id,
            CompanyAction.action_type == ActionType.REQUEST,
        )

    async def _get_filtered(
        self, skip: int, limit: int, *filters
    ) -> tuple[Sequence[CompanyAction], int]:
        count_stmt = select(func.count()).select_from(CompanyAction).where(*filters)
        total = await self.db.scalar(count_stmt)

        stmt = select(CompanyAction).where(*filters).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total or 0
