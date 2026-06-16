from fastapi import APIRouter, Depends
from starlette import status

from app.dependencies.auth import CurrentUser
from app.schemas.auth import TokenResponse, SignInRequest
from app.schemas.user import UserDetailResponse
from app.dependencies.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/me",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(user: CurrentUser) -> UserDetailResponse:
    return UserDetailResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
)
async def login(
    user: SignInRequest,
    service: AuthService,
):
    return await service.login(user)
