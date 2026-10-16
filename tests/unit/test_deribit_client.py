from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from crypto_prices.clients.deribit import DeribitClient, DeribitClientError


@pytest.mark.asyncio
async def test_get_index_price_parses_json_rpc_result() -> None:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value={"jsonrpc": "2.0", "result": {"index_price": 123.45}})
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get.return_value = response

    client = DeribitClient(session=session)
    price = await client.get_index_price("btc_usd")

    assert price == Decimal("123.45")
    session.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_index_price_rejects_json_rpc_error() -> None:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value={"error": {"code": -1, "message": "bad request"}})
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get.return_value = response

    with pytest.raises(DeribitClientError, match="JSON-RPC error"):
        await DeribitClient(session=session).get_index_price("btc_usd")


@pytest.mark.asyncio
async def test_get_index_price_rejects_non_positive_price() -> None:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value={"result": {"index_price": 0}})
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get.return_value = response

    with pytest.raises(DeribitClientError, match="Non-positive"):
        await DeribitClient(session=session).get_index_price("btc_usd")
