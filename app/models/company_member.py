import enum
from uuid import UUID

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

from app.models.mixins import TimestampMixin


class CompanyMemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class CompanyMember(Base, TimestampMixin):
    __tablename__ = "company_members"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[CompanyMemberRole] = mapped_column(
        Enum(CompanyMemberRole), default=CompanyMemberRole.MEMBER
    )
