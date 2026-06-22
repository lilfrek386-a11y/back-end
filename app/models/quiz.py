from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.company import Company


class Quiz(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "quizzes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(), nullable=False)
    participation_frequency: Mapped[int] = mapped_column(default=0, server_default="0")
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    company: Mapped["Company"] = relationship(back_populates="quizzes")
