"""
Basic token counting utility for Quant Autoresearch
"""
import tiktoken
from typing import Optional

class TokenCounter:
    """Simple token counter with fallback support"""
    
    def __init__(self):
        self.tokenizer: Optional[tiktoken.Encoding] = None
        self._load_tokenizer()
    
    def _load_tokenizer(self):
        """Load tiktoken tokenizer with fallback"""
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"[TOKEN] Warning: Could not load tokenizer: {e}")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or fallback"""
        if not text:
            return 0
        
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                print(f"[TOKEN] Tokenizer error, using fallback: {e}")
        
        # Rough fallback: ~4 characters per token (common approximation)
        return len(text) // 4
    
    def estimate_cost(self, text: str, model: str = "llama-3.3-70b") -> float:
        """Estimate cost in USD for given text and model"""
        tokens = self.count_tokens(text)
        
        # Rough cost estimates (these are approximate)
        costs = {
            "llama-3.3-70b": 0.0001,  # $0.0001 per 1K tokens
            "claude-3.5-sonnet": 0.003,  # $0.003 per 1K tokens
            "gpt-4": 0.01,  # $0.01 per 1K tokens
        }
        
        cost_per_1k = costs.get(model, 0.0001)
        return (tokens / 1000) * cost_per_1k
    
    def format_token_count(self, tokens: int) -> str:
        """Format token count for display"""
        if tokens < 1000:
            return f"{tokens} tokens"
        elif tokens < 1000000:
            return f"{tokens/1000:.1f}K tokens"
        else:
            return f"{tokens/1000000:.1f}M tokens"

# Global instance
token_counter = TokenCounter()

def count_tokens(text: str) -> int:
    """Convenience function to count tokens"""
    return token_counter.count_tokens(text)

def estimate_cost(text: str, model: str = "llama-3.3-70b") -> float:
    """Convenience function to estimate cost"""
    return token_counter.estimate_cost(text, model)

if __name__ == "__main__":
    # Test the token counter
    test_text = "This is a test of the token counting system."
    tokens = count_tokens(test_text)
    cost = estimate_cost(test_text)
    
    print(f"Text: '{test_text}'")
    print(f"Tokens: {token_counter.format_token_count(tokens)}")
    print(f"Estimated cost: ${cost:.6f}")
