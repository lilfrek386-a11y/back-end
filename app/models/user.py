from typing import TYPE_CHECKING
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.company_action import CompanyAction
    from app.models.quiz_attempt import QuizAttempt


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(
        String(), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    companies: Mapped[list["Company"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    company_actions: Mapped[list["CompanyAction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    joined_companies: Mapped[list["Company"]] = relationship(
        secondary="company_members", back_populates="members"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"
