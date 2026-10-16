from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Ticker = Literal["btc_usd", "eth_usd"]


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: Ticker
    price: Decimal = Field(gt=0)
    timestamp: int = Field(ge=0)
