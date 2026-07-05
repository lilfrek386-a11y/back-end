from uuid import UUID
from pydantic import BaseModel


class ImportedAnswerOption(BaseModel):
    text: str
    is_correct: bool


class ImportedQuestion(BaseModel):
    title: str
    answer_options: list[ImportedAnswerOption]


class QuizImportResult(BaseModel):
    quiz_id: UUID
    created: bool
    questions_imported: int
