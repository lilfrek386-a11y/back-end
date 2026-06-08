from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.services.user import UserService
from app.schemas.user import (
    SignUpRequest,
    UserUpdateRequest,
    UserDetailResponse,
    UsersListResponse,
)
from app.dependencies.user import get_user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UsersListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: UserService = Depends(get_user_service),
):
    return await service.get_all_users(skip=skip, limit=limit)


@router.get("/email/{user_email}", response_model=UserDetailResponse)
async def get_user_by_email(
    user_email: str, service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    return await service.get_user_by_email(user_email)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: UUID, service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    return await service.get_user_by_id(user_id)


@router.post(
    "/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: SignUpRequest, service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    return await service.create_new_user(user)


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    return await service.update_user(user_id, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID, service: UserService = Depends(get_user_service)
) -> None:
    await service.delete_user(user_id)
