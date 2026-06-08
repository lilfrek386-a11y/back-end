import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def client():
    return TestClient(app)
