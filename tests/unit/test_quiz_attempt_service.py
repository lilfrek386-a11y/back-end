import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.quiz_attempt import QuizAttemptService
from app.schemas.quiz_attempt import QuizSubmission, UserAnswerSubmit
from app.core.exceptions import QuizNotFoundException


@pytest.fixture
def attempt_service(mock_uow):
    return QuizAttemptService(mock_uow)


@pytest.fixture
def test_data():
    return {
        "user_id": uuid4(),
        "company_id": uuid4(),
        "quiz_id": uuid4(),
        "q1_id": uuid4(),
        "q2_id": uuid4(),
        "q1_correct_opt": uuid4(),
        "q1_wrong_opt": uuid4(),
        "q2_correct_opt_1": uuid4(),
        "q2_correct_opt_2": uuid4(),
    }


@pytest.mark.asyncio
async def test_submit_test_success(attempt_service, mock_uow, test_data):
    user_id = test_data["user_id"]
    quiz_id = test_data["quiz_id"]
    company_id = test_data["company_id"]

    mock_company = MagicMock()
    mock_company.owner_id = user_id
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)
    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    mock_quiz = MagicMock()
    mock_quiz.id = quiz_id
    mock_quiz.company_id = company_id
    mock_quiz.participation_frequency = 0

    q1 = MagicMock(id=test_data["q1_id"])
    q1.answer_options = [
        MagicMock(id=test_data["q1_correct_opt"], is_correct=True),
        MagicMock(id=test_data["q1_wrong_opt"], is_correct=False),
    ]

    q2 = MagicMock(id=test_data["q2_id"])
    q2.answer_options = [
        MagicMock(id=test_data["q2_correct_opt_1"], is_correct=True),
        MagicMock(id=test_data["q2_correct_opt_2"], is_correct=True),
    ]

    mock_quiz.questions = [q1, q2]
    mock_uow.quizzes.get_quiz_with_details = AsyncMock(return_value=mock_quiz)

    submission = QuizSubmission(
        answers=[
            UserAnswerSubmit(
                question_id=test_data["q1_id"],
                selected_option_ids=[test_data["q1_correct_opt"]],
            ),
            UserAnswerSubmit(
                question_id=test_data["q2_id"],
                selected_option_ids=[test_data["q2_correct_opt_1"]],
            ),
        ]
    )

    mock_attempt = MagicMock()
    mock_attempt.id = uuid4()
    mock_attempt.user_id = user_id
    mock_attempt.quiz_id = quiz_id
    mock_attempt.company_id = company_id
    mock_attempt.correct_answers_count = 1
    mock_attempt.total_questions_count = 2
    mock_attempt.created_at = datetime.now(timezone.utc)

    mock_uow.quiz_attempts.create = AsyncMock(return_value=mock_attempt)

    result = await attempt_service.submit_test(
        user_id=user_id, quiz_id=quiz_id, submission=submission
    )

    mock_uow.quiz_attempts.create.assert_awaited_once()
    assert result.correct_answers_count == 1

    assert mock_quiz.participation_frequency == 1


@pytest.mark.asyncio
async def test_submit_test_not_a_member_raises(attempt_service, mock_uow, test_data):
    stranger_user_id = test_data["user_id"]
    quiz_id = test_data["quiz_id"]
    company_id = test_data["company_id"]
    real_owner_id = uuid4()

    mock_quiz = MagicMock(id=quiz_id, company_id=company_id)
    mock_uow.quizzes.get_quiz_with_details = AsyncMock(return_value=mock_quiz)

    mock_company = MagicMock(owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    submission = QuizSubmission(answers=[])

    from app.core.exceptions import NotEnoughPermissionsException

    with pytest.raises(NotEnoughPermissionsException):
        await attempt_service.submit_test(
            user_id=stranger_user_id, quiz_id=quiz_id, submission=submission
        )


@pytest.mark.asyncio
async def test_submit_test_quiz_not_found(attempt_service, mock_uow, test_data):
    user_id = test_data["user_id"]
    quiz_id = test_data["quiz_id"]
    submission = QuizSubmission(answers=[])

    mock_uow.quizzes.get_quiz_with_details = AsyncMock(return_value=None)

    with pytest.raises(QuizNotFoundException):
        await attempt_service.submit_test(
            user_id=user_id, quiz_id=quiz_id, submission=submission
        )


@pytest.mark.asyncio
async def test_get_user_system_average(attempt_service, mock_uow, test_data):
    user_id = test_data["user_id"]

    mock_uow.quiz_attempts.get_average_score = AsyncMock(return_value=0.85)

    result = await attempt_service.get_user_system_average(user_id=user_id)

    mock_uow.quiz_attempts.get_average_score.assert_awaited_once_with(user_id=user_id)
    assert result == 0.85


@pytest.mark.asyncio
async def test_get_user_company_average(attempt_service, mock_uow, test_data):
    user_id = test_data["user_id"]
    company_id = test_data["company_id"]

    mock_uow.quiz_attempts.get_average_score = AsyncMock(return_value=0.90)

    result = await attempt_service.get_user_company_average(
        user_id=user_id, company_id=company_id
    )

    mock_uow.quiz_attempts.get_average_score.assert_awaited_once_with(
        user_id=user_id, company_id=company_id
    )
    assert result == 0.90
