from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from crypto_prices.db.base import Base


class PriceRecord(Base):
    __tablename__ = "price_records"
    __table_args__ = (
        CheckConstraint("ticker IN ('btc_usd', 'eth_usd')", name="ck_price_records_ticker"),
        CheckConstraint("price > 0", name="ck_price_records_price_positive"),
        Index("ix_price_records_ticker_timestamp", "ticker", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(30, 10), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    def __repr__(self) -> str:
        return (
            f"PriceRecord(id={self.id!r}, ticker={self.ticker!r}, price={self.price!r},"
            f" timestamp={self.timestamp!r})"
        )
