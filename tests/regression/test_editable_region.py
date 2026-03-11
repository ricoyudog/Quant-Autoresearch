import pytest
import re
from pathlib import Path

def test_editable_region_markers():
    """Regression test for active_strategy.py markers and dead code."""
    strategy_path = Path("src/strategies/active_strategy.py")
    content = strategy_path.read_text()
    
    # Check markers
    break_marker = "# --- EDITABLE REGION BREAK ---"
    end_marker = "# --- EDITABLE REGION END ---"
    
    assert content.count(break_marker) == 1
    assert content.count(end_marker) == 1
    
    # Check for premature return before END marker
    parts = content.split(break_marker)
    after_break = parts[1]
    
    body_and_end = after_break.split(end_marker)
    body = body_and_end[0]
    
    # Ensure no return signals in the body that would make END unreachable
    # We allow 'signals = ...' but not 'return signals'
    # Actually, we should check for a 'return' statement specifically.
    assert "return signals" not in body
    
    # Ensure return signals exists AFTER the end marker
    after_end = body_and_end[1]
    assert "return" in after_end

if __name__ == "__main__":
    pytest.main([__file__])
