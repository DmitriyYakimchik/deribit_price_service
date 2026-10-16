from celery import Celery

from crypto_prices.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "crypto_prices",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["crypto_prices.tasks.collect_prices"],
)
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "collect-deribit-index-prices": {
            "task": "crypto_prices.collect_prices",
            "schedule": settings.price_collection_interval_seconds,
        }
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
