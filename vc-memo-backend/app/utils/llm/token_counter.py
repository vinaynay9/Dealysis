"""
Token counting utilities for accurate cost estimation
"""
import tiktoken
from typing import Optional


# Pricing per 1M tokens (as of 2024)
PRICING = {
    "gpt-4o": {
        "input": 2.50,  # $2.50 per 1M input tokens
        "output": 10.00,  # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.15,  # $0.15 per 1M input tokens
        "output": 0.60,  # $0.60 per 1M output tokens
    },
    "ollama": {
        "input": 0.0,  # FREE
        "output": 0.0,  # FREE
    },
}


# Tokenizer instances (lazy loaded)
_tokenizers = {}


def get_tokenizer(model: str = "gpt-4") -> tiktoken.Encoding:
    """Get or create tokenizer for a model"""
    if model not in _tokenizers:
        try:
            _tokenizers[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base (GPT-4 tokenizer)
            _tokenizers[model] = tiktoken.get_encoding("cl100k_base")
    return _tokenizers[model]


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken
    
    Args:
        text: Text to count tokens in
        model: Model name (gpt-4, gpt-4o, gpt-4o-mini)
    
    Returns:
        Number of tokens
    """
    tokenizer = get_tokenizer(model)
    return len(tokenizer.encode(text))


def estimate_ollama_tokens(text: str) -> int:
    """
    Rough estimate of tokens for Ollama (characters / 4)
    
    Args:
        text: Text to estimate
    
    Returns:
        Estimated token count
    """
    return len(text) // 4


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str
) -> float:
    """
    Estimate cost for API call
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (gpt-4o, gpt-4o-mini, ollama)
    
    Returns:
        Estimated cost in USD
    """
    if model not in PRICING:
        return 0.0
    
    pricing = PRICING[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """Format cost as string"""
    if cost == 0.0:
        return "FREE"
    return f"${cost:.4f}"


def format_tokens(tokens: int) -> str:
    """Format token count with ~ prefix for estimates"""
    return f"~{tokens:,}"

