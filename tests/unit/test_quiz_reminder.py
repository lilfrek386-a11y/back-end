from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

import pytest

from app.tasks.quiz_reminder import _check_quiz_completions


@pytest.mark.asyncio
async def test_check_quiz_completions_sends_notification(mock_uow):
    company_id = uuid4()
    quiz_id = uuid4()
    member_id = uuid4()

    mock_company = MagicMock(id=company_id)
    mock_quiz = MagicMock(id=quiz_id, title="Python Basics")
    mock_member = MagicMock(user_id=member_id)

    mock_uow.companies.get_all = AsyncMock(return_value=([mock_company], 1))
    mock_uow.quizzes.get_all_by_company = AsyncMock(return_value=([mock_quiz], 1))
    mock_uow.company_members.get_company_members = AsyncMock(
        return_value=([mock_member], 1)
    )
    mock_uow.quiz_attempts.get_user_last_attempts = AsyncMock(return_value=[])
    mock_uow.notifications.create = AsyncMock()

    with patch("app.tasks.quiz_reminder.UnitOfWork", return_value=mock_uow):
        await _check_quiz_completions()

    mock_uow.notifications.create.assert_awaited_once()
    call_args = mock_uow.notifications.create.call_args[0][0]
    assert call_args["user_id"] == member_id
    assert "Python Basics" in call_args["message"]


@pytest.mark.asyncio
async def test_check_quiz_completions_no_notification_if_recent(mock_uow):
    company_id = uuid4()
    quiz_id = uuid4()
    member_id = uuid4()

    mock_company = MagicMock(id=company_id)
    mock_quiz = MagicMock(id=quiz_id, title="Python Basics")
    mock_member = MagicMock(user_id=member_id)

    mock_uow.companies.get_all = AsyncMock(return_value=([mock_company], 1))
    mock_uow.quizzes.get_all_by_company = AsyncMock(return_value=([mock_quiz], 1))
    mock_uow.company_members.get_company_members = AsyncMock(
        return_value=([mock_member], 1)
    )

    mock_uow.quiz_attempts.get_user_last_attempts = AsyncMock(
        return_value=[
            (
                quiz_id,
                "Python Basics",
                datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
            )
        ]
    )
    mock_uow.notifications.create = AsyncMock()

    with patch("app.tasks.quiz_reminder.UnitOfWork", return_value=mock_uow):
        await _check_quiz_completions()

    mock_uow.notifications.create.assert_not_called()
