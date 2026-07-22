import asyncio
from app.core.celery import celery_app
from app.core.postgres import engine
from app.utils.uow import UnitOfWork
from app.services.quiz_reminder import QuizReminderService
from functools import wraps


def celery_async_task(coro_func):
    @wraps(coro_func)
    def wrapper(*args, **kwargs):
        async def runner():
            try:
                await coro_func(*args, **kwargs)
            finally:
                await engine.dispose()

        asyncio.run(runner())

    return wrapper


@celery_app.task
@celery_async_task
async def check_quiz_completions():
    uow = UnitOfWork()
    service = QuizReminderService(uow=uow)
    await service.notify_users_about_uncompleted_quizzes()
