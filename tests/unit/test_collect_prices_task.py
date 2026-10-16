from unittest.mock import AsyncMock, patch

from crypto_prices.tasks.collect_prices import collect_prices_task


def test_task_returns_collection_result() -> None:
    async_mock = AsyncMock(return_value={"btc_usd": "saved", "eth_usd": "saved"})
    with patch("crypto_prices.tasks.collect_prices._collect_prices", new=async_mock):
        result = collect_prices_task.apply().get()

    assert result == {"btc_usd": "saved", "eth_usd": "saved"}
    async_mock.assert_awaited_once()


def test_task_propagates_partial_failures() -> None:
    async_mock = AsyncMock(return_value={"btc_usd": "saved", "eth_usd": "failed"})
    with patch("crypto_prices.tasks.collect_prices._collect_prices", new=async_mock):
        result = collect_prices_task.apply().get()

    assert result == {"btc_usd": "saved", "eth_usd": "failed"}
