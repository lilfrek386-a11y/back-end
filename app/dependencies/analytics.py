from typing import Annotated

from fastapi import Depends

from app.dependencies.uow import get_uow
from app.services.analytics import AnalyticsService as AnalyticsServiceClass
from app.utils.uow import UnitOfWork


async def get_analytics_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> AnalyticsServiceClass:
    return AnalyticsServiceClass(uow)


type AnalyticsService = Annotated[AnalyticsServiceClass, Depends(get_analytics_service)]
