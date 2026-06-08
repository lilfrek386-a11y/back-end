import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from fastapi import HTTPException
from uuid import uuid4

from app.services.user import UserService
from app.schemas.user import SignUpRequest
from app.models.user import User


@pytest.mark.asyncio
async def test_create_new_user_success(mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(return_value=None)

    fake_id = uuid4()
    mock_uow.users.create = AsyncMock(
        return_value=User(
            id=fake_id,
            name="Test",
            email="test@example.com",
            age=20,
            hashed_password="hashed",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )

    service = UserService(uow=mock_uow)
    result = await service.create_new_user(
        SignUpRequest(
            name="Test", email="test@example.com", password="password123", age=20
        )
    )

    assert result.email == "test@example.com"
    assert result.id == fake_id
    mock_uow.users.get_user_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_create_new_user_email_taken(mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(
        return_value=User(id=uuid4(), email="taken@example.com")
    )

    service = UserService(uow=mock_uow)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_new_user(
            SignUpRequest(
                name="Bad", email="taken@example.com", password="password123", age=25
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Email already registered"
