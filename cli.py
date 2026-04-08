#!/usr/bin/env python3
"""Quant Autoresearch CLI."""

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import typer

sys.path.append(str(Path(__file__).parent / "src"))

from data.duckdb_connector import (
    DEFAULT_CACHE_PATH,
    build_daily_cache,
    get_trading_days,
    query_minute_data,
    refresh_daily_cache,
)

app = typer.Typer(help="Quant Autoresearch")


def _echo_build_progress(start_date: str, end_date: str) -> None:
    del end_date
    typer.echo(f"Processing {start_date[:7]}...")


def _resolve_fetch_window(start: Optional[str], end: Optional[str]) -> tuple[str, str]:
    if bool(start) != bool(end):
        typer.echo("Provide both --start and --end together, or omit both to use the default 5-trading-day window.")
        raise typer.Exit(code=1)
    if start and end:
        return start, end

    trading_days = get_trading_days()
    if not trading_days:
        typer.echo("No trading days available in the daily cache. Run 'setup-data' first.")
        raise typer.Exit(code=1)

    window_days = trading_days[-5:]
    return window_days[0], window_days[-1]


def _combine_minute_frames(minute_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = [frame for _, frame in minute_data.items() if not frame.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _configure_backtest_env(
    strategy: str,
    start: Optional[str],
    end: Optional[str],
    universe_size: Optional[int],
) -> None:
    os.environ["STRATEGY_FILE"] = strategy

    if start is not None and end is not None:
        os.environ["BACKTEST_START_DATE"] = start
        os.environ["BACKTEST_END_DATE"] = end
    else:
        os.environ.pop("BACKTEST_START_DATE", None)
        os.environ.pop("BACKTEST_END_DATE", None)

    if universe_size is not None:
        os.environ["BACKTEST_UNIVERSE_SIZE"] = str(universe_size)
    else:
        os.environ.pop("BACKTEST_UNIVERSE_SIZE", None)


def load_strategy_class(strategy_path: str):
    """Load a strategy class from disk using the existing sandbox rules."""
    from RestrictedPython import compile_restricted, safe_builtins
    from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
    from RestrictedPython.Guards import safer_getattr

    from core.backtester import find_strategy_class, security_check

    is_safe, message = security_check(strategy_path)
    if not is_safe:
        raise ValueError(f"Security check failed: {message}")

    with open(strategy_path, "r", encoding="utf-8") as handle:
        strategy_lines = handle.readlines()

    sanitized_code = []
    for line in strategy_lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        sanitized_code.append(line)

    safe_globals = {
        "__builtins__": safe_builtins,
        "_getattr_": safer_getattr,
        "_write_": lambda value: value,
        "_getiter_": default_guarded_getiter,
        "_getitem_": default_guarded_getitem,
        "__name__": "sandbox",
        "__metaclass__": type,
        "pd": pd,
        "np": np,
    }

    sandbox_locals = {}
    byte_code = compile_restricted("".join(sanitized_code), filename="strategy.py", mode="exec")
    exec(byte_code, safe_globals, sandbox_locals)

    strategy_class, _ = find_strategy_class(sandbox_locals)
    if not strategy_class:
        raise ValueError("No class with generate_signals found in strategy file")

    return strategy_class


def _coerce_strategy_signals(raw_signals, symbol: str, index: pd.Index) -> pd.Series:
    """Normalize strategy output for a single symbol to an aligned Series."""
    signal_values = raw_signals
    if isinstance(raw_signals, dict):
        signal_values = raw_signals.get(symbol, pd.Series(0.0, index=index))

    if isinstance(signal_values, pd.Series):
        return signal_values.reindex(index).fillna(0.0)

    return pd.Series(signal_values, index=index).fillna(0.0)


def compute_combined_strategy_returns(strategy_class, data: dict[str, pd.DataFrame]) -> pd.Series:
    """Compute combined net returns across all symbols for regime analysis."""
    combined_returns = []

    for symbol, df in data.items():
        if df is None or df.empty:
            continue

        strategy = strategy_class()
        try:
            raw_signals = strategy.generate_signals(df.copy())
        except Exception:
            raw_signals = strategy.generate_signals({symbol: df.copy()})

        signals = _coerce_strategy_signals(raw_signals, symbol, df.index)
        lagged_signals = signals.shift(1).fillna(0)
        trade_changes = lagged_signals.diff().abs().fillna(0)
        volatility = df["volatility"] if "volatility" in df.columns else pd.Series(0.0, index=df.index)
        slippage = volatility.fillna(0) * 0.1
        costs = trade_changes * (0.0005 + slippage)
        net_returns = (df["returns"] * lagged_signals) - costs
        combined_returns.append(net_returns)

    if not combined_returns:
        return pd.Series(dtype=float)

    return pd.concat(combined_returns, axis=1).mean(axis=1).fillna(0)


def _usable_market_data(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Filter out empty cache entries before downstream validation."""
    return {name: df for name, df in data.items() if df is not None and not df.empty}


def _select_regime_market_data(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Resolve the market benchmark used for regime validation."""
    usable_data = _usable_market_data(data)
    if not usable_data:
        raise ValueError("data_config must contain at least one dataframe")

    if len(usable_data) == 1:
        return next(iter(usable_data.values()))

    if "SPY" in usable_data:
        return usable_data["SPY"]

    raise ValueError("Regime validation requires a single symbol or cached SPY benchmark")


def _cpcv_verdict(result: dict) -> str:
    pct_positive = float(result.get("pct_positive", 0.0))
    if pct_positive > 0.8:
        return "STRONG"
    if pct_positive >= 0.6:
        return "MODERATE"
    return "WEAK"


def _regime_verdict(result: dict[str, dict[str, float]]) -> str:
    positive_returns = [max(metrics["return"], 0.0) for metrics in result.values()]
    total_positive = sum(positive_returns)
    if total_positive <= 0:
        return "BALANCED"

    concentration = max(positive_returns) / total_positive
    if concentration > 0.7:
        return "CONCENTRATED"
    return "BALANCED"


@app.command()
def fetch(
    symbol: str,
    start: Optional[str] = typer.Option(None, "--start", help="Start date in YYYY-MM-DD format"),
    end: Optional[str] = typer.Option(None, "--end", help="End date in YYYY-MM-DD format"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write CSV output to this file"),
):
    """Fetch minute-level market data for a specific symbol."""
    try:
        resolved_start, resolved_end = _resolve_fetch_window(start, end)
        minute_data = query_minute_data([symbol], resolved_start, resolved_end)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Fetch failed: {exc}")
        raise typer.Exit(code=1) from exc

    combined = _combine_minute_frames(minute_data)

    if combined.empty:
        typer.echo(f"No minute data found for {symbol} between {resolved_start} and {resolved_end}.")
        raise typer.Exit(code=1)

    csv_output = combined.to_csv(index=False)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(csv_output, encoding="utf-8")
        typer.echo(f"Wrote minute data for {symbol} to {output}")
        return

    typer.echo(csv_output, nl=False)


@app.command()
def setup_data(force: bool = typer.Option(False, "--force", help="Rebuild the daily DuckDB cache from scratch")):
    """Build the DuckDB daily cache used by the V2 data pipeline."""
    cache_path = DEFAULT_CACHE_PATH

    if cache_path.exists():
        if not force:
            typer.echo(f"Daily cache already exists at {cache_path}. Use --force to rebuild.")
            return

        typer.echo(f"Rebuilding daily cache at {cache_path}...")
        cache_path.unlink()
    else:
        typer.echo(f"Building daily cache at {cache_path}...")

    build_daily_cache(output_path=cache_path, progress_callback=_echo_build_progress)
    typer.echo(f"Daily cache ready at {cache_path}")


@app.command()
def backtest(
    strategy: str = typer.Option("src/strategies/active_strategy.py", "--strategy", "-s", help="Path to strategy file"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date in YYYY-MM-DD format"),
    end: Optional[str] = typer.Option(None, "--end", help="End date in YYYY-MM-DD format"),
    universe_size: Optional[int] = typer.Option(None, "--universe-size", help="Maximum number of tickers to backtest"),
):
    """Run the V2 minute-mode backtest on a strategy."""
    typer.echo(f"Running backtest with strategy: {strategy}")

    strategy_path = Path(strategy)
    if not strategy_path.exists():
        typer.echo(f"Strategy file not found: {strategy}")
        raise typer.Exit(code=1)

    if bool(start) != bool(end):
        typer.echo("Provide both --start and --end together, or omit both to use the full daily-cache range.")
        raise typer.Exit(code=1)

    if universe_size is not None and universe_size <= 0:
        typer.echo("--universe-size must be greater than 0.")
        raise typer.Exit(code=1)

    _configure_backtest_env(strategy, start, end, universe_size)

    try:
        from core.backtester import security_check, walk_forward_validation
    except ImportError as exc:
        typer.echo(f"Failed to import backtester: {exc}")
        raise typer.Exit(code=1) from exc

    is_safe, msg = security_check(strategy)
    if not is_safe:
        typer.echo(f"Security check failed: {msg}")
        raise typer.Exit(code=1)

    typer.echo("Security check passed")
    typer.echo("Starting walk-forward validation...")
    typer.echo("-" * 50)

    try:
        walk_forward_validation()
    except Exception as exc:
        typer.echo(f"Backtest failed: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def update_data():
    """Refresh the DuckDB daily cache with newly available sessions."""
    cache_path = DEFAULT_CACHE_PATH
    if cache_path.exists():
        typer.echo(f"Updating daily cache at {cache_path}...")
    else:
        typer.echo(f"Daily cache missing at {cache_path}. Building from scratch...")

    try:
        result = refresh_daily_cache(output_path=cache_path, progress_callback=_echo_build_progress)
    except Exception as exc:
        typer.echo(f"Update failed: {exc}")
        raise typer.Exit(code=1) from exc

    latest_session_date = result.get("latest_session_date")
    if result["mode"] == "up_to_date":
        typer.echo(f"Daily cache already up to date at {cache_path} (latest session date: {latest_session_date}).")
        return

    if result["mode"] == "rebuilt":
        typer.echo(f"Daily cache rebuilt at {cache_path} (latest session date: {latest_session_date}).")
        return

    typer.echo(f"Daily cache updated at {cache_path} (latest session date: {latest_session_date}).")


@app.command()
def validate(
    method: str = typer.Option(..., "--method", "-m", help="Validation method: cpcv, regime, stability"),
    strategy: str = typer.Option("src/strategies/active_strategy.py", "--strategy", "-s", help="Path to strategy file"),
    symbols: Optional[str] = typer.Option(None, "--symbols", "-y", help="Comma-separated symbol list (default: all cached)"),
    groups: int = typer.Option(8, "--groups", help="Number of CPCV groups"),
    test_groups: int = typer.Option(2, "--test-groups", help="Number of CPCV test groups"),
    perturbation: float = typer.Option(0.2, "--perturbation", help="Parameter perturbation range"),
    steps: int = typer.Option(5, "--steps", help="Number of perturbation steps"),
):
    """Run advanced validation tools for overfit defense."""
    normalized_method = method.lower()
    if normalized_method not in {"cpcv", "regime", "stability"}:
        typer.echo(f"Invalid validation method: {method}")
        raise typer.Exit(code=1)

    strategy_path = Path(strategy)
    if not strategy_path.exists():
        typer.echo(f"Strategy file not found: {strategy}")
        raise typer.Exit(code=1)

    try:
        strategy_class = load_strategy_class(strategy)
    except Exception as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    try:
        from core.backtester import load_data
    except ImportError as exc:
        typer.echo(f"Failed to import backtester: {exc}")
        raise typer.Exit(code=1) from exc

    data = load_data()
    if not data:
        typer.echo("No cached data found. Run 'setup-data' or 'fetch' first.")
        raise typer.Exit(code=1)

    if symbols:
        symbol_list = [symbol.strip() for symbol in symbols.split(",")]
        missing_symbols = [symbol for symbol in symbol_list if symbol not in data]
        if missing_symbols:
            typer.echo(f"Warning: symbols not cached: {', '.join(missing_symbols)}")
        data = {name: df for name, df in data.items() if name in symbol_list}
        if not data:
            typer.echo("No valid symbols found after filtering")
            raise typer.Exit(code=1)

    try:
        output_lines: list[str]
        if normalized_method == "cpcv":
            from validation.cpcv import run_cpcv

            result = run_cpcv(strategy_class, data, n_groups=groups, n_test=test_groups)
            output_lines = [
                "METHOD: CPCV",
                f"MEAN_SHARPE: {result['mean_sharpe']:.4f}",
                f"STD_SHARPE: {result['std_sharpe']:.4f}",
                f"PCT_POSITIVE: {result['pct_positive']:.4f}",
                f"WORST_SHARPE: {result['worst_sharpe']:.4f}",
                f"BEST_SHARPE: {result['best_sharpe']:.4f}",
                f"VERDICT: {_cpcv_verdict(result)}",
            ]
        elif normalized_method == "regime":
            from validation.regime import regime_analysis

            market_data = _select_regime_market_data(data)
            strategy_returns = compute_combined_strategy_returns(strategy_class, data)
            result = regime_analysis(strategy_returns, market_data)
            output_lines = ["METHOD: REGIME"]
            for regime_name, metrics in result.items():
                output_lines.append(
                    f"{regime_name.upper()}: sharpe={metrics['sharpe']:.4f} "
                    f"return={metrics['return']:.4f} count={metrics['count']} "
                    f"win_rate={metrics['win_rate']:.4f}"
                )
            output_lines.append(f"VERDICT: {_regime_verdict(result)}")
        else:
            from validation.stability import parameter_stability_test

            result = parameter_stability_test(
                strategy_class,
                data,
                perturbation=perturbation,
                steps=steps,
            )
            output_lines = [
                "METHOD: STABILITY",
                f"OVERALL_STABILITY: {result['overall_stability']:.4f}",
            ]
            for parameter_name, metrics in result["parameters"].items():
                output_lines.append(
                    f"{parameter_name.upper()}: stability={metrics['stability']:.4f} "
                    f"peak={metrics['peak_sharpe']:.4f} min={metrics['min_sharpe']:.4f}"
                )
            if result.get("message"):
                output_lines.append(f"MESSAGE: {result['message']}")
            output_lines.append(f"VERDICT: {result['verdict']}")
    except Exception as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo("---")
    for line in output_lines:
        typer.echo(line)
    typer.echo("---")


if __name__ == "__main__":
    app()
