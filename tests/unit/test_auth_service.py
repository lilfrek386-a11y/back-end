import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.auth import AuthService
from app.schemas.auth import SignInRequest
from app.models.user import User
from app.core.exceptions import IncorrectCredentialsException


@pytest.mark.asyncio
@patch("app.services.auth.verify_password", return_value=True)
async def test_login_success(_, mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(
        return_value=User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(timezone.utc),
            hashed_password="some_fake_hash_string",
        )
    )

    auth_service = AuthService(uow=mock_uow, user_service=AsyncMock())
    result = await auth_service.login(
        SignInRequest(email="test@example.com", password="securepassword123")
    )

    assert result.access_token is not None


@pytest.mark.asyncio
@patch("app.services.auth.verify_password", return_value=False)
async def test_login_wrong_password(_, mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(
        return_value=User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            created_at=datetime.now(timezone.utc),
            hashed_password="some_fake_hash_string",
        )
    )

    auth_service = AuthService(uow=mock_uow, user_service=AsyncMock())

    with pytest.raises(IncorrectCredentialsException):
        await auth_service.login(
            SignInRequest(email="test@example.com", password="WRONG_PASSWORD")
        )


@pytest.mark.asyncio
async def test_login_user_not_found(mock_uow):
    mock_uow.users.get_user_by_email = AsyncMock(return_value=None)

    auth_service = AuthService(uow=mock_uow, user_service=AsyncMock())

    with pytest.raises(IncorrectCredentialsException):
        await auth_service.login(
            SignInRequest(email="notfound@example.com", password="password123")
        )
