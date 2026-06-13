from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyVisibilityUpdate,
    CompanyDetailResponse,
    CompaniesListResponse,
)
from app.models.user import User
from app.services.company import CompanyService
from app.dependencies.auth import get_current_user

from app.dependencies.company import get_company_service

router = APIRouter(prefix="/companies", tags=["Companies"])

CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentCompanyService = Annotated[CompanyService, Depends(get_company_service)]


@router.post(
    "/",
    response_model=CompanyDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company",
)
async def create_company(
    data: CompanyCreate,
    user: CurrentUser,
    service: CurrentCompanyService,
):
    return await service.create_new_company(data, user.id)


@router.get(
    "/",
    response_model=CompaniesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all companies",
)
async def get_companies(
    service: CurrentCompanyService,
    skip: int = 0,
    limit: int = 100,
):
    return await service.get_all_companies(skip=skip, limit=limit)


@router.get(
    "/{company_id}",
    response_model=CompanyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get company details by ID",
)
async def get_company(
    company_id: UUID,
    service: CurrentCompanyService,
):
    return await service.get_company_by_id(company_id)


@router.patch(
    "/{company_id}",
    response_model=CompanyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update company details",
)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    user: CurrentUser,
    service: CurrentCompanyService,
):
    return await service.update_company(company_id, data, user.id)


@router.patch(
    "/{company_id}/visibility",
    response_model=CompanyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Change company visibility",
)
async def change_company_visibility(
    company_id: UUID,
    data: CompanyVisibilityUpdate,
    user: CurrentUser,
    service: CurrentCompanyService,
):
    return await service.change_visibility(company_id, data, user.id)


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a company",
)
async def delete_company(
    company_id: UUID,
    user: CurrentUser,
    service: CurrentCompanyService,
):
    await service.delete_company(company_id, user.id)
