"""Test budget enforcement."""
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
        sys.exit(1)
    return api_key


def make_request(method: str, endpoint: str, api_key: str, json=None, params=None):
    """Make API request."""
    url = f"http://127.0.0.1:8001{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        if method == "GET":
            response = httpx.get(url, headers=headers, params=params, timeout=30.0)
        elif method == "POST":
            response = httpx.post(url, json=json, headers=headers, timeout=30.0)
        elif method == "PUT":
            response = httpx.put(url, json=json, headers=headers, params=params, timeout=30.0)
        
        return response
    except httpx.HTTPError as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)


def test_check_current_budget(api_key: str):
    """Check current budget status."""
    print("=" * 60)
    print("Test 1: Check Current Budget")
    print("=" * 60)
    
    response = make_request("GET", "/v1/budget", api_key)
    data = response.json()
    
    print(f"✓ Total spent: ${data['spending']['total_spent_usd']:.6f}")
    print(f"✓ Spending limit: {data['spending']['spending_limit_usd'] or 'Unlimited'}")
    
    if data['spending']['remaining_budget_usd'] is not None:
        print(f"✓ Remaining: ${data['spending']['remaining_budget_usd']:.6f}")
        print(f"✓ Budget used: {data['spending']['budget_used_percentage']}%")
    
    print()
    return data['spending']


def test_set_low_budget(api_key: str):
    """Set a very low budget limit."""
    print("=" * 60)
    print("Test 2: Set Low Budget Limit")
    print("=" * 60)
    print("Setting limit to $0.000001...\n")
    
    response = make_request("PUT", "/v1/budget/limit", api_key, params={"limit_usd": 0.000001})
    data = response.json()
    
    print(f"✓ {data['message']}")
    print(f"✓ New limit: ${data['spending_limit_usd']:.6f}")
    print()


def test_request_exceeds_budget(api_key: str):
    """Try request that exceeds budget."""
    print("=" * 60)
    print("Test 3: Request Exceeding Budget")
    print("=" * 60)
    print("Attempting cost-optimized request...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "mode": "cost-optimized",
        "provider_filter": ["openai"]
    }
    
    response = make_request("POST", "/v1/chat/completions", api_key, data)
    
    if response.status_code == 402:
        detail = response.json()['detail']
        print(f"✓ Correctly blocked with status 402 (Payment Required)")
        print(f"✓ Reason: {detail['reason']}")
        print(f"✓ Would exceed by: ${detail.get('would_exceed_by_usd', 0):.6f}")
    else:
        print(f"✗ Expected 402, got {response.status_code}")
    
    print()


def test_reset_and_set_reasonable_budget(api_key: str):
    """Reset spending and set reasonable budget."""
    print("=" * 60)
    print("Test 4: Reset and Set Reasonable Budget")
    print("=" * 60)
    
    # Reset spending
    response = make_request("POST", "/v1/budget/reset", api_key)
    print(f"✓ {response.json()['message']}")
    
    # Set reasonable limit
    response = make_request("PUT", "/v1/budget/limit", api_key, params={"limit_usd": 1.00})
    print(f"✓ New limit: ${response.json()['spending_limit_usd']:.2f}")
    print()


def test_request_within_budget(api_key: str):
    """Make request within budget."""
    print("=" * 60)
    print("Test 5: Request Within Budget")
    print("=" * 60)
    print("Making cost-optimized request...\n")
    
    data = {
        "messages": [
            {"role": "user", "content": "Say hi"}
        ],
        "mode": "cost-optimized",
        "expected_output_tokens": 10,
        "provider_filter": ["openai"]
    }
    
    response = make_request("POST", "/v1/chat/completions", api_key, data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Request successful")
        print(f"✓ Model: {result['model']}")
        print(f"✓ Cost: ${result['usage']['total_cost_usd']:.6f}")
        print(f"✓ Response: {result['content'][:30]}...")
    else:
        print(f"✗ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
    
    print()


def test_final_budget_check(api_key: str):
    """Check final budget status."""
    print("=" * 60)
    print("Test 6: Final Budget Check")
    print("=" * 60)
    
    response = make_request("GET", "/v1/budget", api_key)
    data = response.json()
    
    print(f"✓ Total spent: ${data['spending']['total_spent_usd']:.6f}")
    print(f"✓ Spending limit: ${data['spending']['spending_limit_usd']:.2f}")
    print(f"✓ Remaining: ${data['spending']['remaining_budget_usd']:.6f}")
    print(f"✓ Budget used: {data['spending']['budget_used_percentage']}%")
    print()


if __name__ == "__main__":
    print("\n🧪 Testing Budget Enforcement\n")
    
    api_key = get_api_key()
    
    try:
        test_check_current_budget(api_key)
        test_set_low_budget(api_key)
        test_request_exceeds_budget(api_key)
        test_reset_and_set_reasonable_budget(api_key)
        test_request_within_budget(api_key)
        test_final_budget_check(api_key)
        
        print("=" * 60)
        print("✅ All budget tests complete!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)