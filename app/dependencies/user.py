from typing import Annotated

from fastapi import Depends
from app.services.user import UserService as UserServiceClass
from app.dependencies.uow import get_uow
from app.utils.uow import UnitOfWork


async def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserServiceClass:
    return UserServiceClass(uow=uow)


type UserService = Annotated[UserServiceClass, Depends(get_user_service)]
