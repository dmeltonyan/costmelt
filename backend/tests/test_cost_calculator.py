"""
Cost Melt - Cost Calculator Tests

Test suite for the production-grade cost calculator engine.
"""

import pytest
from utils.cost_calculator import CostCalculator, MODEL_PRICING, DEFAULT_BASELINE_MODEL


@pytest.fixture
def cost_calculator():
    """Fixture for cost calculator"""
    return CostCalculator()


@pytest.fixture
def cost_calculator_custom_baseline():
    """Fixture with custom baseline model"""
    return CostCalculator(default_baseline_model="gpt-4o-mini")


def test_compute_request_cost_known_model(cost_calculator):
    """Test cost calculation for known model"""
    # GPT-4o: input=$0.005/1k, output=$0.015/1k
    # 1000 input + 500 output = (1 * 0.005) + (0.5 * 0.015) = 0.005 + 0.0075 = 0.0125
    cost = cost_calculator.compute_request_cost(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == 0.0125


def test_compute_request_cost_gpt4o_mini(cost_calculator):
    """Test cost calculation for GPT-4o-mini"""
    # GPT-4o-mini: input=$0.00015/1k, output=$0.00060/1k
    # 1000 input + 500 output = (1 * 0.00015) + (0.5 * 0.00060) = 0.00015 + 0.00030 = 0.00045
    cost = cost_calculator.compute_request_cost(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == 0.00045


def test_compute_request_cost_missing_model(cost_calculator):
    """Test that missing model returns 0.0"""
    cost = cost_calculator.compute_request_cost(
        model="unknown-model",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == 0.0


def test_compute_baseline_cost_default_model(cost_calculator):
    """Test baseline cost using default model"""
    # Should use gpt-4o as default
    cost = cost_calculator.compute_baseline_cost(
        input_tokens=1000,
        output_tokens=500
    )
    
    # Should match gpt-4o pricing
    expected = cost_calculator.compute_request_cost(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == expected


def test_compute_baseline_cost_custom_model(cost_calculator):
    """Test baseline cost with custom model"""
    cost = cost_calculator.compute_baseline_cost(
        input_tokens=1000,
        output_tokens=500,
        baseline_model="gpt-4o-mini"
    )
    
    # Should match gpt-4o-mini pricing
    expected = cost_calculator.compute_request_cost(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == expected


def test_compute_savings_positive_savings(cost_calculator):
    """Test savings calculation when actual < baseline"""
    # Use cheaper model (gpt-4o-mini) vs baseline (gpt-4o)
    savings = cost_calculator.compute_savings(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert savings["actual_cost"] < savings["baseline_cost"]
    assert savings["absolute_savings"] > 0
    assert savings["savings_pct"] > 0


def test_compute_savings_zero_when_actual_gte_baseline(cost_calculator):
    """Test that savings is 0 when actual >= baseline"""
    # Use same model as baseline (gpt-4o)
    savings = cost_calculator.compute_savings(
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert savings["actual_cost"] == savings["baseline_cost"]
    assert savings["absolute_savings"] == 0.0
    assert savings["savings_pct"] == 0.0


def test_compute_savings_structure(cost_calculator):
    """Test that compute_savings returns correct structure"""
    savings = cost_calculator.compute_savings(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert "actual_cost" in savings
    assert "baseline_cost" in savings
    assert "absolute_savings" in savings
    assert "savings_pct" in savings
    
    assert isinstance(savings["actual_cost"], float)
    assert isinstance(savings["baseline_cost"], float)
    assert isinstance(savings["absolute_savings"], float)
    assert isinstance(savings["savings_pct"], float)


def test_compute_savings_rounding(cost_calculator):
    """Test that costs are properly rounded"""
    savings = cost_calculator.compute_savings(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    # Costs should be rounded to 6 decimal places
    assert len(str(savings["actual_cost"]).split('.')[-1]) <= 6
    assert len(str(savings["baseline_cost"]).split('.')[-1]) <= 6
    
    # Percentage should be rounded to 2 decimal places
    assert len(str(savings["savings_pct"]).split('.')[-1]) <= 2


def test_aggregate_savings_single_record(cost_calculator):
    """Test aggregation with single record"""
    records = [
        {
            "model": "gpt-4o-mini",
            "input_tokens": 1000,
            "output_tokens": 500
        }
    ]
    
    result = cost_calculator.aggregate_savings(records)
    
    assert "total_actual_cost" in result
    assert "total_baseline_cost" in result
    assert "total_absolute_savings" in result
    assert "avg_savings_pct" in result
    
    assert result["total_actual_cost"] > 0
    assert result["total_baseline_cost"] > 0


def test_aggregate_savings_multiple_records(cost_calculator):
    """Test aggregation with multiple records"""
    records = [
        {
            "model": "gpt-4o-mini",
            "input_tokens": 1000,
            "output_tokens": 500
        },
        {
            "model": "deepseek-chat",
            "input_tokens": 2000,
            "output_tokens": 1000
        },
        {
            "model": "claude-3-haiku",
            "input_tokens": 500,
            "output_tokens": 250
        }
    ]
    
    result = cost_calculator.aggregate_savings(records)
    
    assert result["total_actual_cost"] > 0
    assert result["total_baseline_cost"] > 0
    assert result["total_absolute_savings"] >= 0
    assert result["avg_savings_pct"] >= 0
    
    # Total actual should be sum of individual costs
    individual_actual = sum(
        cost_calculator.compute_request_cost(
            model=r["model"],
            input_tokens=r["input_tokens"],
            output_tokens=r["output_tokens"]
        )
        for r in records
    )
    
    assert abs(result["total_actual_cost"] - individual_actual) < 0.000001


def test_aggregate_savings_empty_list(cost_calculator):
    """Test aggregation with empty list"""
    result = cost_calculator.aggregate_savings([])
    
    assert result["total_actual_cost"] == 0.0
    assert result["total_baseline_cost"] == 0.0
    assert result["total_absolute_savings"] == 0.0
    assert result["avg_savings_pct"] == 0.0


def test_aggregate_savings_missing_fields(cost_calculator):
    """Test aggregation handles missing fields gracefully"""
    records = [
        {
            "model": "gpt-4o-mini",
            "input_tokens": 1000,
            "output_tokens": 500
        },
        {
            # Missing model
            "input_tokens": 1000,
            "output_tokens": 500
        }
    ]
    
    # Should not raise exception, should skip invalid record
    result = cost_calculator.aggregate_savings(records)
    
    assert result["total_actual_cost"] > 0  # Should process first record


def test_get_model_pricing_known_model(cost_calculator):
    """Test getting pricing for known model"""
    pricing = cost_calculator.get_model_pricing("gpt-4o")
    
    assert "input_per_1k" in pricing
    assert "output_per_1k" in pricing
    assert "provider" in pricing
    assert pricing["input_per_1k"] == 0.005
    assert pricing["output_per_1k"] == 0.015


def test_get_model_pricing_unknown_model(cost_calculator):
    """Test getting pricing for unknown model"""
    pricing = cost_calculator.get_model_pricing("unknown-model")
    
    assert pricing["input_per_1k"] == 0.0
    assert pricing["output_per_1k"] == 0.0
    assert pricing["provider"] == "unknown"


def test_list_models(cost_calculator):
    """Test listing all available models"""
    models = cost_calculator.list_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models


def test_custom_baseline_model(cost_calculator_custom_baseline):
    """Test cost calculator with custom baseline model"""
    # Should use gpt-4o-mini as baseline
    cost = cost_calculator_custom_baseline.compute_baseline_cost(
        input_tokens=1000,
        output_tokens=500
    )
    
    expected = cost_calculator_custom_baseline.compute_request_cost(
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == expected


def test_all_models_in_pricing_table():
    """Test that all expected models are in pricing table"""
    expected_models = [
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-haiku",
        "claude-3-5-sonnet",
        "llama3-70b-groq",
        "llama-3",
        "deepseek-chat"
    ]
    
    for model in expected_models:
        assert model in MODEL_PRICING, f"Model {model} missing from pricing table"


def test_pricing_structure():
    """Test that pricing table has correct structure"""
    for model, pricing in MODEL_PRICING.items():
        assert "input_per_1k" in pricing
        assert "output_per_1k" in pricing
        assert "provider" in pricing
        
        assert isinstance(pricing["input_per_1k"], (int, float))
        assert isinstance(pricing["output_per_1k"], (int, float))
        assert isinstance(pricing["provider"], str)
        
        assert pricing["input_per_1k"] >= 0
        assert pricing["output_per_1k"] >= 0


def test_savings_percentage_calculation(cost_calculator):
    """Test savings percentage calculation"""
    # Use very cheap model vs expensive baseline
    savings = cost_calculator.compute_savings(
        model="deepseek-chat",  # Very cheap
        input_tokens=1000,
        output_tokens=500,
        baseline_model="gpt-4o"  # Expensive
    )
    
    # Should have high savings percentage
    assert savings["savings_pct"] > 50  # Should save >50%
    assert savings["absolute_savings"] > 0


def test_zero_tokens(cost_calculator):
    """Test handling of zero tokens"""
    cost = cost_calculator.compute_request_cost(
        model="gpt-4o",
        input_tokens=0,
        output_tokens=0
    )
    
    assert cost == 0.0


def test_very_large_token_counts(cost_calculator):
    """Test handling of very large token counts"""
    # 1M input tokens, 500K output tokens
    cost = cost_calculator.compute_request_cost(
        model="gpt-4o",
        input_tokens=1_000_000,
        output_tokens=500_000
    )
    
    # Should be: (1000 * 0.005) + (500 * 0.015) = 5.0 + 7.5 = 12.5
    assert cost == 12.5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

