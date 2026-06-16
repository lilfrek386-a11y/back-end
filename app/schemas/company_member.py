from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemberResponse(BaseModel):
    company_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembersListResponse(BaseModel):
    members: list[MemberResponse]
    total_count: int
