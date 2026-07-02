from os import getenv

from celery import Celery


celery_app = Celery(
    "waybills",
    broker=getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=getenv("REDIS_URL", "redis://localhost:6379/0"),
)


@celery_app.task
def backup_database() -> str:
    return "Backup task placeholder: connect pg_dump or object storage here."

