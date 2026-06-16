from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.company_member import CompanyMemberService
from app.utils.uow import UnitOfWork


def get_member_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CompanyMemberService:
    return CompanyMemberService(uow)


type MemberService = Annotated[CompanyMemberService, Depends(get_member_service)]
