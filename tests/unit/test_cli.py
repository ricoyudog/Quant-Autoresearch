import os
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from typer.testing import CliRunner

# Add root to path for imports
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

import cli
from cli import app

runner = CliRunner()


def help_registers_command(help_text: str, command_name: str) -> bool:
    return any(
        line.strip().startswith("│") and line.strip().strip("│").strip().startswith(f"{command_name} ")
        for line in help_text.splitlines()
    )


class TestCommandRegistration:
    """Tests for verifying which commands are registered in the CLI."""

    def test_setup_data_command_exists(self):
        """Verify setup_data is registered as a command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "setup-data" in result.stdout

    def test_fetch_command_exists(self):
        """Verify fetch is registered with symbol argument."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "fetch" in result.stdout

        # Verify it has SYMBOL argument by checking fetch --help
        result = runner.invoke(app, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "SYMBOL" in result.stdout
        assert "symbol" in result.stdout.lower()
        assert "--start" in result.stdout
        assert "--end" in result.stdout
        assert "--output" in result.stdout

    def test_update_data_command_exists(self):
        """Verify update_data is registered as a CLI command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "update-data" in result.stdout

        result = runner.invoke(app, ["update-data", "--help"])
        assert result.exit_code == 0

    def test_backtest_command_exists(self):
        """Verify backtest is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "backtest" in result.stdout

        result = runner.invoke(app, ["backtest", "--help"])
        assert result.exit_code == 0
        assert "--strategy" in result.stdout
        assert "--start" in result.stdout
        assert "--end" in result.stdout
        assert "--universe-size" in result.stdout

    def test_validate_command_exists(self):
        """Verify validate is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.stdout

    def test_run_command_removed(self):
        """Verify run is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # The run command from the old research loop should not exist
        assert not help_registers_command(result.stdout, "run")
        # Also verify it can't be invoked
        result = runner.invoke(app, ["run"])
        assert result.exit_code != 0

    def test_status_command_removed(self):
        """Verify status is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert not help_registers_command(result.stdout, "status")
        result = runner.invoke(app, ["status"])
        assert result.exit_code != 0

    def test_report_command_removed(self):
        """Verify report is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert not help_registers_command(result.stdout, "report")
        result = runner.invoke(app, ["report"])
        assert result.exit_code != 0

    def test_ingest_command_removed(self):
        """Verify ingest is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert not help_registers_command(result.stdout, "ingest")
        result = runner.invoke(app, ["ingest"])
        assert result.exit_code != 0

    def test_setup_vault_command_exists(self):
        """Verify setup_vault is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "setup_vault" in result.stdout

    def test_research_command_exists(self):
        """Verify research is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "research" in result.stdout

    def test_analyze_command_exists(self):
        """Verify analyze is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout


class TestBacktestCommandBehavior:
    """Tests for backtest command behavior with mocked dependencies."""

    @patch("core.backtester.walk_forward_validation")
    @patch("core.backtester.security_check")
    def test_backtest_invokes_backtester(
        self, mock_security_check, mock_walk_forward
    ):
        """Verify backtest command passes V2 runtime settings into the backtester."""
        mock_security_check.return_value = (True, "Safe")

        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass")
            strategy_path = f.name

        try:
            result = runner.invoke(
                app,
                [
                    "backtest",
                    "-s",
                    strategy_path,
                    "--start",
                    "2024-01-01",
                    "--end",
                    "2024-12-31",
                    "--universe-size",
                    "12",
                ],
            )
            assert result.exit_code == 0
            mock_security_check.assert_called_once_with(strategy_path)
            mock_walk_forward.assert_called_once()
            assert os.environ["STRATEGY_FILE"] == strategy_path
            assert os.environ["BACKTEST_START_DATE"] == "2024-01-01"
            assert os.environ["BACKTEST_END_DATE"] == "2024-12-31"
            assert os.environ["BACKTEST_UNIVERSE_SIZE"] == "12"
        finally:
            Path(strategy_path).unlink(missing_ok=True)
            os.environ.pop("STRATEGY_FILE", None)
            os.environ.pop("BACKTEST_START_DATE", None)
            os.environ.pop("BACKTEST_END_DATE", None)
            os.environ.pop("BACKTEST_UNIVERSE_SIZE", None)

    @patch("core.backtester.security_check")
    def test_backtest_missing_strategy_file_fails_before_runtime(
        self, mock_security_check
    ):
        """Verify a missing strategy file exits cleanly before runtime setup."""
        result = runner.invoke(app, ["backtest", "-s", "missing-strategy.py"])

        assert result.exit_code == 1
        assert "Strategy file not found" in result.stdout
        mock_security_check.assert_not_called()

    @patch("core.backtester.walk_forward_validation")
    @patch("core.backtester.security_check")
    def test_backtest_rejects_one_sided_date_ranges(
        self, mock_security_check, mock_walk_forward
    ):
        """Verify V2 backtest requires both start and end together."""
        mock_security_check.return_value = (True, "Safe")

        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass")
            strategy_path = f.name

        try:
            start_only = runner.invoke(app, ["backtest", "-s", strategy_path, "--start", "2024-01-01"])
            end_only = runner.invoke(app, ["backtest", "-s", strategy_path, "--end", "2024-12-31"])

            assert start_only.exit_code == 1
            assert end_only.exit_code == 1
            assert "Provide both --start and --end together" in start_only.stdout
            assert "Provide both --start and --end together" in end_only.stdout
            mock_security_check.assert_not_called()
            mock_walk_forward.assert_not_called()
        finally:
            Path(strategy_path).unlink(missing_ok=True)

    @patch("core.backtester.walk_forward_validation")
    @patch("core.backtester.security_check")
    def test_backtest_rejects_non_positive_universe_size(
        self, mock_security_check, mock_walk_forward
    ):
        """Verify V2 backtest rejects invalid universe-size overrides."""
        mock_security_check.return_value = (True, "Safe")

        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass")
            strategy_path = f.name

        try:
            result = runner.invoke(app, ["backtest", "-s", strategy_path, "--universe-size", "0"])

            assert result.exit_code == 1
            assert "--universe-size must be greater than 0" in result.stdout
            mock_security_check.assert_not_called()
            mock_walk_forward.assert_not_called()
        finally:
            Path(strategy_path).unlink(missing_ok=True)


class TestSetupDataCommandBehavior:
    """Tests for setup_data command behavior with the DuckDB cache."""

    @patch("cli.build_daily_cache")
    def test_setup_data_builds_daily_cache_when_missing(self, mock_build_daily_cache, monkeypatch, tmp_path):
        cache_path = tmp_path / "daily_cache.duckdb"
        monkeypatch.setattr(cli, "DEFAULT_CACHE_PATH", cache_path)

        def fake_build_daily_cache(*, output_path=None, progress_callback=None):
            assert output_path == cache_path
            assert progress_callback is not None
            progress_callback("2025-11-01", "2025-11-30")

        mock_build_daily_cache.side_effect = fake_build_daily_cache

        result = runner.invoke(app, ["setup-data"])

        assert result.exit_code == 0
        mock_build_daily_cache.assert_called_once()
        assert "Building daily cache" in result.stdout
        assert "Processing 2025-11" in result.stdout

    @patch("cli.build_daily_cache")
    def test_setup_data_skips_existing_cache_without_force(self, mock_build_daily_cache, monkeypatch, tmp_path):
        cache_path = tmp_path / "daily_cache.duckdb"
        cache_path.touch()
        monkeypatch.setattr(cli, "DEFAULT_CACHE_PATH", cache_path)

        result = runner.invoke(app, ["setup-data"])

        assert result.exit_code == 0
        mock_build_daily_cache.assert_not_called()
        assert "already exists" in result.stdout
        assert "--force" in result.stdout

    @patch("cli.build_daily_cache")
    def test_setup_data_force_rebuilds_existing_cache(self, mock_build_daily_cache, monkeypatch, tmp_path):
        cache_path = tmp_path / "daily_cache.duckdb"
        cache_path.touch()
        monkeypatch.setattr(cli, "DEFAULT_CACHE_PATH", cache_path)

        def fake_build_daily_cache(*, output_path=None, progress_callback=None):
            assert output_path == cache_path
            assert not cache_path.exists()
            assert progress_callback is not None
            progress_callback("2025-11-01", "2025-11-30")

        mock_build_daily_cache.side_effect = fake_build_daily_cache

        result = runner.invoke(app, ["setup-data", "--force"])

        assert result.exit_code == 0
        mock_build_daily_cache.assert_called_once()
        assert "Rebuilding daily cache" in result.stdout
        assert "Processing 2025-11" in result.stdout


class TestUpdateDataCommandBehavior:
    """Tests for update_data command behavior with the DuckDB cache."""

    def test_update_data_refreshes_daily_cache(self, monkeypatch, tmp_path):
        """Verify update_data delegates to the incremental refresh helper."""
        cache_path = tmp_path / "daily_cache.duckdb"
        cache_path.touch()
        monkeypatch.setattr(cli, "DEFAULT_CACHE_PATH", cache_path)

        calls = []

        def fake_refresh_daily_cache(*, output_path=None, progress_callback=None):
            calls.append(output_path)
            assert progress_callback is not None
            progress_callback("2025-11-01", "2025-11-30")
            return {
                "mode": "refreshed",
                "start_date": "2025-11-05",
                "end_date": "2025-11-30",
                "latest_session_date": "2025-11-30",
            }

        monkeypatch.setattr(cli, "refresh_daily_cache", fake_refresh_daily_cache, raising=False)

        result = runner.invoke(app, ["update-data"])

        assert result.exit_code == 0
        assert calls == [cache_path]
        assert "Updating daily cache" in result.stdout
        assert "Processing 2025-11" in result.stdout
        assert "2025-11-30" in result.stdout

    def test_update_data_reports_refresh_failure(self, monkeypatch, tmp_path):
        """Verify update_data converts refresh failures into a stable CLI message."""
        cache_path = tmp_path / "daily_cache.duckdb"
        monkeypatch.setattr(cli, "DEFAULT_CACHE_PATH", cache_path)

        def fail_refresh_daily_cache(*, output_path=None, progress_callback=None):
            raise RuntimeError("refresh failed")

        monkeypatch.setattr(cli, "refresh_daily_cache", fail_refresh_daily_cache, raising=False)

        result = runner.invoke(app, ["update-data"])

        assert result.exit_code == 1
        assert "Update failed" in result.stdout
        assert "refresh failed" in result.stdout


class TestFetchCommandBehavior:
    """Tests for fetch command behavior with mocked dependencies."""

    def test_fetch_uses_explicit_date_range_and_prints_csv(self, monkeypatch):
        """Verify fetch queries minute data for the requested range and prints CSV output."""
        calls = []

        def fake_query_minute_data(tickers, start_date, end_date):
            calls.append((tickers, start_date, end_date))
            return {
                "AAPL": pd.DataFrame(
                    {
                        "ticker": ["AAPL", "AAPL"],
                        "session_date": ["2025-11-03", "2025-11-03"],
                        "window_start_ns": [1, 2],
                        "open": [10.0, 10.5],
                        "high": [10.2, 10.7],
                        "low": [9.9, 10.4],
                        "close": [10.1, 10.6],
                        "volume": [100, 120],
                        "transactions": [5, 6],
                    }
                )
            }

        monkeypatch.setattr(cli, "query_minute_data", fake_query_minute_data, raising=False)

        result = runner.invoke(app, ["fetch", "AAPL", "--start", "2025-11-03", "--end", "2025-11-05"])

        assert result.exit_code == 0
        assert calls == [(["AAPL"], "2025-11-03", "2025-11-05")]
        assert "ticker,session_date,window_start_ns,open,high,low,close,volume,transactions" in result.stdout
        assert "AAPL,2025-11-03,1,10.0,10.2,9.9,10.1,100,5" in result.stdout

    def test_fetch_defaults_to_last_five_trading_days(self, monkeypatch):
        """Verify fetch uses the last five trading days when no date range is provided."""
        calls = []

        def fake_get_trading_days(start_date=None, end_date=None):
            assert start_date is None
            assert end_date is None
            return [
                "2025-11-03",
                "2025-11-04",
                "2025-11-05",
                "2025-11-06",
                "2025-11-07",
                "2025-11-10",
            ]

        def fake_query_minute_data(tickers, start_date, end_date):
            calls.append((tickers, start_date, end_date))
            return {
                "AAPL": pd.DataFrame(
                    {
                        "ticker": ["AAPL"],
                        "session_date": ["2025-11-04"],
                        "window_start_ns": [1],
                        "open": [10.0],
                        "high": [10.2],
                        "low": [9.9],
                        "close": [10.1],
                        "volume": [100],
                        "transactions": [5],
                    }
                )
            }

        monkeypatch.setattr(cli, "get_trading_days", fake_get_trading_days, raising=False)
        monkeypatch.setattr(cli, "query_minute_data", fake_query_minute_data, raising=False)

        result = runner.invoke(app, ["fetch", "AAPL"])

        assert result.exit_code == 0
        assert calls == [(["AAPL"], "2025-11-04", "2025-11-10")]

    def test_fetch_writes_csv_to_output_file(self, monkeypatch, tmp_path):
        """Verify fetch writes CSV data to the requested output file."""
        output_path = tmp_path / "aapl.csv"

        def fake_query_minute_data(tickers, start_date, end_date):
            return {
                "AAPL": pd.DataFrame(
                    {
                        "ticker": ["AAPL"],
                        "session_date": ["2025-11-03"],
                        "window_start_ns": [1],
                        "open": [10.0],
                        "high": [10.2],
                        "low": [9.9],
                        "close": [10.1],
                        "volume": [100],
                        "transactions": [5],
                    }
                )
            }

        monkeypatch.setattr(cli, "query_minute_data", fake_query_minute_data, raising=False)

        result = runner.invoke(
            app,
            ["fetch", "AAPL", "--start", "2025-11-03", "--end", "2025-11-05", "--output", str(output_path)],
        )

        assert result.exit_code == 0
        assert output_path.exists()
        assert "ticker,session_date,window_start_ns,open,high,low,close,volume,transactions" in output_path.read_text()

    def test_fetch_reports_missing_trading_days_when_default_range_unavailable(self, monkeypatch):
        """Verify fetch surfaces a setup-data hint when no trading days are available for defaults."""
        monkeypatch.setattr(cli, "get_trading_days", lambda start_date=None, end_date=None: [], raising=False)

        result = runner.invoke(app, ["fetch", "AAPL"])

        assert result.exit_code == 1
        assert "setup-data" in result.stdout

    def test_fetch_reports_empty_minute_results(self, monkeypatch):
        """Verify fetch exits when the minute query returns no rows."""
        monkeypatch.setattr(cli, "query_minute_data", lambda tickers, start_date, end_date: {}, raising=False)

        result = runner.invoke(app, ["fetch", "AAPL", "--start", "2025-11-03", "--end", "2025-11-05"])

        assert result.exit_code == 1
        assert "No minute data found" in result.stdout

    def test_fetch_rejects_one_sided_date_ranges(self):
        """Verify fetch requires both start and end together when overriding the default window."""
        start_only = runner.invoke(app, ["fetch", "AAPL", "--start", "2025-11-03"])
        end_only = runner.invoke(app, ["fetch", "AAPL", "--end", "2025-11-05"])

        assert start_only.exit_code == 1
        assert end_only.exit_code == 1
        assert "Provide both --start and --end together" in start_only.stdout
        assert "Provide both --start and --end together" in end_only.stdout

    def test_fetch_reports_trading_day_lookup_failure(self, monkeypatch):
        """Verify fetch converts default-window lookup failures into a stable CLI message."""
        def fail_get_trading_days(start_date=None, end_date=None):
            raise RuntimeError("daily cache unavailable")

        monkeypatch.setattr(cli, "get_trading_days", fail_get_trading_days, raising=False)

        result = runner.invoke(app, ["fetch", "AAPL"])

        assert result.exit_code == 1
        assert "Fetch failed" in result.stdout
        assert "daily cache unavailable" in result.stdout

    def test_fetch_reports_minute_query_failure(self, monkeypatch):
        """Verify fetch converts minute-query failures into a stable CLI message."""
        def fail_query_minute_data(tickers, start_date, end_date):
            raise RuntimeError("minute query failed")

        monkeypatch.setattr(cli, "query_minute_data", fail_query_minute_data, raising=False)

        result = runner.invoke(app, ["fetch", "AAPL", "--start", "2025-11-03", "--end", "2025-11-05"])

        assert result.exit_code == 1
        assert "Fetch failed" in result.stdout
        assert "minute query failed" in result.stdout
