"""Test token estimator accuracy."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.token_estimator import TokenEstimator


def test_simple_message():
    """Test estimation on a simple message."""
    estimator = TokenEstimator()
    
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    result = estimator.estimate_messages_tokens(messages, "gpt-4o-mini")
    
    print("=" * 60)
    print("Test: Simple Question")
    print("=" * 60)
    print(f"Message: {messages[0]['content']}")
    print(f"\nEstimated tokens: {result['estimated_tokens']}")
    print(f"Buffered tokens: {result['buffered_tokens']}")
    print(f"Buffer: {((result['buffered_tokens'] / result['estimated_tokens']) - 1) * 100:.1f}%")
    print()


def test_conversation():
    """Test estimation on a multi-turn conversation."""
    estimator = TokenEstimator()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about Python programming."},
        {"role": "assistant", "content": "Python is a high-level programming language known for its simplicity and readability."},
        {"role": "user", "content": "What are its main features?"}
    ]
    
    result = estimator.estimate_messages_tokens(messages, "gpt-4o-mini")
    
    print("=" * 60)
    print("Test: Multi-turn Conversation")
    print("=" * 60)
    print(f"Messages: {len(messages)}")
    print(f"\nEstimated tokens: {result['estimated_tokens']}")
    print(f"Buffered tokens: {result['buffered_tokens']}")
    print()


def test_cost_estimation():
    """Test cost estimation."""
    estimator = TokenEstimator()
    
    messages = [
        {"role": "user", "content": "Write a short poem about coding."}
    ]
    
    # GPT-4o-mini pricing
    result = estimator.estimate_cost(
        messages=messages,
        model_id="gpt-4o-mini",
        input_price_per_1m=0.15,
        output_price_per_1m=0.60,
        expected_output_tokens=100
    )
    
    print("=" * 60)
    print("Test: Cost Estimation")
    print("=" * 60)
    print(f"Input tokens: {result['estimated_input_tokens']}")
    print(f"Output tokens: {result['estimated_output_tokens']}")
    print(f"Total tokens: {result['estimated_total_tokens']}")
    print(f"\nInput cost: ${result['estimated_input_cost_usd']:.6f}")
    print(f"Output cost: ${result['estimated_output_cost_usd']:.6f}")
    print(f"Total cost: ${result['estimated_total_cost_usd']:.6f}")
    print()


if __name__ == "__main__":
    test_simple_message()
    test_conversation()
    test_cost_estimation()
    
    print("✅ Token estimator tests complete!")