from typing import TypeVar, Generic, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_one(self, obj_id: int) -> T | None:
        obj = await self.db.get(self.model, obj_id)
        return obj

    async def get_all(self) -> Sequence[T]:
        stmt = select(self.model).order_by(self.model.id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> T:
        dt_obj = self.model(**data)
        self.db.add(dt_obj)
        await self.db.flush()
        await self.db.refresh(dt_obj)
        return dt_obj

    async def update(self, db_obj: T, update_data: dict) -> T:
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        return db_obj

    async def delete(self, dt_obj: T) -> None:
        await self.db.delete(dt_obj)