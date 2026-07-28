import logging
from datetime import datetime, timezone, timedelta

from app.utils.uow import UnitOfWork

logger = logging.getLogger(__name__)


class QuizReminderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def notify_users_about_uncompleted_quizzes(self) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        async with self.uow:
            companies, _ = await self.uow.companies.get_all()

            for company in companies:
                quizzes, _ = await self.uow.quizzes.get_all_by_company(company.id)
                members, _ = await self.uow.company_members.get_company_members(
                    company.id
                )

                if not quizzes or not members:
                    continue

                for member in members:
                    last_attempts = await self.uow.quiz_attempts.get_user_last_attempts(
                        member.user_id
                    )
                    last_attempts_map = {row[0]: row[2] for row in last_attempts}

                    for quiz in quizzes:
                        last_attempt_at = last_attempts_map.get(quiz.id)
                        if last_attempt_at is None or (
                            now - last_attempt_at > timedelta(hours=24)
                        ):
                            await self.uow.notifications.create(
                                {
                                    "user_id": member.user_id,
                                    "message": f"Don't forget to complete quiz '{quiz.title}'!",
                                }
                            )

        logger.info("Finished checking uncompleted quizzes.")
