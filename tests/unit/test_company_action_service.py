import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.services.company_action import CompanyActionService
from app.models.company_action import ActionType, CompanyAction
from app.models.company import Company
from app.models.user import User
from app.core.exceptions import (
    CannotInviteYourselfException,
    UserNotFoundException,
    NotOwnerException,
)


@pytest.fixture
def action_service(mock_uow):
    return CompanyActionService(mock_uow)


@pytest.fixture
def base_uuids():
    return {
        "owner_id": uuid4(),
        "company_id": uuid4(),
        "user_id": uuid4(),
    }


@pytest.mark.asyncio
async def test_send_invitation_success(action_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = Company(id=company_id, owner_id=owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_user = User(id=user_id)
    mock_uow.users.get_one = AsyncMock(return_value=mock_user)

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)
    mock_uow.company_actions.get_by_company_and_user = AsyncMock(return_value=None)
    mock_uow.company_actions.create = AsyncMock()

    await action_service.send_invitation(owner_id, company_id, user_id)

    mock_uow.company_actions.create.assert_awaited_once_with(
        {
            "company_id": company_id,
            "user_id": user_id,
            "action_type": ActionType.INVITATION,
        }
    )


@pytest.mark.asyncio
async def test_send_invitation_to_yourself_raises_error(action_service, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]

    with pytest.raises(CannotInviteYourselfException):
        await action_service.send_invitation(owner_id, company_id, owner_id)


@pytest.mark.asyncio
async def test_send_invitation_user_not_found(action_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = Company(id=company_id, owner_id=owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.users.get_one = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException):
        await action_service.send_invitation(owner_id, company_id, user_id)


@pytest.mark.asyncio
async def test_accept_invitation_success(action_service, mock_uow, base_uuids):
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_action = CompanyAction(
        company_id=company_id, user_id=user_id, action_type=ActionType.INVITATION
    )
    mock_uow.company_actions.get_by_company_and_user = AsyncMock(
        return_value=mock_action
    )

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    mock_uow.company_actions.delete = AsyncMock()
    mock_uow.company_members.create = AsyncMock()

    await action_service.accept_invitation(user_id, company_id)

    mock_uow.company_actions.delete.assert_awaited_once_with(mock_action)
    mock_uow.company_members.create.assert_awaited_once_with(
        {"company_id": company_id, "user_id": user_id}
    )


@pytest.mark.asyncio
async def test_not_owner_cannot_view_requests(action_service, mock_uow, base_uuids):
    not_owner_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = base_uuids["owner_id"]

    mock_company = Company(id=company_id, owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    with pytest.raises(NotOwnerException):
        await action_service.get_company_requests(not_owner_id, company_id)
