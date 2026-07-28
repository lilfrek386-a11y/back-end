from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnswerOptionResponse(BaseModel):
    id: UUID
    text: str
    is_correct: bool
    question_id: UUID

    model_config = ConfigDict(from_attributes=True)


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool


class AnswerOptionsResponseList(BaseModel):
    options: list[AnswerOptionResponse]
    total_count: int
