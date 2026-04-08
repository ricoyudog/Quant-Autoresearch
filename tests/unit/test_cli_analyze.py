from math import nan

import pandas as pd
from typer.testing import CliRunner

from analysis import format_analysis_report
from cli import app

runner = CliRunner()


def build_symbol_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=120, freq="D")
    close = pd.Series([100 + i for i in range(120)], index=dates, dtype=float)
    return pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 1,
            "Low": close - 2,
            "Close": close,
            "Volume": pd.Series([1000 + i * 10 for i in range(120)], index=dates, dtype=float),
        }
    )


def test_analyze_stdout_reports_sections(monkeypatch):
    frame = build_symbol_frame()

    class StubConnector:
        def load_symbol(self, symbol):
            return frame

    monkeypatch.setattr("cli.DataConnector", lambda: StubConnector())

    result = runner.invoke(
        app,
        ["analyze", "SPY", "--start", "2025-01-01", "--output", "stdout"],
    )

    assert result.exit_code == 0
    assert "# Stock Analysis: SPY" in result.stdout
    assert "## Momentum" in result.stdout
    assert "## Market Context" in result.stdout


def test_analyze_fails_clearly_when_cached_data_is_missing(monkeypatch):
    class StubConnector:
        def load_symbol(self, symbol):
            return None

    monkeypatch.setattr("cli.DataConnector", lambda: StubConnector())

    result = runner.invoke(app, ["analyze", "SPY", "--output", "stdout"])

    assert result.exit_code == 1
    assert "No cached data found for SPY" in result.stdout


def test_format_analysis_report_renders_nan_values_as_na():
    report = format_analysis_report(
        tickers=["SPY"],
        analyses={
            "SPY": {
                "momentum": {"roc_5d": nan, "roc_20d": nan, "roc_60d": nan},
                "volatility": {"vol_5d": 0.2, "vol_20d": 0.18, "vol_60d": 0.14},
                "volume": {
                    "current_volume": 1000.0,
                    "average_volume_20d": 900.0,
                    "relative_volume": 1.1,
                    "volume_trend": 0.05,
                },
                "price_structure": {
                    "high_60d": 100.0,
                    "low_60d": 90.0,
                    "close": nan,
                    "pct_from_high": nan,
                    "pct_from_low": nan,
                    "vwap": 95.0,
                },
                "regime": {
                    "current": "bear_volatile",
                    "vol_percentile": 83.67,
                    "distribution": {"bear_volatile": 10},
                },
                "market_context": {
                    "correlation_to_spy": 1.0,
                    "distance_from_50d_ma": nan,
                    "distance_from_200d_ma": nan,
                },
                "statistics": {
                    "sharpe": -1.0,
                    "max_drawdown": -0.08,
                    "win_rate": 0.47,
                    "avg_daily_range": 0.01,
                },
            }
        },
        start="2025-01-01",
        end="2025-04-07",
    )

    assert "nan" not in report.lower()
    assert "N/A" in report
