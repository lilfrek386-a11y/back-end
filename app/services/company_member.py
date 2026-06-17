import logging
from uuid import UUID

from app.models.company_member import CompanyMemberRole
from app.schemas.company_member import MembersListResponse, MemberResponse
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    UserNotMemberException,
    CannotKickYourselfException,
    OwnerCannotLeaveException,
    UserNotAdminException,
    UserAlreadyAdminException,
    CannotChangeOwnerRoleException,
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

    async def appoint_admin(
        self, owner_id: UUID, company_id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            await check_company_owner(self.uow, company_id, owner_id)
            member = await self._get_member_or_raise(company_id, user_id)

            if member.role == CompanyMemberRole.OWNER:
                raise CannotChangeOwnerRoleException()
            if member.role == CompanyMemberRole.ADMIN:
                raise UserAlreadyAdminException()

            await self.uow.company_members.update(
                member, {"role": CompanyMemberRole.ADMIN}
            )

    async def remove_admin(
        self, owner_id: UUID, company_id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            await check_company_owner(self.uow, company_id, owner_id)
            member = await self._get_member_or_raise(company_id, user_id)

            if member.role != CompanyMemberRole.ADMIN:
                raise UserNotAdminException()

            await self.uow.company_members.update(
                member, {"role": CompanyMemberRole.MEMBER}
            )

    async def get_company_admins(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> MembersListResponse:
        async with self.uow:
            admins, total = await self.uow.company_members.get_by_role(
                company_id, CompanyMemberRole.ADMIN, skip, limit
            )
            return MembersListResponse(
                members=[MemberResponse.model_validate(a) for a in admins],
                total_count=total,
            )

    async def _get_member_or_raise(self, company_id: UUID, user_id: UUID):
        member = await self.uow.company_members.get_by_company_and_user(
            company_id, user_id
        )
        if not member:
            raise UserNotMemberException()
        return member
