import pytest
import os
import json
from unittest.mock import MagicMock, patch
from core.engine import QuantAutoresearchEngine
from safety.guard import SafetyLevel

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GROQ_API_KEY", "mock_key")
    
    # Setup minimal project structure
    with open("program.md", "w") as f: f.write("Role: Researcher")
    os.makedirs("prompts", exist_ok=True)
    for p in ["identity.md", "safety_policy.md", "tool_guidance.md", "quant_rules.md", "git_rules.md"]:
        with open(f"prompts/{p}", "w") as f: f.write(f"# {p}")
        
    os.makedirs("src/strategies", exist_ok=True)

@pytest.mark.asyncio
async def test_engine_reversion(mock_env, monkeypatch, tmp_path):
    """Verifies that the engine reverts changes when the score does not improve."""
    test_strategy_path = os.path.join(tmp_path, "local_strategy_rev.py")
    with open(test_strategy_path, "w") as f:
        f.write("class TradingStrategy:\n    def generate_signals(self, data):\n        # --- EDITABLE REGION BREAK ---\n        # Original\n        # --- EDITABLE REGION END ---\n        return pd.Series(0, index=data.index)")
        
    engine = QuantAutoresearchEngine(safety_level=SafetyLevel.LOW, strategy_file=test_strategy_path)
    
    # Mock research context
    monkeypatch.setattr("core.engine.get_research_context", lambda x: "Mock Research Context")
    
    # Mock Model Router
    engine.model_router = MagicMock()
    # Phase 1 Thinking response
    engine.model_router.thinking_phase.return_value = {"success": True, "content": "Thinking trace", "model_used": "mock"}
    
    # Phase 2 Reasoning (Generate Hypothesis and then Code)
    def mock_route_request(phase, messages):
        if "thinking trace" in str(messages).lower():
            return {"success": True, "content": '```json\n[{"tool_name": "generate_strategy_code", "parameters": {"code": "# Improved?"}}, {"tool_name": "run_backtest"}]\n```', "model_used": "mock"}
        return {"success": True, "content": "[]", "model_used": "mock"}
    
    engine.model_router.route_request.side_effect = mock_route_request
    
    # Mock Tool Registry to avoid real subprocesses
    engine.tool_registry = MagicMock()
    def mock_execute_tool(tool_name, params, subagent_type):
        if tool_name == "generate_strategy_code":
            # Real writing logic if we want to test file changes
            from tools.registry import LazyToolRegistry
            real_registry = LazyToolRegistry(strategy_file=test_strategy_path)
            # Load the tool first
            real_registry.load_tool_schema("generate_strategy_code")
            return real_registry.execute_tool(tool_name, params, subagent_type)
        elif tool_name == "run_backtest":
            score, dd, trades, p_val, output = engine.run_backtest_with_output()
            return {"success": True, "result": {"score": score, "drawdown": dd, "trades": trades, "p_value": p_val, "output": output}}
        return {"success": True, "result": {}}
    
    engine.tool_registry.execute_tool.side_effect = mock_execute_tool
    
    # Mock run_backtest_with_output: score 0.5 (baseline) then 0.1 (new strategy)
    scores = [0.5, 0.1, 0.5, 0.1, 0.5]
    def mock_run_backtest():
        return scores.pop(0), 0.0, 0, 0.05, {"stdout": "SCORE: 0.5", "stderr": ""}
    engine.run_backtest_with_output = MagicMock(side_effect=mock_run_backtest)
    
    # Run 1 iteration
    await engine.run(max_iterations=1)
    
    # Verify reversion
    with open(test_strategy_path, "r") as f:
        content = f.read()
    assert "Original" in content
    assert "Improved?" not in content

@pytest.mark.asyncio
async def test_engine_improvement(mock_env, monkeypatch, tmp_path):
    """Verifies that the engine keeps changes when the score improves."""
    test_strategy_path = os.path.join(tmp_path, "local_strategy_imp.py")
    with open(test_strategy_path, "w") as f:
        f.write("class TradingStrategy:\n    def generate_signals(self, data):\n        # --- EDITABLE REGION BREAK ---\n        # Original\n        # --- EDITABLE REGION END ---\n        return pd.Series(0, index=data.index)")
        
    engine = QuantAutoresearchEngine(safety_level=SafetyLevel.LOW, strategy_file=test_strategy_path)
    
    monkeypatch.setattr("core.engine.get_research_context", lambda x: "Mock Research Context")
    
    engine.model_router = MagicMock()
    engine.model_router.thinking_phase.return_value = {"success": True, "content": "Thinking trace", "model_used": "mock"}
    
    def mock_route_request(phase, messages):
        if "thinking trace" in str(messages).lower():
            return {"success": True, "content": '```json\n[{"tool_name": "generate_strategy_code", "parameters": {"code": "# Better!"}}, {"tool_name": "run_backtest"}]\n```', "model_used": "mock"}
        return {"success": True, "content": "[]", "model_used": "mock"}
    
    engine.model_router.route_request.side_effect = mock_route_request
    
    # Mock Tool Registry to avoid real subprocesses
    engine.tool_registry = MagicMock()
    def mock_execute_tool(tool_name, params, subagent_type):
        if tool_name == "generate_strategy_code":
            from tools.registry import LazyToolRegistry
            real_registry = LazyToolRegistry(strategy_file=test_strategy_path)
            real_registry.load_tool_schema("generate_strategy_code")
            return real_registry.execute_tool(tool_name, params, subagent_type)
        elif tool_name == "run_backtest":
            score, dd, trades, p_val, output = engine.run_backtest_with_output()
            return {"success": True, "result": {"score": score, "drawdown": dd, "trades": trades, "p_value": p_val, "output": output}}
        return {"success": True, "result": {}}
        
    engine.tool_registry.execute_tool.side_effect = mock_execute_tool
    
    # Mock run_backtest_with_output: score 0.1 (baseline) then 0.5 (new strategy)
    scores = [0.1, 0.5, 0.1, 0.5, 0.1]
    def mock_run_backtest():
        return scores.pop(0), 0.0, 0, 0.05, {"stdout": "SCORE: 0.5", "stderr": ""}
    engine.run_backtest_with_output = MagicMock(side_effect=mock_run_backtest)
    
    await engine.run(max_iterations=1)
    
    with open(test_strategy_path, "r") as f:
        content = f.read()
    assert "Better!" in content
    assert "Original" not in content
