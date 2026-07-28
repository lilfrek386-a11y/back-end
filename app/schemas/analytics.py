from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UserQuizAverageResponse(BaseModel):
    quiz_id: UUID
    title: str
    average_score: float


class UserLastAttemptResponse(BaseModel):
    quiz_id: UUID
    title: str
    last_attempt_at: datetime


class WeeklyTrendPoint(BaseModel):
    week_start: datetime
    average_score: float


class MemberWeeklyAnalytics(BaseModel):
    user_id: UUID
    email: str
    trends: list[WeeklyTrendPoint]


class QuizWeeklyAnalytics(BaseModel):
    quiz_id: UUID
    title: str
    trends: list[WeeklyTrendPoint]


class CompanyMemberLastAttempt(BaseModel):
    user_id: UUID
    email: str
    last_attempt_at: datetime | None
