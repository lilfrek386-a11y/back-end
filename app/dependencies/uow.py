from app.utils.uow import UnitOfWork


async def get_uow() -> UnitOfWork:
    return UnitOfWork()
