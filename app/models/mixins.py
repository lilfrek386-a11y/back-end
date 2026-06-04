from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column


def get_utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=get_utcnow)
