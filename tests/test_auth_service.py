from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth import AuthService
from app.schemas.auth import SignInRequest
from app.models.user import User
from app.core.exceptions import IncorrectCredentialsException


@pytest.mark.asyncio
@patch("app.services.auth.verify_password", return_value=True)
async def test_login_success(mock_verify_password):
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_user_service = AsyncMock()

    fake_user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="some_fake_hash_string",
    )
    mock_uow.users.get_user_by_email = AsyncMock(return_value=fake_user)

    auth_service = AuthService(uow=mock_uow, user_service=mock_user_service)
    request_data = SignInRequest(email="test@example.com", password="securepassword123")

    result = await auth_service.login(request_data)

    assert result.access_token is not None
    assert isinstance(result.access_token, str)


@pytest.mark.asyncio
@patch("app.services.auth.verify_password", return_value=False)
async def test_login_wrong_password(mock_verify_password):
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_user_service = AsyncMock()

    fake_user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="some_fake_hash_string",
    )
    mock_uow.users.get_user_by_email = AsyncMock(return_value=fake_user)

    auth_service = AuthService(uow=mock_uow, user_service=mock_user_service)
    request_data = SignInRequest(email="test@example.com", password="WRONG_PASSWORD")

    with pytest.raises(IncorrectCredentialsException):
        await auth_service.login(request_data)


@pytest.mark.asyncio
async def test_login_user_not_found():
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_user_service = AsyncMock()

    mock_uow.users.get_user_by_email = AsyncMock(return_value=None)

    auth_service = AuthService(uow=mock_uow, user_service=mock_user_service)
    request_data = SignInRequest(email="notfound@example.com", password="password123")

    with pytest.raises(IncorrectCredentialsException):
        await auth_service.login(request_data)
