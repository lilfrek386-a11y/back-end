from fastapi import APIRouter, Depends
from starlette import status

from app.dependencies.auth import get_auth_service, get_current_user
from app.schemas.auth import TokenResponse, SignInRequest
from app.schemas.user import UserDetailResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get(
    "/me",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(user=Depends(get_current_user)) -> UserDetailResponse:
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
)
async def login(
    user: SignInRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(user)
