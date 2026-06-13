import logging

from app.schemas.user import UserDetailResponse
from app.services.user import UserService
from app.utils.uow import UnitOfWork
from app.schemas.auth import TokenResponse, SignInRequest
from app.core.security import (
    verify_password,
    create_access_token,
    verify_auth0_token,
    create_refresh_token,
)
from app.core.exceptions import (
    IncorrectCredentialsException,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, uow: UnitOfWork, user_service: UserService):
        self.uow = uow
        self.user_service = user_service

    async def login(self, data: SignInRequest) -> TokenResponse:
        if data.auth0_token:
            logger.info("Initiating login flow via Auth0")
            return await self._login_via_auth0(data.auth0_token)

        if data.email and data.password:
            logger.info(
                f"Initiating login flow with credentials for email: {data.email}"
            )
            return await self._login_with_credentials(data.email, data.password)

        logger.warning(
            "Login attempt failed: No valid credentials or Auth0 token provided"
        )
        raise IncorrectCredentialsException()

    async def _login_with_credentials(self, email: str, password: str) -> TokenResponse:
        async with self.uow as uow:
            db_user = await uow.users.get_user_by_email(email)

        if not db_user or not db_user.hashed_password:
            logger.warning(
                f"Login failed: User with email {email} not found or lacks a password"
            )
            raise IncorrectCredentialsException

        if not verify_password(password, db_user.hashed_password):
            logger.warning(
                f"Login failed: Incorrect password provided for email {email}"
            )
            raise IncorrectCredentialsException

        logger.info(f"Successfully logged in user: {db_user.id} via credentials")

        user = UserDetailResponse.model_validate(db_user)
        return self._create_token_response(user)

    async def _login_via_auth0(self, auth0_token: str) -> TokenResponse:
        payload = verify_auth0_token(auth0_token)
        user_email = payload.get("email")

        if not user_email:
            logger.error("Auth0 token is valid, but missing 'email' claim")
            raise IncorrectCredentialsException

        async with self.uow as uow:
            db_user = await uow.users.get_user_by_email(user_email)

        if db_user:
            user = UserDetailResponse.model_validate(db_user)
        else:
            user = await self.user_service.create_by_email(user_email)

        return self._create_token_response(user)

    def _create_token_response(self, user: UserDetailResponse) -> TokenResponse:
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
