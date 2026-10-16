from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from crypto_prices.api.dependencies import get_price_service
from crypto_prices.main import app


def _override(service: object) -> None:
    app.dependency_overrides[get_price_service] = lambda: service


def _clear() -> None:
    app.dependency_overrides.clear()


def test_latest_price_returns_404_when_empty() -> None:
    service = SimpleNamespace(get_latest_price=AsyncMock(return_value=None))
    _override(service)
    try:
        response = TestClient(app).get("/api/v1/prices/latest", params={"ticker": "btc_usd"})
        assert response.status_code == 404
    finally:
        _clear()


def test_ticker_is_required() -> None:
    service = SimpleNamespace(get_latest_price=AsyncMock(return_value=None))
    _override(service)
    try:
        response = TestClient(app).get("/api/v1/prices/latest")
        assert response.status_code == 422
    finally:
        _clear()


def test_invalid_ticker_is_rejected() -> None:
    service = SimpleNamespace(get_latest_price=AsyncMock(return_value=None))
    _override(service)
    try:
        response = TestClient(app).get("/api/v1/prices/latest", params={"ticker": "xrp_usd"})
        assert response.status_code == 422
    finally:
        _clear()


def test_latest_price_serializes_record() -> None:
    record = SimpleNamespace(
        id=1, ticker="btc_usd", price=Decimal("123.4500000000"), timestamp=1800000000
    )
    service = SimpleNamespace(get_latest_price=AsyncMock(return_value=record))
    _override(service)
    try:
        response = TestClient(app).get("/api/v1/prices/latest", params={"ticker": "btc_usd"})
        assert response.status_code == 200
        assert response.json()["ticker"] == "btc_usd"
        assert response.json()["timestamp"] == 1800000000
    finally:
        _clear()


def test_list_prices_returns_serialized_records() -> None:
    records = [
        SimpleNamespace(id=1, ticker="btc_usd", price=Decimal("100"), timestamp=1),
        SimpleNamespace(id=2, ticker="btc_usd", price=Decimal("200"), timestamp=2),
    ]
    service = SimpleNamespace(list_prices=AsyncMock(return_value=records))
    _override(service)
    try:
        response = TestClient(app).get("/api/v1/prices", params={"ticker": "btc_usd"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["price"] == "100"
        assert body[1]["price"] == "200"
    finally:
        _clear()


def test_list_prices_forwards_pagination() -> None:
    service = SimpleNamespace(list_prices=AsyncMock(return_value=[]))
    _override(service)
    try:
        response = TestClient(app).get(
            "/api/v1/prices",
            params={"ticker": "btc_usd", "offset": 10, "limit": 25},
        )
        assert response.status_code == 200
        service.list_prices.assert_awaited_once_with("btc_usd", offset=10, limit=25)
    finally:
        _clear()


def test_history_accepts_valid_range() -> None:
    service = SimpleNamespace(get_price_history=AsyncMock(return_value=[]))
    _override(service)
    try:
        response = TestClient(app).get(
            "/api/v1/prices/history",
            params={"ticker": "btc_usd", "from_timestamp": 100, "to_timestamp": 200},
        )
        assert response.status_code == 200
        service.get_price_history.assert_awaited_once_with(
            "btc_usd",
            from_timestamp=100,
            to_timestamp=200,
            offset=0,
            limit=100,
        )
    finally:
        _clear()


def test_history_rejects_inverted_range() -> None:
    service = SimpleNamespace(get_price_history=AsyncMock(return_value=[]))
    _override(service)
    try:
        response = TestClient(app).get(
            "/api/v1/prices/history",
            params={"ticker": "btc_usd", "from_timestamp": 200, "to_timestamp": 100},
        )
        assert response.status_code == 422
        service.get_price_history.assert_not_awaited()
    finally:
        _clear()


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
