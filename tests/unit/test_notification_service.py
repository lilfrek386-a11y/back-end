import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.notification import (
    NotificationService,
    send_quiz_notifications_bg,
)
from app.core.exceptions import (
    NotificationNotFoundException,
    NotEnoughPermissionsException,
)


@pytest.fixture
def notification_service(mock_uow):
    return NotificationService(mock_uow)


@pytest.fixture
def base_uuids():
    return {
        "user_id": uuid4(),
        "notification_id": uuid4(),
        "company_id": uuid4(),
    }


@pytest.mark.asyncio
async def test_get_my_notifications_success(notification_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]

    mock_notification = MagicMock()
    mock_notification.id = uuid4()
    mock_notification.user_id = user_id
    mock_notification.message = "New quiz 'Python Basics' is available!"
    mock_notification.is_read = False
    mock_notification.created_at = datetime.now(timezone.utc)

    mock_uow.notifications.get_by_user = AsyncMock(
        return_value=([mock_notification], 1)
    )

    result = await notification_service.get_my_notifications(user_id)

    assert result.total_count == 1
    assert len(result.notifications) == 1
    assert result.notifications[0].message == "New quiz 'Python Basics' is available!"
    mock_uow.notifications.get_by_user.assert_awaited_once_with(
        user_id=user_id, skip=0, limit=100
    )


@pytest.mark.asyncio
async def test_get_my_notifications_empty(notification_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]

    mock_uow.notifications.get_by_user = AsyncMock(return_value=([], 0))

    result = await notification_service.get_my_notifications(user_id)

    assert result.total_count == 0
    assert result.notifications == []


@pytest.mark.asyncio
async def test_get_my_notifications_respects_pagination(
    notification_service, mock_uow, base_uuids
):
    user_id = base_uuids["user_id"]
    mock_uow.notifications.get_by_user = AsyncMock(return_value=([], 0))

    await notification_service.get_my_notifications(user_id, skip=20, limit=10)

    mock_uow.notifications.get_by_user.assert_awaited_once_with(
        user_id=user_id, skip=20, limit=10
    )


@pytest.mark.asyncio
async def test_mark_notification_as_read_success(
    notification_service, mock_uow, base_uuids
):
    user_id = base_uuids["user_id"]
    notification_id = base_uuids["notification_id"]

    mock_notification = MagicMock()
    mock_notification.id = notification_id
    mock_notification.user_id = user_id
    mock_notification.is_read = False
    mock_notification.message = "New quiz available!"
    mock_notification.created_at = datetime.now(timezone.utc)

    mock_uow.notifications.get_one = AsyncMock(return_value=mock_notification)

    mock_updated = MagicMock()
    mock_updated.id = notification_id
    mock_updated.user_id = user_id
    mock_updated.is_read = True
    mock_updated.message = "New quiz available!"
    mock_updated.created_at = mock_notification.created_at
    mock_uow.notifications.update = AsyncMock(return_value=mock_updated)

    result = await notification_service.mark_notification_as_read(
        user_id=user_id, notification_id=notification_id
    )

    assert result.is_read is True
    mock_uow.notifications.update.assert_awaited_once_with(
        mock_notification, {"is_read": True}
    )


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(
    notification_service, mock_uow, base_uuids
):
    user_id = base_uuids["user_id"]
    notification_id = base_uuids["notification_id"]

    mock_uow.notifications.get_one = AsyncMock(return_value=None)

    with pytest.raises(NotificationNotFoundException):
        await notification_service.mark_notification_as_read(
            user_id=user_id, notification_id=notification_id
        )


@pytest.mark.asyncio
async def test_mark_notification_as_read_wrong_owner_raises(
    notification_service, mock_uow, base_uuids
):
    user_id = base_uuids["user_id"]
    notification_id = base_uuids["notification_id"]
    actual_owner_id = uuid4()

    mock_notification = MagicMock()
    mock_notification.id = notification_id
    mock_notification.user_id = actual_owner_id  # belongs to someone else

    mock_uow.notifications.get_one = AsyncMock(return_value=mock_notification)

    with pytest.raises(NotEnoughPermissionsException):
        await notification_service.mark_notification_as_read(
            user_id=user_id, notification_id=notification_id
        )

    mock_uow.notifications.update.assert_not_called()


@pytest.mark.asyncio
async def test_send_quiz_notifications_bg_notifies_all_members_except_creator(
    base_uuids,
):
    company_id = base_uuids["company_id"]
    creator_id = uuid4()
    member_1_id = uuid4()
    member_2_id = uuid4()

    member_creator = MagicMock(user_id=creator_id)
    member_1 = MagicMock(user_id=member_1_id)
    member_2 = MagicMock(user_id=member_2_id)

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.company_members.get_company_members = AsyncMock(
        return_value=([member_creator, member_1, member_2], 3)
    )
    mock_uow.notifications.create = AsyncMock()

    with patch("app.services.notification.UnitOfWork", return_value=mock_uow):
        await send_quiz_notifications_bg(
            company_id=company_id,
            quiz_title="Python Basics",
            creator_id=creator_id,
        )

    assert mock_uow.notifications.create.await_count == 2

    created_for = {
        call.args[0]["user_id"]
        for call in mock_uow.notifications.create.await_args_list
    }
    assert created_for == {member_1_id, member_2_id}

    first_call_data = mock_uow.notifications.create.await_args_list[0].args[0]
    assert "Python Basics" in first_call_data["message"]


@pytest.mark.asyncio
async def test_send_quiz_notifications_bg_no_members_creates_nothing(base_uuids):
    company_id = base_uuids["company_id"]
    creator_id = uuid4()

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.company_members.get_company_members = AsyncMock(return_value=([], 0))
    mock_uow.notifications.create = AsyncMock()

    with patch("app.services.notification.UnitOfWork", return_value=mock_uow):
        await send_quiz_notifications_bg(
            company_id=company_id,
            quiz_title="Empty Company Quiz",
            creator_id=creator_id,
        )

    mock_uow.notifications.create.assert_not_called()


@pytest.mark.asyncio
async def test_send_quiz_notifications_bg_only_creator_in_company(base_uuids):
    company_id = base_uuids["company_id"]
    creator_id = uuid4()
    member_creator = MagicMock(user_id=creator_id)

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.company_members.get_company_members = AsyncMock(
        return_value=([member_creator], 1)
    )
    mock_uow.notifications.create = AsyncMock()

    with patch("app.services.notification.UnitOfWork", return_value=mock_uow):
        await send_quiz_notifications_bg(
            company_id=company_id,
            quiz_title="Solo Quiz",
            creator_id=creator_id,
        )

    mock_uow.notifications.create.assert_not_called()
