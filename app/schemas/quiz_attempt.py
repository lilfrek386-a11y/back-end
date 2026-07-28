from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserAnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_ids: list[UUID]


class QuizSubmission(BaseModel):
    answers: list[UserAnswerSubmit]


class QuizAttemptResponse(BaseModel):
    id: UUID
    user_id: UUID
    quiz_id: UUID
    company_id: UUID
    correct_answers_count: int
    total_questions_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AverageScoreResponse(BaseModel):
    average_score: float
