import numpy as np
import pandas as pd


class TradingStrategy:
    def __init__(
        self,
        risk_per_trade_pct=0.5,
        max_stop_pct=2.5,
        opening_range_bars=5,
        ema_exit_period=9,
        leader_adr_min_pct=5.0,
        max_universe_size=30,
        avg_dollar_volume_min=0.0,
    ):
        """Initialize the bounded Phase 4 MartinLuk dry-run primitive."""
        self.risk_per_trade_pct = float(risk_per_trade_pct)
        self.max_stop_pct = float(max_stop_pct)
        self.opening_range_bars = max(int(opening_range_bars), 1)
        self.ema_exit_period = max(int(ema_exit_period), 1)
        self.leader_adr_min_pct = float(leader_adr_min_pct)
        self.max_universe_size = max(int(max_universe_size), 1)
        self.avg_dollar_volume_min = float(avg_dollar_volume_min)
        self.market_regime = "neutral"
        self.signal_trace_entries = []

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
        Select latest-session hot leaders for the Phase 4 ORH primitive.

        Ranking uses positive latest 20-session return first, then latest
        20-session average dollar volume, then ticker. When daily high/low/close
        are available, tickers must also satisfy the configured ADR threshold.
        """
        if daily_data is None or daily_data.empty or "ticker" not in daily_data.columns:
            self.market_regime = "neutral"
            return []

        self.market_regime = self.classify_market_regime(daily_data)

        ranked = daily_data.dropna(subset=["ticker"]).copy()
        if ranked.empty:
            return []

        ranked["ticker"] = ranked["ticker"].astype(str)
        if "session_date" in ranked.columns:
            ranked["session_date"] = pd.to_datetime(ranked["session_date"])
            latest_session = ranked["session_date"].max()
            latest_tickers = set(
                ranked.loc[ranked["session_date"] == latest_session, "ticker"]
                .dropna()
                .astype(str)
                .tolist()
            )
            ranked = ranked[ranked["ticker"].isin(latest_tickers)].copy()
            ranked = ranked.sort_values(["ticker", "session_date"], kind="mergesort")
        else:
            ranked = ranked.sort_values(["ticker"], kind="mergesort")

        if ranked.empty or "close" not in ranked.columns:
            return []

        rows = []
        can_compute_adr = {"high", "low", "close"}.issubset(set(ranked.columns))
        has_volume = "volume" in ranked.columns

        for ticker, group in ranked.groupby("ticker", sort=False):
            latest = group.tail(20).copy()
            if len(latest) < 2:
                continue

            close = latest["close"].astype(float)
            first_close = close.iloc[0]
            last_close = close.iloc[-1]
            if not np.isfinite(first_close) or not np.isfinite(last_close) or first_close == 0:
                continue

            return_20 = (last_close / first_close) - 1.0
            if not np.isfinite(return_20) or return_20 <= 0:
                continue

            avg_dollar_volume = 0.0
            if has_volume:
                dollar_volume = close * latest["volume"].astype(float)
                dollar_volume = dollar_volume.replace([np.inf, -np.inf], np.nan).dropna()
                if dollar_volume.empty:
                    continue
                avg_dollar_volume = float(dollar_volume.mean())
                if avg_dollar_volume < self.avg_dollar_volume_min:
                    continue

            adr_pct = None
            if can_compute_adr:
                adr = (
                    (latest["high"].astype(float) - latest["low"].astype(float))
                    / close.replace(0, np.nan)
                    * 100.0
                )
                adr = adr.replace([np.inf, -np.inf], np.nan).dropna()
                if not adr.empty:
                    adr_pct = float(adr.mean())
                    if adr_pct < self.leader_adr_min_pct:
                        continue

            rows.append(
                {
                    "ticker": str(ticker),
                    "return_20": float(return_20),
                    "avg_dollar_volume": float(avg_dollar_volume),
                    "adr_pct": adr_pct,
                }
            )

        if not rows:
            return []

        universe = pd.DataFrame(rows).sort_values(
            ["return_20", "avg_dollar_volume", "ticker"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        return universe["ticker"].astype(str).head(self.max_universe_size).tolist()

    def get_signal_trace(self) -> "dict":
        """Return a validator-compatible side-band trace from the latest signal run."""
        return {
            "schema_version": "martinluk_public_signal_trace_v1",
            "replication_target": "public_operation_reproducibility",
            "signals": [dict(entry) for entry in self.signal_trace_entries],
        }

    def ticker_from_frame(self, frame: "pd.DataFrame") -> "str":
        if "ticker" not in frame.columns or frame.empty:
            return "UNKNOWN"
        ticker = frame["ticker"].dropna()
        if ticker.empty:
            return "UNKNOWN"
        return str(ticker.iloc[0])

    def signal_date(self, frame: "pd.DataFrame", entry_position: "int") -> "str":
        if "session_date" in frame.columns and len(frame.index) > entry_position:
            value = pd.to_datetime(frame["session_date"].iloc[entry_position])
            if not pd.isna(value):
                return value.date().isoformat()
        index_value = frame.index[entry_position] if len(frame.index) > entry_position else None
        if isinstance(index_value, pd.Timestamp):
            return index_value.date().isoformat()
        return "1970-01-01"

    def append_trace_entry(
        self,
        frame: "pd.DataFrame",
        ticker: "str",
        entry_position: "int",
        exit_position: "int",
        entry_price: "float",
        stop_price: "float",
        exit_type: "str",
        signals: "pd.Series",
    ) -> None:
        risk = entry_price - stop_price
        if risk <= 0 or not np.isfinite(risk):
            return

        trade_slice = frame.iloc[entry_position : exit_position + 1]
        high = trade_slice["high"].astype(float)
        low = trade_slice["low"].astype(float)
        mae = float(((low - entry_price) / risk).min())
        mfe = float(((high - entry_price) / risk).max())
        exit_price = float(frame["close"].astype(float).iloc[exit_position])
        if exit_type == "hard_stop":
            r_multiple = -1.0
        else:
            r_multiple = float((exit_price - entry_price) / risk)

        self.signal_trace_entries.append(
            {
                "signal_id": f"phase4-{ticker.lower()}-orh-{self.signal_date(frame, entry_position)}",
                "case_id": f"PHASE4-{ticker}-ORH",
                "symbol": ticker,
                "direction": "long",
                "date": self.signal_date(frame, entry_position),
                "setup_type": "leader_pullback_orh",
                "entry_trigger": "opening_range_high_breakout",
                "data_status": "available",
                "r_multiple": r_multiple,
                "mae": mae,
                "mae_unit": "R",
                "mfe": mfe,
                "mfe_unit": "R",
                "stop_width_pct": float(((entry_price - stop_price) / entry_price) * 100.0),
                "entry_type": "opening_range_high_breakout",
                "trim_type": "no_partial_trim_phase4",
                "exit_type": exit_type,
                "holding_period_bars": int(exit_position - entry_position + 1),
            }
        )

    def append_open_trace_entry(
        self,
        frame: "pd.DataFrame",
        ticker: "str",
        entry_position: "int",
        entry_price: "float",
        stop_price: "float",
    ) -> None:
        risk = entry_price - stop_price
        if risk <= 0 or not np.isfinite(risk):
            return

        last_position = len(frame.index) - 1
        trade_slice = frame.iloc[entry_position : last_position + 1]
        high = trade_slice["high"].astype(float)
        low = trade_slice["low"].astype(float)
        self.signal_trace_entries.append(
            {
                "signal_id": f"phase4-{ticker.lower()}-orh-{self.signal_date(frame, entry_position)}-open",
                "case_id": f"PHASE4-{ticker}-ORH",
                "symbol": ticker,
                "direction": "long",
                "date": self.signal_date(frame, entry_position),
                "setup_type": "leader_pullback_orh",
                "entry_trigger": "opening_range_high_breakout",
                "data_status": "available",
                "r_multiple": None,
                "mae": float(((low - entry_price) / risk).min()),
                "mae_unit": "R",
                "mfe": float(((high - entry_price) / risk).max()),
                "mfe_unit": "R",
                "stop_width_pct": float(((entry_price - stop_price) / entry_price) * 100.0),
                "entry_type": "opening_range_high_breakout",
                "trim_type": "no_partial_trim_phase4",
                "exit_type": "open",
                "holding_period_bars": int(last_position - entry_position + 1),
            }
        )

    def generate_signal_series(self, frame: "pd.DataFrame") -> "pd.Series":
        """Generate long/flat ORH primitive signals aligned to one ticker frame."""
        if frame is None:
            return pd.Series(index=pd.Index([]), dtype=float)

        if frame.empty:
            return pd.Series(index=frame.index, dtype=float)

        required_columns = {"close", "high", "low"}
        if not required_columns.issubset(set(frame.columns)):
            return pd.Series(0.0, index=frame.index)

        signals = pd.Series(0.0, index=frame.index)
        if len(frame.index) <= self.opening_range_bars:
            return signals

        close = frame["close"].astype(float)
        high = frame["high"].astype(float)
        low = frame["low"].astype(float)
        ema = close.ewm(span=self.ema_exit_period, adjust=False, min_periods=1).mean()
        opening_range = frame.iloc[: self.opening_range_bars]
        opening_range_high = float(opening_range["high"].astype(float).max())
        opening_range_low = float(opening_range["low"].astype(float).min())

        ticker = self.ticker_from_frame(frame)
        in_trade = False
        entry_position = None
        entry_price = None
        stop_price = opening_range_low

        for position in range(self.opening_range_bars, len(frame.index)):
            idx = frame.index[position]
            current_close = float(close.iloc[position])
            current_low = float(low.iloc[position])

            if not in_trade:
                if current_close > opening_range_high and current_close > float(ema.iloc[position]):
                    stop_width_pct = ((current_close - stop_price) / current_close) * 100.0
                    if stop_width_pct <= self.max_stop_pct:
                        in_trade = True
                        entry_position = position
                        entry_price = current_close
                        signals.loc[idx] = 1.0
                continue

            if current_low < stop_price:
                signals.loc[idx] = 0.0
                self.append_trace_entry(
                    frame,
                    ticker,
                    entry_position,
                    position,
                    entry_price,
                    stop_price,
                    "hard_stop",
                    signals,
                )
                in_trade = False
                entry_position = None
                entry_price = None
                continue

            if current_close < float(ema.iloc[position]):
                signals.loc[idx] = 0.0
                self.append_trace_entry(
                    frame,
                    ticker,
                    entry_position,
                    position,
                    entry_price,
                    stop_price,
                    "nine_ema_close_break",
                    signals,
                )
                in_trade = False
                entry_position = None
                entry_price = None
                continue

            signals.loc[idx] = 1.0

        if in_trade and entry_position is not None and entry_price is not None:
            self.append_open_trace_entry(frame, ticker, entry_position, entry_price, stop_price)

        return signals

    def generate_signals(self, data):
        """
        Generate runtime signals from minute-bar frames.

        The public return shape stays unchanged: dict input returns dict[str,
        pd.Series], and DataFrame input returns one pd.Series. Validator trace
        output is side-band state available through get_signal_trace().
        """
        self.signal_trace_entries = []

        if isinstance(data, dict):
            return {
                str(ticker): self.generate_signal_series(frame)
                for ticker, frame in data.items()
            }

        if isinstance(data, pd.DataFrame):
            return self.generate_signal_series(data)

        return {}
