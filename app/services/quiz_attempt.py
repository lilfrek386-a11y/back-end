import csv
import io
import logging
from uuid import UUID

from app.schemas.quiz_attempt import QuizSubmission, QuizAttemptResponse
from app.schemas.redis import RedisQuizAttemptDetail, QuestionDetail
from app.services.redis import RedisService
from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    QuizNotFoundException,
    NotEnoughPermissionsException,
    UnsupportedExportFormatException,
)

logger = logging.getLogger(__name__)


class QuizAttemptService:

    def __init__(self, uow: UnitOfWork, redis_service: RedisService):
        self.uow = uow
        self.redis_service = redis_service

    async def submit_test(
        self, user_id: UUID, quiz_id: UUID, submission: QuizSubmission
    ) -> QuizAttemptResponse:

        async with self.uow:
            quiz = await self.uow.quizzes.get_quiz_with_details(quiz_id)
            if not quiz:
                raise QuizNotFoundException()

            company = await self.uow.companies.get_one(quiz.company_id)
            member = await self.uow.company_members.get_by_company_and_user(
                company_id=quiz.company_id, user_id=user_id
            )

            if company.owner_id != user_id and not member:
                raise NotEnoughPermissionsException()

            correct_answers_count = 0
            total_questions_count = len(quiz.questions)

            submitted_answers_map = {
                answer.question_id: set(answer.selected_option_ids)
                for answer in submission.answers
            }

            redis_answers_detail = []

            for question in quiz.questions:
                correct_option_ids = {
                    option.id for option in question.answer_options if option.is_correct
                }
                user_selected_ids = submitted_answers_map.get(question.id, set())
                is_correct = correct_option_ids == user_selected_ids

                if is_correct:
                    correct_answers_count += 1

                redis_answers_detail.append(
                    QuestionDetail(
                        question_id=question.id,
                        selected_option_ids=list(user_selected_ids),
                        is_correct=is_correct,
                    )
                )

            quiz.participation_frequency += 1

            attempt_data = {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "company_id": quiz.company_id,
                "correct_answers_count": correct_answers_count,
                "total_questions_count": total_questions_count,
            }

            quiz_attempt = await self.uow.quiz_attempts.create(attempt_data)

            redis_payload = RedisQuizAttemptDetail(
                attempt_id=quiz_attempt.id,
                user_id=user_id,
                company_id=quiz.company_id,
                quiz_id=quiz_id,
                created_at=quiz_attempt.created_at,
                answers=redis_answers_detail,
            )

        await self.redis_service.save_quiz_attempt_details(redis_payload)

        logger.info(
            f"[AUDIT] User {user_id} completed Quiz {quiz_id} "
            f"(Attempt ID: {quiz_attempt.id}). Score: {correct_answers_count}/{total_questions_count}"
        )
        return QuizAttemptResponse.model_validate(quiz_attempt)

    async def get_user_system_average(self, user_id: UUID) -> float:
        async with self.uow:
            return await self.uow.quiz_attempts.get_average_score(user_id=user_id)

    async def get_user_company_average(self, user_id: UUID, company_id: UUID) -> float:
        async with self.uow:
            return await self.uow.quiz_attempts.get_average_score(
                user_id=user_id, company_id=company_id
            )

    async def export_attempts(
        self,
        export_format: str,
        user_id: UUID | None = None,
        company_id: UUID | None = None,
        quiz_id: UUID | None = None,
    ) -> list[RedisQuizAttemptDetail] | str:

        async with self.uow:
            if company_id is not None and quiz_id is not None:
                quiz = await self.uow.quizzes.get_one(quiz_id)
                if not quiz or quiz.company_id != company_id:
                    raise QuizNotFoundException()

            attempt_ids: list[UUID] = (
                await self.uow.quiz_attempts.get_attempt_ids_for_export(
                    user_id=user_id,
                    company_id=company_id,
                    quiz_id=quiz_id,
                )
            )

        if not attempt_ids:
            return [] if export_format == "json" else ""

        attempts_data: list[RedisQuizAttemptDetail] = (
            await self.redis_service.get_quiz_attempts_details(attempt_ids=attempt_ids)
        )

        if export_format == "json":
            return attempts_data

        if export_format == "csv":
            question_ids = {
                a.question_id for attempt in attempts_data for a in attempt.answers
            }
            option_ids = {
                opt
                for attempt in attempts_data
                for a in attempt.answers
                for opt in a.selected_option_ids
            }
            user_ids = {attempt.user_id for attempt in attempts_data}
            quiz_ids = {attempt.quiz_id for attempt in attempts_data}
            company_ids = {attempt.company_id for attempt in attempts_data}

            async with self.uow:
                questions_map = await self.uow.questions.get_texts_by_ids(question_ids)
                options_map = await self.uow.answer_options.get_texts_by_ids(option_ids)
                users_map = await self.uow.users.get_emails_by_ids(user_ids)
                quizzes_map = await self.uow.quizzes.get_titles_by_ids(quiz_ids)
                companies_map = await self.uow.companies.get_names_by_ids(company_ids)

            output = io.StringIO()
            output.write("\ufeff")
            writer = csv.writer(output)
            writer.writerow(
                [
                    "Date",
                    "User Email",
                    "Company Name",
                    "Quiz Title",
                    "Question",
                    "Selected Answer",
                    "Is Correct",
                ]
            )

            for attempt in attempts_data:
                for answer in attempt.answers:
                    writer.writerow(
                        [
                            attempt.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                            users_map.get(attempt.user_id, str(attempt.user_id)),
                            companies_map.get(
                                attempt.company_id, str(attempt.company_id)
                            ),
                            quizzes_map.get(attempt.quiz_id, str(attempt.quiz_id)),
                            questions_map.get(
                                answer.question_id, str(answer.question_id)
                            ),
                            " | ".join(
                                options_map.get(opt, str(opt))
                                for opt in answer.selected_option_ids
                            ),
                            answer.is_correct,
                        ]
                    )

            return output.getvalue()

        raise UnsupportedExportFormatException(export_format)
