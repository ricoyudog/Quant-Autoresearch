import pandas as pd
from unittest.mock import MagicMock, patch

def test_data_connector_fetch_and_cache_saves_featured_parquet(tmp_path):
    from data.cache_connector import CacheConnector

    cache_dir = tmp_path / "data_cache_test"
    connector = CacheConnector(str(cache_dir))

    dates = pd.date_range(start="2023-01-01", periods=20, freq="D")
    market_data = pd.DataFrame(
        {
            "Open": [100.0 + index for index in range(20)],
            "High": [101.0 + index for index in range(20)],
            "Low": [99.0 + index for index in range(20)],
            "Close": [100.5 + index for index in range(20)],
            "Volume": [1000 + index for index in range(20)],
        },
        index=dates,
    )

    with patch("yfinance.download", return_value=market_data):
        assert connector.fetch_and_cache("SPY", "2023-01-01") is True

    saved_frame = pd.read_parquet(cache_dir / "SPY.parquet")
    assert {"returns", "volatility", "atr"}.issubset(saved_frame.columns)


def test_data_connector_fetches_crypto_via_ccxt(tmp_path):
    from data.cache_connector import CacheConnector

    cache_dir = tmp_path / "data_cache_test"
    connector = CacheConnector(str(cache_dir))

    mock_exchange = MagicMock()
    mock_exchange.fetch_ohlcv.return_value = [
        [1672531200000, 100.0, 105.0, 95.0, 102.0, 1000],
    ]
    mock_exchange.parse8601.return_value = 1672531200000
    mock_exchange.milliseconds.return_value = 1672531200000 + 1000
    mock_exchange.rateLimit = 0

    with patch("ccxt.binance", return_value=mock_exchange):
        assert connector.fetch_and_cache("BTC-USD", "2023-01-01") is True

    saved_frame = pd.read_parquet(cache_dir / "BTC_USD.parquet")
    assert {"returns", "volatility", "atr"}.issubset(saved_frame.columns)
