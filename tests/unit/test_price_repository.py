from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_prices.models.price import PriceRecord
from crypto_prices.repositories.prices import PriceRepository


@pytest.mark.asyncio
async def test_create_adds_record_and_flushes() -> None:
    session = MagicMock(spec=AsyncSession)
    session.flush = AsyncMock()
    repo = PriceRepository(session)

    record = await repo.create("btc_usd", Decimal("100"), 12345)

    session.add.assert_called_once_with(record)
    session.flush.assert_awaited_once()
    assert isinstance(record, PriceRecord)
    assert record.ticker == "btc_usd"
    assert record.price == Decimal("100")
    assert record.timestamp == 12345


@pytest.mark.asyncio
async def test_list_by_ticker_returns_sequence() -> None:
    session = MagicMock(spec=AsyncSession)
    scalars_result = MagicMock()
    scalars_result.all.return_value = [
        MagicMock(spec=PriceRecord),
        MagicMock(spec=PriceRecord),
    ]
    session.scalars = AsyncMock(return_value=scalars_result)
    repo = PriceRepository(session)

    result = await repo.list_by_ticker("btc_usd", offset=0, limit=10)

    session.scalars.assert_awaited_once()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_latest_returns_none_when_missing() -> None:
    session = MagicMock(spec=AsyncSession)
    scalars_result = MagicMock()
    scalars_result.first.return_value = None
    session.scalars = AsyncMock(return_value=scalars_result)
    repo = PriceRepository(session)

    assert await repo.get_latest("btc_usd") is None


@pytest.mark.asyncio
async def test_get_latest_returns_record_when_present() -> None:
    expected = MagicMock(spec=PriceRecord)
    session = MagicMock(spec=AsyncSession)
    scalars_result = MagicMock()
    scalars_result.first.return_value = expected
    session.scalars = AsyncMock(return_value=scalars_result)
    repo = PriceRepository(session)

    assert await repo.get_latest("btc_usd") is expected


@pytest.mark.asyncio
async def test_list_by_timestamp_range_returns_sequence() -> None:
    session = MagicMock(spec=AsyncSession)
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    session.scalars = AsyncMock(return_value=scalars_result)
    repo = PriceRepository(session)

    result = await repo.list_by_timestamp_range(
        "eth_usd", from_timestamp=100, to_timestamp=200, offset=0, limit=5
    )

    session.scalars.assert_awaited_once()
    assert list(result) == []
