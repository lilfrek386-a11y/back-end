from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActionResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    action_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionsListResponse(BaseModel):
    actions: list[ActionResponse]
    total_count: int
