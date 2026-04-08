#!/usr/bin/env python3
"""
Quant Autoresearch CLI
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from analysis import (
    analyze_volume,
    calculate_market_context,
    calculate_momentum,
    calculate_summary_stats,
    calculate_volatility,
    classify_regime,
    find_key_levels,
    render_analysis_report,
)
from config.vault import ensure_vault_directories, get_vault_paths
from core.research import (
    ensure_knowledge_notes,
    find_existing_research_note,
    render_research_report,
    search_arxiv,
    search_web,
)
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


@app.command("setup_vault")
def setup_vault():
    """Create the quant-autoresearch vault directory tree."""
    try:
        paths = get_vault_paths()
        statuses = ensure_vault_directories()
    except OSError as exc:
        typer.echo(f"Failed to prepare vault directories: {exc}")
        raise typer.Exit(code=1)

    typer.echo(f"Resolved vault root: {paths.vault_root}")
    typer.echo(f"Project root: {paths.project_root}")
    for status in statuses:
        state = "created" if status.created else "already existed"
        typer.echo(f"{status.name}: {state} -> {status.path}")


@app.command()
def research(
    query: str,
    depth: str = typer.Option("shallow", "--depth", help="Research depth: shallow or deep"),
    output: str = typer.Option("vault", "--output", help="Output target: vault or stdout"),
):
    """Run research and format the result as a vault-native note."""
    depth = depth.lower()
    output = output.lower()
    if depth not in {"shallow", "deep"}:
        typer.echo("Depth must be one of: shallow, deep")
        raise typer.Exit(code=1)
    if output not in {"vault", "stdout"}:
        typer.echo("Output must be one of: vault, stdout")
        raise typer.Exit(code=1)

    ensure_knowledge_notes()

    if output == "vault":
        existing_note = find_existing_research_note(query, get_vault_paths().research)
        if existing_note is not None:
            typer.echo(f"Reused existing research note: {existing_note}")
            raise typer.Exit(code=0)

    papers = search_arxiv(query)
    web_results = []
    if depth == "deep":
        if os.getenv("EXA_API_KEY") or os.getenv("SERPAPI_KEY"):
            web_results = search_web(query)
        else:
            typer.echo("Deep web search skipped: EXA_API_KEY / SERPAPI_KEY missing. Returning ArXiv-only report.")

    report, output_path, reused_existing = render_research_report(
        query=query,
        papers=papers,
        web_results=web_results,
        output=output,
        depth=depth,
    )
    if output == "stdout":
        typer.echo(report)
        raise typer.Exit(code=0)

    if reused_existing and output_path is not None:
        typer.echo(f"Reused existing research note: {output_path}")
    elif output_path is not None:
        typer.echo(f"Wrote research note: {output_path}")


def _slice_date_range(frame, start: Optional[str], end: Optional[str]):
    sliced = frame.sort_index()
    if start:
        sliced = sliced.loc[sliced.index >= start]
    if end:
        sliced = sliced.loc[sliced.index <= end]
    return sliced


@app.command()
def analyze(
    tickers: list[str] = typer.Argument(..., help="One or more tickers to analyze"),
    start: Optional[str] = typer.Option(None, "--start", help="Inclusive start date"),
    end: Optional[str] = typer.Option(None, "--end", help="Inclusive end date"),
    output: str = typer.Option("vault", "--output", help="Output target: vault or stdout"),
):
    """Generate a deterministic stock-analysis report from cached market data."""
    output = output.lower()
    if output not in {"vault", "stdout"}:
        typer.echo("Output must be one of: vault, stdout")
        raise typer.Exit(code=1)

    connector = DataConnector()
    frames = {}
    for ticker in tickers:
        frame = connector.load_symbol(ticker)
        if frame is None or frame.empty:
            typer.echo(
                f"No cached data found for {ticker} in data/cache. "
                "Run 'uv run python cli.py fetch "
                f"{ticker}' or 'uv run python cli.py setup_data' first."
            )
            raise typer.Exit(code=1)
        sliced = _slice_date_range(frame, start, end)
        if sliced.empty:
            typer.echo(f"No data available for {ticker} in the requested date range.")
            raise typer.Exit(code=1)
        frames[ticker] = sliced

    benchmark = frames.get("SPY")
    if benchmark is None:
        benchmark = connector.load_symbol("SPY")
    if benchmark is not None and not benchmark.empty:
        benchmark = _slice_date_range(benchmark, start, end)

    analyses = {}
    for ticker, frame in frames.items():
        benchmark_frame = benchmark if benchmark is not None else frame
        analyses[ticker] = {
            "momentum": calculate_momentum(frame),
            "volatility": calculate_volatility(frame),
            "volume": analyze_volume(frame),
            "price_structure": find_key_levels(frame),
            "regime": classify_regime(frame),
            "market_context": calculate_market_context(frame, benchmark_frame),
            "statistics": calculate_summary_stats(frame),
        }

    ensure_knowledge_notes()
    effective_start = start or frames[tickers[0]].index.min().strftime("%Y-%m-%d")
    effective_end = end or frames[tickers[0]].index.max().strftime("%Y-%m-%d")
    report, output_path = render_analysis_report(
        tickers=tickers,
        analyses=analyses,
        start=effective_start,
        end=effective_end,
        output=output,
        generated_at=datetime.now(),
    )

    if output == "stdout":
        typer.echo(report)
        raise typer.Exit(code=0)

    if output_path is not None:
        typer.echo(f"Wrote analysis note: {output_path}")


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
