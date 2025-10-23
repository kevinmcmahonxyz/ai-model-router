"""Tests for cost calculation service."""
import pytest
from src.services.cost_calculator import calculate_cost


class TestCostCalculator:
    """Test cost calculation logic."""
    
    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        result = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            input_price_per_1m=0.15,  # $0.15 per 1M tokens
            output_price_per_1m=0.60   # $0.60 per 1M tokens
        )
        
        # Expected: (1000/1M * 0.15) + (500/1M * 0.60)
        # = 0.00015 + 0.0003 = 0.00045
        assert result["input_cost_usd"] == pytest.approx(0.00015, abs=1e-8)
        assert result["output_cost_usd"] == pytest.approx(0.0003, abs=1e-8)
        assert result["total_cost_usd"] == pytest.approx(0.00045, abs=1e-8)
    
    def test_calculate_cost_zero_tokens(self):
        """Test with zero tokens."""
        result = calculate_cost(
            input_tokens=0,
            output_tokens=0,
            input_price_per_1m=0.15,
            output_price_per_1m=0.60
        )
        
        assert result["input_cost_usd"] == 0.0
        assert result["output_cost_usd"] == 0.0
        assert result["total_cost_usd"] == 0.0
    
    def test_calculate_cost_large_numbers(self):
        """Test with large token counts."""
        result = calculate_cost(
            input_tokens=100_000,
            output_tokens=50_000,
            input_price_per_1m=2.50,
            output_price_per_1m=10.00
        )
        
        # (100k/1M * 2.50) + (50k/1M * 10.00) = 0.25 + 0.50 = 0.75
        assert result["total_cost_usd"] == pytest.approx(0.75, abs=1e-8)
    
    def test_calculate_cost_precision(self):
        """Test that rounding is precise to 8 decimal places."""
        result = calculate_cost(
            input_tokens=1,
            output_tokens=1,
            input_price_per_1m=0.15,
            output_price_per_1m=0.60
        )
        
        # Should be rounded to 8 decimals
        assert len(str(result["input_cost_usd"]).split('.')[-1]) <= 8
        assert len(str(result["output_cost_usd"]).split('.')[-1]) <= 8