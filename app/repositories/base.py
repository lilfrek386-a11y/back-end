from collections.abc import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[T: Base]:
    model: type[T]

    def __init__(self, db: AsyncSession, model: type[T]) -> None:
        self.db = db
        self.model = model

    async def get_one(self, obj_id: int) -> T | None:
        return await self.db.get(self.model, obj_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[Sequence[T], int]:
        count_stmt = select(func.count()).select_from(self.model)
        total_count = await self.db.scalar(count_stmt)

        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total_count or 0

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
