import numpy as np
import pandas as pd

class TradingStrategy:
    def __init__(self, fast_ma=20, slow_ma=50):
        """
        Initialize hyperparameters. 
        The AI Agent can modify these or add new ones here.
        """
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma

    def select_universe(self, daily_data: "pd.DataFrame") -> "list[str]":
        """
        Select tickers from the full daily-data frame loaded from DuckDB.

        The input frame is expected to include ticker-level daily bars with
        columns such as ticker, session_date, open, high, low, close, volume,
        transactions, and vwap. The default rule keeps the top 30 tickers by
        latest 20-session average volume.
        """
        if daily_data is None or daily_data.empty:
            return []

        if "ticker" not in daily_data.columns:
            return []

        ranked = daily_data.dropna(subset=["ticker"]).copy()
        if ranked.empty:
            return []

        if "volume" not in ranked.columns:
            return ranked["ticker"].astype(str).drop_duplicates().head(30).tolist()

        ranked = ranked.dropna(subset=["volume"]).copy()
        if ranked.empty:
            return []

        if "session_date" in ranked.columns:
            ranked = ranked.sort_values(["ticker", "session_date"], kind="mergesort")
        else:
            ranked = ranked.sort_values(["ticker"], kind="mergesort")

        latest_20_sessions = ranked.groupby("ticker", group_keys=False).tail(20)
        if latest_20_sessions.empty:
            return []

        universe = (
            latest_20_sessions.groupby("ticker", as_index=False)["volume"]
            .mean()
            .sort_values(["volume", "ticker"], ascending=[False, True], kind="mergesort")
        )
        return universe["ticker"].astype(str).head(30).tolist()

    def generate_signal_series(self, frame: "pd.DataFrame") -> "pd.Series":
        """Generate raw long/flat/short signals aligned to one ticker frame."""
        if frame is None:
            return pd.Series(index=pd.Index([]), dtype=float)

        if frame.empty:
            return pd.Series(index=frame.index, dtype=float)

        close_col = (
            "close" if "close" in frame.columns
            else "Close" if "Close" in frame.columns
            else None
        )
        if close_col is None:
            return pd.Series(0.0, index=frame.index)

        close = frame[close_col].astype(float)
        momentum = close - close.shift(20)

        signals = pd.Series(0.0, index=frame.index)
        signals[momentum > 0] = 1.0
        signals[momentum < 0] = -1.0
        return signals

    def generate_signals(self, data):
        """
        Generate raw signals from minute-bar frames.

        Preferred Step 4 contract:
            dict[str, pd.DataFrame] -> dict[str, pd.Series]

        Temporary compatibility path:
            pd.DataFrame -> pd.Series

        The backtester remains responsible for applying the enforced 1-bar lag.
        """
        if isinstance(data, dict):
            return {
                str(ticker): self.generate_signal_series(frame)
                for ticker, frame in data.items()
            }

        if isinstance(data, pd.DataFrame):
            return self.generate_signal_series(data)

        return {}
