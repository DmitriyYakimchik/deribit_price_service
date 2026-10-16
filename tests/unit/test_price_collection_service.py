from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from crypto_prices.services.prices import PriceCollectionService


class FakeClient:
    """Stub that succeeds for btc_usd and fails for eth_usd."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_index_price(self, ticker: str) -> Decimal:
        self.calls.append(ticker)
        if ticker == "btc_usd":
            return Decimal("65000.25")
        raise RuntimeError("simulated exchange error")


class AlwaysFailingClient:
    async def get_index_price(self, ticker: str) -> Decimal:
        raise RuntimeError(f"boom for {ticker}")


@pytest.mark.asyncio
async def test_collection_saves_successful_ticker_when_other_fails() -> None:
    client = FakeClient()
    save_price = AsyncMock()
    service = PriceCollectionService(client, save_price)  # type: ignore[arg-type]

    results = await service.collect()

    assert results == {"btc_usd": "saved", "eth_usd": "failed"}
    assert client.calls == ["btc_usd", "eth_usd"]
    save_price.assert_awaited_once()

    call = save_price.await_args
    assert call is not None
    assert call.args[0] == "btc_usd"
    assert call.args[1] == Decimal("65000.25")
    assert isinstance(call.args[2], int)


@pytest.mark.asyncio
async def test_collection_marks_every_ticker_failed_when_client_fails() -> None:
    save_price = AsyncMock()
    service = PriceCollectionService(AlwaysFailingClient(), save_price)  # type: ignore[arg-type]

    results = await service.collect()

    assert results == {"btc_usd": "failed", "eth_usd": "failed"}
    save_price.assert_not_awaited()


@pytest.mark.asyncio
async def test_collection_marks_ticker_failed_when_save_raises() -> None:
    client = FakeClient()
    save_price = AsyncMock(side_effect=RuntimeError("db is down"))
    service = PriceCollectionService(client, save_price)  # type: ignore[arg-type]

    results = await service.collect()

    # btc_usd: client ok, save fails -> "failed"
    # eth_usd: client fails -> "failed"
    assert results == {"btc_usd": "failed", "eth_usd": "failed"}
    save_price.assert_awaited_once()
