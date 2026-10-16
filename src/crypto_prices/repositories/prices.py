import logging
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_prices.models.price import PriceRecord

logger = logging.getLogger(__name__)


class PriceRepository:
    """Data-access layer for the price_records table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, ticker: str, price: Decimal, timestamp: int) -> PriceRecord:
        record = PriceRecord(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_by_ticker(
        self,
        ticker: str,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> Sequence[PriceRecord]:
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.ticker == ticker)
            .order_by(PriceRecord.timestamp.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_latest(self, ticker: str) -> PriceRecord | None:
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.ticker == ticker)
            .order_by(PriceRecord.timestamp.desc())
            .limit(1)
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def list_by_timestamp_range(
        self,
        ticker: str,
        *,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> Sequence[PriceRecord]:
        stmt = select(PriceRecord).where(PriceRecord.ticker == ticker)
        if from_timestamp is not None:
            stmt = stmt.where(PriceRecord.timestamp >= from_timestamp)
        if to_timestamp is not None:
            stmt = stmt.where(PriceRecord.timestamp <= to_timestamp)
        stmt = stmt.order_by(PriceRecord.timestamp.desc()).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.scalars(stmt)
        return list(result.all())
