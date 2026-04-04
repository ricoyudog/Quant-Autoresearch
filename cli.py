#!/usr/bin/env python3
"""
Quant Autoresearch CLI
"""
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from data.duckdb_connector import (
    DEFAULT_CACHE_PATH,
    build_daily_cache,
    get_trading_days,
    query_minute_data,
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
        from core.backtester import (
            security_check,
            walk_forward_validation,
        )
    except ImportError as e:
        typer.echo(f"Failed to import backtester: {e}")
        raise typer.Exit(code=1)

    is_safe, msg = security_check(strategy)
    if not is_safe:
        typer.echo(f"Security check failed: {msg}")
        raise typer.Exit(code=1)

    typer.echo("Security check passed")

    typer.echo("Starting walk-forward validation...")
    typer.echo("-" * 50)

    try:
        walk_forward_validation()
    except Exception as e:
        typer.echo(f"Backtest failed: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
