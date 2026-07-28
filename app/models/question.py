from typing import TYPE_CHECKING

from sqlalchemy import String, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from .answer_option import AnswerOption
    from .quiz import Quiz


class Question(Base, UUIDMixin):
    __tablename__ = "questions"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    answer_options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
