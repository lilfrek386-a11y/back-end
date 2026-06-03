from fastapi import Depends
from app.services.user import UserService
from app.dependencies.uow import get_uow
from app.utils.uow import UnitOfWork


async def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow=uow)
