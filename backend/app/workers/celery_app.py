import os
from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize Celery app
celery_app = Celery(
    "vixenbliss",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Example: Clean up old data every day at 2 AM
    "cleanup-old-data": {
        "task": "app.workers.tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),
    },
    # Example: Update avatar statistics every hour
    "update-avatar-stats": {
        "task": "app.workers.tasks.update_avatar_statistics",
        "schedule": crontab(minute=0),  # Every hour
    },
}

if __name__ == "__main__":
    celery_app.start()
