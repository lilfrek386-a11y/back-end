from typing import Annotated
from uuid import UUID

from fastapi import Depends
from app.core.exceptions import (
    NotEnoughPermissionsException,
    CompanyNotFoundException,
    NotOwnerException,
)
from app.dependencies.auth import CurrentUser
from app.dependencies.company_actions import ActionService
from app.models.company_member import CompanyMemberRole


async def require_company_owner(
    company_id: UUID,
    current_user: CurrentUser,
    service: ActionService,
):
    async with service.uow:
        company = await service.uow.companies.get_one(company_id)
        if not company:
            raise CompanyNotFoundException()

        if company.owner_id != current_user.id:
            raise NotOwnerException()


async def require_company_owner_or_admin(
    company_id: UUID,
    current_user: CurrentUser,
    service: ActionService,
):
    async with service.uow:
        company = await service.uow.companies.get_one(company_id)
        if not company:
            raise CompanyNotFoundException()

        if company.owner_id == current_user.id:
            return current_user

        member = await service.uow.company_members.get_by_company_and_user(
            company_id=company_id, user_id=current_user.id
        )

        if not member or member.role not in (
            CompanyMemberRole.ADMIN,
            CompanyMemberRole.OWNER,
        ):
            raise NotEnoughPermissionsException()

        return current_user


type RequireCompanyOwnerOrAdmin = Annotated[
    None, Depends(require_company_owner_or_admin)
]
type RequireCompanyOwner = Annotated[None, Depends(require_company_owner)]
