from uuid import UUID

from fastapi import APIRouter, status, BackgroundTasks

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
    QuizzesResponseList,
)
from app.dependencies.quiz import QuizService
from app.dependencies.auth import CurrentUser
from app.dependencies.pagination import SkipQuery, LimitQuery

router = APIRouter(tags=["Quizzes"])


@router.post(
    "/companies/{company_id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new quiz in a company",
)
async def create_quiz(
    company_id: UUID,
    quiz_data: QuizCreate,
    current_user: CurrentUser,
    service: QuizService,
    background_tasks: BackgroundTasks,
):
    return await service.create_quiz(
        user_id=current_user.id,
        company_id=company_id,
        quiz_data=quiz_data,
        background_tasks=background_tasks,
    )


@router.get(
    "/companies/{company_id}/quizzes",
    response_model=QuizzesResponseList,
    status_code=status.HTTP_200_OK,
    summary="Get multi quizzes for a company",
)
async def get_company_quizzes(
    company_id: UUID,
    current_user: CurrentUser,
    skip: SkipQuery,
    limit: LimitQuery,
    service: QuizService,
):
    return await service.get_all_by_company(
        company_id=company_id, skip=skip, limit=limit
    )


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific quiz",
)
async def get_quiz(
    quiz_id: UUID,
    current_user: CurrentUser,
    service: QuizService,
):
    return await service.get_quiz_by_id(quiz_id=quiz_id)


@router.put(
    "/quizzes/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Update quiz details (title, description)",
)
async def update_quiz(
    quiz_id: UUID,
    quiz_data: QuizUpdate,
    current_user: CurrentUser,
    service: QuizService,
):
    return await service.update_quiz(
        user_id=current_user.id, quiz_id=quiz_id, quiz_data=quiz_data
    )


@router.delete(
    "/quizzes/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a quiz completely",
)
async def delete_quiz(
    quiz_id: UUID,
    current_user: CurrentUser,
    service: QuizService,
):
    await service.delete_quiz(user_id=current_user.id, quiz_id=quiz_id)
