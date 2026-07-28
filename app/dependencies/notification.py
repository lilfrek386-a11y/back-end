from typing import Annotated

from fastapi.params import Depends
from app.dependencies.uow import get_uow
from app.utils.uow import UnitOfWork
from app.services.notification import NotificationService as NotificationServiceClass


def get_notification_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> NotificationServiceClass:
    return NotificationServiceClass(uow)


type NotificationService = Annotated[
    NotificationServiceClass, Depends(get_notification_service)
]
