import asyncio
from uuid import UUID

from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect

from app.dependencies.auth import CurrentUser, get_current_user
from app.dependencies.notification import NotificationService
from app.dependencies.pagination import SkipQuery, LimitQuery
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.core.redis import get_redis_client
from app.utils.uow import UnitOfWork

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


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await websocket.accept()

    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
        token = auth_message.get("token")
        if not token:
            raise ValueError("No token provided")

        async with UnitOfWork() as uow:
            user = await get_current_user(token=token, uow=uow)
            user_id = user.id

    except asyncio.TimeoutError:
        await websocket.send_json({"detail": "Authentication timeout"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception:
        await websocket.send_json({"detail": "Incorrect credentials"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.send_json({"detail": "Connected"})

    redis = get_redis_client()
    pubsub = redis.pubsub()
    channel_name = f"channel:notifications:{user_id}"
    await pubsub.subscribe(channel_name)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
