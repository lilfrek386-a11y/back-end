from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column


def get_utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(default=get_utcnow)


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        default=get_utcnow, onupdate=get_utcnow, nullable=True
    )
