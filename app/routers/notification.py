from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUser
from app.dependencies.notification import NotificationService
from app.dependencies.pagination import SkipQuery, LimitQuery
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter(tags=["Notifications"])


@router.get(
    "/users/me/notifications",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current user's notifications",
)
async def get_notifications(
    current_user: CurrentUser,
    service: NotificationService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_my_notifications(current_user.id, skip=skip, limit=limit)


@router.patch(
    "/users/me/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    service: NotificationService,
):
    return await service.mark_notification_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )
