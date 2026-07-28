import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.user import UserService
from app.schemas.user import SignUpRequest
from app.models.user import User
from app.core.exceptions import EmailAlreadyTakenException


@pytest.mark.asyncio
async def test_create_new_user_success(mock_uow):
    user_id = uuid4()

    mock_uow.users.get_user_by_email = AsyncMock(return_value=None)

    mock_db_user = MagicMock()
    mock_db_user.id = user_id
    mock_db_user.email = "test@example.com"
    mock_db_user.name = "Good"
    mock_db_user.age = 25
    mock_uow.users.create = AsyncMock(return_value=mock_db_user)

    service = UserService(uow=mock_uow)

    result = await service.create_new_user(
        SignUpRequest(
            name="Good", email="test@example.com", password="password123", age=25
        )
    )

    assert result.email == "test@example.com"
    mock_uow.users.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_user_email_taken(mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(
        return_value=User(id=uuid4(), email="taken@example.com")
    )

    service = UserService(uow=mock_uow)

    with pytest.raises(EmailAlreadyTakenException):
        await service.create_new_user(
            SignUpRequest(
                name="Bad", email="taken@example.com", password="password123", age=25
            )
        )
