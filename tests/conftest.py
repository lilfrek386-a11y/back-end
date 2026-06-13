import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app

from app.dependencies.uow import get_uow


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def client(mock_uow):
    app.dependency_overrides[get_uow] = lambda: mock_uow

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
