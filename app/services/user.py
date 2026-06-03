import logging
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.utils.uow import UnitOfWork
from app.schemas.user import (
    SignUpRequest,
    UserUpdateRequest,
    UserDetailResponse,
    UsersListResponse,
)
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_user_by_id(self, user_id: int) -> UserDetailResponse:
        async with self.uow:
            user = await self.uow.users.get_one(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return UserDetailResponse.model_validate(user)

    async def get_user_by_email(self, user_email: str) -> UserDetailResponse:
        async with self.uow:
            user = await self.uow.users.get_user_by_email(user_email)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return UserDetailResponse.model_validate(user)

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> UsersListResponse:
        async with self.uow:
            users, total_count = await self.uow.users.get_all(skip=skip, limit=limit)
            users_list = [UserDetailResponse.model_validate(u) for u in users]
            return UsersListResponse(users=users_list, total_count=total_count)

    async def create_new_user(self, user_data: SignUpRequest) -> UserDetailResponse:
        logger.info(f"Attempting to create new user with email: {user_data.email}")
        try:
            async with self.uow:
                existing_user = await self.uow.users.get_user_by_email(user_data.email)
                if existing_user:
                    logger.warning(
                        f"Registration failed: Email {user_data.email} is already taken."
                    )
                    raise HTTPException(
                        status_code=409, detail="Email already registered"
                    )

                hashed_password = get_password_hash(user_data.password)
                db_user_data = user_data.model_dump(exclude={"password"})
                db_user_data["hashed_password"] = hashed_password

                new_user = await self.uow.users.create(db_user_data)
                logger.info(f"Successfully created user with email: {user_data.email}")
                return UserDetailResponse.model_validate(new_user)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while creating user {user_data.email}: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error occurred during registration.",
            )

    async def update_user(
        self, user_id: int, user_data: UserUpdateRequest
    ) -> UserDetailResponse:
        logger.info(f"Attempting to update user with ID: {user_id}")
        try:
            async with self.uow:
                user = await self.uow.users.get_one(user_id)
                if not user:
                    logger.warning(f"Update failed: User with ID {user_id} not found.")
                    raise HTTPException(status_code=404, detail="User not found")

                update_dict = user_data.model_dump(exclude_unset=True)

                if "password" in update_dict:
                    update_dict["hashed_password"] = get_password_hash(
                        update_dict.pop("password")
                    )

                updated_user = await self.uow.users.update(user, update_dict)
                logger.info(
                    f"Successfully updated user ID: {user_id}. Fields modified: {list(update_dict.keys())}"
                )
                return UserDetailResponse.model_validate(updated_user)

        except SQLAlchemyError as e:
            logger.error(f"Database error while updating user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to update user due to a database error."
            )

    async def delete_user(self, user_id: int) -> None:
        logger.info(f"Attempting to delete user with ID: {user_id}")
        try:
            async with self.uow:
                user = await self.uow.users.get_one(user_id)
                if not user:
                    logger.warning(
                        f"Deletion failed: User with ID {user_id} not found."
                    )
                    raise HTTPException(status_code=404, detail="User not found")

                await self.uow.users.delete(user)
                logger.info(f"Successfully deleted user ID: {user_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to delete user due to a database error."
            )
