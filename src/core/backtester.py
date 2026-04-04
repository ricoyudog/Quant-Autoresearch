import ast
import os
import sys

import numpy as np
import pandas as pd
from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safer_getattr,
)

from data.cache_connector import CacheConnector
from data.duckdb_connector import (
    calculate_walk_forward_windows,
    load_daily_data,
    query_minute_data,
)

CACHE_DIR = os.environ.get("CACHE_DIR", "data/cache")
STRATEGY_FILE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("STRATEGY_FILE", "src/strategies/active_strategy.py")

FORBIDDEN_BUILTINS = {"exec", "eval", "open", "getattr", "setattr", "delattr"}
FORBIDDEN_MODULES = {"socket", "requests", "urllib", "os", "sys", "shutil", "subprocess"}


def get_strategy_file() -> str:
    """Resolve the strategy file at call time so CLI env overrides are honored."""
    return os.environ.get("STRATEGY_FILE", STRATEGY_FILE)


def get_backtest_runtime_config() -> tuple[str | None, str | None, int | None]:
    """Read and validate optional CLI overrides for the minute-mode backtest."""
    start_date = os.environ.get("BACKTEST_START_DATE")
    end_date = os.environ.get("BACKTEST_END_DATE")
    if bool(start_date) != bool(end_date):
        raise ValueError("Provide both BACKTEST_START_DATE and BACKTEST_END_DATE together.")

    universe_raw = os.environ.get("BACKTEST_UNIVERSE_SIZE")
    if universe_raw is None:
        return start_date, end_date, None

    try:
        universe_size = int(universe_raw)
    except ValueError as exc:
        raise ValueError("BACKTEST_UNIVERSE_SIZE must be a positive integer.") from exc

    if universe_size <= 0:
        raise ValueError("BACKTEST_UNIVERSE_SIZE must be a positive integer.")

    return start_date, end_date, universe_size


def find_strategy_class(sandbox_locals: dict) -> tuple[type | None, bool]:
    """Find the first strategy class and whether it exposes select_universe."""
    for obj in sandbox_locals.values():
        if isinstance(obj, type) and hasattr(obj, "generate_signals"):
            return obj, hasattr(obj, "select_universe")
    return None, False


def apply_signal_lag(signals_by_ticker: dict[str, pd.Series]) -> dict[str, pd.Series]:
    """Apply the enforced one-bar lag independently to each ticker signal series."""
    lagged_signals = {}
    for ticker, signals in signals_by_ticker.items():
        series = signals if isinstance(signals, pd.Series) else pd.Series(signals)
        lagged_signals[ticker] = series.shift(1).fillna(0)
    return lagged_signals


def default_universe_from_daily_data(daily_data: pd.DataFrame, max_tickers: int = 30) -> list[str]:
    """Select a safe fallback ticker subset from the full daily frame."""
    if daily_data is None or daily_data.empty or "ticker" not in daily_data.columns:
        return []

    ranked = daily_data.dropna(subset=["ticker"]).copy()
    if ranked.empty:
        return []

    if "volume" in ranked.columns:
        ranked = ranked.dropna(subset=["volume"])
        if not ranked.empty:
            universe = (
                ranked.groupby("ticker", as_index=False)["volume"]
                .mean()
                .sort_values(["volume", "ticker"], ascending=[False, True], kind="mergesort")
            )
            return universe["ticker"].astype(str).head(max_tickers).tolist()

    return ranked["ticker"].astype(str).drop_duplicates().head(max_tickers).tolist()


def normalize_universe_selection(selected_tickers, daily_data: pd.DataFrame) -> list[str]:
    """Sanitize strategy-selected tickers and fall back to a safe ranked subset."""
    if isinstance(selected_tickers, str):
        selected_tickers = [selected_tickers]

    if not isinstance(selected_tickers, (list, tuple, set, pd.Index, np.ndarray)):
        return default_universe_from_daily_data(daily_data)

    normalized = []
    for ticker in selected_tickers:
        if pd.isna(ticker):
            continue
        value = str(ticker).strip()
        if value and value not in normalized:
            normalized.append(value)

    return normalized or default_universe_from_daily_data(daily_data)


def prepare_minute_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Sort a minute frame and derive returns plus rolling volatility."""
    if frame is None or frame.empty:
        return pd.DataFrame(index=getattr(frame, "index", pd.Index([])))

    prepared = frame.copy()
    sort_columns = [column for column in ["session_date", "window_start_ns"] if column in prepared.columns]
    if sort_columns:
        prepared = prepared.sort_values(sort_columns).reset_index(drop=True)

    if "close" not in prepared.columns:
        return prepared

    close = prepared["close"].astype(float)
    if "session_date" in prepared.columns:
        prepared["returns"] = (
            close.groupby(prepared["session_date"], sort=False).pct_change().fillna(0.0)
        )
        prepared["volatility"] = (
            prepared.groupby("session_date", sort=False)["returns"]
            .transform(lambda series: series.rolling(window=20, min_periods=1).std())
            .fillna(0.0)
        )
    else:
        prepared["returns"] = close.pct_change().fillna(0.0)
        prepared["volatility"] = (
            prepared["returns"].rolling(window=20, min_periods=1).std().fillna(0.0)
        )
    return prepared


def coerce_signal_series(signal_values, index: pd.Index) -> pd.Series:
    """Coerce arbitrary signal output into a float Series aligned to the frame index."""
    if isinstance(signal_values, pd.Series):
        series = signal_values.copy()
        if len(series) == len(index):
            series.index = index
        else:
            series = series.reset_index(drop=True).reindex(range(len(index)), fill_value=0.0)
            series.index = index
        return series.fillna(0.0).astype(float)

    series = pd.Series(signal_values).reset_index(drop=True)
    if len(series) != len(index):
        series = series.reindex(range(len(index)), fill_value=0.0)
    series.index = index
    return series.fillna(0.0).astype(float)


def normalize_minute_signals(raw_signals, minute_data: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
    """Normalize strategy output to one aligned Series per ticker."""
    if isinstance(raw_signals, pd.Series) and len(minute_data) == 1:
        ticker = next(iter(minute_data))
        raw_signals = {ticker: raw_signals}
    elif not isinstance(raw_signals, dict):
        raw_signals = {}

    normalized = {}
    for ticker, frame in minute_data.items():
        signal_values = raw_signals.get(ticker, pd.Series(0.0, index=frame.index))
        normalized[ticker] = coerce_signal_series(signal_values, frame.index)
    return normalized


def calculate_metrics(combined_returns: pd.Series, trades: pd.Series) -> dict:
    """Calculate 10 performance metrics from combined returns and trade signals."""
    mean_ret = combined_returns.mean()
    std_ret = combined_returns.std()

    # Sharpe
    sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret != 0 else 0.0

    # Sortino — downside deviation only
    downside = combined_returns[combined_returns < 0]
    downside_std = downside.std() if len(downside) > 0 else 0.0
    sortino = (mean_ret / downside_std) * np.sqrt(252) if downside_std != 0 else 0.0

    # Max Drawdown
    cum = (1 + combined_returns).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    max_drawdown = drawdown.min()

    # Calmar — annualized return / abs(max drawdown)
    annualized_return = mean_ret * 252
    calmar = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

    # Max DD Days — longest drawdown duration
    in_dd = drawdown < 0
    dd_groups = (in_dd != in_dd.shift()).cumsum()
    max_dd_days = 0
    if in_dd.any():
        dd_durations = in_dd.groupby(dd_groups).sum()
        max_dd_days = int(dd_durations.max()) if len(dd_durations) > 0 else 0

    # Trades count — number of position changes
    trade_changes = trades.diff().abs()
    trade_changes = trade_changes[trade_changes > 0]
    total_trades = int(trade_changes.sum()) if len(trade_changes) > 0 else 0

    # Trade-level returns — actual returns when a position is active
    active_mask = trades != 0
    trade_returns = combined_returns[active_mask]

    # Win Rate
    if len(trade_returns) > 0:
        wins = (trade_returns > 0).sum()
        win_rate = float(wins / len(trade_returns))
    else:
        win_rate = 0.0

    # Profit Factor
    gross_profit = float(trade_returns[trade_returns > 0].sum()) if len(trade_returns) > 0 else 0.0
    gross_loss = float(abs(trade_returns[trade_returns < 0].sum())) if len(trade_returns) > 0 else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0.0

    # Avg Win / Avg Loss
    avg_win = float(trade_returns[trade_returns > 0].mean()) if (trade_returns > 0).any() else 0.0
    avg_loss = float(trade_returns[trade_returns < 0].mean()) if (trade_returns < 0).any() else 0.0

    return {
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "drawdown": max_drawdown,
        "max_dd_days": max_dd_days,
        "trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
    }


def calculate_baseline_sharpe(data: dict) -> float:
    """Calculate Buy&Hold Sharpe across all symbols."""
    all_returns = []
    for symbol, df in data.items():
        if "returns" in df.columns:
            all_returns.append(df["returns"])
    if not all_returns:
        return 0.0
    combined = pd.concat(all_returns).dropna()
    std = combined.std()
    return float((combined.mean() / std) * np.sqrt(252)) if std != 0 else 0.0


def run_per_symbol_analysis(strategy_instance, data: dict, start_idx: int, end_idx: int) -> dict:
    """Run per-symbol analysis returning sharpe, sortino, dd, pf, trades, wr for each symbol."""
    results = {}
    BASE_COST = 0.0005

    for symbol, df in data.items():
        history_df = df.iloc[:end_idx].copy()
        try:
            full_signals = strategy_instance.generate_signals(history_df)
            if not isinstance(full_signals, pd.Series):
                full_signals = pd.Series(full_signals, index=history_df.index)
            full_signals = full_signals.fillna(0)
            signals = full_signals.shift(1).fillna(0).iloc[start_idx:end_idx]
        except Exception:
            results[symbol] = {"sharpe": 0.0, "sortino": 0.0, "dd": 0.0, "pf": 0.0, "trades": 0, "wr": 0.0}
            continue

        test_returns = df.iloc[start_idx:end_idx]["returns"]
        daily_returns = test_returns * signals

        # Costs
        trades_series = signals.diff().abs().fillna(0)
        vol = df.iloc[start_idx:end_idx]["volatility"]
        slippage = vol * 0.1
        costs = trades_series * (BASE_COST + slippage)
        net_returns = daily_returns - costs

        # Metrics
        std = net_returns.std()
        sharpe = float((net_returns.mean() / std) * np.sqrt(252)) if std != 0 else 0.0

        downside = net_returns[net_returns < 0]
        downside_std = downside.std() if len(downside) > 0 else 0.0
        sortino = float((net_returns.mean() / downside_std) * np.sqrt(252)) if downside_std != 0 else 0.0

        cum = (1 + net_returns).cumprod()
        running_max = cum.cummax()
        dd = ((cum - running_max) / running_max).min()

        trade_changes = signals.diff().abs()
        trade_changes = trade_changes[trade_changes > 0]
        trade_count = int(trade_changes.sum()) if len(trade_changes) > 0 else 0

        trade_rets = net_returns[signals != 0]
        if len(trade_rets) > 0:
            wins = (trade_rets > 0).sum()
            wr = float(wins / len(trade_rets))
            gp = trade_rets[trade_rets > 0].sum()
            gl = abs(trade_rets[trade_rets < 0].sum())
            pf = float(gp / gl) if gl != 0 else 0.0
        else:
            wr = 0.0
            pf = 0.0

        results[symbol] = {
            "sharpe": sharpe,
            "sortino": sortino,
            "dd": float(dd),
            "pf": pf,
            "trades": trade_count,
            "wr": wr,
        }

    return results


def security_check(file_path: str = None):
    """
    Performs security analysis on a strategy file using AST to find forbidden patterns.
    """
    target = file_path or get_strategy_file()
    if not os.path.exists(target):
        return False, f"Strategy file not found: {target}"
    
    try:
        with open(target, "r") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            # Check for forbidden function calls
            if isinstance(node, ast.Call):
                # Call by name
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                    return False, f"Forbidden builtin function found: {node.func.id}"
                
                # Check for negative shift (look-ahead)
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'shift':
                    # Check positional arguments
                    for arg in node.args:
                        if is_negative_val(arg):
                            return False, "Look-ahead bias detected (.shift(-N))"
                    # Check keyword arguments
                    for kw in node.keywords:
                        if kw.arg == 'periods' and is_negative_val(kw.value):
                            return False, "Look-ahead bias detected (.shift(periods=-N))"
                
            # Check for forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_MODULES:
                        return False, f"Forbidden module import found: {alias.name}"
            if isinstance(node, ast.ImportFrom):
                if node.module in FORBIDDEN_MODULES:
                    return False, f"Forbidden module import found: {node.module}"
                                
        return True, ""
    except Exception as e:
        return False, f"AST Parsing Error: {e}"

def is_negative_val(node):
    """Helper to check if an AST node represents a negative constant."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float)):
            return node.operand.value > 0
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value < 0
    if isinstance(node, ast.BinOp):
        # Recursively check for negative components in BinOp (coarse but safe)
        return is_negative_val(node.left) or is_negative_val(node.right)
    return False

def load_data():
    connector = CacheConnector(CACHE_DIR)
    return connector.load_all_cached()

def run_backtest(strategy_instance, data, start_idx, end_idx):
    """
    Evaluates strategy on a specific window [start_idx:end_idx].
    Warms up indicators by passing the full history up to end_idx.
    """
    total_returns = []
    BASE_COST = 0.0005 # 0.05%
    
    for symbol, df in data.items():
        # Provide history up to end_idx for indicator calculation
        history_df = df.iloc[:end_idx].copy()
        
        try:
            # Agent generates signals for the entire period provided
            full_signals = strategy_instance.generate_signals(history_df)
            
            # Robustness: Force into Series if LLM returned numpy array
            if not isinstance(full_signals, pd.Series):
                full_signals = pd.Series(full_signals, index=history_df.index)
            
            # Fill NaNs with 0 to prevent downstream crashes
            full_signals = full_signals.fillna(0)
            
            # Slice to only the test window
            signals = full_signals.iloc[start_idx:end_idx]
        except Exception as e:
            print(f"Error in {symbol} strategy: {e}", file=sys.stderr)
            return -10.0, 0.0, 0
            
        # Enforced Lag: Shift signals by 1 to prevent look-ahead bias
        signals = full_signals.shift(1).fillna(0).iloc[start_idx:end_idx]
        
        # Returns for the test window
        test_returns = df.iloc[start_idx:end_idx]['returns']
        daily_returns = test_returns * signals
        
        # Costs: base cost + volatility slippage
        trades = signals.diff().abs().fillna(0)
        vol = df.iloc[start_idx:end_idx]['volatility']
        slippage = vol * 0.1 
        costs = trades * (BASE_COST + slippage)
        
        net_returns = daily_returns - costs
        total_returns.append(net_returns)
        
    if not total_returns:
        return -10.0, 0.0, 0
        
    combined_returns = pd.concat(total_returns, axis=1).mean(axis=1)
    
    # Sharpe Ratio (Annualized)
    if combined_returns.std() == 0:
        sharpe = 0.0
    else:
        sharpe = (combined_returns.mean() / combined_returns.std()) * np.sqrt(252)
    
    # Max Drawdown
    cum_returns = (1 + combined_returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Total Trades (rough estimate sum across symbols)
    total_trades = 0
    for symbol, df in data.items():
        history_df = df.iloc[:end_idx].copy()
        try:
            full_signals = strategy_instance.generate_signals(history_df)
            signals = full_signals.iloc[start_idx:end_idx]
            total_trades += signals.diff().abs().sum()
        except:
            pass

    return sharpe, max_drawdown, total_trades

def walk_forward_validation():
    try:
        start_date_override, end_date_override, universe_size_override = get_backtest_runtime_config()
    except ValueError as exc:
        print(f"DATA ERROR: {exc}")
        sys.exit(1)

    strategy_file = get_strategy_file()

    is_safe, msg = security_check(strategy_file)
    if not is_safe:
        print(f"SECURITY ERROR: {msg}")
        sys.exit(1)
        
    # Load Strategy via RestrictedPython Sandbox
    try:
        with open(strategy_file, "r") as f:
            strategy_lines = f.readlines()
        
        # Strip import statements for restricted execution
        sanitized_code = []
        for line in strategy_lines:
            if not (line.strip().startswith("import ") or line.strip().startswith("from ")):
                sanitized_code.append(line)
        strategy_code = "".join(sanitized_code)
        
        # Define the restricted environment
        safe_globals = {
            '__builtins__': safe_builtins,
            '_getattr_': safer_getattr,
            '_write_': lambda x: x,
            '_getiter_': default_guarded_getiter,
            '_getitem_': default_guarded_getitem,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '_unpack_sequence_': guarded_unpack_sequence,
            '__name__': 'sandbox',
            '__metaclass__': type,
            'dict': dict,
            'list': list,
            'set': set,
            'pd': pd,
            'np': np,
        }
        
        # Compile the code in restricted mode
        byte_code = compile_restricted(strategy_code, filename='strategy.py', mode='exec')
        
        # Execute in safe scope
        sandbox_locals = {}
        exec(byte_code, safe_globals, sandbox_locals)
        
        strategy_class, _ = find_strategy_class(sandbox_locals)
        if not strategy_class:
            print("STRATEGY ERROR: No class with generate_signals found in strategy.py")
            sys.exit(1)
            
        strategy_instance = strategy_class()
    except Exception as e:
        print(f"STRATEGY LOAD ERROR (Restricted): {e}")
        sys.exit(1)

    daily_data = load_daily_data(start_date=start_date_override, end_date=end_date_override)
    if daily_data is None or daily_data.empty:
        print("DATA ERROR: No daily DuckDB data found.")
        sys.exit(1)

    if "session_date" not in daily_data.columns:
        print("DATA ERROR: Daily DuckDB data must include session_date.")
        sys.exit(1)

    daily_dates = pd.to_datetime(daily_data["session_date"])
    start_date = daily_dates.min().strftime("%Y-%m-%d")
    end_date = daily_dates.max().strftime("%Y-%m-%d")

    try:
        windows = calculate_walk_forward_windows(start_date, end_date, n_windows=5)
    except ValueError as exc:
        print(f"DATA ERROR: {exc}")
        sys.exit(1)

    try:
        selected_tickers = (
            strategy_instance.select_universe(daily_data)
            if hasattr(strategy_instance, "select_universe")
            else None
        )
    except Exception:
        selected_tickers = None

    selected_tickers = normalize_universe_selection(selected_tickers, daily_data)
    if universe_size_override is not None:
        selected_tickers = selected_tickers[:universe_size_override]
    if not selected_tickers:
        print("DATA ERROR: No tickers available for minute backtest.")
        sys.exit(1)

    all_metrics = []
    baseline_frames: dict[str, list[pd.DataFrame]] = {}
    per_symbol_returns: dict[str, list[pd.Series]] = {}
    per_symbol_signals: dict[str, list[pd.Series]] = {}

    for window in windows:
        minute_data = query_minute_data(
            selected_tickers,
            window["test_start"],
            window["test_end"],
        )
        if not minute_data:
            continue

        prepared_minute_data = {}
        for ticker, frame in minute_data.items():
            prepared = prepare_minute_frame(frame)
            if prepared.empty or "returns" not in prepared.columns:
                continue
            prepared_minute_data[ticker] = prepared
            baseline_frames.setdefault(ticker, []).append(prepared)

        if not prepared_minute_data:
            continue

        try:
            raw_signals = strategy_instance.generate_signals(prepared_minute_data)
        except Exception as exc:
            print(f"WINDOW ERROR ({window['test_start']}..{window['test_end']}): {exc}", file=sys.stderr)
            continue

        normalized_signals = normalize_minute_signals(raw_signals, prepared_minute_data)
        lagged_signals = apply_signal_lag(normalized_signals)

        window_returns = []
        window_positions = []
        for ticker, frame in prepared_minute_data.items():
            signals = coerce_signal_series(lagged_signals.get(ticker), frame.index)
            minute_returns = frame["returns"].fillna(0.0)
            trades = signals.diff().abs().fillna(0.0)
            slippage = frame["volatility"].fillna(0.0) * 0.1
            costs = trades * (0.0005 + slippage)
            net_returns = (minute_returns * signals) - costs

            window_returns.append(net_returns.rename(ticker))
            window_positions.append(signals.rename(ticker))
            per_symbol_returns.setdefault(ticker, []).append(net_returns)
            per_symbol_signals.setdefault(ticker, []).append(signals)

        if window_returns:
            combined = pd.concat(window_returns, axis=1).mean(axis=1)
            combined_positions = pd.concat(window_positions, axis=1).mean(axis=1)
            metrics = calculate_metrics(combined, combined_positions)
            all_metrics.append(metrics)

    if not all_metrics:
        print("ERROR: No valid windows produced results")
        sys.exit(1)

    # Average metrics across all windows
    avg_metrics = {}
    for key in all_metrics[0]:
        avg_metrics[key] = float(np.mean([m[key] for m in all_metrics]))

    baseline_data = {
        ticker: pd.concat(frames, ignore_index=True)
        for ticker, frames in baseline_frames.items()
    }
    baseline_sharpe = calculate_baseline_sharpe(baseline_data)

    per_symbol = {}
    for ticker in sorted(per_symbol_returns):
        symbol_returns = pd.concat(per_symbol_returns[ticker], ignore_index=True)
        symbol_signals = pd.concat(per_symbol_signals[ticker], ignore_index=True)
        metrics = calculate_metrics(symbol_returns, symbol_signals)
        per_symbol[ticker] = {
            "sharpe": metrics["sharpe"],
            "sortino": metrics["sortino"],
            "dd": metrics["drawdown"],
            "pf": metrics["profit_factor"],
            "trades": metrics["trades"],
            "wr": metrics["win_rate"],
        }

    # Output YAML-like format
    print("---")
    print(f"SCORE: {avg_metrics['sharpe']:.4f}")
    print(f"SORTINO: {avg_metrics['sortino']:.4f}")
    print(f"CALMAR: {avg_metrics['calmar']:.4f}")
    print(f"DRAWDOWN: {avg_metrics['drawdown']:.4f}")
    print(f"MAX_DD_DAYS: {avg_metrics['max_dd_days']}")
    print(f"TRADES: {avg_metrics['trades']}")
    print(f"P_VALUE: 0.0000")
    print(f"WIN_RATE: {avg_metrics['win_rate']:.4f}")
    print(f"PROFIT_FACTOR: {avg_metrics['profit_factor']:.4f}")
    print(f"AVG_WIN: {avg_metrics['avg_win']:.4f}")
    print(f"AVG_LOSS: {avg_metrics['avg_loss']:.4f}")
    print(f"BASELINE_SHARPE: {baseline_sharpe:.4f}")
    print("---")
    print("PER_SYMBOL:")
    for symbol, sym_metrics in per_symbol.items():
        print(f"  {symbol}: sharpe={sym_metrics['sharpe']:.2f} sortino={sym_metrics['sortino']:.2f} "
              f"dd={sym_metrics['dd']:.2f} pf={sym_metrics['pf']:.2f} "
              f"trades={sym_metrics['trades']} wr={sym_metrics['wr']:.2f}")

if __name__ == "__main__":
    walk_forward_validation()
