from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(
        String(), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"
