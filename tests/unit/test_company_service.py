import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.company import CompanyService
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.core.exceptions import (
    CompanyNotFoundException,
    NotOwnerException,
    CompanyNameAlreadyTakenException,
)


@pytest.fixture
def company_service(mock_uow):
    mock_uow.companies.create = AsyncMock()
    mock_uow.companies.get_one = AsyncMock()
    mock_uow.companies.update = AsyncMock()
    mock_uow.companies.delete = AsyncMock()
    mock_uow.companies.get_all = AsyncMock()

    return CompanyService(mock_uow)


@pytest.mark.asyncio
async def test_create_new_company_success(company_service, mock_uow):
    user_id = uuid4()
    company_data = CompanyCreate(name="Test Corp", description="A test company")

    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=None)

    mock_db_company = MagicMock()
    mock_db_company.id = uuid4()
    mock_db_company.name = company_data.name
    mock_db_company.description = company_data.description
    mock_db_company.owner_id = user_id
    mock_db_company.is_visible = False

    mock_uow.companies.create = AsyncMock(return_value=mock_db_company)
    mock_uow.company_members.create = AsyncMock()

    result = await company_service.create_new_company(company_data, user_id)

    mock_uow.companies.create.assert_awaited_once()
    mock_uow.company_members.create.assert_awaited_once()
    assert result.name == "Test Corp"


@pytest.mark.asyncio
async def test_create_new_company_already_taken(company_service, mock_uow):
    user_id = uuid4()
    company_data = CompanyCreate(name="Test Corp", description="A test company")

    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=MagicMock())

    with pytest.raises(CompanyNameAlreadyTakenException):
        await company_service.create_new_company(company_data, user_id)


@pytest.mark.asyncio
async def test_update_company_success(company_service, mock_uow):
    user_id = uuid4()
    company_id = uuid4()
    company_data = CompanyUpdate(name="New Name")

    mock_db_company = MagicMock()
    mock_db_company.owner_id = user_id
    mock_uow.companies.get_one.return_value = mock_db_company
    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=None)

    mock_updated_company = MagicMock()
    mock_updated_company.id = company_id
    mock_updated_company.name = "New Name"
    mock_updated_company.description = "Some description"
    mock_updated_company.owner_id = user_id
    mock_updated_company.is_visible = False
    mock_uow.companies.update.return_value = mock_updated_company

    result = await company_service.update_company(company_id, company_data, user_id)

    assert result.name == "New Name"
    mock_uow.companies.update.assert_called_once_with(
        mock_db_company, company_data.model_dump(exclude_unset=True)
    )


@pytest.mark.asyncio
async def test_update_company_not_owner(company_service, mock_uow):
    user_id = uuid4()
    other_user_id = uuid4()
    company_id = uuid4()
    company_data = CompanyUpdate(name="New Name")

    mock_db_company = MagicMock()
    mock_db_company.owner_id = other_user_id
    mock_uow.companies.get_one.return_value = mock_db_company

    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=None)

    with pytest.raises(NotOwnerException):
        await company_service.update_company(company_id, company_data, user_id)


@pytest.mark.asyncio
async def test_update_company_name_already_taken(company_service, mock_uow):
    user_id = uuid4()
    company_id = uuid4()
    company_data = CompanyUpdate(name="Taken Name")

    mock_db_company = MagicMock()
    mock_db_company.id = company_id
    mock_db_company.name = "Old Name"
    mock_db_company.description = "Desc"
    mock_db_company.owner_id = user_id
    mock_db_company.is_visible = False
    mock_uow.companies.get_one.return_value = mock_db_company

    mock_existing = MagicMock()
    mock_existing.id = uuid4()
    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=mock_existing)

    mock_uow.companies.update.return_value = mock_db_company

    with pytest.raises(CompanyNameAlreadyTakenException):
        await company_service.update_company(company_id, company_data, user_id)


@pytest.mark.asyncio
async def test_update_company_same_name_allowed(company_service, mock_uow):
    user_id = uuid4()
    company_id = uuid4()
    company_data = CompanyUpdate(name="Same Name")

    mock_db_company = MagicMock()
    mock_db_company.id = company_id
    mock_db_company.name = "Same Name"
    mock_db_company.description = "Desc"
    mock_db_company.owner_id = user_id
    mock_db_company.is_visible = False
    mock_uow.companies.get_one.return_value = mock_db_company

    mock_existing = MagicMock()
    mock_existing.id = company_id
    mock_uow.companies.get_by_name_and_owner = AsyncMock(return_value=mock_existing)

    mock_uow.companies.update.return_value = mock_db_company

    result = await company_service.update_company(company_id, company_data, user_id)

    assert result.id == company_id
    mock_uow.companies.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_company_by_id_success(company_service, mock_uow):
    company_id = uuid4()

    mock_db_company = MagicMock()
    mock_db_company.id = company_id
    mock_db_company.name = "Found Corp"
    mock_db_company.description = "Desc"
    mock_db_company.owner_id = uuid4()
    mock_db_company.is_visible = False

    mock_uow.companies.get_one.return_value = mock_db_company

    result = await company_service.get_company_by_id(company_id)

    assert result.id == company_id
    assert result.name == "Found Corp"
    mock_uow.companies.get_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_company_not_found(company_service, mock_uow):
    company_id = uuid4()
    mock_uow.companies.get_one.return_value = None

    with pytest.raises(CompanyNotFoundException):
        await company_service.get_company_by_id(company_id)


@pytest.mark.asyncio
async def test_get_all_companies(company_service, mock_uow):
    mock_db_company = MagicMock()
    mock_db_company.id = uuid4()
    mock_db_company.name = "List Corp"
    mock_db_company.description = "Desc"
    mock_db_company.owner_id = uuid4()
    mock_db_company.is_visible = False

    mock_uow.companies.get_all.return_value = ([mock_db_company], 1)

    result = await company_service.get_multi_companies(skip=0, limit=100)

    mock_uow.companies.get_all.assert_called_once_with(skip=0, limit=100)
    assert result is not None


@pytest.mark.asyncio
async def test_delete_company_success(company_service, mock_uow):
    user_id = uuid4()
    company_id = uuid4()

    mock_db_company = MagicMock()
    mock_db_company.owner_id = user_id
    mock_uow.companies.get_one.return_value = mock_db_company

    await company_service.delete_company(company_id, user_id)

    mock_uow.companies.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_company_not_owner(company_service, mock_uow):
    user_id = uuid4()
    other_user_id = uuid4()
    company_id = uuid4()

    mock_db_company = MagicMock()
    mock_db_company.owner_id = other_user_id
    mock_uow.companies.get_one.return_value = mock_db_company

    with pytest.raises(NotOwnerException):
        await company_service.delete_company(company_id, user_id)

    mock_uow.companies.delete.assert_not_called()
