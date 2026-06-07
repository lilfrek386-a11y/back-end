import logging
from fastapi import HTTPException, status

from app.services.user import UserService
from app.utils.uow import UnitOfWork
from app.schemas.user import SignInRequest
from app.schemas.auth import TokenResponse, Auth0TokenRequest
from app.core.security import verify_password, create_access_token, verify_auth0_token

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, uow: UnitOfWork, user_service: UserService):
        self.uow = uow
        self.user_service = user_service

    async def login(self, user: SignInRequest) -> TokenResponse:
        async with self.uow as uow:
            db_user = await uow.users.get_user_by_email(user.email)

            invalid_creds_exc = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

            if db_user is None:
                raise invalid_creds_exc

            if not db_user.hashed_password:
                raise invalid_creds_exc

            is_valid = verify_password(user.password, db_user.hashed_password)
            if not is_valid:
                raise invalid_creds_exc

        token = create_access_token({"sub": str(db_user.id), "email": db_user.email})

        return TokenResponse(access_token=token)

    async def login_via_auth0(self, token_data: Auth0TokenRequest) -> TokenResponse:
        payload = verify_auth0_token(token_data.access_token)
        user_email = payload.get("email")

        async with self.uow as uow:
            user = await uow.users.get_user_by_email(user_email)

        if not user:
            user = await self.user_service.create_by_email(user_email)

        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        return TokenResponse(access_token=access_token)
