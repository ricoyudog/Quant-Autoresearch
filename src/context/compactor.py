"""
4-stage Adaptive Context Compaction (ACC) for OPENDEV architecture
"""
import json
import tiktoken
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.router import model_router

class ContextCompactor:
    """4-stage Adaptive Context Compaction with LLM summarization"""
    
    def __init__(self, max_context_percent: int = 95):
        self.max_context_percent = max_context_percent
        self.max_tokens = 128000  # Llama model limit
        
        # 4-stage ACC thresholds (per OPENDEV paper)
        self.warning_threshold = 70    # >70%: Log warning
        self.masking_threshold = 80    # >80%: Mask old tool outputs
        self.pruning_threshold = 90    # >90%: Aggressive pruning
        self.summarization_threshold = 99  # >99%: LLM summarization
        
        # Context tracking
        self.context_history = []
        self.masked_outputs = {}
        self.pruned_operations = []
        self.summarized_contexts = []
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"[CONTEXT] Warning: Could not load tokenizer: {e}")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken or fallback"""
        if not text:
            return 0
        
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback: ~4 chars per token
        return len(text) // 4
    
    def get_context_status(self) -> Dict[str, Any]:
        """Get current context usage and stage"""
        recent_context = self._get_recent_context()
        current_tokens = self.count_tokens(str(recent_context))
        usage_percent = (current_tokens / self.max_tokens) * 100
        
        # Determine ACC stage
        if usage_percent >= self.summarization_threshold:
            stage = "CRITICAL_SUMMARIZATION"
            action_required = "LLM_SUMMARIZATION"
        elif usage_percent >= self.pruning_threshold:
            stage = "CRITICAL_PRUNING"
            action_required = "AGGRESSIVE_PRUNING"
        elif usage_percent >= self.masking_threshold:
            stage = "WARNING_MASKING"
            action_required = "MASK_OUTPUTS"
        elif usage_percent >= self.warning_threshold:
            stage = "WARNING"
            action_required = "LOG_WARNING"
        else:
            stage = "SAFE"
            action_required = "NONE"
        
        return {
            "current_tokens": current_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": usage_percent,
            "acc_stage": stage,
            "action_required": action_required,
            "context_history": self.context_history,
            "masked_outputs": self.masked_outputs,
            "pruned_operations": self.pruned_operations,
            "summarized_contexts": self.summarized_contexts
        }
    
    def check_context_usage(self, operation: str):
        """Check context usage and trigger ACC if needed"""
        current_tokens = self.count_tokens(str(self._get_recent_context()))
        usage_percent = (current_tokens / self.max_tokens) * 100
        
        if usage_percent >= self.summarization_threshold:
            self.adaptive_context_compaction(operation, {
                "current_tokens": current_tokens,
                "usage_percent": usage_percent
            })
        
        return usage_percent
    
    def _get_recent_context(self) -> Dict[str, Any]:
        """Get recent context for token counting"""
        return {
            "recent_operations": self.context_history[-10:],  # Last 10 operations
            "masked_outputs": list(self.masked_outputs.keys())[-5:],  # Last 5 masked
            "pruned_count": len(self.pruned_operations),
            "summarized_count": len(self.summarized_contexts),
            "timestamp": datetime.now().isoformat()
        }
    
    def adaptive_context_compaction(self, operation: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute 4-stage ACC based on current usage"""
        
        # Log the operation
        operation_entry = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "data": context_data,
            "tokens": self.count_tokens(str(context_data))
        }
        
        self.context_history.append(operation_entry)
        
        # Get current status
        status = self.get_context_status()
        stage = status["acc_stage"]
        
        compaction_actions = []
        
        # Execute appropriate ACC stage
        if stage == "CRITICAL_SUMMARIZATION":
            compaction_actions.append(self._llm_summarization())
        elif stage == "CRITICAL_PRUNING":
            compaction_actions.append(self._aggressive_pruning())
        elif stage == "WARNING_MASKING":
            compaction_actions.append(self._mask_old_outputs())
        elif stage == "WARNING":
            compaction_actions.append(self._log_warning())
        
        # Keep history manageable
        if len(self.context_history) > 50:
            self.context_history = self.context_history[-50:]
        
        return {
            "stage": stage,
            "actions_taken": compaction_actions,
            "usage_percent": status["usage_percent"],
            "operation_logged": operation
        }
    
    def _log_warning(self) -> str:
        """Stage 1: Log warning at >70% usage"""
        status = self.get_context_status()
        print(f"[ACC] WARNING: Context usage at {status['usage_percent']:.1f}%")
        return f"Logged warning at {status['usage_percent']:.1f}% usage"
    
    def _mask_old_outputs(self) -> str:
        """Stage 2: Mask old tool outputs at >80% usage"""
        if len(self.context_history) > 15:
            # Mask outputs from operations older than last 10
            old_operations = self.context_history[:-10]
            masked_count = 0
            
            for op in old_operations:
                op_key = f"{op['operation']}_{op['timestamp']}"
                if op_key not in self.masked_outputs:
                    # Replace large data with reference
                    if op["tokens"] > 1000:
                        self.masked_outputs[op_key] = {
                            "original_tokens": op["tokens"],
                            "masked_at": datetime.now().isoformat(),
                            "operation": op["operation"]
                        }
                        op["data"] = f"[MASKED_OUTPUT: {op['tokens']} tokens]"
                        op["tokens"] = op["tokens"] // 10  # Reduce to 10%
                        masked_count += 1
            
            return f"Masked {masked_count} old outputs"
        return "No outputs to mask"
    
    def _aggressive_pruning(self) -> str:
        """Stage 3: Aggressive pruning at >90% usage"""
        original_count = len(self.context_history)
        
        # Keep only last 5 operations
        if len(self.context_history) > 5:
            pruned_ops = self.context_history[:-5]
            self.pruned_operations.extend(pruned_ops)
            self.context_history = self.context_history[-5:]
        
        # Clear half of masked outputs
        if len(self.masked_outputs) > 2:
            keys_to_remove = list(self.masked_outputs.keys())[:-2]
            for key in keys_to_remove:
                del self.masked_outputs[key]
        
        pruned_count = original_count - len(self.context_history)
        return f"Aggressively pruned {pruned_count} operations"
    
    def _llm_summarization(self) -> str:
        """Stage 4: LLM summarization at >99% usage"""
        
        # Collect context to summarize
        context_to_summarize = {
            "recent_operations": self.context_history[-3:],
            "key_decisions": self._extract_key_decisions(),
            "errors": self._extract_recent_errors(),
            "current_state": self._get_current_state()
        }
        
        context_text = json.dumps(context_to_summarize, indent=2)
        
        # Use cheap model for summarization
        try:
            summary_result = model_router.summarize_context(context_text, max_length=1000)
            
            if summary_result["success"]:
                summary_entry = {
                    "original_context_tokens": self.count_tokens(context_text),
                    "summary": summary_result["content"],
                    "summary_tokens": self.count_tokens(summary_result["content"]),
                    "created_at": datetime.now().isoformat(),
                    "model_used": summary_result["model_used"]
                }
                
                self.summarized_contexts.append(summary_entry)
                
                # Replace detailed context with summary
                self.context_history = [{
                    "operation": "SUMMARIZED_CONTEXT",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "summary": summary_result["content"],
                        "original_token_count": summary_entry["original_context_tokens"]
                    },
                    "tokens": summary_entry["summary_tokens"]
                }]
                
                # Clear masked outputs and pruned operations
                self.masked_outputs = {}
                self.pruned_operations = []
                
                return f"LLM summarized context using {summary_result['model_used']}"
            else:
                return f"LLM summarization failed: {summary_result['error']}"
                
        except Exception as e:
            return f"LLM summarization error: {str(e)}"
    
    def _extract_key_decisions(self) -> List[str]:
        """Extract key decisions from recent operations"""
        decisions = []
        for op in self.context_history[-10:]:
            if "decision" in str(op.get("data", {})).lower():
                decisions.append(f"{op['operation']}: {op['timestamp']}")
        return decisions
    
    def _extract_recent_errors(self) -> List[str]:
        """Extract recent errors"""
        errors = []
        for op in self.context_history[-10:]:
            if "error" in str(op.get("data", {})).lower():
                errors.append(f"{op['operation']}: {op['timestamp']}")
        return errors
    
    def _get_current_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            "total_operations": len(self.context_history),
            "masked_outputs": len(self.masked_outputs),
            "pruned_operations": len(self.pruned_operations),
            "summarizations": len(self.summarized_contexts),
            "current_usage_percent": self.get_context_status()["usage_percent"]
        }
    
    def optimize_tool_result(self, result: Any, tool_name: str) -> Any:
        """Optimize tool results >8k characters (per OPENDEV paper)"""
        if isinstance(result, dict):
            result_str = str(result)
        else:
            result_str = str(result)
        
        if len(result_str) <= 8000:
            return result
        
        print(f"[ACC] Optimizing large result from {tool_name} ({len(result_str)} chars)")
        
        # Create optimized version
        if isinstance(result, dict):
            optimized = {
                "_optimized": True,
                "_original_size": len(result_str),
                "_tool_name": tool_name,
                "_optimization_method": "acc_tool_result_optimization",
                "_timestamp": datetime.now().isoformat()
            }
            
            # Keep important keys if they exist and are small
            important_keys = ["stdout", "stderr", "score", "error", "status"]
            for key in important_keys:
                if key in result and len(str(result[key])) < 1000:
                    optimized[key] = result[key]
                elif key in result:
                    # Summarize large content
                    content = str(result[key])
                    if len(content) > 500:
                        optimized[key] = content[:200] + f"\n\n[... {len(content) - 400} characters omitted ...]\n\n" + content[-200:]
                    else:
                        optimized[key] = content
            
            return optimized
        else:
            return {
                "_optimized": True,
                "_original_size": len(result_str),
                "_tool_name": tool_name,
                "_optimization_method": "acc_tool_result_optimization",
                "_summary": self._create_summary(result_str),
                "_timestamp": datetime.now().isoformat()
            }
    
    def _create_summary(self, text: str) -> str:
        """Create summary of large text"""
        if len(text) <= 500:
            return text
        
        first_part = text[:200]
        last_part = text[-200:]
        
        return f"{first_part}\n\n[... {len(text) - 400} characters omitted ...]\n\n{last_part}"
    
    def get_acc_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ACC statistics"""
        return {
            "current_status": self.get_context_status(),
            "total_masked": len(self.masked_outputs),
            "total_pruned": len(self.pruned_operations),
            "total_summarized": len(self.summarized_contexts),
            "compression_ratio": self._calculate_compression_ratio(),
            "stage_history": self._get_stage_history()
        }
    
    def _calculate_compression_ratio(self) -> float:
        """Calculate overall compression ratio"""
        if not self.masked_outputs and not self.pruned_operations:
            return 1.0
        
        original_size = sum(op.get("tokens", 0) for op in self.context_history)
        original_size += sum(masked.get("original_tokens", 0) for masked in self.masked_outputs.values())
        original_size += sum(pruned.get("tokens", 0) for pruned in self.pruned_operations)
        
        current_size = sum(op.get("tokens", 0) for op in self.context_history)
        
        return current_size / max(original_size, 1)
    
    def _get_stage_history(self) -> List[str]:
        """Get history of ACC stages triggered"""
        stages = []
        for op in self.context_history:
            if "acc_stage" in op.get("data", {}):
                stages.append(f"{op['timestamp']}: {op['data']['acc_stage']}")
        return stages

if __name__ == "__main__":
    # Test the 4-stage ACC
    compactor = ContextCompactor()
    
    # Simulate operations to trigger different stages
    for i in range(25):
        large_data = {"result": "x" * 1000, "iteration": i}
        compaction = compactor.adaptive_context_compaction(f"test_operation_{i}", large_data)
        print(f"Operation {i}: {compaction['stage']} - {compaction['usage_percent']:.1f}%")
    
    print("\nACC Statistics:", compactor.get_acc_statistics())
