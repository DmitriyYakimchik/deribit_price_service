import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from crypto_prices.api.routes.prices import router as prices_router
from crypto_prices.core.config import get_settings
from crypto_prices.db.session import dispose_engine

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(prices_router)


@app.get("/health", tags=["health"], summary="Application liveness check")
async def health() -> dict[str, str]:
    return {"status": "ok"}
