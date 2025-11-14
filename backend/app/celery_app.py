"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "catchcore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

# Configure task routes for priority and concurrency control
celery_app.conf.task_routes = {
    "app.services.scan_service.*": {"queue": "scans", "routing_key": "scan.#"},
    "app.services.port_scan_service.*": {"queue": "scans", "routing_key": "scan.port"},
    "app.services.service_identify_service.*": {"queue": "scans", "routing_key": "scan.service"},
    "app.services.fingerprint_service.*": {"queue": "scans", "routing_key": "scan.fingerprint"},
}

# Configure task priorities
celery_app.conf.task_default_priority = 5  # Default priority 1-10
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "tasks"
celery_app.conf.task_default_routing_key = "task.default"

# Configure queues
celery_app.conf.task_queues = (
    {
        "name": "default",
        "exchange": "tasks",
        "routing_key": "task.default",
    },
    {
        "name": "scans",
        "exchange": "scans",
        "routing_key": "scan.#",
        "priority": 10,
    },
)

# Configure periodic tasks (beat scheduler)
celery_app.conf.beat_schedule = {
    # Clean up old task results every hour
    "cleanup-results": {
        "task": "app.services.maintenance.cleanup_old_results",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Update task statuses from Redis every 30 seconds
    "sync-task-status": {
        "task": "app.services.maintenance.sync_task_status",
        "schedule": 30.0,  # Every 30 seconds
    },
}

# Task options
celery_app.conf.task_acks_late = True  # Acknowledge task only after execution
celery_app.conf.worker_prefetch_multiplier = 1  # Don't prefetch tasks
celery_app.conf.task_reject_on_worker_lost = True  # Reject task if worker dies


__all__ = ["celery_app"]
