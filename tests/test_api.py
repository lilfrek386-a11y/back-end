import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from main import app
from app.dependencies.user import get_user_service
from app.schemas.user import UsersListResponse, UserDetailResponse
from datetime import datetime, timezone

client = TestClient(app)


def test_get_users_empty():
    mock_service = AsyncMock()
    mock_service.get_all_users.return_value = UsersListResponse(users=[], total_count=0)

    app.dependency_overrides[get_user_service] = lambda: mock_service

    response = client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0

    app.dependency_overrides.clear()


def test_create_user():
    mock_service = AsyncMock()

    mock_user_response = UserDetailResponse(
        id=1,
        name="Ivan",
        email="ivan@test.com",
        age=None,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )
    mock_service.create_new_user.return_value = mock_user_response

    app.dependency_overrides[get_user_service] = lambda: mock_service

    response = client.post(
        "/users/",
        json={"name": "Ivan", "email": "ivan@test.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "ivan@test.com"

    app.dependency_overrides.clear()
