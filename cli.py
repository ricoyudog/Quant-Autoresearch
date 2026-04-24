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
    load_daily_data,
    query_minute_data,
    refresh_daily_cache,
)

from datetime import datetime

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
    find_reusable_research_note,
    render_research_report,
    search_arxiv,
    search_web,
)
from data.cache_connector import CacheConnector
from memory.experiment_memory import CONTINUATION_MANIFEST_PATH, refresh_research_base

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

    from core.backtester import find_strategy_class, security_check, validate_strategy_class_contract

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
        "max": max,
        "min": min,
        "pd": pd,
        "np": np,
    }

    sandbox_locals = {}
    byte_code = compile_restricted("".join(sanitized_code), filename="strategy.py", mode="exec")
    exec(byte_code, safe_globals, sandbox_locals)

    strategy_class = validate_strategy_class_contract(find_strategy_class(sandbox_locals))

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


def _slice_date_range(frame, start: Optional[str], end: Optional[str]):
    sliced = frame.sort_index()
    if start:
        sliced = sliced.loc[sliced.index >= start]
    if end:
        sliced = sliced.loc[sliced.index <= end]
    return sliced


def _clean_cached_market_frame(frame):
    cleaned = frame.sort_index()
    ohlc_columns = [column for column in ("Open", "High", "Low", "Close") if column in cleaned.columns]
    if ohlc_columns:
        cleaned = cleaned.dropna(subset=ohlc_columns, how="any")
    return cleaned


def _load_symbol_from_daily_cache(symbol: str, start: Optional[str], end: Optional[str]) -> Optional[pd.DataFrame]:
    try:
        frame = load_daily_data(start_date=start, end_date=end)
    except Exception:
        return None

    if frame is None or frame.empty or "ticker" not in frame.columns:
        return None

    symbol_frame = frame.loc[frame["ticker"] == symbol].copy()
    if symbol_frame.empty:
        return None

    symbol_frame["session_date"] = pd.to_datetime(symbol_frame["session_date"])
    symbol_frame = symbol_frame.sort_values("session_date").set_index("session_date")
    symbol_frame = symbol_frame.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "vwap": "VWAP",
        }
    )
    return symbol_frame


def _run_quietly(func, *args, **kwargs):
    from contextlib import redirect_stderr, redirect_stdout
    from io import StringIO

    sink = StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        return func(*args, **kwargs)


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


@app.command("refresh_research_base")
def refresh_research_base_command(
    manifest_path: str = typer.Option(
        str(CONTINUATION_MANIFEST_PATH),
        "--manifest-path",
        help="Path to the canonical continuation manifest written under the repo.",
    ),
):
    """Refresh the Obsidian-derived research base and emit a continuation manifest."""
    manifest = refresh_research_base(manifest_path=manifest_path)
    typer.echo(f"Manifest: {manifest['manifest_path']}")
    typer.echo(f"Index note: {manifest['index_note_path']}")
    typer.echo(f"Experiments parsed: {len(manifest['experiments'])}")

    current_baseline = manifest.get("current_baseline")
    if current_baseline is None:
        typer.echo("Current baseline: none")
    else:
        typer.echo(f"Current baseline: {current_baseline['title']}")
        typer.echo(f"Baseline note: {current_baseline['raw_note_path']}")
        typer.echo(f"Validation status: {current_baseline['validation_status']}")

    typer.echo(f"Rejected branches: {len(manifest['failed_branches'])}")
    next_experiment = manifest.get("next_recommended_experiment") or "none"
    typer.echo(f"Next experiment: {next_experiment}")


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
        existing_note = find_reusable_research_note(query, get_vault_paths().research, depth=depth)
        if existing_note is not None:
            typer.echo(f"Reused existing research note: {existing_note}")
            raise typer.Exit(code=0)

    papers = _run_quietly(search_arxiv, query) if output == "stdout" else search_arxiv(query)
    web_results = []
    if depth == "deep":
        if os.getenv("EXA_API_KEY") or os.getenv("SERPAPI_KEY"):
            web_results = _run_quietly(search_web, query) if output == "stdout" else search_web(query)
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

    connector = CacheConnector()
    frames = {}
    for ticker in tickers:
        frame = connector.load_symbol(ticker)
        if frame is None or frame.empty:
            frame = _load_symbol_from_daily_cache(ticker, start, end)
        if frame is None or frame.empty:
            typer.echo(
                f"No cached data found for {ticker} in data/cache or data/daily_cache.duckdb. "
                "Run 'uv run python cli.py setup-data' first or populate data/cache manually."
            )
            raise typer.Exit(code=1)
        cleaned = _clean_cached_market_frame(frame)
        sliced = _slice_date_range(cleaned, start, end)
        if sliced.empty:
            typer.echo(f"No data available for {ticker} in the requested date range.")
            raise typer.Exit(code=1)
        frames[ticker] = sliced

    benchmark = frames.get("SPY")
    if benchmark is None:
        benchmark = connector.load_symbol("SPY")
    if benchmark is None or benchmark.empty:
        benchmark = _load_symbol_from_daily_cache("SPY", start, end)
    if benchmark is not None and not benchmark.empty:
        benchmark = _slice_date_range(_clean_cached_market_frame(benchmark), start, end)
        if benchmark.empty:
            benchmark = None

    analyses = {}
    for ticker, frame in frames.items():
        analyses[ticker] = {
            "momentum": calculate_momentum(frame),
            "volatility": calculate_volatility(frame),
            "volume": analyze_volume(frame),
            "price_structure": find_key_levels(frame),
            "regime": classify_regime(frame),
            "market_context": calculate_market_context(frame, benchmark),
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
