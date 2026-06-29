from uuid import UUID
from datetime import datetime
from collections import defaultdict

from app.utils.uow import UnitOfWork
from app.schemas.analytics import (
    UserQuizAverageResponse,
    UserLastAttemptResponse,
    WeeklyTrendPoint,
    MemberWeeklyAnalytics,
    QuizWeeklyAnalytics,
    CompanyMemberLastAttempt,
)
from app.services.utils import check_company_admin_or_owner


class AnalyticsService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # Analytics: user-specific

    async def get_user_overall_average(self, user_id: UUID) -> float:
        async with self.uow:
            return await self.uow.quiz_attempts.get_average_score(user_id)

    async def get_user_quizzes_averages(
        self,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[UserQuizAverageResponse]:
        async with self.uow:
            rows = await self.uow.quiz_attempts.get_user_quiz_averages(
                user_id=user_id, date_from=date_from, date_to=date_to
            )
            return [
                UserQuizAverageResponse(
                    quiz_id=row[0], title=row[1], average_score=row[2]
                )
                for row in rows
            ]

    async def get_user_recent_attempts(
        self, user_id: UUID
    ) -> list[UserLastAttemptResponse]:
        async with self.uow:
            rows = await self.uow.quiz_attempts.get_user_last_attempts(user_id=user_id)
            return [
                UserLastAttemptResponse(
                    quiz_id=row[0], title=row[1], last_attempt_at=row[2]
                )
                for row in rows
            ]

    # Analytics: company-specific

    async def get_company_members_trends(
        self, company_id: UUID, current_user_id: UUID
    ) -> list[MemberWeeklyAnalytics]:
        async with self.uow:
            await check_company_admin_or_owner(self.uow, company_id, current_user_id)
            rows = await self.uow.quiz_attempts.get_company_members_weekly_scores(
                company_id
            )

        emails: dict[UUID, str] = {}
        trends_by_user: dict[UUID, list[WeeklyTrendPoint]] = defaultdict(list)

        for user_id, email, week_start, avg_score in rows:
            emails[user_id] = email
            trends_by_user[user_id].append(
                WeeklyTrendPoint(week_start=week_start, average_score=avg_score)
            )

        return [
            MemberWeeklyAnalytics(user_id=uid, email=emails[uid], trends=trends)
            for uid, trends in trends_by_user.items()
        ]

    async def get_company_user_detailed_trends(
        self, company_id: UUID, target_user_id: UUID, current_user_id: UUID
    ) -> list[QuizWeeklyAnalytics]:
        async with self.uow:
            await check_company_admin_or_owner(self.uow, company_id, current_user_id)
            rows = await self.uow.quiz_attempts.get_user_quiz_weekly_scores(
                company_id, target_user_id
            )

        titles: dict[UUID, str] = {}
        trends_by_quiz: dict[UUID, list[WeeklyTrendPoint]] = defaultdict(list)

        for quiz_id, title, week_start, avg_score in rows:
            titles[quiz_id] = title
            trends_by_quiz[quiz_id].append(
                WeeklyTrendPoint(week_start=week_start, average_score=avg_score)
            )

        return [
            QuizWeeklyAnalytics(quiz_id=qid, title=titles[qid], trends=trends)
            for qid, trends in trends_by_quiz.items()
        ]

    async def get_company_recent_attempts(
        self, company_id: UUID, current_user_id: UUID
    ) -> list[CompanyMemberLastAttempt]:
        async with self.uow:
            await check_company_admin_or_owner(self.uow, company_id, current_user_id)
            rows = await self.uow.quiz_attempts.get_company_last_attempts(company_id)

            return [
                CompanyMemberLastAttempt(
                    user_id=row[0], email=row[1], last_attempt_at=row[2]
                )
                for row in rows
            ]
