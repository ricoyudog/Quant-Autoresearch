"""
Unit tests for CLI commands.

Tests verify:
1. Which commands are registered
2. Which legacy commands remain removed
3. Command behavior with mocked dependencies
"""
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Add root to path for imports
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

from cli import app

runner = CliRunner()


def help_registers_command(help_text: str, command_name: str) -> bool:
    """Return True when Typer help lists the command in the Commands table."""
    pattern = rf"^│\s+{re.escape(command_name)}\s"
    return re.search(pattern, help_text, re.MULTILINE) is not None


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


class TestFetchCommandBehavior:
    """Tests for fetch command behavior with mocked dependencies."""

    @patch("cli.DataConnector")
    def test_fetch_creates_connector(self, mock_connector_class):
        """Verify fetch command instantiates DataConnector and calls fetch_and_cache."""
        # Setup mock
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = True
        mock_connector_class.return_value = mock_connector

        result = runner.invoke(app, ["fetch", "AAPL"])

        assert result.exit_code == 0
        mock_connector_class.assert_called_once()
        mock_connector.fetch_and_cache.assert_called_once_with("AAPL", "2020-01-01")

    @patch("cli.DataConnector")
    def test_fetch_with_custom_start_date(self, mock_connector_class):
        """Verify fetch command passes custom start date to connector."""
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = True
        mock_connector_class.return_value = mock_connector

        # Use --start option as typer interprets the default value as an option
        result = runner.invoke(app, ["fetch", "AAPL", "--start", "2021-06-01"])

        assert result.exit_code == 0
        mock_connector.fetch_and_cache.assert_called_once_with("AAPL", "2021-06-01")

    @patch("cli.DataConnector")
    def test_fetch_handles_failure(self, mock_connector_class):
        """Verify fetch command handles connector failure."""
        mock_connector = MagicMock()
        mock_connector.fetch_and_cache.return_value = False
        mock_connector_class.return_value = mock_connector

        result = runner.invoke(app, ["fetch", "INVALID"])

        assert result.exit_code == 0
        assert "Failed" in result.stdout


class TestSetupVaultCommandBehavior:
    """Tests for setup_vault behavior with mocked helpers."""

    @patch("cli.ensure_vault_directories")
    @patch("cli.get_vault_paths")
    def test_setup_vault_reports_directory_status(self, mock_get_vault_paths, mock_ensure_vault_directories):
        from config.vault import DirectoryStatus, VaultPaths

        paths = VaultPaths(
            vault_root=Path("/tmp/vault"),
            project_root=Path("/tmp/vault/quant-autoresearch"),
            experiments=Path("/tmp/vault/quant-autoresearch/experiments"),
            research=Path("/tmp/vault/quant-autoresearch/research"),
            knowledge=Path("/tmp/vault/quant-autoresearch/knowledge"),
        )
        mock_get_vault_paths.return_value = paths
        mock_ensure_vault_directories.return_value = [
            DirectoryStatus("project_root", paths.project_root, True),
            DirectoryStatus("experiments", paths.experiments, True),
            DirectoryStatus("research", paths.research, False),
            DirectoryStatus("knowledge", paths.knowledge, False),
        ]

        result = runner.invoke(app, ["setup_vault"])

        assert result.exit_code == 0
        assert "Resolved vault root: /tmp/vault" in result.stdout
        assert "project_root: created" in result.stdout
        assert "research: already existed" in result.stdout
