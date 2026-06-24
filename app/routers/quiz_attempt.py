from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUser
from app.dependencies.quiz_attempt import QuizAttemptService
from app.schemas.quiz_attempt import (
    QuizSubmission,
    QuizAttemptResponse,
    AverageScoreResponse,
)

router = APIRouter(tags=["Quiz Attempts & Analytics"])


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit quiz answers and get the result",
)
async def submit_quiz(
    quiz_id: UUID,
    submission: QuizSubmission,
    current_user: CurrentUser,
    service: QuizAttemptService,
):
    return await service.submit_test(
        user_id=current_user.id, quiz_id=quiz_id, submission=submission
    )


@router.get(
    "/users/me/analytics/average-score",
    response_model=AverageScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's overall average score across all companies (System wide)",
)
async def get_system_average_score(
    current_user: CurrentUser,
    service: QuizAttemptService,
):
    score = await service.get_user_system_average(user_id=current_user.id)
    return AverageScoreResponse(average_score=score)


@router.get(
    "/companies/{company_id}/users/me/analytics/average-score",
    response_model=AverageScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's average score within a specific company",
)
async def get_company_average_score(
    company_id: UUID,
    current_user: CurrentUser,
    service: QuizAttemptService,
):
    score = await service.get_user_company_average(
        user_id=current_user.id, company_id=company_id
    )
    return AverageScoreResponse(average_score=score)
