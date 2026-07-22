import logging
from uuid import UUID

from app.schemas.quiz_attempt import QuizSubmission, QuizAttemptResponse
from app.schemas.redis import RedisQuizAttemptDetail, QuestionDetail
from app.services.redis import RedisService
from app.utils.uow import UnitOfWork
from app.core.exceptions import QuizNotFoundException, NotEnoughPermissionsException

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
