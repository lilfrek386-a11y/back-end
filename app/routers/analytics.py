from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, status

from app.schemas.analytics import (
    UserQuizAverageResponse,
    UserLastAttemptResponse,
    MemberWeeklyAnalytics,
    QuizWeeklyAnalytics,
    CompanyMemberLastAttempt,
)
from app.schemas.quiz_attempt import AverageScoreResponse
from app.dependencies.auth import CurrentUser
from app.dependencies.analytics import AnalyticsService

router = APIRouter(tags=["Analytics"])


@router.get(
    "/users/me/analytics/overall-average",
    response_model=AverageScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's overall average score across all companies",
)
async def get_my_overall_average(
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
):
    score = await analytics_service.get_user_overall_average(current_user.id)
    return AverageScoreResponse(average_score=score)


@router.get(
    "/users/me/analytics/quizzes",
    response_model=list[UserQuizAverageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get average score per quiz for the current user, optionally filtered by date range",
)
async def get_my_quizzes_analytics(
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    return await analytics_service.get_user_quizzes_averages(
        current_user.id, date_from=date_from, date_to=date_to
    )


@router.get(
    "/users/me/analytics/recent",
    response_model=list[UserLastAttemptResponse],
    status_code=status.HTTP_200_OK,
    summary="Get last completion timestamp per quiz for the current user",
)
async def get_my_recent_attempts(
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
):
    return await analytics_service.get_user_recent_attempts(current_user.id)


@router.get(
    "/companies/{company_id}/analytics/members",
    response_model=list[MemberWeeklyAnalytics],
    status_code=status.HTTP_200_OK,
    summary="Get weekly average score trends for all company members (Owners/Admins)",
)
async def get_company_members_analytics(
    company_id: UUID,
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
):
    return await analytics_service.get_company_members_trends(
        company_id, current_user.id
    )


@router.get(
    "/companies/{company_id}/analytics/members/{target_user_id}",
    response_model=list[QuizWeeklyAnalytics],
    status_code=status.HTTP_200_OK,
    summary="Get weekly average score trends per quiz for a specific company member (Owners/Admins)",
)
async def get_company_member_detailed_analytics(
    company_id: UUID,
    target_user_id: UUID,
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
):
    return await analytics_service.get_company_user_detailed_trends(
        company_id=company_id,
        target_user_id=target_user_id,
        current_user_id=current_user.id,
    )


@router.get(
    "/companies/{company_id}/analytics/recent",
    response_model=list[CompanyMemberLastAttempt],
    status_code=status.HTTP_200_OK,
    summary="List all company members with the timestamp of their last quiz attempt (Owners/Admins)",
)
async def get_company_recent_attempts(
    company_id: UUID,
    current_user: CurrentUser,
    analytics_service: AnalyticsService,
):
    return await analytics_service.get_company_recent_attempts(
        company_id, current_user.id
    )
