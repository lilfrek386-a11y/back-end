import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
from app.dependencies.auth import get_current_user
from app.dependencies.user import get_user_service
from app.schemas.user import UsersListResponse, UserDetailResponse
from main import app


def test_get_users_empty(client):
    mock_service = AsyncMock()
    mock_service.get_multi_users.return_value = UsersListResponse(
        users=[], total_count=0
    )

    app.dependency_overrides[get_user_service] = lambda: mock_service
    response = client.get("/users/")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_count"] == 0


def test_create_user(client):
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


def test_update_me_success_and_ignores_email(client):
    fake_user_id = uuid4()

    mock_current_user = UserDetailResponse(
        id=fake_user_id,
        name="Old Name",
        email="old@test.com",
        age=25,
        created_at=datetime.now(timezone.utc),
    )

    mock_service = AsyncMock()
    mock_service.update_user.return_value = mock_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_user_service] = lambda: mock_service

    payload = {
        "name": "New Hacker Name",
        "email": "hacker@test.com",
        "password": "newpassword123",
    }
    response = client.patch("/users/me", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200

    mock_service.update_user.assert_called_once()

    args, kwargs = mock_service.update_user.call_args
    passed_user_id = args[0]
    passed_user_data = args[1]
    assert passed_user_id == fake_user_id

    assert passed_user_data.name == "New Hacker Name"
    assert passed_user_data.password == "newpassword123"

    assert not hasattr(passed_user_data, "email")


def test_update_user_by_id_success(client):
    """Новый тест для проверки эндпоинта PATCH /users/{user_id}"""
    target_user_id = uuid4()

    mock_updated_user = UserDetailResponse(
        id=target_user_id,
        name="Updated User",
        email="target@test.com",
        age=30,
        created_at=datetime.now(timezone.utc),
    )

    mock_service = AsyncMock()
    mock_service.update_user.return_value = mock_updated_user

    app.dependency_overrides[get_user_service] = lambda: mock_service

    payload = {
        "name": "Updated User",
        "age": 30,
    }

    response = client.patch(f"/users/{target_user_id}", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_service.update_user.assert_called_once()

    args, kwargs = mock_service.update_user.call_args
    passed_user_id = args[0]
    assert passed_user_id == target_user_id


def test_delete_me(client):
    fake_user_id = uuid4()

    mock_current_user = UserDetailResponse(
        id=fake_user_id,
        name="Old Name",
        email="old@test.com",
        age=25,
        created_at=datetime.now(timezone.utc),
    )

    mock_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_user_service] = lambda: mock_service

    response = client.delete("/users/me")

    app.dependency_overrides.clear()

    assert response.status_code == 204

    mock_service.delete_user.assert_called_once_with(fake_user_id)
