from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.company_action import CompanyActionService
from app.utils.uow import UnitOfWork


def get_action_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CompanyActionService:
    return CompanyActionService(uow)


type ActionService = Annotated[CompanyActionService, Depends(get_action_service)]
