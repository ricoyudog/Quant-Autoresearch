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

from data.connector import DataConnector
from data.preprocessor import prepare_data as prepare_all_data

app = typer.Typer(help="Quant Autoresearch")


def load_strategy_class(strategy_path: str):
    """Load a strategy class from disk using the existing sandbox rules."""
    from RestrictedPython import compile_restricted, safe_builtins
    from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
    from RestrictedPython.Guards import safer_getattr

    from core.backtester import find_strategy_class, security_check

    is_safe, message = security_check(strategy_path)
    if not is_safe:
        raise ValueError(f"Security check failed: {message}")

    with open(strategy_path, "r") as handle:
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

    strategy_class = find_strategy_class(sandbox_locals)
    if not strategy_class:
        raise ValueError("No class with generate_signals found in strategy file")

    return strategy_class


def compute_combined_strategy_returns(strategy_class, data: dict[str, pd.DataFrame]) -> pd.Series:
    """Compute combined net returns across all symbols for regime analysis."""
    strategy = strategy_class()
    combined_returns = []

    for _, df in data.items():
        if df.empty:
            continue

        signals = strategy.generate_signals(df.copy())
        if not isinstance(signals, pd.Series):
            signals = pd.Series(signals, index=df.index)

        signals = signals.reindex(df.index).fillna(0)
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
    except Exception as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    try:
        from core.backtester import load_data
    except ImportError as e:
        typer.echo(f"Failed to import backtester: {e}")
        raise typer.Exit(code=1)

    data = load_data()
    if not data:
        typer.echo("No cached data found. Run 'setup_data' or 'fetch' first.")
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

    typer.echo("---")

    if normalized_method == "cpcv":
        from validation.cpcv import run_cpcv

        result = run_cpcv(strategy_class, data, n_groups=groups, n_test=test_groups)
        typer.echo(f"METHOD: CPCV")
        typer.echo(f"MEAN_SHARPE: {result['mean_sharpe']:.4f}")
        typer.echo(f"STD_SHARPE: {result['std_sharpe']:.4f}")
        typer.echo(f"PCT_POSITIVE: {result['pct_positive']:.4f}")
        typer.echo(f"WORST_SHARPE: {result['worst_sharpe']:.4f}")
        typer.echo(f"BEST_SHARPE: {result['best_sharpe']:.4f}")
        typer.echo(f"VERDICT: {_cpcv_verdict(result)}")

    elif normalized_method == "regime":
        from validation.regime import regime_analysis

        strategy_returns = compute_combined_strategy_returns(strategy_class, data)
        market_data = next(iter(data.values()))
        result = regime_analysis(strategy_returns, market_data)
        typer.echo("METHOD: REGIME")
        for regime_name, metrics in result.items():
            typer.echo(
                f"{regime_name.upper()}: sharpe={metrics['sharpe']:.4f} "
                f"return={metrics['return']:.4f} count={metrics['count']} "
                f"win_rate={metrics['win_rate']:.4f}"
            )
        typer.echo(f"VERDICT: {_regime_verdict(result)}")

    else:
        from validation.stability import parameter_stability_test

        result = parameter_stability_test(
            strategy_class,
            data,
            perturbation=perturbation,
            steps=steps,
        )
        typer.echo("METHOD: STABILITY")
        typer.echo(f"OVERALL_STABILITY: {result['overall_stability']:.4f}")
        for parameter_name, metrics in result["parameters"].items():
            typer.echo(
                f"{parameter_name.upper()}: stability={metrics['stability']:.4f} "
                f"peak={metrics['peak_sharpe']:.4f} min={metrics['min_sharpe']:.4f}"
            )
        if result.get("message"):
            typer.echo(f"MESSAGE: {result['message']}")
        typer.echo(f"VERDICT: {result['verdict']}")

    typer.echo("---")


if __name__ == "__main__":
    app()
