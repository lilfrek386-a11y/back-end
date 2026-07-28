from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CompanyBase(BaseModel):
    name: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=300)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=300)


class CompanyVisibilityUpdate(BaseModel):
    is_visible: bool


class CompanyDetailResponse(CompanyBase):
    id: UUID
    owner_id: UUID
    is_visible: bool

    model_config = ConfigDict(from_attributes=True)


class CompaniesListResponse(BaseModel):
    companies: list[CompanyDetailResponse]
    total_count: int
