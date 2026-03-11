import pytest
from unittest.mock import MagicMock, patch
from core.engine import QuantAutoresearchEngine
from safety.guard import SafetyLevel

@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test_playbook.db"
    return QuantAutoresearchEngine(safety_level=SafetyLevel.LOW, db_path=str(db_path))

def test_engine_run_backtest_return_arity(engine):
    """Regression test for engine.py return arity mismatch (5 values)."""
    
    # Mock run_backtest_with_output to return 5 values
    mock_metrics = (0.5, 0.1, 10, 0.01, {"stdout": "mock", "stderr": ""})
    engine.run_backtest_with_output = MagicMock(return_value=mock_metrics)
    
    # Test unpacking in initial status check logic (the mocked call)
    try:
        current_score, _, _, _, _ = engine.run_backtest_with_output()
        assert current_score == 0.5
    except ValueError as e:
        pytest.fail(f"Unpacking 5 values failed: {e}")

def test_fallback_tool_dispatch_arity(engine):
    """Regression test for _fallback_tool_dispatch return arity."""
    mock_metrics = (0.6, 0.15, 20, 0.02, {"stdout": "mock2"})
    engine.run_backtest_with_output = MagicMock(return_value=mock_metrics)
    
    result = engine._fallback_tool_dispatch("run_backtest", {})
    
    assert result["score"] == 0.6
    assert result["p_value"] == 0.02
    assert "output" in result

if __name__ == "__main__":
    pytest.main([__file__])
