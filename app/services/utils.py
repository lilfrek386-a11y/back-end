import logging
from uuid import UUID
from app.models import Company
from app.models.company_member import CompanyMemberRole, CompanyMember
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    NotOwnerException,
    NotEnoughPermissionsException,
)

logger = logging.getLogger(__name__)


async def check_company_owner(
    uow: UnitOfWork, company_id: UUID, user_id: UUID
) -> Company:
    if uow.session is None:
        raise RuntimeError("Must be called within an active UoW context")

    company = await uow.companies.get_one(company_id)
    if not company:
        raise CompanyNotFoundException()

    if company.owner_id != user_id:
        logger.warning(
            f"Access denied: User {user_id} is not the owner of company {company_id}"
        )
        raise NotOwnerException()

    return company


async def add_company_member(
    uow: UnitOfWork,
    company_id: UUID,
    user_id: UUID,
    role: CompanyMemberRole = CompanyMemberRole.MEMBER,
) -> CompanyMember:
    return await uow.company_members.create(
        {
            "company_id": company_id,
            "user_id": user_id,
            "role": role,
        }
    )


async def check_company_admin_or_owner(
    uow: UnitOfWork, company_id: UUID, user_id: UUID
) -> Company:
    if uow.session is None:
        raise RuntimeError("Must be called within an active UoW context")

    company = await uow.companies.get_one(company_id)
    if not company:
        raise CompanyNotFoundException()

    if company.owner_id == user_id:
        return company

    member = await uow.company_members.get_by_company_and_user(
        company_id=company_id, user_id=user_id
    )

    if member:
        if member.role == CompanyMemberRole.ADMIN:
            return company
        else:
            logger.warning(
                f"Access denied: User {user_id} is a member but not an ADMIN in company {company_id}"
            )
            raise NotEnoughPermissionsException()
    else:
        logger.warning(
            f"Access denied: User {user_id} is not a member of company {company_id} at all"
        )
        raise NotEnoughPermissionsException()
