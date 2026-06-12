import uuid

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.dependencies.uow import get_uow
from app.models.user import User
from app.services.auth import AuthService
from app.utils.uow import UnitOfWork
from app.core.exceptions import IncorrectCredentialsException

from app.core.security import verify_auth0_token


async def get_auth_service(uow: UnitOfWork = Depends(get_uow)) -> AuthService:
    from app.services.user import UserService

    return AuthService(uow=uow, user_service=UserService(uow=uow))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), uow: UnitOfWork = Depends(get_uow)
) -> User:

    user_email: str | None = None
    user_id: str | None = None

    try:
        auth0_payload = verify_auth0_token(token)
        user_email = auth0_payload.get("email")
    except IncorrectCredentialsException:
        try:
            local_payload = jwt.decode(
                token, settings.jwt.SECRET_KEY, algorithms=[settings.jwt.ALGORITHM]
            )
            user_id = local_payload.get("sub")
            user_email = local_payload.get("email")
        except jwt.PyJWTError:
            raise IncorrectCredentialsException

    async with uow:
        if user_id:
            try:
                user = await uow.users.get_one(uuid.UUID(user_id))
            except ValueError:
                raise IncorrectCredentialsException
        elif user_email:
            user = await uow.users.get_user_by_email(user_email)
        else:
            raise IncorrectCredentialsException

    if user is None:
        raise IncorrectCredentialsException

    return user
