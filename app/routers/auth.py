from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.dependencies.auth import get_auth_service, get_current_user
from app.schemas.auth import TokenResponse, Auth0TokenRequest
from app.schemas.user import SignInRequest, UserDetailResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    user_credentials = SignInRequest(
        email=form_data.username,
        password=form_data.password,
    )

    return await service.login(user_credentials)


@router.get("/me", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def get_me(user=Depends(get_current_user)) -> UserDetailResponse:
    return user


@router.post(
    "/auth0-login", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def login_via_auth0(
    token_data: Auth0TokenRequest, service: AuthService = Depends(get_auth_service)
):
    return await service.login_via_auth0(token_data)
