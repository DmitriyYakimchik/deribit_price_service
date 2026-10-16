from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from crypto_prices.api.dependencies import get_price_service
from crypto_prices.core.config import Ticker
from crypto_prices.schemas.price import PriceResponse
from crypto_prices.services.prices import PriceService

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])
ServiceDependency = Annotated[PriceService, Depends(get_price_service)]
TickerQuery = Annotated[Ticker, Query(description="Supported index ticker: btc_usd or eth_usd")]


@router.get("", response_model=list[PriceResponse], summary="Get saved prices for a ticker")
async def list_prices(
    ticker: TickerQuery,
    service: ServiceDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PriceResponse]:
    records = await service.list_prices(ticker, offset=offset, limit=limit)
    return [PriceResponse.model_validate(record) for record in records]


@router.get("/latest", response_model=PriceResponse, summary="Get the latest saved price")
async def latest_price(ticker: TickerQuery, service: ServiceDependency) -> PriceResponse:
    record = await service.get_latest_price(ticker)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No saved price found for ticker '{ticker}'")
    return PriceResponse.model_validate(record)


@router.get(
    "/history", response_model=list[PriceResponse], summary="Get prices filtered by timestamp"
)
async def price_history(
    ticker: TickerQuery,
    service: ServiceDependency,
    from_timestamp: Annotated[
        int | None, Query(ge=0, description="Inclusive lower UNIX timestamp in seconds")
    ] = None,
    to_timestamp: Annotated[
        int | None, Query(ge=0, description="Inclusive upper UNIX timestamp in seconds")
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PriceResponse]:
    if from_timestamp is not None and to_timestamp is not None and from_timestamp > to_timestamp:
        raise HTTPException(
            status_code=422, detail="from_timestamp must be less than or equal to to_timestamp"
        )
    records = await service.get_price_history(
        ticker, from_timestamp=from_timestamp, to_timestamp=to_timestamp, offset=offset, limit=limit
    )
    return [PriceResponse.model_validate(record) for record in records]
