import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from uuid import uuid4

from app.services.user import UserService
from app.schemas.user import SignUpRequest
from app.models.user import User


@pytest.mark.asyncio
async def test_create_new_user_success():
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    mock_uow.users.get_user_by_email = AsyncMock(return_value=None)

    fake_id = uuid4()
    fake_db_user = User(
        id=fake_id,
        name="Test",
        email="test@example.com",
        age=20,
        hashed_password="hashed",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    mock_uow.users.create = AsyncMock(return_value=fake_db_user)

    service = UserService(uow=mock_uow)
    request_data = SignUpRequest(
        name="Test", email="test@example.com", password="password123", age=20
    )

    result = await service.create_new_user(request_data)

    assert result.email == "test@example.com"
    assert result.id == fake_id
    mock_uow.users.get_user_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_create_new_user_email_taken():
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    mock_uow.users.get_user_by_email = AsyncMock(
        return_value=User(id=uuid4(), email="taken@example.com")
    )

    service = UserService(uow=mock_uow)
    request_data = SignUpRequest(
        name="Bad", email="taken@example.com", password="password123", age=25
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_new_user(request_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Email already registered"
