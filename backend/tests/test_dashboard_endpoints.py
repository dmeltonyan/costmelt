"""
Cost Melt - Dashboard Endpoints Tests

Test suite for the production-grade dashboard backend API.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any
from datetime import datetime, timedelta


# Mock classes
class MockSupabaseClient:
    """Mock Supabase client"""
    
    def __init__(self):
        self.client = Mock()
        self.requests_data = []
    
    def set_requests(self, requests: List[Dict[str, Any]]):
        """Set mock request data"""
        self.requests_data = requests
        
        # Setup mock query chain
        mock_result = Mock()
        mock_result.data = requests
        mock_result.execute.return_value = mock_result
        
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        self.client.table.return_value = mock_query


class MockCostCalculator:
    """Mock cost calculator"""
    
    def __init__(self):
        self.calls = []
    
    def compute_request_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Mock cost calculation"""
        self.calls.append(("compute_request_cost", model, input_tokens, output_tokens))
        
        # Simple mock: $0.01 per 1000 tokens
        return (input_tokens + output_tokens) / 1000.0 * 0.01
    
    def compute_baseline_cost(self, input_tokens: int, output_tokens: int, baseline_model: str = None) -> float:
        """Mock baseline cost"""
        self.calls.append(("compute_baseline_cost", input_tokens, output_tokens, baseline_model))
        
        # Mock baseline: $0.05 per 1000 tokens (more expensive)
        return (input_tokens + output_tokens) / 1000.0 * 0.05
    
    def compute_savings(self, model: str, input_tokens: int, output_tokens: int, baseline_model: str = None) -> Dict[str, float]:
        """Mock savings calculation"""
        self.calls.append(("compute_savings", model, input_tokens, output_tokens))
        
        actual = self.compute_request_cost(model, input_tokens, output_tokens)
        baseline = self.compute_baseline_cost(input_tokens, output_tokens, baseline_model)
        
        return {
            "actual_cost": actual,
            "baseline_cost": baseline,
            "absolute_savings": max(baseline - actual, 0.0),
            "savings_pct": ((baseline - actual) / baseline * 100.0) if baseline > 0 else 0.0
        }


@pytest.fixture
def mock_supabase():
    """Fixture for mock Supabase client"""
    return MockSupabaseClient()


@pytest.fixture
def mock_cost_calculator():
    """Fixture for mock cost calculator"""
    return MockCostCalculator()


@pytest.fixture
def dashboard_router(mock_supabase, mock_cost_calculator):
    """Fixture for dashboard router with mocks"""
    from api.dashboard import router, supabase, cost_calculator
    
    # Replace with mocks
    import api.dashboard as dashboard_module
    dashboard_module.supabase = mock_supabase
    dashboard_module.cost_calculator = mock_cost_calculator
    
    return router


@pytest.mark.asyncio
async def test_stats_returns_expected_fields(mock_supabase, mock_cost_calculator):
    """Test that stats endpoint returns expected fields"""
    from api.dashboard import get_stats
    
    # Setup mock data
    mock_supabase.set_requests([
        {
            "id": "1",
            "model_used": "gpt-4o-mini",
            "tokens_in": 100,
            "tokens_out": 50,
            "cache_hit": False,
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "2",
            "model_used": "gpt-4o-mini",
            "tokens_in": 200,
            "tokens_out": 100,
            "cache_hit": True,
            "created_at": "2025-01-01T00:00:00Z"
        }
    ])
    
    result = await get_stats()
    
    assert "total_requests" in result
    assert "total_tokens_in" in result
    assert "total_tokens_out" in result
    assert "total_actual_cost" in result
    assert "total_baseline_cost" in result
    assert "total_savings" in result
    assert "savings_pct" in result
    assert "cache_hit_rate" in result
    
    assert result["total_requests"] == 2
    assert result["cache_hit_rate"] == 50.0


@pytest.mark.asyncio
async def test_usage_sorted_by_model(mock_supabase, mock_cost_calculator):
    """Test that usage endpoint returns models sorted by count"""
    from api.dashboard import get_usage
    
    mock_supabase.set_requests([
        {"model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50},
        {"model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50},
        {"model_used": "llama-3", "tokens_in": 50, "tokens_out": 25}
    ])
    
    result = await get_usage()
    
    assert "models" in result
    assert len(result["models"]) == 2
    
    # Should be sorted by count (descending)
    assert result["models"][0]["count"] >= result["models"][1]["count"]


@pytest.mark.asyncio
async def test_cache_hit_miss_calculations(mock_supabase, mock_cost_calculator):
    """Test cache hit/miss calculations are correct"""
    from api.dashboard import get_cache
    
    mock_supabase.set_requests([
        {"cache_hit": True},
        {"cache_hit": True},
        {"cache_hit": False},
        {"cache_hit": False},
        {"cache_hit": False}
    ])
    
    result = await get_cache()
    
    assert result["cache_hits"] == 2
    assert result["cache_misses"] == 3
    assert result["hit_rate"] == 40.0


@pytest.mark.asyncio
async def test_routing_complexity_grouped(mock_supabase, mock_cost_calculator):
    """Test routing complexity distribution"""
    from api.dashboard import get_routing
    
    mock_supabase.set_requests([
        {"complexity": 0, "model_used": "gpt-4o-mini"},
        {"complexity": 0, "model_used": "gpt-4o-mini"},
        {"complexity": 1, "model_used": "claude-3-haiku"},
        {"complexity": 2, "model_used": "gpt-4o"}
    ])
    
    result = await get_routing()
    
    assert "complexity_distribution" in result
    assert "model_distribution" in result
    
    assert result["complexity_distribution"]["0"] == 2
    assert result["complexity_distribution"]["1"] == 1
    assert result["complexity_distribution"]["2"] == 1
    
    assert result["model_distribution"]["gpt-4o-mini"] == 2
    assert result["model_distribution"]["claude-3-haiku"] == 1


@pytest.mark.asyncio
async def test_daily_metrics_sorted_chronologically(mock_supabase, mock_cost_calculator):
    """Test daily metrics are sorted chronologically"""
    from api.dashboard import get_daily
    
    mock_supabase.set_requests([
        {"created_at": "2025-01-03T00:00:00Z", "model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50},
        {"created_at": "2025-01-01T00:00:00Z", "model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50},
        {"created_at": "2025-01-02T00:00:00Z", "model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50}
    ])
    
    result = await get_daily(days=30)
    
    assert "days" in result
    assert len(result["days"]) == 3
    
    # Should be sorted chronologically
    dates = [day["date"] for day in result["days"]]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_models_endpoint_uses_cost_calculator(mock_supabase, mock_cost_calculator):
    """Test models endpoint uses cost calculator"""
    from api.dashboard import get_models
    
    mock_supabase.set_requests([
        {"model_used": "gpt-4o-mini", "tokens_in": 1000, "tokens_out": 500},
        {"model_used": "gpt-4o-mini", "tokens_in": 1000, "tokens_out": 500}
    ])
    
    result = await get_models()
    
    assert "entries" in result
    assert len(result["entries"]) > 0
    
    # Check that cost calculator was called
    assert len(mock_cost_calculator.calls) > 0
    
    # Check entry structure
    entry = result["entries"][0]
    assert "model" in entry
    assert "requests" in entry
    assert "actual_cost" in entry
    assert "baseline_cost" in entry
    assert "savings_pct" in entry


@pytest.mark.asyncio
async def test_savings_endpoint_returns_non_negative(mock_supabase, mock_cost_calculator):
    """Test savings endpoint returns non-negative values"""
    from api.dashboard import get_savings
    
    mock_supabase.set_requests([
        {"created_at": "2025-01-01T00:00:00Z", "model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50},
        {"created_at": "2025-01-02T00:00:00Z", "model_used": "deepseek-chat", "tokens_in": 100, "tokens_out": 50}
    ])
    
    result = await get_savings(days=30)
    
    assert "savings_over_time" in result
    
    for entry in result["savings_over_time"]:
        assert "date" in entry
        assert "saved" in entry
        assert entry["saved"] >= 0  # Should be non-negative


@pytest.mark.asyncio
async def test_stats_empty_data(mock_supabase, mock_cost_calculator):
    """Test stats with empty data"""
    from api.dashboard import get_stats
    
    mock_supabase.set_requests([])
    
    result = await get_stats()
    
    assert result["total_requests"] == 0
    assert result["total_actual_cost"] == 0.0
    assert result["cache_hit_rate"] == 0.0


@pytest.mark.asyncio
async def test_usage_model_breakdown(mock_supabase, mock_cost_calculator):
    """Test usage breakdown includes all required fields"""
    from api.dashboard import get_usage
    
    mock_supabase.set_requests([
        {"model_used": "gpt-4o-mini", "tokens_in": 1000, "tokens_out": 500}
    ])
    
    result = await get_usage()
    
    assert "models" in result
    assert len(result["models"]) > 0
    
    model = result["models"][0]
    assert "model" in model
    assert "count" in model
    assert "input_tokens" in model
    assert "output_tokens" in model
    assert "actual_cost" in model


@pytest.mark.asyncio
async def test_cache_recent_hits_limit(mock_supabase, mock_cost_calculator):
    """Test that recent hits are limited"""
    from api.dashboard import get_cache
    
    # Create 20 cache hits
    requests = [
        {"cache_hit": True, "prompt": f"Prompt {i}", "response": "Response"}
        for i in range(20)
    ]
    mock_supabase.set_requests(requests)
    
    result = await get_cache()
    
    # Should limit to 10 recent hits
    assert len(result["recent_hits"]) <= 10


@pytest.mark.asyncio
async def test_daily_includes_all_fields(mock_supabase, mock_cost_calculator):
    """Test daily endpoint includes all required fields"""
    from api.dashboard import get_daily
    
    mock_supabase.set_requests([
        {"created_at": "2025-01-01T00:00:00Z", "model_used": "gpt-4o-mini", "tokens_in": 100, "tokens_out": 50}
    ])
    
    result = await get_daily(days=30)
    
    assert "days" in result
    if result["days"]:
        day = result["days"][0]
        assert "date" in day
        assert "requests" in day
        assert "tokens_in" in day
        assert "tokens_out" in day
        assert "actual_cost" in day
        assert "baseline_cost" in day
        assert "savings" in day


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

