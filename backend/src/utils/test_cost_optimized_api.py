"""Test cost-optimized API mode."""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import httpx


def get_api_key():
    """Get API key from environment."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("❌ Error: API_KEY environment variable not set")
        print("Run: export API_KEY='your_test_key'")
        sys.exit(1)
    return api_key


def make_request(data: dict, api_key: str) -> dict:
    """Make API request and return response."""
    url = "http://127.0.0.1:8001/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        response = httpx.post(url, json=data, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def test_manual_mode(api_key: str):
    """Test manual model selection."""
    print("=" * 60)
    print("Test 1: Manual Mode")
    print("=" * 60)
    print("Specifying gpt-4o-mini explicitly...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "Say hello in one word"}
        ],
        "model": "gpt-4o-mini",
        "mode": "manual"
    }
    
    response = make_request(data, api_key)
    
    print(f"✓ Model used: {response['model']}")
    print(f"✓ Provider: {response['provider']}")
    print(f"✓ Mode: {response.get('selection_mode', 'N/A')}")
    print(f"✓ Cost: ${response['usage']['total_cost_usd']:.6f}")
    print(f"✓ Response: {response['content'][:50]}...")
    print()


def test_cost_optimized_mode(api_key: str):
    """Test cost-optimized model selection."""
    print("=" * 60)
    print("Test 2: Cost-Optimized Mode")
    print("=" * 60)
    print("Automatically selecting cheapest model...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "What is 2+2?"}
        ],
        "mode": "cost-optimized",
        "expected_output_tokens": 50,
        "provider_filter": ["openai"]  # Add this line
    }
    
    response = make_request(data, api_key)
    
    print(f"✓ Model selected: {response['model']}")
    print(f"✓ Provider: {response['provider']}")
    print(f"✓ Selection mode: {response['selection_mode']}")
    print(f"✓ Models considered: {response['models_considered']}")
    print(f"✓ Estimated cost: ${response['usage'].get('estimated_cost_usd', 0):.6f}")
    print(f"✓ Actual cost: ${response['usage']['total_cost_usd']:.6f}")
    print(f"✓ Response: {response['content'][:50]}...")
    print()

def test_max_cost_constraint(api_key: str):
    """Test cost-optimized with max cost constraint."""
    print("=" * 60)
    print("Test 3: Cost-Optimized with Max Cost")
    print("=" * 60)
    print("Limiting to models under $0.001...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "Name three colors"}
        ],
        "mode": "cost-optimized",
        "expected_output_tokens": 20,
        "max_cost": 0.001,
        "provider_filter": ["openai"]  # Add this line
    }
    
    response = make_request(data, api_key)
    
    print(f"✓ Model selected: {response['model']}")
    print(f"✓ Models considered: {response['models_considered']}")
    print(f"✓ Actual cost: ${response['usage']['total_cost_usd']:.6f}")
    print(f"✓ Under budget: {response['usage']['total_cost_usd'] <= 0.001}")
    print(f"✓ Response: {response['content'][:50]}...")
    print()


def test_provider_filter(api_key: str):
    """Test cost-optimized with provider filter."""
    print("=" * 60)
    print("Test 4: Cost-Optimized with Provider Filter")
    print("=" * 60)
    print("Only considering OpenAI models...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "Count to 5"}
        ],
        "mode": "cost-optimized",
        "expected_output_tokens": 30,
        "provider_filter": ["openai"]
    }
    
    response = make_request(data, api_key)
    
    print(f"✓ Model selected: {response['model']}")
    print(f"✓ Provider: {response['provider']}")
    print(f"✓ Provider filter applied: openai")
    print(f"✓ Cost: ${response['usage']['total_cost_usd']:.6f}")
    print(f"✓ Response: {response['content'][:50]}...")
    print()


def test_missing_model_in_manual_mode(api_key: str):
    """Test error handling when model not specified in manual mode."""
    print("=" * 60)
    print("Test 5: Error Handling - Missing Model in Manual Mode")
    print("=" * 60)
    print("Attempting manual mode without specifying model...\n")
    
    url = "http://127.0.0.1:8001/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "mode": "manual"
        # Note: no "model" field
    }
    
    response = httpx.post(url, json=data, headers=headers, timeout=30.0)
    
    if response.status_code == 400:
        print(f"✓ Correctly rejected with status 400")
        print(f"✓ Error: {response.json()['detail']}")
    else:
        print(f"✗ Expected 400, got {response.status_code}")
    
    print()


if __name__ == "__main__":
    print("\n🧪 Testing Cost-Optimized API Mode\n")
    
    api_key = get_api_key()
    
    try:
        test_manual_mode(api_key)
        test_cost_optimized_mode(api_key)
        test_max_cost_constraint(api_key)
        test_provider_filter(api_key)
        test_missing_model_in_manual_mode(api_key)
        
        print("=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)