from decimal import Decimal, InvalidOperation
from typing import Any

import aiohttp

from crypto_prices.core.config import Ticker, get_settings


class DeribitClientError(Exception):
    """Raised when Deribit cannot provide a valid index price."""


class DeribitClient:
    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        self._session = session
        self._owns_session = session is None
        self._settings = get_settings()

    async def __aenter__(self) -> DeribitClient:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._settings.deribit_timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
            self._owns_session = True
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def get_index_price(self, ticker: Ticker) -> Decimal:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._settings.deribit_timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
            self._owns_session = True
        return await self._request_index_price(self._session, ticker)

    async def _request_index_price(self, session: aiohttp.ClientSession, ticker: Ticker) -> Decimal:
        url = f"{self._settings.deribit_base_url}/public/get_index_price"
        try:
            async with session.get(url, params={"index_name": ticker}) as response:
                response.raise_for_status()
                payload: Any = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
            raise DeribitClientError(f"Failed to request Deribit index {ticker}: {exc}") from exc

        if not isinstance(payload, dict):
            raise DeribitClientError("Deribit returned a non-object JSON response")
        if payload.get("error") is not None:
            raise DeribitClientError(f"Deribit JSON-RPC error for {ticker}: {payload['error']}")
        result = payload.get("result")
        if not isinstance(result, dict) or "index_price" not in result:
            raise DeribitClientError(
                f"Deribit response does not contain result.index_price for {ticker}"
            )
        try:
            price = Decimal(str(result["index_price"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise DeribitClientError(f"Invalid index price for {ticker}") from exc
        if not price.is_finite() or price <= 0:
            raise DeribitClientError(f"Non-positive or non-finite index price for {ticker}")
        return price

    async def close(self) -> None:
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
