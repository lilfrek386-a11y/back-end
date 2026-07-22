import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.quiz_attempt import QuizAttemptService
from app.schemas.quiz_attempt import QuizSubmission, UserAnswerSubmit
from app.core.exceptions import QuizNotFoundException, UnsupportedExportFormatException

from app.schemas.redis import RedisQuizAttemptDetail, QuestionDetail


@pytest.fixture
def mock_redis_service():
    service = MagicMock()
    service.save_quiz_attempt_details = AsyncMock()
    return service


@pytest.fixture
def attempt_service(mock_uow, mock_redis_service):
    return QuizAttemptService(mock_uow, mock_redis_service)


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
async def test_submit_test_success(
    attempt_service, mock_uow, test_data, mock_redis_service
):
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

    attempt_id = uuid4()
    mock_attempt = MagicMock()
    mock_attempt.id = attempt_id
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

    mock_redis_service.save_quiz_attempt_details.assert_awaited_once()

    redis_payload = mock_redis_service.save_quiz_attempt_details.call_args[0][0]
    assert isinstance(redis_payload, RedisQuizAttemptDetail)
    assert redis_payload.attempt_id == attempt_id
    assert len(redis_payload.answers) == 2

    assert redis_payload.answers[0].is_correct is True
    assert redis_payload.answers[1].is_correct is False


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


@pytest.mark.asyncio
async def test_export_attempts_json_success(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    user_id = test_data["user_id"]
    attempt_id = uuid4()

    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(
        return_value=[attempt_id]
    )

    mock_redis_data = RedisQuizAttemptDetail(
        attempt_id=attempt_id,
        user_id=user_id,
        company_id=test_data["company_id"],
        quiz_id=test_data["quiz_id"],
        created_at=datetime.now(timezone.utc),
        answers=[],
    )
    mock_redis_service.get_quiz_attempts_details = AsyncMock(
        return_value=[mock_redis_data]
    )

    result = await attempt_service.export_attempts(
        export_format="json", user_id=user_id
    )

    assert result == [mock_redis_data]
    mock_uow.quiz_attempts.get_attempt_ids_for_export.assert_awaited_once_with(
        user_id=user_id, company_id=None, quiz_id=None
    )
    mock_redis_service.get_quiz_attempts_details.assert_awaited_once_with(
        attempt_ids=[attempt_id]
    )


@pytest.mark.asyncio
async def test_export_attempts_csv_success(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    user_id = test_data["user_id"]
    attempt_id = uuid4()
    option_id = test_data["q1_correct_opt"]

    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(
        return_value=[attempt_id]
    )

    mock_redis_data = RedisQuizAttemptDetail(
        attempt_id=attempt_id,
        user_id=user_id,
        company_id=test_data["company_id"],
        quiz_id=test_data["quiz_id"],
        created_at=datetime.now(timezone.utc),
        answers=[
            QuestionDetail(
                question_id=test_data["q1_id"],
                selected_option_ids=[option_id],
                is_correct=True,
            )
        ],
    )
    mock_redis_service.get_quiz_attempts_details = AsyncMock(
        return_value=[mock_redis_data]
    )

    mock_uow.questions.get_texts_by_ids = AsyncMock(
        return_value={test_data["q1_id"]: "Question 1"}
    )
    mock_uow.answer_options.get_texts_by_ids = AsyncMock(
        return_value={option_id: "Correct option"}
    )
    mock_uow.users.get_emails_by_ids = AsyncMock(
        return_value={user_id: "user@example.com"}
    )
    mock_uow.quizzes.get_titles_by_ids = AsyncMock(
        return_value={test_data["quiz_id"]: "Quiz Title"}
    )
    mock_uow.companies.get_names_by_ids = AsyncMock(
        return_value={test_data["company_id"]: "Company Name"}
    )

    result = await attempt_service.export_attempts(export_format="csv", user_id=user_id)

    assert isinstance(result, str)
    assert (
        "Date,User Email,Company Name,Quiz Title,Question,Selected Answer,Is Correct"
        in result
    )
    assert "user@example.com" in result
    assert "Company Name" in result
    assert "Quiz Title" in result
    assert "Question 1" in result
    assert "Correct option" in result
    assert "True" in result


@pytest.mark.asyncio
async def test_export_attempts_empty_data(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    user_id = test_data["user_id"]

    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(return_value=[])
    mock_redis_service.get_quiz_attempts_details = AsyncMock()

    result_json = await attempt_service.export_attempts(
        export_format="json", user_id=user_id
    )
    result_csv = await attempt_service.export_attempts(
        export_format="csv", user_id=user_id
    )

    assert result_json == []
    assert result_csv == ""
    mock_redis_service.get_quiz_attempts_details.assert_not_called()


@pytest.mark.asyncio
async def test_export_attempts_unsupported_format(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    user_id = test_data["user_id"]

    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(
        return_value=[uuid4()]
    )
    mock_redis_service.get_quiz_attempts_details = AsyncMock(return_value=[])

    with pytest.raises(UnsupportedExportFormatException):
        await attempt_service.export_attempts(export_format="pdf", user_id=user_id)


@pytest.mark.asyncio
async def test_export_attempts_quiz_not_in_company_raises(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    company_id = test_data["company_id"]
    quiz_id = test_data["quiz_id"]
    foreign_company_id = uuid4()

    mock_quiz = MagicMock()
    mock_quiz.id = quiz_id
    mock_quiz.company_id = foreign_company_id

    mock_uow.quizzes.get_one = AsyncMock(return_value=mock_quiz)
    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock()

    with pytest.raises(QuizNotFoundException):
        await attempt_service.export_attempts(
            export_format="json",
            company_id=company_id,
            quiz_id=quiz_id,
        )

    mock_uow.quiz_attempts.get_attempt_ids_for_export.assert_not_called()


@pytest.mark.asyncio
async def test_export_attempts_quiz_does_not_exist_raises(
    attempt_service, mock_uow, test_data
):
    company_id = test_data["company_id"]
    quiz_id = uuid4()

    mock_uow.quizzes.get_one = AsyncMock(return_value=None)
    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock()

    with pytest.raises(QuizNotFoundException):
        await attempt_service.export_attempts(
            export_format="json",
            company_id=company_id,
            quiz_id=quiz_id,
        )

    mock_uow.quiz_attempts.get_attempt_ids_for_export.assert_not_called()


@pytest.mark.asyncio
async def test_export_attempts_quiz_in_company_succeeds(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    company_id = test_data["company_id"]
    quiz_id = test_data["quiz_id"]

    mock_quiz = MagicMock()
    mock_quiz.id = quiz_id
    mock_quiz.company_id = company_id  # matches

    mock_uow.quizzes.get_one = AsyncMock(return_value=mock_quiz)
    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(return_value=[])
    mock_redis_service.get_quiz_attempts_details = AsyncMock()

    result = await attempt_service.export_attempts(
        export_format="json",
        company_id=company_id,
        quiz_id=quiz_id,
    )

    assert result == []
    mock_uow.quiz_attempts.get_attempt_ids_for_export.assert_awaited_once_with(
        user_id=None, company_id=company_id, quiz_id=quiz_id
    )


@pytest.mark.asyncio
async def test_export_attempts_csv_contains_bom(
    attempt_service, mock_uow, test_data, mock_redis_service
):
    user_id = test_data["user_id"]
    attempt_id = uuid4()

    mock_uow.quiz_attempts.get_attempt_ids_for_export = AsyncMock(
        return_value=[attempt_id]
    )

    mock_redis_data = RedisQuizAttemptDetail(
        attempt_id=attempt_id,
        user_id=user_id,
        company_id=test_data["company_id"],
        quiz_id=test_data["quiz_id"],
        created_at=datetime.now(timezone.utc),
        answers=[
            QuestionDetail(
                question_id=test_data["q1_id"],
                selected_option_ids=[test_data["q1_correct_opt"]],
                is_correct=True,
            )
        ],
    )
    mock_redis_service.get_quiz_attempts_details = AsyncMock(
        return_value=[mock_redis_data]
    )

    mock_uow.questions.get_texts_by_ids = AsyncMock(return_value={})
    mock_uow.answer_options.get_texts_by_ids = AsyncMock(return_value={})
    mock_uow.users.get_emails_by_ids = AsyncMock(return_value={})
    mock_uow.quizzes.get_titles_by_ids = AsyncMock(return_value={})
    mock_uow.companies.get_names_by_ids = AsyncMock(return_value={})

    result = await attempt_service.export_attempts(export_format="csv", user_id=user_id)

    assert result.startswith("\ufeff")
    assert "Date,User Email,Company Name,Quiz Title" in result
