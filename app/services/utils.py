import logging
from uuid import UUID
from app.models import Company
from app.utils.uow import UnitOfWork
from app.core.exceptions import CompanyNotFoundException, NotOwnerException

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
