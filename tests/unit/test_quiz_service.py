import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.quiz import QuizService
from app.schemas.quiz import QuizCreate, QuizUpdate
from app.schemas.question import QuestionCreate
from app.models.quiz import Quiz
from app.models.company import Company
from app.models.company_member import CompanyMember, CompanyMemberRole
from app.core.exceptions import (
    CompanyNotFoundException,
    QuizNotFoundException,
    NotEnoughPermissionsException,
)


@pytest.fixture
def quiz_service(mock_uow):
    return QuizService(mock_uow)


@pytest.fixture
def base_uuids():
    return {
        "user_id": uuid4(),
        "company_id": uuid4(),
        "quiz_id": uuid4(),
    }


@pytest.fixture
def valid_quiz_data():
    return QuizCreate(
        title="Python Basics",
        description="A quiz about Python fundamentals",
        questions=[
            QuestionCreate(
                title="What is a list?",
                answer_options=[
                    {"text": "A mutable sequence", "is_correct": True},
                    {"text": "An immutable sequence", "is_correct": False},
                ],
            ),
            QuestionCreate(
                title="What is a tuple?",
                answer_options=[
                    {"text": "A mutable sequence", "is_correct": False},
                    {"text": "An immutable sequence", "is_correct": True},
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_create_quiz_success_as_owner(
    quiz_service, mock_uow, base_uuids, valid_quiz_data
):
    user_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]

    mock_company = Company(id=company_id, owner_id=user_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = uuid4()
    mock_quiz.title = valid_quiz_data.title
    mock_quiz.description = valid_quiz_data.description
    mock_quiz.company_id = company_id
    mock_quiz.participation_frequency = 0
    mock_quiz.questions = []

    mock_uow.quizzes.create_quiz = AsyncMock(return_value=mock_quiz)

    result = await quiz_service.create_quiz(
        user_id=user_id, company_id=company_id, quiz_data=valid_quiz_data
    )

    mock_uow.quizzes.create_quiz.assert_awaited_once()
    assert result.title == "Python Basics"


@pytest.mark.asyncio
async def test_create_quiz_success_as_admin(
    quiz_service, mock_uow, base_uuids, valid_quiz_data
):
    user_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = uuid4()

    mock_company = Company(id=company_id, owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.ADMIN
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = uuid4()
    mock_quiz.title = valid_quiz_data.title
    mock_quiz.description = valid_quiz_data.description
    mock_quiz.company_id = company_id
    mock_quiz.participation_frequency = 0
    mock_quiz.questions = []

    mock_uow.quizzes.create_quiz = AsyncMock(return_value=mock_quiz)

    result = await quiz_service.create_quiz(
        user_id=user_id, company_id=company_id, quiz_data=valid_quiz_data
    )

    assert result.title == "Python Basics"


@pytest.mark.asyncio
async def test_create_quiz_company_not_found(
    quiz_service, mock_uow, base_uuids, valid_quiz_data
):
    user_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]

    mock_uow.companies.get_one = AsyncMock(return_value=None)

    with pytest.raises(CompanyNotFoundException):
        await quiz_service.create_quiz(
            user_id=user_id, company_id=company_id, quiz_data=valid_quiz_data
        )


@pytest.mark.asyncio
async def test_create_quiz_member_without_admin_role_raises(
    quiz_service, mock_uow, base_uuids, valid_quiz_data
):
    user_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = uuid4()

    mock_company = Company(id=company_id, owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_member = CompanyMember(
        company_id=company_id, user_id=user_id, role=CompanyMemberRole.MEMBER
    )
    mock_uow.company_members.get_by_company_and_user = AsyncMock(
        return_value=mock_member
    )

    with pytest.raises(NotEnoughPermissionsException):
        await quiz_service.create_quiz(
            user_id=user_id, company_id=company_id, quiz_data=valid_quiz_data
        )


@pytest.mark.asyncio
async def test_create_quiz_not_a_member_raises(
    quiz_service, mock_uow, base_uuids, valid_quiz_data
):
    user_id = base_uuids["user_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = uuid4()

    mock_company = Company(id=company_id, owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    with pytest.raises(NotEnoughPermissionsException):
        await quiz_service.create_quiz(
            user_id=user_id, company_id=company_id, quiz_data=valid_quiz_data
        )


@pytest.mark.asyncio
async def test_get_quiz_by_id_success(quiz_service, mock_uow, base_uuids):
    quiz_id = base_uuids["quiz_id"]

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = quiz_id
    mock_quiz.title = "Found Quiz"
    mock_quiz.description = "Desc"
    mock_quiz.company_id = base_uuids["company_id"]
    mock_quiz.participation_frequency = 0
    mock_quiz.questions = []

    mock_uow.quizzes.get_quiz_with_details = AsyncMock(return_value=mock_quiz)

    result = await quiz_service.get_quiz_by_id(quiz_id)

    assert result.id == quiz_id
    assert result.title == "Found Quiz"


@pytest.mark.asyncio
async def test_get_quiz_by_id_not_found(quiz_service, mock_uow, base_uuids):
    quiz_id = base_uuids["quiz_id"]
    mock_uow.quizzes.get_quiz_with_details = AsyncMock(return_value=None)

    with pytest.raises(QuizNotFoundException):
        await quiz_service.get_quiz_by_id(quiz_id)


@pytest.mark.asyncio
async def test_get_all_by_company_success(quiz_service, mock_uow, base_uuids):
    company_id = base_uuids["company_id"]

    mock_company = Company(id=company_id, owner_id=uuid4())
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = uuid4()
    mock_quiz.title = "Quiz 1"
    mock_quiz.description = "Desc"
    mock_quiz.company_id = company_id
    mock_quiz.participation_frequency = 0
    mock_quiz.questions = []

    mock_uow.quizzes.get_all_by_company = AsyncMock(return_value=([mock_quiz], 1))

    result = await quiz_service.get_all_by_company(company_id, skip=0, limit=100)

    assert result.total_count == 1
    assert len(result.quizzes) == 1


@pytest.mark.asyncio
async def test_get_all_by_company_not_found(quiz_service, mock_uow, base_uuids):
    company_id = base_uuids["company_id"]
    mock_uow.companies.get_one = AsyncMock(return_value=None)

    with pytest.raises(CompanyNotFoundException):
        await quiz_service.get_all_by_company(company_id)


@pytest.mark.asyncio
async def test_update_quiz_success(quiz_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]
    quiz_id = base_uuids["quiz_id"]
    company_id = base_uuids["company_id"]

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = quiz_id
    mock_quiz.company_id = company_id
    mock_uow.quizzes.get_one = AsyncMock(return_value=mock_quiz)

    mock_company = Company(id=company_id, owner_id=user_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_updated_quiz = MagicMock(spec=Quiz)
    mock_updated_quiz.id = quiz_id
    mock_updated_quiz.title = "New Title"
    mock_updated_quiz.description = "Desc"
    mock_updated_quiz.company_id = company_id
    mock_updated_quiz.participation_frequency = 0
    mock_updated_quiz.questions = []
    mock_uow.quizzes.update = AsyncMock(return_value=mock_updated_quiz)

    quiz_data = QuizUpdate(title="New Title")
    result = await quiz_service.update_quiz(
        user_id=user_id, quiz_id=quiz_id, quiz_data=quiz_data
    )

    assert result.title == "New Title"
    mock_uow.quizzes.update.assert_awaited_once_with(mock_quiz, {"title": "New Title"})


@pytest.mark.asyncio
async def test_update_quiz_not_found(quiz_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]
    quiz_id = base_uuids["quiz_id"]

    mock_uow.quizzes.get_one = AsyncMock(return_value=None)

    with pytest.raises(QuizNotFoundException):
        await quiz_service.update_quiz(
            user_id=user_id, quiz_id=quiz_id, quiz_data=QuizUpdate(title="New")
        )


@pytest.mark.asyncio
async def test_update_quiz_no_permissions_raises(quiz_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]
    quiz_id = base_uuids["quiz_id"]
    company_id = base_uuids["company_id"]
    real_owner_id = uuid4()

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = quiz_id
    mock_quiz.company_id = company_id
    mock_uow.quizzes.get_one = AsyncMock(return_value=mock_quiz)

    mock_company = Company(id=company_id, owner_id=real_owner_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.company_members.get_by_company_and_user = AsyncMock(return_value=None)

    with pytest.raises(NotEnoughPermissionsException):
        await quiz_service.update_quiz(
            user_id=user_id, quiz_id=quiz_id, quiz_data=QuizUpdate(title="New")
        )


@pytest.mark.asyncio
async def test_delete_quiz_success(quiz_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]
    quiz_id = base_uuids["quiz_id"]
    company_id = base_uuids["company_id"]

    mock_quiz = MagicMock(spec=Quiz)
    mock_quiz.id = quiz_id
    mock_quiz.company_id = company_id
    mock_uow.quizzes.get_one = AsyncMock(return_value=mock_quiz)

    mock_company = Company(id=company_id, owner_id=user_id)
    mock_uow.companies.get_one = AsyncMock(return_value=mock_company)

    mock_uow.quizzes.delete = AsyncMock()

    await quiz_service.delete_quiz(user_id=user_id, quiz_id=quiz_id)

    mock_uow.quizzes.delete.assert_awaited_once_with(mock_quiz)


@pytest.mark.asyncio
async def test_delete_quiz_not_found(quiz_service, mock_uow, base_uuids):
    user_id = base_uuids["user_id"]
    quiz_id = base_uuids["quiz_id"]

    mock_uow.quizzes.get_one = AsyncMock(return_value=None)

    with pytest.raises(QuizNotFoundException):
        await quiz_service.delete_quiz(user_id=user_id, quiz_id=quiz_id)
