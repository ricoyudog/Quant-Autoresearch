from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Dict

import yaml

from config.vault import ensure_vault_directories, get_vault_paths

from .market_context import calculate_market_context
from .regime import classify_regime
from .technical import (
    analyze_volume,
    calculate_momentum,
    calculate_summary_stats,
    calculate_volatility,
    find_key_levels,
)


def _format_float(value: float | None, digits: int = 4) -> str:
    if value is None or not isfinite(value):
        return "N/A"
    return f"{value:.{digits}f}"


def _format_percent(value: float | None, digits: int = 2) -> str:
    if value is None or not isfinite(value):
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def _format_regime_name(value: str) -> str:
    return value.replace("_", " ").title()


def format_analysis_report(
    tickers: list[str],
    analyses: Dict[str, Dict[str, object]],
    start: str,
    end: str,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()
    frontmatter = {
        "note_type": "research",
        "research_type": "stock-analysis",
        "tickers": tickers,
        "date": generated_at.strftime("%Y-%m-%d"),
        "period": f"{start} to {end}",
        "tags": ["stock-analysis", *tickers],
    }
    lines = [
        "---",
        yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
        "---",
        "",
        f"# Stock Analysis: {', '.join(tickers)}",
        "",
    ]

    for ticker in tickers:
        analysis = analyses[ticker]
        momentum = analysis["momentum"]
        volatility = analysis["volatility"]
        regime = analysis["regime"]
        price_structure = analysis["price_structure"]
        market_context = analysis["market_context"]
        statistics = analysis["statistics"]

        lines.extend(
            [
                f"## Executive Summary ({ticker})",
                f"- **Regime**: {_format_regime_name(regime['current'])}",
                f"- **Momentum (20d)**: {_format_percent(momentum['roc_20d'])}",
                f"- **Volatility (20d)**: {_format_percent(volatility['vol_20d'])}",
                f"- **Price**: {_format_float(price_structure['close'], 2)}",
                "",
                "## Momentum",
                f"- 5d ROC: {_format_percent(momentum['roc_5d'])}",
                f"- 20d ROC: {_format_percent(momentum['roc_20d'])}",
                f"- 60d ROC: {_format_percent(momentum['roc_60d'])}",
                "",
                "## Volatility",
                f"- 5d realized vol: {_format_percent(volatility['vol_5d'])}",
                f"- 20d realized vol: {_format_percent(volatility['vol_20d'])}",
                f"- 60d realized vol: {_format_percent(volatility['vol_60d'])}",
                "",
                "## Regime Classification",
                f"- Current: {_format_regime_name(regime['current'])}",
                f"- Vol percentile: {_format_float(regime['vol_percentile'], 2)}",
                f"- Distribution: {regime['distribution']}",
                "",
                "## Price Structure",
                f"- 60d High: {_format_float(price_structure['high_60d'], 2)}",
                f"- 60d Low: {_format_float(price_structure['low_60d'], 2)}",
                f"- VWAP: {_format_float(price_structure['vwap'], 2)}",
                f"- Pct from high: {_format_percent(price_structure['pct_from_high'])}",
                f"- Pct from low: {_format_percent(price_structure['pct_from_low'])}",
                "",
                "## Market Context",
                f"- Correlation to SPY: {_format_float(market_context['correlation_to_spy'], 2)}",
                f"- Distance from 50d MA: {_format_percent(market_context['distance_from_50d_ma'])}",
                f"- Distance from 200d MA: {_format_percent(market_context['distance_from_200d_ma'])}",
                "",
                "## Statistics",
                f"- Sharpe: {_format_float(statistics['sharpe'], 2)}",
                f"- Max Drawdown: {_format_percent(statistics['max_drawdown'])}",
                f"- Win Rate: {_format_percent(statistics['win_rate'])}",
                f"- Avg Daily Range: {_format_percent(statistics['avg_daily_range'])}",
                "",
                "## Strategy Implications",
                "- Use this deterministic report as structured context for strategy design and note-taking.",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_analysis_report(
    tickers: list[str],
    analyses: Dict[str, Dict[str, object]],
    start: str,
    end: str,
    output: str = "vault",
    generated_at: datetime | None = None,
) -> tuple[str, Path | None]:
    generated_at = generated_at or datetime.now()
    report = format_analysis_report(tickers, analyses, start, end, generated_at=generated_at)
    if output == "stdout":
        return report, None

    ensure_vault_directories()
    paths = get_vault_paths()
    slug = "-".join(ticker.lower() for ticker in tickers)
    note_path = paths.research / f"{generated_at.strftime('%Y-%m-%d')}-{slug}-analysis.md"
    note_path.write_text(report)
    return report, note_path
