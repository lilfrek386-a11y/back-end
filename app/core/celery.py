from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "backend",
    broker=f"redis://{settings.redis.HOST}:{settings.redis.PORT}/0",
    backend=f"redis://{settings.redis.HOST}:{settings.redis.PORT}/0",
    include=["app.tasks.quiz_reminder"],
)

celery_app.conf.beat_schedule = {
    "check-quiz-completions-daily": {
        "task": "app.tasks.quiz_reminder.check_quiz_completions",
        "schedule": crontab(hour=0, minute=0),
    }
}

celery_app.conf.timezone = "UTC"
