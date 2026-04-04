"""
Unit tests for CLI commands.

Tests verify:
1. Which commands are registered
2. Which legacy commands are removed
3. Command behavior with mocked dependencies
"""
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add root to path for imports
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

import cli
from cli import app

runner = CliRunner()


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

    def test_backtest_command_exists(self):
        """Verify backtest is registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "backtest" in result.stdout

    def test_run_command_removed(self):
        """Verify run is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # The run command from the old research loop should not exist
        assert " run " not in result.stdout  # spaces to avoid partial matches
        # Also verify it can't be invoked
        result = runner.invoke(app, ["run"])
        assert result.exit_code != 0

    def test_status_command_removed(self):
        """Verify status is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert " status " not in result.stdout
        result = runner.invoke(app, ["status"])
        assert result.exit_code != 0

    def test_report_command_removed(self):
        """Verify report is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert " report " not in result.stdout
        result = runner.invoke(app, ["report"])
        assert result.exit_code != 0

    def test_ingest_command_removed(self):
        """Verify ingest is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert " ingest " not in result.stdout
        result = runner.invoke(app, ["ingest"])
        assert result.exit_code != 0

    def test_research_command_removed(self):
        """Verify research is NOT a registered command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert " research " not in result.stdout
        result = runner.invoke(app, ["research"])
        assert result.exit_code != 0


class TestBacktestCommandBehavior:
    """Tests for backtest command behavior with mocked dependencies."""

    @patch("core.backtester.walk_forward_validation")
    @patch("core.backtester.load_data")
    @patch("core.backtester.security_check")
    def test_backtest_invokes_backtester(
        self, mock_security_check, mock_load_data, mock_walk_forward
    ):
        """Verify backtest command calls security_check and walk_forward_validation."""
        # Setup mocks
        mock_security_check.return_value = (True, "Safe")
        mock_load_data.return_value = {"SPY": MagicMock()}

        # Create a temporary strategy file
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass")
            strategy_path = f.name

        try:
            result = runner.invoke(app, ["backtest", "-s", strategy_path])
            assert result.exit_code == 0
            mock_security_check.assert_called_once()
            mock_walk_forward.assert_called_once()
        finally:
            Path(strategy_path).unlink(missing_ok=True)

    @patch("core.backtester.load_data")
    @patch("core.backtester.security_check")
    def test_backtest_missing_cache_reports_setup_data_hint(
        self, mock_security_check, mock_load_data
    ):
        """Verify the no-cache hint uses the actual setup-data command name."""
        mock_security_check.return_value = (True, "Safe")
        mock_load_data.return_value = {}

        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass")
            strategy_path = f.name

        try:
            result = runner.invoke(app, ["backtest", "-s", strategy_path])
            assert result.exit_code == 1
            assert "setup-data" in result.stdout
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


class TestFetchCommandBehavior:
    """Tests for fetch command behavior with mocked dependencies."""

    @patch("cli.CacheConnector")
    def test_fetch_creates_connector(self, mock_connector_class):
        """Verify fetch command instantiates CacheConnector and calls fetch_and_cache."""
        # Setup mock
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = True
        mock_connector_class.return_value = mock_connector

        result = runner.invoke(app, ["fetch", "AAPL"])

        assert result.exit_code == 0
        mock_connector_class.assert_called_once()
        mock_connector.fetch_and_cache.assert_called_once_with("AAPL", "2020-01-01")

    @patch("cli.CacheConnector")
    def test_fetch_with_custom_start_date(self, mock_connector_class):
        """Verify fetch command passes custom start date to connector."""
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = True
        mock_connector_class.return_value = mock_connector

        # Use --start option as typer interprets the default value as an option
        result = runner.invoke(app, ["fetch", "AAPL", "--start", "2021-06-01"])

        assert result.exit_code == 0
        mock_connector.fetch_and_cache.assert_called_once_with("AAPL", "2021-06-01")

    @patch("cli.CacheConnector")
    def test_fetch_handles_failure(self, mock_connector_class):
        """Verify fetch command handles connector failure."""
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = False
        mock_connector_class.return_value = mock_connector

        result = runner.invoke(app, ["fetch", "INVALID"])

        assert result.exit_code == 0
        assert "Failed" in result.stdout
