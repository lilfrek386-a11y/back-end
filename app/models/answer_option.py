from typing import TYPE_CHECKING

from sqlalchemy import String, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from .question import Question


class AnswerOption(Base, UUIDMixin):
    __tablename__ = "answer_options"

    text: Mapped[str] = mapped_column(String(255), nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )

    question: Mapped["Question"] = relationship(back_populates="answer_options")
