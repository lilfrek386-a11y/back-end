import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., max_length=50)
    age: int | None = Field(default=None, ge=0, le=120)


class UserSchema(UserBase):
    pass


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(UserBase):
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=0, le=120)
    password: str | None = Field(default=None, min_length=8)


class UserDetailResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UsersListResponse(BaseModel):
    users: list[UserDetailResponse]
    total_count: int


class UserUpdateMeRequest(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    password: str | None = Field(default=None, min_length=8)
