import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company import Company


class ActionType(str, enum.Enum):
    INVITATION = "invitation"
    REQUEST = "request"


class CompanyAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_actions"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType))

    user: Mapped["User"] = relationship(back_populates="company_actions")
    company: Mapped["Company"] = relationship(back_populates="actions")

    __table_args__ = (
        UniqueConstraint(
            "company_id", "user_id", "action_type", name="uq_company_user_action_type"
        ),
    )
