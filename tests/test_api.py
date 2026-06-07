from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from main import app
from app.dependencies.user import get_user_service
from app.schemas.user import UsersListResponse, UserDetailResponse

client = TestClient(app)


def test_get_users_empty():
    mock_service = AsyncMock()
    mock_service.get_all_users.return_value = UsersListResponse(users=[], total_count=0)

    app.dependency_overrides[get_user_service] = lambda: mock_service
    response = client.get("/users/")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_count"] == 0


def test_create_user():
    mock_service = AsyncMock()
    mock_service.create_new_user.return_value = UserDetailResponse(
        id=uuid4(),
        name="Ivan",
        email="ivan@test.com",
        age=None,
        created_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_user_service] = lambda: mock_service
    response = client.post(
        "/users/",
        json={"name": "Ivan", "email": "ivan@test.com", "password": "password123"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["email"] == "ivan@test.com"
