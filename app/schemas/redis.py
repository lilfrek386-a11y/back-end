from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class QuestionDetail(BaseModel):
    question_id: UUID
    selected_option_ids: list[UUID]
    is_correct: bool


class RedisQuizAttemptDetail(BaseModel):
    attempt_id: UUID
    user_id: UUID
    company_id: UUID
    quiz_id: UUID
    created_at: datetime
    answers: list[QuestionDetail]
