from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.company_member import CompanyMemberRole


class MemberResponse(BaseModel):
    company_id: UUID
    user_id: UUID
    created_at: datetime
    role: CompanyMemberRole
    model_config = ConfigDict(from_attributes=True)


class MembersListResponse(BaseModel):
    members: list[MemberResponse]
    total_count: int
