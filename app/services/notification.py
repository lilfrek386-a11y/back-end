from uuid import UUID

from app.core.exceptions import (
    NotEnoughPermissionsException,
    NotificationNotFoundException,
)
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.utils.uow import UnitOfWork


class NotificationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_my_notifications(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> NotificationListResponse:
        async with self.uow:
            notifications, total_count = await self.uow.notifications.get_by_user(
                user_id=user_id, skip=skip, limit=limit
            )

            notifications_list = [
                NotificationResponse.model_validate(n) for n in notifications
            ]

            return NotificationListResponse(
                notifications=notifications_list, total_count=total_count
            )

    async def mark_notification_as_read(
        self, user_id: UUID, notification_id: UUID
    ) -> NotificationResponse:
        async with self.uow:
            notification = await self.uow.notifications.get_one(notification_id)
            if not notification:
                raise NotificationNotFoundException()

            if notification.user_id != user_id:
                raise NotEnoughPermissionsException()

            updated_notification = await self.uow.notifications.update(
                notification, {"is_read": True}
            )
            return NotificationResponse.model_validate(updated_notification)


async def send_quiz_notifications_bg(
    company_id: UUID, quiz_title: str, creator_id: UUID
) -> None:
    async with UnitOfWork() as uow:
        members, _ = await uow.company_members.get_company_members(
            company_id, skip=0, limit=10_000
        )

        for member in members:
            if member.user_id == creator_id:
                continue

            await uow.notifications.create(
                {
                    "user_id": member.user_id,
                    "message": f"New quiz '{quiz_title}' is available in your company!",
                }
            )
