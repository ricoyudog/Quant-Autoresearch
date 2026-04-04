import os
import subprocess
import tempfile
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import pandas as pd

DEFAULT_CACHE_PATH = Path("data/daily_cache.duckdb")
MINUTE_AGGS_CLI = Path(
    os.environ.get(
        "MINUTE_AGGS_CLI",
        "/Users/chunsingyu/softwares/massive-minute-aggs-parquet/.venv/bin/minute-aggs",
    )
)
DATASET_ROOT = os.path.expanduser(
    os.environ.get(
        "MINUTE_AGGS_DATASET_ROOT",
        "~/Library/Mobile Documents/com~apple~CloudDocs/massive data/us_stocks_sip/minute_aggs_parquet_v1",
    )
)
QUERY_TIMEOUT_SECONDS = 300
DAILY_CACHE_START = date(2021, 3, 1)

DAILY_BARS_TABLE_SQL = """
CREATE TABLE daily_bars (
    ticker VARCHAR,
    session_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    transactions INTEGER,
    vwap DOUBLE,
    PRIMARY KEY (ticker, session_date)
)
"""

__all__ = [
    "build_daily_cache",
    "get_trading_days",
    "load_daily_data",
    "query_minute_data",
]


def _resolve_cache_path(output_path: Optional[os.PathLike | str] = None) -> Path:
    if output_path is None:
        return DEFAULT_CACHE_PATH
    return Path(output_path)


def _iter_month_ranges(start: date, end: date) -> List[Tuple[str, str]]:
    current = start.replace(day=1)
    last_month = end.replace(day=1)
    ranges: List[Tuple[str, str]] = []

    while current <= last_month:
        last_day = monthrange(current.year, current.month)[1]
        month_end = date(current.year, current.month, last_day)
        range_start = start if current == start.replace(day=1) else current
        range_end = end if current == last_month else month_end
        ranges.append((range_start.isoformat(), range_end.isoformat()))

        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return ranges


def _build_daily_cache_query(start_date: str, end_date: str) -> str:
    return f"""
        SELECT
            ticker,
            session_date,
            arg_min(open, window_start_ns) AS open,
            max(high) AS high,
            min(low) AS low,
            arg_max(close, window_start_ns) AS close,
            sum(volume) AS volume,
            sum(transactions) AS transactions,
            sum(close * volume) / NULLIF(sum(volume), 0) AS vwap
        FROM minute_aggs
        WHERE session_date BETWEEN DATE '{start_date}' AND DATE '{end_date}'
        GROUP BY ticker, session_date
        ORDER BY session_date, ticker
    """


def _read_daily_cache_frame(db_path: Path, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    connection = duckdb.connect(str(db_path), read_only=True)
    clauses: List[str] = []
    params: List[str] = []

    if start_date:
        clauses.append("session_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("session_date <= ?")
        params.append(end_date)

    query = "SELECT * FROM daily_bars"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY session_date, ticker"

    try:
        return connection.execute(query, params).fetchdf()
    finally:
        connection.close()


def build_daily_cache(output_path: Optional[os.PathLike | str] = None) -> None:
    """Build the local DuckDB daily-bar cache from the minute-aggs dataset."""
    cache_path = _resolve_cache_path(output_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(cache_path))
    try:
        connection.execute("DROP TABLE IF EXISTS daily_bars")
        connection.execute(DAILY_BARS_TABLE_SQL)

        for start_date, end_date in _iter_month_ranges(DAILY_CACHE_START, date.today()):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as handle:
                csv_path = Path(handle.name)

            command = [
                str(MINUTE_AGGS_CLI),
                "sql",
                "--dataset-root",
                DATASET_ROOT,
                "--query",
                _build_daily_cache_query(start_date, end_date),
                "--output",
                str(csv_path),
            ]

            try:
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=QUERY_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(f"Timed out building daily cache for {start_date} to {end_date}") from exc
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"minute-aggs sql failed for {start_date} to {end_date}") from exc

            try:
                if not csv_path.exists() or csv_path.stat().st_size == 0:
                    continue

                escaped_csv_path = str(csv_path).replace("'", "''")
                connection.execute(
                    f"""
                    INSERT INTO daily_bars
                    SELECT
                        ticker::VARCHAR,
                        session_date::DATE,
                        open::DOUBLE,
                        high::DOUBLE,
                        low::DOUBLE,
                        close::DOUBLE,
                        volume::DOUBLE,
                        transactions::INTEGER,
                        vwap::DOUBLE
                    FROM read_csv_auto('{escaped_csv_path}', header=True)
                    """
                )
            finally:
                csv_path.unlink(missing_ok=True)
    finally:
        connection.close()


def load_daily_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Load daily bars from the local DuckDB cache."""
    return _read_daily_cache_frame(_resolve_cache_path(), start_date, end_date)


def get_trading_days(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
    """Return ordered trading-day strings from the local daily cache."""
    frame = _read_daily_cache_frame(_resolve_cache_path(), start_date, end_date)
    if frame.empty:
        return []

    dates = frame["session_date"].drop_duplicates().sort_values()
    return [value.strftime("%Y-%m-%d") for value in dates]


def query_minute_data(tickers: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """Query minute bars for a ticker subset and split them into per-ticker dataframes."""
    if not tickers:
        return {}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as handle:
        output_path = Path(handle.name)

    command = [
        str(MINUTE_AGGS_CLI),
        "bars",
        "--dataset-root",
        DATASET_ROOT,
        "--symbols",
        *tickers,
        "--start",
        start_date,
        "--end",
        end_date,
        "--output",
        str(output_path),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"Timed out querying minute data for {', '.join(tickers)} between {start_date} and {end_date}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"minute-aggs bars failed for {', '.join(tickers)} between {start_date} and {end_date}"
        ) from exc

    try:
        if not output_path.exists():
            raise FileNotFoundError(f"minute-aggs did not create output file: {output_path}")

        if output_path.stat().st_size == 0:
            return {}

        frame = pd.read_csv(output_path)
        if frame.empty:
            return {}

        if "session_date" in frame.columns:
            frame["session_date"] = pd.to_datetime(frame["session_date"])

        sort_columns = [column for column in ["ticker", "session_date", "window_start_ns"] if column in frame.columns]
        if sort_columns:
            frame = frame.sort_values(sort_columns)

        grouped: Dict[str, pd.DataFrame] = {}
        for ticker, group in frame.groupby("ticker", sort=False):
            grouped[str(ticker)] = group.reset_index(drop=True)
        return grouped
    finally:
        output_path.unlink(missing_ok=True)
