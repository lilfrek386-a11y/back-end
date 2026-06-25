import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from redis.exceptions import ConnectionError

from app.services.redis import RedisService
from app.schemas.redis import RedisQuizAttemptDetail, QuestionDetail


@pytest.fixture
def mock_redis_client():
    client = MagicMock()
    client.set = AsyncMock()
    return client


@pytest.fixture
def redis_service(mock_redis_client):
    return RedisService(redis=mock_redis_client, ttl_seconds=172800)


@pytest.fixture
def valid_quiz_details():
    return RedisQuizAttemptDetail(
        attempt_id=uuid4(),
        user_id=uuid4(),
        company_id=uuid4(),
        quiz_id=uuid4(),
        answers=[
            QuestionDetail(
                question_id=uuid4(), selected_option_ids=[uuid4()], is_correct=True
            )
        ],
    )


@pytest.mark.asyncio
async def test_save_quiz_attempt_details_success(
    redis_service, mock_redis_client, valid_quiz_details
):
    await redis_service.save_quiz_attempt_details(valid_quiz_details)

    expected_key = f"quiz_attempt:{valid_quiz_details.attempt_id}"
    expected_value = valid_quiz_details.model_dump_json()

    mock_redis_client.set.assert_awaited_once_with(
        name=expected_key, value=expected_value, ex=172800
    )


@pytest.mark.asyncio
async def test_save_quiz_attempt_details_custom_ttl(
    mock_redis_client, valid_quiz_details
):
    custom_ttl = 3600
    custom_service = RedisService(redis=mock_redis_client, ttl_seconds=custom_ttl)

    await custom_service.save_quiz_attempt_details(valid_quiz_details)

    expected_key = f"quiz_attempt:{valid_quiz_details.attempt_id}"
    expected_value = valid_quiz_details.model_dump_json()

    mock_redis_client.set.assert_awaited_once_with(
        name=expected_key, value=expected_value, ex=custom_ttl
    )


@pytest.mark.asyncio
async def test_save_quiz_attempt_details_connection_error(
    redis_service, mock_redis_client, valid_quiz_details
):
    mock_redis_client.set.side_effect = ConnectionError("Redis server is unreachable")

    with pytest.raises(ConnectionError, match="Redis server is unreachable"):
        await redis_service.save_quiz_attempt_details(valid_quiz_details)
