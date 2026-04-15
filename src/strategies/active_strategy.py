import numpy as np
import pandas as pd

class TradingStrategy:
    def __init__(self, fast_ma=20, slow_ma=50, confirmation_bars=3, min_hold_bars=5):
        """
        Initialize hyperparameters. 
        The AI Agent can modify these or add new ones here.
        """
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.confirmation_bars = confirmation_bars if confirmation_bars and confirmation_bars > 0 else 1
        self.min_hold_bars = min_hold_bars if min_hold_bars and min_hold_bars > 0 else 1
        self.market_regime = "neutral"

    def classify_market_regime(self, daily_data: "pd.DataFrame") -> "str":
        """Classify a simple broad-market regime from SPY daily bars."""
        if daily_data is None or daily_data.empty:
            return "neutral"

        required_columns = {"ticker", "session_date", "close"}
        if not required_columns.issubset(set(daily_data.columns)):
            return "neutral"

        spy_data = daily_data.loc[daily_data["ticker"].astype(str) == "SPY"].copy()
        if spy_data.empty:
            return "neutral"

        spy_data["session_date"] = pd.to_datetime(spy_data["session_date"])
        spy_data = spy_data.sort_values("session_date", kind="mergesort")

        close = spy_data["close"].astype(float)
        if len(close) < 21:
            return "neutral"

        daily_returns = close.pct_change().fillna(0.0)
        momentum_20 = close.pct_change(periods=20).iloc[-1]
        realized_vol_20 = daily_returns.rolling(20, min_periods=20).std() * np.sqrt(252)
        realized_vol_20 = realized_vol_20.dropna()
        if realized_vol_20.empty:
            return "neutral"

        latest_vol = realized_vol_20.iloc[-1]
        vol_reference = realized_vol_20.quantile(0.6)
        if momentum_20 < 0 and latest_vol >= vol_reference and latest_vol > 0:
            return "bear_volatile"

        return "neutral"

    def select_universe(self, daily_data: "pd.DataFrame") -> "list[str]":
        """
        Select tickers from the full daily-data frame loaded from DuckDB.

        The input frame is expected to include ticker-level daily bars with
        columns such as ticker, session_date, open, high, low, close, volume,
        transactions, and vwap. The default rule keeps the top 30 tickers by
        latest 20-session average volume.
        """
        if daily_data is None or daily_data.empty:
            self.market_regime = "neutral"
            return []

        if "ticker" not in daily_data.columns:
            self.market_regime = "neutral"
            return []

        self.market_regime = self.classify_market_regime(daily_data)

        ranked = daily_data.dropna(subset=["ticker"]).copy()
        if ranked.empty:
            return []

        if "session_date" in ranked.columns:
            ranked["ticker"] = ranked["ticker"].astype(str)
            latest_session = pd.to_datetime(ranked["session_date"]).max()
            active_tickers = (
                ranked.loc[pd.to_datetime(ranked["session_date"]) == latest_session, "ticker"]
                .dropna()
                .astype(str)
                .tolist()
            )
            if active_tickers:
                ranked = ranked[ranked["ticker"].isin(active_tickers)].copy()
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

    def apply_confirmation_filter(self, raw_signals: "pd.Series") -> "pd.Series":
        """Require the same directional raw signal for the configured confirmation window."""
        series = pd.Series(raw_signals, copy=True).fillna(0.0).astype(float)
        if series.empty:
            return pd.Series(index=series.index, dtype=float)

        if self.confirmation_bars <= 1:
            return series

        long_confirmed = (
            series.eq(1.0)
            .rolling(self.confirmation_bars, min_periods=self.confirmation_bars)
            .sum()
            .eq(float(self.confirmation_bars))
        )
        short_confirmed = (
            series.eq(-1.0)
            .rolling(self.confirmation_bars, min_periods=self.confirmation_bars)
            .sum()
            .eq(float(self.confirmation_bars))
        )

        confirmed = pd.Series(0.0, index=series.index)
        confirmed[long_confirmed] = 1.0
        confirmed[short_confirmed] = -1.0
        return confirmed

    def apply_minimum_hold_filter(self, raw_signals: "pd.Series") -> "pd.Series":
        """Apply confirmation and minimum-hold rules without accumulating reversals during hold."""
        series = pd.Series(raw_signals, copy=True).fillna(0.0).astype(float)
        if series.empty:
            return pd.Series(index=series.index, dtype=float)

        if self.min_hold_bars <= 1:
            return self.apply_confirmation_filter(series)

        held = pd.Series(0.0, index=series.index)
        current_position = 0.0
        hold_bars_remaining = 0
        candidate_direction = 0.0
        candidate_streak = 0

        for idx, signal in series.items():
            if current_position != 0.0 and hold_bars_remaining > 0:
                held.loc[idx] = current_position
                hold_bars_remaining = hold_bars_remaining - 1
                candidate_direction = 0.0
                candidate_streak = 0
                continue

            if current_position == 0.0:
                if signal == 0.0:
                    candidate_direction = 0.0
                    candidate_streak = 0
                elif signal == candidate_direction:
                    candidate_streak = candidate_streak + 1
                else:
                    candidate_direction = float(signal)
                    candidate_streak = 1

                if candidate_direction != 0.0 and candidate_streak >= self.confirmation_bars:
                    current_position = candidate_direction
                    hold_bars_remaining = self.min_hold_bars - 1
                    candidate_direction = 0.0
                    candidate_streak = 0
            else:
                if signal == current_position:
                    candidate_direction = 0.0
                    candidate_streak = 0
                else:
                    if signal == 0.0:
                        current_position = 0.0
                        candidate_direction = 0.0
                        candidate_streak = 0
                    else:
                        current_position = 0.0
                        candidate_direction = float(signal)
                        candidate_streak = 1

            held.loc[idx] = current_position

        return held

    def generate_signal_series(self, frame: "pd.DataFrame") -> "pd.Series":
        """Generate confirmed long/flat/short signals aligned to one ticker frame."""
        if frame is None:
            return pd.Series(index=pd.Index([]), dtype=float)

        if frame.empty:
            return pd.Series(index=frame.index, dtype=float)

        if self.market_regime == "bear_volatile":
            return pd.Series(0.0, index=frame.index)

        close_col = (
            "close" if "close" in frame.columns
            else "Close" if "Close" in frame.columns
            else None
        )
        if close_col is None:
            return pd.Series(0.0, index=frame.index)

        close = frame[close_col].astype(float)
        momentum = close - close.shift(20)

        raw_signals = pd.Series(0.0, index=frame.index)
        raw_signals[momentum > 0] = 1.0
        raw_signals[momentum < 0] = -1.0
        return self.apply_minimum_hold_filter(raw_signals)

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
