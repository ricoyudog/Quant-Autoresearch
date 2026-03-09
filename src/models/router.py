"""
Multi-model routing for OPENDEV architecture
"""
import os
from typing import Dict, Any, Optional, List
from groq import Groq
from dotenv import load_dotenv
import tiktoken

load_dotenv()

class ModelRouter:
    """Multi-model routing for thinking vs reasoning phases"""
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Model configurations
        self.models = {
            "thinking": {
                "primary": "llama-3.1-8b-instant",  # Fast, cheap for thinking
                "fallback": "llama-3.3-70b-versatile",
                "max_tokens": 4096,
                "temperature": 0.1
            },
            "reasoning": {
                "primary": "llama-3.3-70b-versatile",  # Powerful for reasoning
                "fallback": "mixtral-8x7b-32768",
                "max_tokens": 8192,
                "temperature": 0.3
            },
            "summarization": {
                "primary": "llama-3.1-8b-instant",  # Cheap for summarization
                "fallback": "llama-3.3-70b-versatile",
                "max_tokens": 2048,
                "temperature": 0.1
            }
        }
        
        # Cost tracking
        self.cost_per_1k = {
            "llama-3.1-8b-instant": 0.00005,
            "llama-3.3-70b-versatile": 0.0001,
            "mixtral-8x7b-32768": 0.0003
        }
        
        self.usage_stats = {
            "thinking_calls": 0,
            "reasoning_calls": 0,
            "summarization_calls": 0,
            "total_cost": 0.0
        }
    
    def route_request(self, phase: str, messages: List[Dict[str, str]], 
                     max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Route request to appropriate model based on phase"""
        
        model_config = self.models.get(phase, self.models["reasoning"])
        model_name = model_config["primary"]
        
        try:
            # Calculate tokens for cost estimation
            total_tokens = sum(len(self.tokenizer.encode(msg["content"])) for msg in messages)
            estimated_cost = (total_tokens / 1000) * self.cost_per_1k.get(model_name, 0.0001)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens or model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            # Update stats
            self.usage_stats[f"{phase}_calls"] += 1
            self.usage_stats["total_cost"] += estimated_cost
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model_used": model_name,
                "phase": phase,
                "tokens_used": total_tokens,
                "estimated_cost": estimated_cost
            }
            
        except Exception as e:
            # Try fallback model
            if model_config.get("fallback") and model_name != model_config["fallback"]:
                try:
                    response = self.client.chat.completions.create(
                        model=model_config["fallback"],
                        messages=messages,
                        max_tokens=max_tokens or model_config["max_tokens"],
                        temperature=model_config["temperature"]
                    )
                    
                    return {
                        "success": True,
                        "content": response.choices[0].message.content,
                        "model_used": model_config["fallback"],
                        "phase": phase,
                        "fallback_used": True,
                        "error": f"Primary model failed: {str(e)}"
                    }
                except Exception as fallback_error:
                    return {
                        "success": False,
                        "error": f"Both models failed: {str(e)}, Fallback: {str(fallback_error)}",
                        "phase": phase
                    }
            
            return {
                "success": False,
                "error": str(e),
                "phase": phase
            }
    
    def thinking_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute thinking phase with reasoning trace"""
        
        thinking_prompt = f"""
You are in the THINKING phase. Generate a reasoning trace WITHOUT using any tools.

Context:
{context.get('current_situation', 'No context provided')}

Previous Actions:
{context.get('recent_actions', 'No recent actions')}

Current Goal:
{context.get('current_goal', 'No goal specified')}

Generate a step-by-step reasoning trace:
1. Analyze the current situation
2. Identify what needs to be done
3. Plan the next actions
4. Consider potential risks

Do NOT use any tools. This is pure reasoning only.

Return your reasoning trace:
"""
        
        messages = [{"role": "user", "content": thinking_prompt}]
        return self.route_request("thinking", messages)
    
    def reasoning_phase(self, context: Dict[str, Any], thinking_trace: str) -> Dict[str, Any]:
        """Execute reasoning phase with tool access"""
        
        reasoning_prompt = f"""
You are in the REASONING phase. Based on the thinking trace, decide what tools to use.

Thinking Trace:
{thinking_trace}

Available Tools:
{context.get('available_tools', 'No tools specified')}

Context:
{context.get('current_situation', 'No context')}

Decide what action to take and which tools to use. Be specific about tool parameters.

Return your action plan:
"""
        
        messages = [{"role": "user", "content": reasoning_prompt}]
        return self.route_request("reasoning", messages)
    
    def summarize_context(self, context_text: str, max_length: int = 1000) -> Dict[str, Any]:
        """Summarize context using cheap model"""
        
        summarization_prompt = f"""
Summarize the following context to under {max_length} characters while preserving key information:

{context_text}

Focus on:
- Recent actions and their outcomes
- Current state and constraints
- Important decisions made
- Errors or issues encountered

Return concise summary:
"""
        
        messages = [{"role": "user", "content": summarization_prompt}]
        return self.route_request("summarization", messages)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            "calls": self.usage_stats,
            "total_cost": self.usage_stats["total_cost"],
            "cost_breakdown": {
                "thinking": self.usage_stats["thinking_calls"] * self.cost_per_1k[self.models["thinking"]["primary"]],
                "reasoning": self.usage_stats["reasoning_calls"] * self.cost_per_1k[self.models["reasoning"]["primary"]],
                "summarization": self.usage_stats["summarization_calls"] * self.cost_per_1k[self.models["summarization"]["primary"]]
            }
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            "thinking_calls": 0,
            "reasoning_calls": 0,
            "summarization_calls": 0,
            "total_cost": 0.0
        }

# Global instance
model_router = ModelRouter()

if __name__ == "__main__":
    # Test the model router
    router = ModelRouter()
    
    # Test thinking phase
    context = {
        "current_situation": "Need to generate a trading hypothesis",
        "current_goal": "Improve Sharpe ratio",
        "recent_actions": "No previous actions"
    }
    
    thinking_result = router.thinking_phase(context)
    print("Thinking phase result:", thinking_result["success"])
    
    if thinking_result["success"]:
        reasoning_result = router.reasoning_phase(context, thinking_result["content"])
        print("Reasoning phase result:", reasoning_result["success"])
    
    print("Usage stats:", router.get_usage_stats())
