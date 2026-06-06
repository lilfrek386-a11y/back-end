import uuid
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone


def get_utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=get_utcnow)


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
