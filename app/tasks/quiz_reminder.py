import asyncio
from datetime import datetime, timezone, timedelta
from app.core.celery import celery_app
from app.utils.uow import UnitOfWork


@celery_app.task
def check_quiz_completions():
    asyncio.run(_check_quiz_completions())


async def _check_quiz_completions():
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with UnitOfWork() as uow:
        companies, _ = await uow.companies.get_all()

        for company in companies:
            quizzes, _ = await uow.quizzes.get_all_by_company(company.id)
            members, _ = await uow.company_members.get_company_members(company.id)

            if not quizzes or not members:
                continue

            for member in members:
                last_attempts = await uow.quiz_attempts.get_user_last_attempts(
                    member.user_id
                )
                last_attempts_map = {row[0]: row[2] for row in last_attempts}

                for quiz in quizzes:
                    last_attempt_at = last_attempts_map.get(quiz.id)

                    if last_attempt_at is None or (
                        now - last_attempt_at > timedelta(hours=24)
                    ):
                        await uow.notifications.create(
                            {
                                "user_id": member.user_id,
                                "message": f"Don't forget to complete quiz '{quiz.title}'!",
                            }
                        )
