import logging
from uuid import UUID

from app.schemas.quiz_attempt import QuizSubmission, QuizAttemptResponse
from app.utils.uow import UnitOfWork
from app.core.exceptions import QuizNotFoundException, NotEnoughPermissionsException

logger = logging.getLogger(__name__)


class QuizAttemptService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def submit_test(
        self, user_id: UUID, quiz_id: UUID, submission: QuizSubmission
    ) -> QuizAttemptResponse:
        logger.info(
            f"Attempting to submit test for quiz ID: {quiz_id} by user ID: {user_id}"
        )
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

            for question in quiz.questions:
                correct_option_ids = {
                    option.id for option in question.answer_options if option.is_correct
                }
                user_selected_ids = submitted_answers_map.get(question.id, set())

                if correct_option_ids == user_selected_ids:
                    correct_answers_count += 1

            quiz.participation_frequency += 1

            attempt_data = {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "company_id": quiz.company_id,
                "correct_answers_count": correct_answers_count,
                "total_questions_count": total_questions_count,
            }

            quiz_attempt = await self.uow.quiz_attempts.create(attempt_data)

            logger.info(
                f"Successfully submitted test for quiz ID: {quiz_id} by user ID: {user_id}. "
                f"Score: {correct_answers_count}/{total_questions_count}"
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
