"""Test model selector logic."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.database import SessionLocal
from src.services.model_selector import ModelSelector


def test_cheapest_selection():
    """Test finding the cheapest model."""
    db = SessionLocal()
    selector = ModelSelector(db)
    
    messages = [
        {"role": "user", "content": "What is Python?"}
    ]
    
    cheapest = selector.get_cheapest_model(
        messages=messages,
        expected_output_tokens=100
    )
    
    print("=" * 60)
    print("Test: Find Cheapest Model")
    print("=" * 60)
    print(f"Selected Model: {cheapest['display_name']} ({cheapest['model_id']})")
    print(f"Provider: {cheapest['provider_name']}")
    print(f"Estimated Cost: ${cheapest['estimated_cost']:.6f}")
    print(f"\nCost Breakdown:")
    print(f"  Input tokens: {cheapest['cost_breakdown']['estimated_input_tokens']}")
    print(f"  Output tokens: {cheapest['cost_breakdown']['estimated_output_tokens']}")
    print(f"  Input cost: ${cheapest['cost_breakdown']['estimated_input_cost_usd']:.6f}")
    print(f"  Output cost: ${cheapest['cost_breakdown']['estimated_output_cost_usd']:.6f}")
    print()
    
    db.close()


def test_model_comparison():
    """Test comparing all models."""
    db = SessionLocal()
    selector = ModelSelector(db)
    
    messages = [
        {"role": "user", "content": "Write a short essay about artificial intelligence."}
    ]
    
    comparison = selector.get_model_comparison(
        messages=messages,
        expected_output_tokens=500  # Longer response expected
    )
    
    print("=" * 60)
    print("Test: Model Comparison")
    print("=" * 60)
    print(f"Total Models Available: {comparison['total_models']}")
    print(f"\nCheapest Option:")
    print(f"  {comparison['cheapest']['display_name']}: ${comparison['cheapest']['estimated_cost']:.6f}")
    print(f"\nMost Expensive Option:")
    print(f"  {comparison['most_expensive']['display_name']}: ${comparison['most_expensive']['estimated_cost']:.6f}")
    print(f"\nPotential Savings: ${comparison['potential_savings_usd']:.6f} ({comparison['savings_percentage']}%)")
    print(f"\nAll Models (Ranked by Cost):")
    
    for i, model in enumerate(comparison['models'], 1):
        print(f"  {i}. {model['display_name']}: ${model['estimated_cost']:.6f}")
    
    print()
    
    db.close()


def test_provider_filter():
    """Test filtering by provider."""
    db = SessionLocal()
    selector = ModelSelector(db)
    
    messages = [
        {"role": "user", "content": "Hello!"}
    ]
    
    # Get only OpenAI models
    ranked = selector.get_ranked_models(
        messages=messages,
        expected_output_tokens=50,
        provider_filter=["openai"]
    )
    
    print("=" * 60)
    print("Test: Provider Filter (OpenAI only)")
    print("=" * 60)
    
    for model in ranked:
        print(f"{model['display_name']} ({model['provider_name']}): ${model['estimated_cost']:.6f}")
    
    print()
    
    db.close()


def test_max_cost_constraint():
    """Test maximum cost filtering."""
    db = SessionLocal()
    selector = ModelSelector(db)
    
    messages = [
        {"role": "user", "content": "Explain quantum computing in detail."}
    ]
    
    max_cost = 0.001  # $0.001 maximum
    
    ranked = selector.get_ranked_models(
        messages=messages,
        expected_output_tokens=1000,
        max_cost=max_cost
    )
    
    print("=" * 60)
    print(f"Test: Max Cost Constraint (${max_cost})")
    print("=" * 60)
    print(f"Models under budget: {len(ranked)}")
    
    for model in ranked:
        print(f"  {model['display_name']}: ${model['estimated_cost']:.6f}")
    
    print()
    
    db.close()


if __name__ == "__main__":
    print("🧪 Testing Model Selector\n")
    
    test_cheapest_selection()
    test_model_comparison()
    test_provider_filter()
    test_max_cost_constraint()
    
    print("✅ Model selector tests complete!")