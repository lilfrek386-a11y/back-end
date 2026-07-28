from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUser
from app.schemas.user import (
    SignUpRequest,
    UserUpdateRequest,
    UserDetailResponse,
    UsersListResponse,
    UserUpdateMeRequest,
)
from app.dependencies.user import UserService
from app.dependencies.pagination import SkipQuery, LimitQuery

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=UsersListResponse,
    summary="Get multiple users",
)
async def get_multi_users(
    service: UserService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_multi_users(skip=skip, limit=limit)


@router.get(
    "/email/{user_email}",
    response_model=UserDetailResponse,
    summary="Get user by email",
)
async def get_user_by_email(
    user_email: str, service: UserService
) -> UserDetailResponse:
    return await service.get_user_by_email(user_email)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user by ID",
)
async def get_user_by_id(user_id: UUID, service: UserService) -> UserDetailResponse:
    return await service.get_user_by_id(user_id)


@router.post(
    "/",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(user: SignUpRequest, service: UserService) -> UserDetailResponse:
    return await service.create_new_user(user)


@router.patch(
    "/me",
    response_model=UserDetailResponse,
    summary="Update current user",
)
async def update_me(
    user_data: UserUpdateMeRequest,
    current_user: CurrentUser,
    service: UserService,
) -> UserDetailResponse:
    return await service.update_user(current_user.id, user_data)


@router.patch(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Update user by ID",
)
async def update_user(
    user_id: UUID,
    user: UserUpdateRequest,
    service: UserService,
) -> UserDetailResponse:
    return await service.update_user(user_id, user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user",
)
async def delete_me(
    current_user: CurrentUser,
    service: UserService,
) -> None:
    await service.delete_user(current_user.id)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID",
)
async def delete_user(user_id: UUID, service: UserService) -> None:
    # TODO: restrict to admin only
    await service.delete_user(user_id)
