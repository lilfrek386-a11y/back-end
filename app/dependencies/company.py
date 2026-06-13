from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.company import CompanyService
from app.utils.uow import UnitOfWork


def get_company_service(uow: UnitOfWork = Depends(get_uow)) -> CompanyService:
    return CompanyService(uow=uow)
