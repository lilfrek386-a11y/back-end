import io
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from openpyxl import Workbook
from fastapi import UploadFile

from app.services.quiz_import import QuizImportService


def make_excel_upload_file(rows: list[tuple]) -> UploadFile:
    wb = Workbook()
    ws = wb.active

    assert ws is not None, "Workbook must have an active sheet"

    ws.append(("question_title", "option_text", "is_correct"))
    for row in rows:
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return UploadFile(filename="quiz.xlsx", file=buffer)


@pytest.mark.asyncio
async def test_import_creates_new_quiz_when_no_quiz_id():
    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.quizzes.create_quiz.return_value = MagicMock(id=uuid4())

    user_id = uuid4()
    company_id = uuid4()

    mock_uow.companies.get_one.return_value = MagicMock(owner_id=user_id)

    service = QuizImportService(mock_uow)
    file = make_excel_upload_file(
        [
            ("Q1", "Answer A", True),
            ("Q1", "Answer B", False),
        ]
    )

    result = await service.import_quiz(
        user_id=user_id,
        company_id=company_id,
        file=file,
        title="Test Quiz",
        description="desc",
        quiz_id=None,
    )

    assert result.created is True
    assert result.questions_imported == 1
    mock_uow.quizzes.create_quiz.assert_called_once()


@pytest.mark.asyncio
async def test_import_updates_existing_quiz_when_quiz_id_given():
    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow

    user_id = uuid4()
    company_id = uuid4()

    mock_uow.companies.get_one.return_value = MagicMock(owner_id=user_id)

    existing_quiz = MagicMock(id=uuid4(), company_id=company_id)
    mock_uow.quizzes.get_one.return_value = existing_quiz

    service = QuizImportService(mock_uow)
    file = make_excel_upload_file([("Q1", "Answer A", True)])

    result = await service.import_quiz(
        user_id=user_id,
        company_id=company_id,
        file=file,
        title="Updated Quiz",
        description="desc",
        quiz_id=existing_quiz.id,
    )

    assert result.created is False
    mock_uow.quizzes.replace_questions_from_import.assert_called_once()
