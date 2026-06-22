from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.answer_option import AnswerOptionResponse, AnswerOptionCreate


class QuestionResponse(BaseModel):
    id: UUID
    title: str
    quiz_id: UUID
    answer_options: list[AnswerOptionResponse]
    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(BaseModel):
    title: str
    answer_options: list[AnswerOptionCreate] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def check_has_correct_answer(self) -> "QuestionCreate":
        if not any(opt.is_correct for opt in self.answer_options):
            raise ValueError("At least one answer option must be marked as correct.")
        return self

class QuestionsResponseList(BaseModel):
    questions: list[QuestionResponse]
    total_count: int
