import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "modelops_worker",
    broker=broker_url,
    backend=result_backend,
    include=[
        "apps.worker.app.tasks.training_tasks",
        "apps.worker.app.tasks.batch_inference_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=1800,       # 30 minute hard limit
    task_soft_time_limit=1500,  # 25 minute soft limit
    broker_connection_retry_on_startup=True,
)
