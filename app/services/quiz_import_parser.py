import io
import zipfile
import logging

import openpyxl
from fastapi import UploadFile

from app.core.exceptions import InvalidExcelFormatException
from app.schemas.quiz_import import ImportedQuestion, ImportedAnswerOption

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = (".xlsx", ".xls")


async def parse_quiz_excel(file: UploadFile) -> list[ImportedQuestion]:
    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise InvalidExcelFormatException("Only .xlsx or .xls files are allowed.")

    content = await file.read()

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        sheet = workbook.active
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        logger.warning(f"Failed to parse uploaded Excel file: {e}")
        raise InvalidExcelFormatException(
            "The file is corrupted or not a valid Excel file."
        )

    assert sheet is not None, "Excel file must have an active sheet"

    questions_map: dict[str, list[ImportedAnswerOption]] = {}

    rows = sheet.iter_rows(min_row=2, values_only=True)
    for row in rows:
        if not row or len(row) < 3:
            continue

        question_title, option_text, is_correct = row[0], row[1], row[2]
        if not question_title or not option_text:
            continue

        questions_map.setdefault(str(question_title).strip(), []).append(
            ImportedAnswerOption(
                text=str(option_text).strip(),
                is_correct=bool(is_correct),
            )
        )

    if not questions_map:
        raise InvalidExcelFormatException("No valid quiz data found in the file.")

    return [
        ImportedQuestion(title=title, answer_options=options)
        for title, options in questions_map.items()
    ]
