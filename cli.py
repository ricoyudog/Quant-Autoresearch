#!/usr/bin/env python3
"""
Quant Autoresearch CLI
"""
import os
import sys
from pathlib import Path
from typing import Optional

import typer

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from data.connector import DataConnector
from data.preprocessor import prepare_data as prepare_all_data

app = typer.Typer(help="Quant Autoresearch")


@app.command()
def fetch(symbol: str, start: str = "2020-01-01"):
    """Fetch market data for a specific symbol"""
    typer.echo(f"Fetching data for {symbol} starting from {start}...")
    connector = DataConnector()
    if connector.fetch_and_cache(symbol, start):
        typer.echo(f"Successfully cached {symbol}")
    else:
        typer.echo(f"Failed to fetch data for {symbol}")


@app.command()
def setup_data():
    """Download default market data symbols (SPY, BTC, etc.)"""
    typer.echo("Preparing default research dataset...")
    prepare_all_data()


@app.command()
def backtest(
    strategy: str = typer.Option("src/strategies/active_strategy.py", "--strategy", "-s", help="Path to strategy file"),
    symbols: Optional[str] = typer.Option(None, "--symbols", "-y", help="Comma-separated symbol list (default: all cached)")
):
    """Run backtest on a strategy"""
    typer.echo(f"Running backtest with strategy: {strategy}")

    # Check strategy file exists
    strategy_path = Path(strategy)
    if not strategy_path.exists():
        typer.echo(f"Strategy file not found: {strategy}")
        raise typer.Exit(code=1)

    # Import backtester functions
    try:
        from core.backtester import (
            security_check,
            load_data,
            walk_forward_validation,
        )
    except ImportError as e:
        typer.echo(f"Failed to import backtester: {e}")
        raise typer.Exit(code=1)

    # Set strategy file via environment
    os.environ["STRATEGY_FILE"] = strategy

    # Run security check first
    is_safe, msg = security_check(strategy)
    if not is_safe:
        typer.echo(f"Security check failed: {msg}")
        raise typer.Exit(code=1)

    typer.echo("Security check passed")

    # Load data to verify availability
    data = load_data()
    if not data:
        typer.echo("No cached data found. Run 'setup_data' or 'fetch' first.")
        raise typer.Exit(code=1)

    # Filter symbols if specified
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",")]
        missing = [s for s in symbol_list if s not in data]
        if missing:
            typer.echo(f"Warning: symbols not cached: {', '.join(missing)}")
        data = {k: v for k, v in data.items() if k in symbol_list}
        if not data:
            typer.echo("No valid symbols found after filtering")
            raise typer.Exit(code=1)
        typer.echo(f"Testing symbols: {', '.join(data.keys())}")
    else:
        typer.echo(f"Testing all cached symbols: {', '.join(data.keys())}")

    typer.echo("Starting walk-forward validation...")
    typer.echo("-" * 50)

    # Run the backtest
    try:
        # Temporarily monkey-patch load_data to use filtered data
        import core.backtester as bt_module
        original_load_data = bt_module.load_data
        bt_module.load_data = lambda: data

        walk_forward_validation()

        # Restore original
        bt_module.load_data = original_load_data
    except Exception as e:
        typer.echo(f"Backtest failed: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
