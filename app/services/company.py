import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.schemas.company import (
    CompanyUpdate,
    CompanyDetailResponse,
    CompaniesListResponse,
    CompanyCreate,
    CompanyVisibilityUpdate,
)
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    DatabaseException,
    NotOwnerException,
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
                raise CompanyNotFoundException
            return CompanyDetailResponse.model_validate(company)

    async def get_all_companies(
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
        try:
            async with self.uow:
                existing_company = await self.uow.companies.get_by_name_and_owner(
                    name=company_data.name, owner_id=user_id
                )
                if existing_company:
                    logger.warning(
                        f"User {user_id} already has a company named {company_data.name}."
                    )
                    raise CompanyNameAlreadyTakenException

                db_company_data = company_data.model_dump()
                db_company_data["owner_id"] = user_id

                new_company = await self.uow.companies.create(db_company_data)
                logger.info(f"Successfully created company: {company_data.name}")
                return CompanyDetailResponse.model_validate(new_company)

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while creating company {company_data.name}: {str(e)}"
            )
            raise DatabaseException

    async def update_company(
        self,
        company_id: UUID,
        company_data: CompanyUpdate,
        user_id: UUID,
    ) -> CompanyDetailResponse:
        logger.info(f"Attempting to update company ID: {company_id}")
        try:
            async with self.uow:
                update_dict = company_data.model_dump(exclude_unset=True)

                if "name" in update_dict:
                    existing_company = await self.uow.companies.get_by_name_and_owner(
                        name=update_dict["name"], owner_id=user_id
                    )
                    if existing_company and existing_company.id != company_id:
                        logger.warning(
                            f"Update failed: Company name '{update_dict['name']}' "
                            f"is already taken by user {user_id}"
                        )
                        raise CompanyNameAlreadyTakenException

                updated_company = await self._apply_update(
                    company_id, update_dict, user_id
                )
                logger.info(f"Successfully updated company ID: {company_id}")
                return updated_company

        except SQLAlchemyError as e:
            logger.error(f"Database error updating company {company_id}: {str(e)}")
            raise DatabaseException

    async def change_visibility(
        self,
        company_id: UUID,
        company_data: CompanyVisibilityUpdate,
        user_id: UUID,
    ) -> CompanyDetailResponse:
        logger.info(f"Attempting to change visibility for company ID: {company_id}")
        try:
            async with self.uow:
                update_dict = company_data.model_dump(exclude_unset=True)
                updated_company = await self._apply_update(
                    company_id, update_dict, user_id
                )
                logger.info(f"Visibility updated for company ID: {company_id}")
                return updated_company

        except SQLAlchemyError as e:
            logger.error(
                f"Database error changing visibility for {company_id}: {str(e)}"
            )
            raise DatabaseException

    async def delete_company(self, company_id: UUID, user_id: UUID) -> None:
        logger.info(f"Attempting to delete company ID: {company_id}")
        try:
            async with self.uow:
                company = await self._get_company_and_check_owner(company_id, user_id)
                await self.uow.companies.delete(company)
                logger.info(f"Successfully deleted company ID: {company_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting company {company_id}: {str(e)}")
            raise DatabaseException

    async def _get_company_and_check_owner(self, company_id: UUID, user_id: UUID):
        if self.uow.session is None:
            raise RuntimeError("Must be called within an active UoW context")

        company = await self.uow.companies.get_one(company_id)
        if not company:
            raise CompanyNotFoundException

        if company.owner_id != user_id:
            logger.warning(
                f"Access denied: User {user_id} is not the owner of {company_id}"
            )
            raise NotOwnerException

        return company

    async def _apply_update(
        self, company_id: UUID, update_dict: dict, user_id: UUID
    ) -> CompanyDetailResponse:
        company = await self._get_company_and_check_owner(company_id, user_id)
        updated_company = await self.uow.companies.update(company, update_dict)
        return CompanyDetailResponse.model_validate(updated_company)
