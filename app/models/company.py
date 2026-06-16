from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import String, ForeignKey, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company_action import CompanyAction


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    is_visible: Mapped[bool] = mapped_column(default=False, server_default=false())
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="companies")
    members: Mapped[list["User"]] = relationship(
        secondary="company_members", back_populates="joined_companies"
    )
    actions: Mapped[list["CompanyAction"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"Company(id={self.id!r}, name={self.name!r}, description={self.description!r}, is_visible={self.is_visible!r}, owner_id={self.owner_id!r})"
