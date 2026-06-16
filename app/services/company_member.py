import logging
from uuid import UUID

from app.schemas.company_member import MembersListResponse, MemberResponse
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    UserNotMemberException,
    CannotKickYourselfException,
    OwnerCannotLeaveException,
)
from app.services.utils import check_company_owner

logger = logging.getLogger(__name__)


class CompanyMemberService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def kick_user(self, owner_id: UUID, company_id: UUID, user_id: UUID) -> None:
        if owner_id == user_id:
            raise CannotKickYourselfException()

        async with self.uow:
            await check_company_owner(self.uow, company_id, owner_id)

            member = await self.uow.company_members.get_by_company_and_user(
                company_id, user_id
            )
            if not member:
                raise UserNotMemberException()

            await self.uow.company_members.delete(member)

    async def leave_company(self, user_id: UUID, company_id: UUID) -> None:
        async with self.uow:
            company = await self.uow.companies.get_one(company_id)
            if not company:
                raise CompanyNotFoundException()

            if company.owner_id == user_id:
                raise OwnerCannotLeaveException()

            member = await self.uow.company_members.get_by_company_and_user(
                company_id, user_id
            )
            if not member:
                raise UserNotMemberException()

            await self.uow.company_members.delete(member)

    async def get_company_members(
        self, company_id: UUID, skip: int, limit: int
    ) -> MembersListResponse:
        async with self.uow:
            company = await self.uow.companies.get_one(company_id)
            if not company:
                raise CompanyNotFoundException()

            members, total_count = await self.uow.company_members.get_company_members(
                company_id, skip, limit
            )

            members_list = [MemberResponse.model_validate(m) for m in members]

            return MembersListResponse(members=members_list, total_count=total_count)
