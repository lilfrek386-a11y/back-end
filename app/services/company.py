import logging
from uuid import UUID

from app.schemas.company import (
    CompanyUpdate,
    CompanyDetailResponse,
    CompaniesListResponse,
    CompanyCreate,
    CompanyVisibilityUpdate,
)
from app.services.utils import check_company_owner
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    CompanyNameAlreadyTakenException,
)

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_company_by_id(self, company_id: UUID) -> CompanyDetailResponse:
        async with self.uow:
            company = await self.uow.companies.get_one(company_id)
            if not company:
                raise CompanyNotFoundException()
            return CompanyDetailResponse.model_validate(company)

    async def get_multi_companies(
        self, skip: int = 0, limit: int = 100
    ) -> CompaniesListResponse:
        async with self.uow:
            companies, total_count = await self.uow.companies.get_all(
                skip=skip, limit=limit
            )
            companies_list = [
                CompanyDetailResponse.model_validate(c) for c in companies
            ]
            return CompaniesListResponse(
                companies=companies_list, total_count=total_count
            )

    async def create_new_company(
        self, company_data: CompanyCreate, user_id: UUID
    ) -> CompanyDetailResponse:
        logger.info(f"Attempting to create new company: {company_data.name}")
        async with self.uow:
            await self._check_name_is_unique(company_data.name, user_id)

            db_company_data = company_data.model_dump()
            db_company_data["owner_id"] = user_id

            new_company = await self.uow.companies.create(db_company_data)
            await self.uow.company_members.create(
                {"company_id": new_company.id, "user_id": user_id}
            )

            logger.info(f"Successfully created company: {company_data.name}")
            return CompanyDetailResponse.model_validate(new_company)

    async def update_company(
        self,
        company_id: UUID,
        company_data: CompanyUpdate,
        user_id: UUID,
    ) -> CompanyDetailResponse:
        logger.info(f"Attempting to update company ID: {company_id}")
        async with self.uow:
            update_dict = company_data.model_dump(exclude_unset=True)

            if "name" in update_dict:
                await self._check_name_is_unique(
                    update_dict["name"], user_id, exclude_id=company_id
                )

            updated_company = await self._apply_update(company_id, update_dict, user_id)
            logger.info(f"Successfully updated company ID: {company_id}")
            return updated_company

    async def change_visibility(
        self,
        company_id: UUID,
        company_data: CompanyVisibilityUpdate,
        user_id: UUID,
    ) -> CompanyDetailResponse:
        logger.info(f"Attempting to change visibility for company ID: {company_id}")
        async with self.uow:
            update_dict = company_data.model_dump(exclude_unset=True)
            updated_company = await self._apply_update(company_id, update_dict, user_id)
            logger.info(f"Visibility updated for company ID: {company_id}")
            return updated_company

    async def delete_company(self, company_id: UUID, user_id: UUID) -> None:
        logger.info(f"Attempting to delete company ID: {company_id}")
        async with self.uow:
            company = await check_company_owner(self.uow, company_id, user_id)
            await self.uow.companies.delete(company)
            logger.info(f"Successfully deleted company ID: {company_id}")

    async def _check_name_is_unique(
        self, name: str, owner_id: UUID, exclude_id: UUID | None = None
    ) -> None:
        existing_company = await self.uow.companies.get_by_name_and_owner(
            name=name, owner_id=owner_id
        )
        if existing_company and existing_company.id != exclude_id:
            logger.warning(f"User {owner_id} already has a company named {name}.")
            raise CompanyNameAlreadyTakenException()

    async def _apply_update(
        self, company_id: UUID, update_dict: dict, user_id: UUID
    ) -> CompanyDetailResponse:
        company = await check_company_owner(self.uow, company_id, user_id)
        updated_company = await self.uow.companies.update(company, update_dict)
        return CompanyDetailResponse.model_validate(updated_company)
