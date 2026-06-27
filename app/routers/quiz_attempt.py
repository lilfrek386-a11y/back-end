from typing import Literal
from uuid import UUID

from fastapi import APIRouter, status, Response

from app.dependencies.auth import CurrentUser
from app.dependencies.quiz_attempt import QuizAttemptService
from app.dependencies.company_owner import RequireCompanyOwnerOrAdmin
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


@router.get(
    "/users/me/export",
    status_code=status.HTTP_200_OK,
    summary="Export current user's quiz attempts",
)
async def export_my_attempts(
    export_format: Literal["json", "csv"],
    current_user: CurrentUser,
    service: QuizAttemptService,
):
    data = await service.export_attempts(
        export_format=export_format, user_id=current_user.id
    )

    if export_format == "json":
        return data

    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_quiz_attempts.csv"},
    )


@router.get(
    "/companies/{company_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Export company quiz attempts (Owners/Admins)",
)
async def export_company_attempts(
    company_id: UUID,
    export_format: Literal["json", "csv"],
    service: QuizAttemptService,
    _: RequireCompanyOwnerOrAdmin,
    user_id: UUID | None = None,
    quiz_id: UUID | None = None,
):
    data = await service.export_attempts(
        export_format=export_format,
        company_id=company_id,
        user_id=user_id,
        quiz_id=quiz_id,
    )

    if export_format == "json":
        return data

    return Response(
        content=data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=company_{company_id}_attempts.csv"
        },
    )
