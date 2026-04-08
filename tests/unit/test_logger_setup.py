import subprocess
import sys
from pathlib import Path


def test_logger_import_creates_default_log_directory(tmp_path):
    """Importing the logger module should create its default log directory."""
    logger_path = Path(__file__).resolve().parents[2] / "src" / "utils" / "logger.py"
    script = (
        "import runpy\n"
        f"runpy.run_path({str(logger_path)!r}, run_name='__main__')\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "experiments" / "logs" / "run.log").exists()
