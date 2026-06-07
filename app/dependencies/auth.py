import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.dependencies.uow import get_uow
from app.schemas.user import UserDetailResponse
from app.services.auth import AuthService
from app.utils.uow import UnitOfWork


async def get_auth_service(uow: UnitOfWork = Depends(get_uow)) -> AuthService:
    from app.services.user import UserService

    return AuthService(uow=uow, user_service=UserService(uow=uow))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), uow: UnitOfWork = Depends(get_uow)
) -> UserDetailResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.jwt.SECRET_KEY, algorithms=[settings.jwt.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    async with uow as ouw:
        user = await ouw.users.get_one(uuid.UUID(user_id))

    if user is None:
        raise credentials_exception

    return user
