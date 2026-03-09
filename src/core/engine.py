import os
import sys
import json
import re
import ast
import subprocess
from typing import Dict, List, Optional, Tuple
from groq import Groq
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from research_engine import get_research_context
from context.compactor import ContextCompactor
from safety.guard import SafetyGuard, SafetyLevel, ApprovalMode
from models.router import model_router
from tools.registry import LazyToolRegistry
from memory.playbook import Playbook
from prompts.composer import PromptComposer

load_dotenv()

class QuantAutoresearchEngine:
    """OPENDEV Enhanced ReAct Loop engine for Quant Autoresearch"""
    
    def __init__(self, safety_level: SafetyLevel = SafetyLevel.HIGH, 
                 max_context_percent: int = 95, thinking_model: str = "llama-3.1-8b-instant",
                 reasoning_model: str = "llama-3.3-70b-versatile", lazy_tools: bool = True,
                 approval_mode: ApprovalMode = ApprovalMode.SEMI):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.safety_level = safety_level
        self.max_context_percent = max_context_percent
        self.thinking_model = thinking_model
        self.reasoning_model = reasoning_model
        self.lazy_tools = lazy_tools
        self.approval_mode = approval_mode
        
        # Core components
        self.compactor = ContextCompactor(max_context_percent=max_context_percent)
        self.safety_guard = SafetyGuard(safety_level=safety_level, approval_mode=approval_mode)
        
        # OPENDEV components
        self.model_router = model_router
        self.tool_registry = LazyToolRegistry() if lazy_tools else None
        self.playbook = Playbook()
        self.prompt_composer = PromptComposer()
        
        # Update model configurations if custom models are provided
        if thinking_model != "llama-3.1-8b-instant":
            self.model_router.models["thinking"]["primary"] = thinking_model
        if reasoning_model != "llama-3.3-70b-versatile":
            self.model_router.models["reasoning"]["primary"] = reasoning_model
        # Summarization uses thinking model
        self.model_router.models["summarization"]["primary"] = thinking_model
        
        # File paths
        self.strategy_file = "strategy.py"
        self.program_file = "program.md"
        self.backtest_runner = "backtest_runner.py"
        self.experiment_log = "experiment_log.json"
        
        # State tracking
        self.iteration_count = 0
        self.tool_history = []
        
    def get_current_strategy(self) -> str:
        """Read current strategy code"""
        with open(self.strategy_file, "r") as f:
            return f.read()
    
    def get_program_constitution(self) -> str:
        """Read the program constitution"""
        with open(self.program_file, "r") as f:
            return f.read()
    
    def run_backtest_with_output(self) -> Tuple[float, float, int, Dict]:
        """Execute backtest and parse results"""
        import subprocess
        
        result = subprocess.run(["uv", "run", "python", self.backtest_runner], 
                              capture_output=True, text=True)
        output = result.stdout
        error_output = result.stderr
        score = -10.0
        drawdown = 0.0
        trades = 0
        
        match_score = re.search(r"SCORE:\s*(-?[\d\.]+)", output)
        if match_score:
            score = float(match_score.group(1))
            if score == -10.0:
                print("--- BACKTEST RETURNED ERROR SCORE ---")
                print("STDOUT:", output)
                print("STDERR:", error_output)
        else:
            print("--- BACKTEST FAILED COMPLETELY ---")
            print("STDOUT:", output)
            print("STDERR:", error_output)
        
        match_dd = re.search(r"DRAWDOWN:\s*(-?[\d\.]+)", output)
        if match_dd:
            drawdown = float(match_dd.group(1))
            
        match_trades = re.search(r"TRADES:\s*(\d+)", output)
        if match_trades:
            trades = int(match_trades.group(1))
            
        return score, drawdown, trades, {"stdout": output, "stderr": error_output}
    
    def load_experiment_log(self) -> List[Dict]:
        """Load experiment history"""
        if os.path.exists(self.experiment_log):
            with open(self.experiment_log, "r") as f:
                return json.load(f)
        return []
    
    def save_experiment_log(self, log: List[Dict]):
        """Save experiment history"""
        with open(self.experiment_log, "w") as f:
            json.dump(log, f, indent=2)
    
    def log_to_tsv(self, score: float, drawdown: float, trades: int, 
                   status: str, description: str):
        """Log results to TSV file"""
        file_exists = os.path.exists("results.tsv")
        with open("results.tsv", "a") as f:
            if not file_exists:
                f.write("commit\tscore\tdrawdown\ttrades\tstatus\tdescription\n")
            timestamp = subprocess.check_output(["date", "+%Y%m%d_%H%M%S"]).decode().strip()
            f.write(f"{timestamp}\t{score}\t{drawdown}\t{trades}\t{status}\t{description}\n")
    
    def generate_hypothesis(self, program: str, current_code: str, 
                          current_score: float, log: List[Dict]) -> Tuple[str, str]:
        """Phase 1: Generate hypothesis using current context"""
        print("Step 1: Generating Hypothesis...")
        
        # Check context before generation
        self.compactor.check_context_usage("hypothesis_generation")
        
        hypothesis_prompt = f"""
{program}

Current Strategy Code:
```python
{current_code}
```

Current Baseline Score: {current_score}

Previous Experiments Summaries:
{json.dumps([{"hypothesis": e["hypothesis"], "score": e["score"], "status": e.get("status"), "error": e.get("error")} for e in log[-5:]], indent=2)}

Task:
Propose a single focused quantitative hypothesis to improve the Sharpe Ratio. 
Focus on specific features (volatility, momentum, mean reversion) or regime detection.

Return only a JSON object: {{"hypothesis": "Your reasoning here", "search_query": "specific terms for arxiv search"}}
"""
        try:
            resp_h = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": hypothesis_prompt}],
                response_format={"type": "json_object"}
            )
            res_h = json.loads(resp_h.choices[0].message.content)
            hypothesis = res_h["hypothesis"]
            search_query = res_h.get("search_query", hypothesis)
            return hypothesis, search_query
        except Exception as e:
            print(f"Hypothesis Generation API Error: {str(e)}")
            raise
    
    def generate_strategy_code(self, program: str, current_code: str, 
                             hypothesis: str, research_context: str,
                             attempt: int = 1, max_tries: int = 2,
                             error_msg: str = "") -> Optional[str]:
        """Phase 2: Generate strategy code with safety checks"""
        print(f"Step 2: Generating Strategy Code (Attempt {attempt}/{max_tries})...")
        
        # Check for doom loops
        tool_fingerprint = f"generate_code_{hypothesis[:50]}"
        if self.safety_guard.check_doom_loop(tool_fingerprint, self.tool_history):
            print("[SAFETY] Doom-loop detected. Halting code generation.")
            return None
        
        self.tool_history.append(tool_fingerprint)
        
        # Check context before generation
        self.compactor.check_context_usage("code_generation")
        
        extra_instr = ""
        if attempt > 0:
            extra_instr = f"\n\nERROR FROM PREVIOUS ATTEMPT:\n{error_msg}\n\nPlease fix the error. Ensure valid indentation and syntax. Use only pandas and numpy."

        code_prompt = f"""
{program}

Current Strategy Code:
```python
{current_code}
```

Proposed Hypothesis:
{hypothesis}

{research_context}
{extra_instr}

Task:
Implement the proposed logic in the `generate_signals` method body for the `# --- EDITABLE REGION ---`.
Cite the relevant concepts from the research context in your code comments.

Return only a JSON object: {{"code": "The entire content of the generate_signals method body"}}
"""
        try:
            resp_c = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": code_prompt}],
                response_format={"type": "json_object"}
            )
            res_c = json.loads(resp_c.choices[0].message.content)
            return res_c["code"]
        except Exception as e:
            error_msg = f"Code Generation API Error: {str(e)}"
            print(f"  {error_msg}")
            return None
    
    def clean_and_indent(self, code_body: str) -> str:
        """Clean and indent code body properly"""
        lines = code_body.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        min_indent = 999
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                if indent < min_indent:
                    min_indent = indent
        if min_indent == 999:
            min_indent = 0
        cleaned_lines = []
        for line in lines:
            cleaned_line = line[min_indent:] if len(line) >= min_indent else line.lstrip()
            cleaned_lines.append("        " + cleaned_line if cleaned_line.strip() else "")
        return "\n".join(cleaned_lines)
    
    def run_iteration(self) -> bool:
        """Run a single iteration of the simplified ReAct loop"""
        print(f"\n--- Starting Engine Iteration {self.iteration_count + 1} ---")
        
        try:
            # Load current state
            program = self.get_program_constitution()
            current_code = self.get_current_strategy()
            current_score, current_dd, current_trades, _ = self.run_backtest_with_output()
            
            if not os.path.exists("results.tsv"):
                self.log_to_tsv(current_score, current_dd, current_trades, "KEEP", "Baseline Strategy")

            print(f"Current Score: {current_score}")
            log = self.load_experiment_log()
            
            # Phase 0: Context Monitoring
            print("Phase 0: Monitoring context usage...")
            context_status = self.compactor.get_context_status()
            if context_status["acc_stage"] != "SAFE":
                print(f"[CONTEXT] ACC Stage: {context_status['acc_stage']} ({context_status['usage_percent']}% used)")
            
            # Phase 1: Hypothesis Generation
            hypothesis, search_query = self.generate_hypothesis(program, current_code, current_score, log)
            print(f"  Proposed Hypothesis: {hypothesis}")
            
            # Phase 2: Research Context
            print("Phase 2: Fetching Research Context...")
            research_context = get_research_context(search_query)
            
            # Phase 3: Code Generation & Self-Correction Loop
            max_tries = 2
            for attempt in range(max_tries):
                print(f"Phase 3: Generating Strategy Code (Attempt {attempt+1}/{max_tries})...")
                
                new_code_body = self.generate_strategy_code(
                    program, current_code, hypothesis, research_context, attempt, max_tries
                )
                
                if not new_code_body:
                    new_score, new_dd, new_trades = -10.0, 0.0, 0
                    backtest_output = {"stderr": "Code generation failed"}
                    break
                    
                # Indentation cleanup
                indented_body = self.clean_and_indent(new_code_body)
                
                pattern = r"(# --- EDITABLE REGION BREAK ---)(.*?)(# --- EDITABLE REGION END ---)"
                new_strategy_content = re.sub(pattern, f"\\1\n{indented_body}\n        \\3", 
                                           current_code, flags=re.DOTALL)
                
                # AST Check before writing
                try:
                    ast.parse(new_strategy_content)
                except Exception as e:
                    error_msg = f"Syntax Error: {e}"
                    print(f"  Pre-write AST Check Failed: {error_msg}")
                    if attempt < max_tries - 1:
                        continue
                    else:
                        break

                # Write and Backtest
                with open(self.strategy_file, "w") as f:
                    f.write(new_strategy_content)
                new_score, new_dd, new_trades, backtest_output = self.run_backtest_with_output()
                
                # Optimize result if too large
                if len(str(backtest_output)) > 8000:
                    backtest_output = self.compactor.optimize_tool_result(backtest_output, "backtest")
                
                if new_score != -10.0:
                    break  # Success or valid result
                else:
                    error_msg = backtest_output.get("stderr", "Unknown Error")
                    print(f"  Backtest Failed: {error_msg[:100]}...")
                    if attempt < max_tries - 1:
                        # Revert before next try
                        with open(self.strategy_file, "w") as f:
                            f.write(current_code)
                        continue
            
            print(f"Final Score: {new_score}")
            status = "KEEP" if (new_score > current_score and new_score != -10.0) else "DISCARD"
            error_msg = ""
            if new_score == -10.0:
                status = "CRASH"
                error_msg = backtest_output.get("stderr", "Syntax/Indentation Error")
                
            self.log_to_tsv(new_score, new_dd, new_trades, status, hypothesis)
            log.append({
                "hypothesis": hypothesis, 
                "score": new_score, 
                "status": status, 
                "error": error_msg[:500], 
                "code": new_code_body or "",
                "iteration": self.iteration_count
            })
            self.save_experiment_log(log)
            
            if status != "KEEP":
                with open(self.strategy_file, "w") as f:
                    f.write(current_code)
            else:
                print("Improvement found! Keeping changes.")
            
            self.iteration_count += 1
            return True
            
        except Exception as e:
            print(f"[ENGINE] Iteration failed: {str(e)}")
            return False
    
    def run(self, max_iterations: int = 10):
        """Run the engine for specified iterations"""
        print(f"Starting Quant Autoresearch Engine (Safety: {self.safety_level}, Max Context: {self.max_context_percent}%)")
        
        for i in range(max_iterations):
            if not self.run_iteration():
                print(f"[ENGINE] Stopping after {i} iterations due to error")
                break
            
            # Check if we should stop due to context limits
            context_status = self.compactor.get_context_status()
            if context_status["usage_percent"] > 90:
                print(f"[ENGINE] Stopping due to context limit ({context_status['usage_percent']}% used)")
                break
        
        print(f"Engine completed {self.iteration_count} iterations")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--safety-level", type=str, default="HIGH", choices=["LOW", "HIGH"])
    parser.add_argument("--max-context", type=int, default=95)
    args = parser.parse_args()
    
    engine = QuantAutoresearchEngine(
        safety_level=args.safety_level,
        max_context_percent=args.max_context
    )
    engine.run(max_iterations=args.iterations)
