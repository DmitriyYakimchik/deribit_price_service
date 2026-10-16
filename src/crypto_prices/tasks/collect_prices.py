import asyncio
import logging
from decimal import Decimal

from celery import Task, shared_task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from crypto_prices.clients.deribit import DeribitClient
from crypto_prices.core.config import get_settings
from crypto_prices.db.session import build_engine, build_session_factory
from crypto_prices.repositories.prices import PriceRepository
from crypto_prices.services.prices import PriceCollectionService

logger = logging.getLogger(__name__)


async def _collect_prices() -> dict[str, str]:
    engine = build_engine()
    session_factory: async_sessionmaker[AsyncSession] = build_session_factory(engine)

    async def save_price(ticker: str, price: Decimal, timestamp: int) -> None:
        async with session_factory() as session:
            await PriceRepository(session).create(ticker, price, timestamp)
            await session.commit()

    try:
        async with DeribitClient() as client:
            service = PriceCollectionService(client, save_price)
            return await service.collect()
    finally:
        await engine.dispose()


@shared_task(  # type: ignore[untyped-decorator]
    name="crypto_prices.collect_prices",
    bind=True,
    max_retries=get_settings().collection_retry_attempts,
)
def collect_prices_task(self: Task) -> dict[str, str]:
    try:
        return asyncio.run(_collect_prices())
    except Exception as exc:
        logger.exception("Unexpected failure in price collection task")
        raise self.retry(
            exc=exc,
            countdown=get_settings().collection_retry_delay_seconds,
        ) from exc
