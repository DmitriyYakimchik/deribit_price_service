from crypto_prices.core.config import Settings, get_settings


def test_trailing_slash_is_stripped() -> None:
    settings = Settings(deribit_base_url="https://www.deribit.com/api/v2/")
    assert settings.deribit_base_url == "https://www.deribit.com/api/v2"


def test_no_trailing_slash_remains_unchanged() -> None:
    settings = Settings(deribit_base_url="https://www.deribit.com/api/v2")
    assert settings.deribit_base_url == "https://www.deribit.com/api/v2"


def test_default_supported_tickers() -> None:
    settings = Settings()
    assert settings.supported_tickers == ("btc_usd", "eth_usd")


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
