from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "004-martinluk-primitive"
    / "run_phase5_bounded_replay.py"
)
REQUEST_PATH = MODULE_PATH.with_name("phase5-1-replay-request.json")
PROTECTED_PHASE5_OUTPUTS = [
    MODULE_PATH.with_name("phase5-bounded-validation-report.json"),
    MODULE_PATH.with_name("phase5-bounded-validation-report.md"),
    MODULE_PATH.with_name("phase5-dry-run-report.json"),
]


def load_phase5_1_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "martinluk_phase5_bounded_replay",
        MODULE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureLoaders:
    daily_calls: list[tuple[str, str]]
    minute_calls: list[tuple[tuple[str, ...], str, str]]

    def __init__(self) -> None:
        self.daily_calls = []
        self.minute_calls = []

    def load_daily_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        self.daily_calls.append((start_date, end_date))
        # Include an overfetched symbol; the runner must filter before strategy calls.
        return pd.DataFrame(
            {
                "ticker": ["SOFI", "SMCI", "COIN", "LMND", "QQQ", "EXTRA"],
                "session_date": [start_date] * 6,
                "open": [10.0] * 6,
                "high": [11.0] * 6,
                "low": [9.0] * 6,
                "close": [10.5] * 6,
                "volume": [1000] * 6,
            }
        )

    def query_minute_data(self, tickers: list[str], start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
        self.minute_calls.append((tuple(tickers), start_date, end_date))
        return {
            ticker: pd.DataFrame(
                {
                    "ticker": [ticker],
                    "session_date": [start_date],
                    "open": [10.0],
                    "high": [11.0],
                    "low": [9.0],
                    "close": [10.5],
                    "volume": [1000],
                }
            )
            for ticker in tickers
        }


class NoSignalStrategy:
    seen_symbols: list[str] = []

    def select_universe(self, *_args: Any, **_kwargs: Any) -> list[str]:  # pragma: no cover - must not be called
        raise AssertionError("Phase 5.1 must not call select_universe")

    def generate_signals(self, frames: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
        type(self).seen_symbols.extend(sorted(frames))
        return {symbol: pd.Series([0.0], index=frame.index) for symbol, frame in frames.items()}

    def get_signal_trace(self) -> dict[str, Any]:
        return {"signals": []}


def test_phase5_1_fixture_replay_writes_artifacts_and_preserves_phase5_outputs(tmp_path: Path) -> None:
    phase5_1 = load_phase5_1_module()
    before = {path: path.read_bytes() for path in PROTECTED_PHASE5_OUTPUTS}
    loaders = FixtureLoaders()

    result = phase5_1.run_bounded_replay(
        request_path=REQUEST_PATH,
        query_ledger_path=tmp_path / "phase5-1-query-ledger.json",
        runtime_path=tmp_path / "phase5-1-runtime.json",
        output_json_path=tmp_path / "phase5-1-bounded-replay-report.json",
        output_md_path=tmp_path / "phase5-1-bounded-replay-report.md",
        loaders=loaders,
        strategy_cls=NoSignalStrategy,
    )

    assert result["ok"] is True
    for path in before:
        assert path.read_bytes() == before[path]
    assert loaders.daily_calls
    assert loaders.minute_calls
    assert all(len(call[0]) == 1 for call in loaders.minute_calls)

    query_ledger = json.loads((tmp_path / "phase5-1-query-ledger.json").read_text())
    runtime = json.loads((tmp_path / "phase5-1-runtime.json").read_text())
    report = json.loads((tmp_path / "phase5-1-bounded-replay-report.json").read_text())

    assert runtime["loader_call_count"] == query_ledger["query_count"]
    assert report["query_ledger_sha256"] == phase5_1.sha256_path(tmp_path / "phase5-1-query-ledger.json")
    assert report["runtime_sha256"] == runtime["runtime_sha256"]
    assert report["overall_run_status"] == "research_only"
    assert report["promoted"] is False
    assert report["controls_counted_toward_promotion"] == 0
    assert report["audit_only_summary"]["market_data_query_allowed"] is False
    assert all(row["realized_outcome"]["realized_account_pnl"] == "N/A" for row in report["row_results"])
    assert "profit proof" in report["no_overclaim_statement"]
    assert "exact-fill" in report["no_overclaim_statement"]
    assert "EXTRA" not in set(NoSignalStrategy.seen_symbols)
