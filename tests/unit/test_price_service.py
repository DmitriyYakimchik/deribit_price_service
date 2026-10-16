from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_prices.services.prices import PriceService


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(repository: MagicMock) -> PriceService:
    return PriceService(repository)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_list_prices_delegates_to_repository(
    service: PriceService, repository: MagicMock
) -> None:
    repository.list_by_ticker = AsyncMock(return_value=[])
    result = await service.list_prices("btc_usd", offset=5, limit=10)
    repository.list_by_ticker.assert_awaited_once_with("btc_usd", offset=5, limit=10)
    assert result == []


@pytest.mark.asyncio
async def test_get_latest_price_returns_none_when_missing(
    service: PriceService, repository: MagicMock
) -> None:
    repository.get_latest = AsyncMock(return_value=None)
    assert await service.get_latest_price("btc_usd") is None
    repository.get_latest.assert_awaited_once_with("btc_usd")


@pytest.mark.asyncio
async def test_get_price_history_forwards_all_filters(
    service: PriceService, repository: MagicMock
) -> None:
    repository.list_by_timestamp_range = AsyncMock(return_value=[])
    await service.get_price_history(
        "eth_usd",
        from_timestamp=100,
        to_timestamp=200,
        offset=0,
        limit=50,
    )
    repository.list_by_timestamp_range.assert_awaited_once_with(
        "eth_usd",
        from_timestamp=100,
        to_timestamp=200,
        offset=0,
        limit=50,
    )


@pytest.mark.asyncio
async def test_get_price_history_accepts_none_filters(
    service: PriceService, repository: MagicMock
) -> None:
    repository.list_by_timestamp_range = AsyncMock(return_value=[])
    await service.get_price_history("btc_usd")
    repository.list_by_timestamp_range.assert_awaited_once_with(
        "btc_usd",
        from_timestamp=None,
        to_timestamp=None,
        offset=0,
        limit=None,
    )
