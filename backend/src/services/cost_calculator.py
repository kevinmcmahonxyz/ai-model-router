"""Cost calculation service."""
from typing import Dict


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float
) -> Dict[str, float]:
    """
    Calculate cost for a request.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        input_price_per_1m: Price per 1M input tokens (USD)
        output_price_per_1m: Price per 1M output tokens (USD)
    
    Returns:
        Dict with input_cost, output_cost, and total_cost in USD
    """
    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m
    total_cost = input_cost + output_cost
    
    return {
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "total_cost_usd": round(total_cost, 8)
    }