import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.dependencies.auth import get_current_user
from app.dependencies.analytics import get_analytics_service
from app.schemas.user import UserDetailResponse
from app.schemas.analytics import (
    UserQuizAverageResponse,
    UserLastAttemptResponse,
    WeeklyTrendPoint,
    MemberWeeklyAnalytics,
    QuizWeeklyAnalytics,
    CompanyMemberLastAttempt,
)
from app.core.exceptions import NotEnoughPermissionsException
from main import app


@pytest.fixture
def fake_user():
    return UserDetailResponse(
        id=uuid4(),
        name="Test User",
        email="test@test.com",
        age=None,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def override_current_user(fake_user):
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield fake_user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_analytics_service():
    service = AsyncMock()
    app.dependency_overrides[get_analytics_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_analytics_service, None)


# User-specific analytics


def test_get_my_overall_average_success(
    client, override_current_user, mock_analytics_service
):
    mock_analytics_service.get_user_overall_average.return_value = 0.75

    response = client.get("/users/me/analytics/overall-average")

    assert response.status_code == 200
    assert response.json() == {"average_score": 0.75}
    mock_analytics_service.get_user_overall_average.assert_awaited_once_with(
        override_current_user.id
    )


def test_get_my_quizzes_analytics_no_filters(
    client, override_current_user, mock_analytics_service
):
    quiz_id = uuid4()
    mock_analytics_service.get_user_quizzes_averages.return_value = [
        UserQuizAverageResponse(
            quiz_id=quiz_id, title="Python Basics", average_score=0.9
        )
    ]

    response = client.get("/users/me/analytics/quizzes")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Python Basics"
    assert body[0]["average_score"] == 0.9

    mock_analytics_service.get_user_quizzes_averages.assert_awaited_once_with(
        override_current_user.id, date_from=None, date_to=None
    )


def test_get_my_quizzes_analytics_with_date_range(
    client, override_current_user, mock_analytics_service
):
    mock_analytics_service.get_user_quizzes_averages.return_value = []

    response = client.get(
        "/users/me/analytics/quizzes",
        params={"date_from": "2026-01-01T00:00:00", "date_to": "2026-06-01T00:00:00"},
    )

    assert response.status_code == 200
    assert response.json() == []

    args, kwargs = mock_analytics_service.get_user_quizzes_averages.call_args
    assert kwargs["date_from"] == datetime(2026, 1, 1)
    assert kwargs["date_to"] == datetime(2026, 6, 1)


def test_get_my_recent_attempts_success(
    client, override_current_user, mock_analytics_service
):
    quiz_id = uuid4()
    last_attempt = datetime.now(timezone.utc)
    mock_analytics_service.get_user_recent_attempts.return_value = [
        UserLastAttemptResponse(
            quiz_id=quiz_id, title="SQL Basics", last_attempt_at=last_attempt
        )
    ]

    response = client.get("/users/me/analytics/recent")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["title"] == "SQL Basics"
    mock_analytics_service.get_user_recent_attempts.assert_awaited_once_with(
        override_current_user.id
    )


def test_get_my_overall_average_requires_auth(client, mock_analytics_service):
    response = client.get("/users/me/analytics/overall-average")

    assert response.status_code in (401, 403)
    mock_analytics_service.get_user_overall_average.assert_not_awaited()


# Company-specific analytics


def test_get_company_members_analytics_success(
    client, override_current_user, mock_analytics_service
):
    company_id = uuid4()
    user_id = uuid4()
    week_start = datetime(2026, 6, 1)

    mock_analytics_service.get_company_members_trends.return_value = [
        MemberWeeklyAnalytics(
            user_id=user_id,
            email="member@test.com",
            trends=[WeeklyTrendPoint(week_start=week_start, average_score=0.8)],
        )
    ]

    response = client.get(f"/companies/{company_id}/analytics/members")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["email"] == "member@test.com"
    assert body[0]["trends"][0]["average_score"] == 0.8

    mock_analytics_service.get_company_members_trends.assert_awaited_once_with(
        company_id, override_current_user.id
    )


def test_get_company_members_analytics_forbidden(
    client, override_current_user, mock_analytics_service
):
    company_id = uuid4()
    mock_analytics_service.get_company_members_trends.side_effect = (
        NotEnoughPermissionsException()
    )

    response = client.get(f"/companies/{company_id}/analytics/members")

    assert response.status_code == 403


def test_get_company_member_detailed_analytics_success(
    client, override_current_user, mock_analytics_service
):
    company_id = uuid4()
    target_user_id = uuid4()
    quiz_id = uuid4()
    week_start = datetime(2026, 6, 8)

    mock_analytics_service.get_company_user_detailed_trends.return_value = [
        QuizWeeklyAnalytics(
            quiz_id=quiz_id,
            title="Python Basics",
            trends=[WeeklyTrendPoint(week_start=week_start, average_score=0.65)],
        )
    ]

    response = client.get(f"/companies/{company_id}/analytics/members/{target_user_id}")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["title"] == "Python Basics"
    assert body[0]["trends"][0]["average_score"] == 0.65

    mock_analytics_service.get_company_user_detailed_trends.assert_awaited_once_with(
        company_id=company_id,
        target_user_id=target_user_id,
        current_user_id=override_current_user.id,
    )


def test_get_company_recent_attempts_success(
    client, override_current_user, mock_analytics_service
):
    company_id = uuid4()
    user_id = uuid4()
    last_attempt = datetime.now(timezone.utc)

    mock_analytics_service.get_company_recent_attempts.return_value = [
        CompanyMemberLastAttempt(
            user_id=user_id, email="member@test.com", last_attempt_at=last_attempt
        )
    ]

    response = client.get(f"/companies/{company_id}/analytics/recent")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["email"] == "member@test.com"

    mock_analytics_service.get_company_recent_attempts.assert_awaited_once_with(
        company_id, override_current_user.id
    )


def test_get_company_recent_attempts_includes_members_without_attempts(
    client, override_current_user, mock_analytics_service
):
    company_id = uuid4()
    user_id = uuid4()

    mock_analytics_service.get_company_recent_attempts.return_value = [
        CompanyMemberLastAttempt(
            user_id=user_id, email="never-played@test.com", last_attempt_at=None
        )
    ]

    response = client.get(f"/companies/{company_id}/analytics/recent")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["last_attempt_at"] is None
