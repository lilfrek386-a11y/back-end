from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.question import QuestionResponse, QuestionCreate


class QuizResponse(BaseModel):
    id: UUID
    title: str
    description: str
    participation_frequency: int
    company_id: UUID
    questions: list[QuestionResponse]

    model_config = ConfigDict(from_attributes=True)


class QuizCreate(BaseModel):
    title: str
    description: str
    questions: list[QuestionCreate] = Field(min_length=2)


class QuizUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class QuizzesResponseList(BaseModel):
    quizzes: list[QuizResponse]
    total_count: int
