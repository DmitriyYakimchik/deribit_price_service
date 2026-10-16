import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from decimal import Decimal

from crypto_prices.clients.deribit import DeribitClient
from crypto_prices.core.config import Ticker, get_settings
from crypto_prices.models.price import PriceRecord
from crypto_prices.repositories.prices import PriceRepository

logger = logging.getLogger(__name__)
SavePrice = Callable[[str, Decimal, int], Awaitable[None]]


class PriceService:
    """Read-oriented application service for historical prices."""

    def __init__(self, repository: PriceRepository) -> None:
        self._repository = repository

    async def list_prices(
        self, ticker: Ticker, *, offset: int = 0, limit: int | None = None
    ) -> Sequence[PriceRecord]:
        return await self._repository.list_by_ticker(ticker, offset=offset, limit=limit)

    async def get_latest_price(self, ticker: Ticker) -> PriceRecord | None:
        return await self._repository.get_latest(ticker)

    async def get_price_history(
        self,
        ticker: Ticker,
        *,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> Sequence[PriceRecord]:
        return await self._repository.list_by_timestamp_range(
            ticker,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            offset=offset,
            limit=limit,
        )


class PriceCollectionService:
    """Fetch each supported index independently and persist successful results."""

    def __init__(self, client: DeribitClient, save_price: SavePrice) -> None:
        self._client = client
        self._save_price = save_price
        self._settings = get_settings()

    async def collect(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for ticker in self._settings.supported_tickers:
            try:
                price = await self._client.get_index_price(ticker)
                timestamp = int(time.time())
                await self._save_price(ticker, price, timestamp)
                results[ticker] = "saved"
                logger.info(
                    "Saved index price",
                    extra={"ticker": ticker, "price": str(price), "timestamp": timestamp},
                )
            except Exception:
                logger.exception("Failed to collect or save index price", extra={"ticker": ticker})
                results[ticker] = "failed"
        return results
