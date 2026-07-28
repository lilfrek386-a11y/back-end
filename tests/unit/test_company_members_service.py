from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.company_member import CompanyMemberService
from app.models.company_member import CompanyMember, CompanyMemberRole
from app.core.exceptions import (
    NotOwnerException,
    UserNotMemberException,
    UserAlreadyAdminException,
    UserNotAdminException,
    CannotChangeOwnerRoleException,
)


@pytest.fixture
def member_service(mock_uow):
    return CompanyMemberService(mock_uow)


@pytest.fixture
def base_uuids():
    return {
        "owner_id": uuid4(),
        "company_id": uuid4(),
        "user_id": uuid4(),
    }


@pytest.mark.asyncio
async def test_appoint_admin_success(member_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.MEMBER
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )
    mock_uow.company_members.update = AsyncMock()

    await member_service.appoint_admin(owner_id, company_id, user_id)

    mock_uow.company_members.update.assert_awaited_once_with(
        mock_member, {"role": CompanyMemberRole.ADMIN}
    )


@pytest.mark.asyncio
async def test_appoint_admin_not_owner_raises(member_service, mock_uow, base_uuids):
    not_owner_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = base_uuids["owner_id"]
    target_user_id = uuid4()

    mock_company = MagicMock()
    mock_company.owner_id = real_owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    with pytest.raises(NotOwnerException):
        await member_service.appoint_admin(not_owner_id, company_id, target_user_id)


@pytest.mark.asyncio
async def test_appoint_admin_user_not_member_raises(
    member_service, mock_uow, base_uuids
):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    with pytest.raises(UserNotMemberException):
        await member_service.appoint_admin(owner_id, company_id, user_id)


@pytest.mark.asyncio
async def test_appoint_admin_already_admin_raises(member_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.ADMIN
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )

    with pytest.raises(UserAlreadyAdminException):
        await member_service.appoint_admin(owner_id, company_id, user_id)


@pytest.mark.asyncio
async def test_appoint_admin_on_owner_raises(member_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=owner_id, role=CompanyMemberRole.OWNER
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )

    with pytest.raises(CannotChangeOwnerRoleException):
        await member_service.appoint_admin(owner_id, company_id, owner_id)


@pytest.mark.asyncio
async def test_remove_admin_success(member_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.ADMIN
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )
    mock_uow.company_members.update = AsyncMock()

    await member_service.remove_admin(owner_id, company_id, user_id)

    mock_uow.company_members.update.assert_awaited_once_with(
        mock_member, {"role": CompanyMemberRole.MEMBER}
    )


@pytest.mark.asyncio
async def test_remove_admin_not_admin_raises(member_service, mock_uow, base_uuids):
    owner_id = base_uuids["owner_id"]
    company_id = base_uuids["company_id"]
    user_id = base_uuids["user_id"]

    mock_company = MagicMock()
    mock_company.owner_id = owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.MEMBER
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )

    with pytest.raises(UserNotAdminException):
        await member_service.remove_admin(owner_id, company_id, user_id)


@pytest.mark.asyncio
async def test_remove_admin_not_owner_raises(member_service, mock_uow, base_uuids):
    not_owner_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = base_uuids["owner_id"]
    target_user_id = uuid4()

    mock_company = MagicMock()
    mock_company.owner_id = real_owner_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    with pytest.raises(NotOwnerException):
        await member_service.remove_admin(not_owner_id, company_id, target_user_id)


@pytest.mark.asyncio
async def test_get_company_admins_returns_only_admins(
    member_service, mock_uow, base_uuids
):
    company_id = base_uuids["company_id"]

    mock_company = MagicMock()
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_admin = CompanyMember(
        company_id=company_id,
        user_id=uuid4(),
        role=CompanyMemberRole.ADMIN,
        created_at=datetime.now(timezone.utc),
    )
    mock_uow.company_members.get_by_role = AsyncMock(return_value=([mock_admin], 1))

    result = await member_service.get_company_admins(company_id, skip=0, limit=100)

    mock_uow.company_members.get_by_role.assert_awaited_once_with(
        company_id, CompanyMemberRole.ADMIN, 0, 100
    )
    assert result.total_count == 1
    assert len(result.members) == 1


@pytest.mark.asyncio
async def test_get_company_admins_empty(member_service, mock_uow, base_uuids):
    company_id = base_uuids["company_id"]

    mock_company = MagicMock()
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.company_members.get_by_role = AsyncMock(return_value=([], 0))

    result = await member_service.get_company_admins(company_id)

    assert result.total_count == 0
    assert result.members == []
