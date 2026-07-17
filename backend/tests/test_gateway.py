"""
Cost Melt - Gateway Tests

Test suite for the production-grade API Gateway & Orchestration Layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.gateway import (
    router,
    LLMOrchestrator,
    RouteRequest,
    RouteResponse
)


# Mock classes
#
# Each public method is an AsyncMock/Mock wired with side_effect=<impl>.
# This keeps the realistic default behavior (impl) AND still lets tests
# use `.assert_called()` / reassign `.return_value` — assigning a bare
# `self.method = AsyncMock()` here would silently shadow the impl below
# it and swallow real return values, which caused cost math to receive
# unconfigured Mock objects instead of numbers.
class MockSemanticCache:
    def __init__(self):
        self.lookup = AsyncMock(side_effect=self._lookup)
        self.store = AsyncMock(side_effect=self._store)
        self._embed = AsyncMock(side_effect=self._embed_impl)

    async def _lookup(self, prompt: str):
        return {"hit": False}

    async def _store(self, prompt: str, response: str, embedding: list):
        pass

    async def _embed_impl(self, prompt: str):
        return [0.1] * 1536


class MockPromptCompressor:
    def __init__(self):
        self.compress = AsyncMock(side_effect=self._compress)

    async def _compress(self, prompt: str):
        return {
            "compressed_prompt": prompt,
            "tokens_before": 100,
            "tokens_after": 80,
            "reduction_pct": 20.0,
            "strategy": ["rules"]
        }


class MockOverkillDetector:
    def __init__(self):
        self.score = AsyncMock(side_effect=self._score)

    async def _score(self, prompt: str):
        return 1


class MockRoutingEngine:
    def __init__(self):
        self.route = AsyncMock(side_effect=self._route)

    async def _route(self, prompt: str, user_id: str):
        return {
            "model": "gpt-4o-mini",
            "provider": "openai",
            "complexity": 1,
            "reason": "medium complexity"
        }


class MockBatchQueue:
    def __init__(self):
        self.enqueue = AsyncMock(side_effect=self._enqueue)

    async def _enqueue(self, job: dict):
        return {
            "status": "ok",
            "response": "This is a test response from the LLM.",
            "request_id": job.get("id")
        }


class MockCostCalculator:
    def __init__(self):
        self.compute_savings = Mock(side_effect=self._compute_savings)
        self.compute_baseline_cost = Mock(side_effect=self._compute_baseline_cost)

    def _compute_savings(self, model: str, input_tokens: int, output_tokens: int, baseline_model: str = None):
        return {
            "actual_cost": 0.00028,
            "baseline_cost": 0.00192,
            "absolute_savings": 0.00164,
            "savings_pct": 85.4
        }

    def _compute_baseline_cost(self, input_tokens: int, output_tokens: int, baseline_model: str = None):
        return 0.00192


class MockTokenCounter:
    def __init__(self):
        self.count = Mock(side_effect=self._count)

    def _count(self, text: str):
        return len(text.split()) * 2  # Rough estimate


class MockSupabaseClient:
    def __init__(self):
        self.insert_request_log = AsyncMock(side_effect=self._insert_request_log)

    async def _insert_request_log(self, **kwargs):
        return {"id": "test-id"}


@pytest.fixture
def mock_services():
    """Fixture providing all mocked services"""
    return {
        "semantic_cache": MockSemanticCache(),
        "prompt_compressor": MockPromptCompressor(),
        "overkill_detector": MockOverkillDetector(),
        "routing_engine": MockRoutingEngine(),
        "batch_queue": MockBatchQueue(),
        "cost_calculator": MockCostCalculator(),
        "token_counter": MockTokenCounter(),
        "supabase_client": MockSupabaseClient()
    }


@pytest.fixture
def orchestrator(mock_services):
    """Fixture for LLMOrchestrator with mocked services"""
    return LLMOrchestrator(**mock_services)


@pytest.mark.asyncio
async def test_cache_hit(orchestrator, mock_services):
    """Test that cache hits return immediately"""
    # Setup cache hit
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={
        "hit": True,
        "response": "Cached response",
        "similarity": 0.95,
        "complexity": 0
    })
    
    result = await orchestrator.orchestrate(
        prompt="Test prompt",
        user_id="test-user"
    )
    
    assert result["cache_hit"] is True
    assert result["model_used"] == "cache"
    assert result["response"] == "Cached response"
    assert result["cost"]["actual_cost"] == 0.0001


@pytest.mark.asyncio
async def test_compression_path(orchestrator, mock_services):
    """Test prompt compression is applied"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    result = await orchestrator.orchestrate(
        prompt="This is a test prompt that should be compressed",
        user_id="test-user"
    )
    
    # Verify compression was called
    mock_services["prompt_compressor"].compress.assert_called_once()
    assert result["cache_hit"] is False


@pytest.mark.asyncio
async def test_routing_path(orchestrator, mock_services):
    """Test routing engine is called"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    result = await orchestrator.orchestrate(
        prompt="Test prompt for routing",
        user_id="test-user"
    )
    
    # Verify routing was called
    mock_services["routing_engine"].route.assert_called_once()
    assert result["model_used"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_batch_queue_integration(orchestrator, mock_services):
    """Test batch queue integration"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    result = await orchestrator.orchestrate(
        prompt="Test prompt for batching",
        user_id="test-user"
    )
    
    # Verify batch queue was called
    mock_services["batch_queue"].enqueue.assert_called_once()
    assert result["response"] == "This is a test response from the LLM."


@pytest.mark.asyncio
async def test_cost_calculator_integration(orchestrator, mock_services):
    """Test cost calculator is used"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    result = await orchestrator.orchestrate(
        prompt="Test prompt for cost calculation",
        user_id="test-user"
    )
    
    # Verify cost calculator was called
    mock_services["cost_calculator"].compute_savings.assert_called()
    assert "cost" in result
    assert result["cost"]["actual_cost"] > 0
    assert result["cost"]["savings_pct"] > 0


@pytest.mark.asyncio
async def test_supabase_logging(orchestrator, mock_services):
    """Test Supabase logging"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    await orchestrator.orchestrate(
        prompt="Test prompt for logging",
        user_id="test-user"
    )
    
    # Verify Supabase logging was called
    mock_services["supabase_client"].insert_request_log.assert_called()


@pytest.mark.asyncio
async def test_timeout_handling(orchestrator, mock_services):
    """Test batch queue timeout handling"""
    from fastapi import HTTPException
    
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    # Setup timeout
    mock_services["batch_queue"].enqueue = AsyncMock(return_value={
        "status": "timeout"
    })
    
    # Should raise HTTPException with 504
    with pytest.raises(HTTPException) as exc_info:
        await orchestrator.orchestrate(
            prompt="Test prompt for timeout",
            user_id="test-user"
        )
    
    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_invalid_input(orchestrator):
    """Test invalid input handling"""
    from fastapi import HTTPException
    
    # Empty prompt
    with pytest.raises(HTTPException) as exc_info:
        await orchestrator.orchestrate(prompt="")
    
    assert exc_info.value.status_code == 400
    
    # Whitespace-only prompt
    with pytest.raises(HTTPException) as exc_info:
        await orchestrator.orchestrate(prompt="   \n\t  ")
    
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_normalize_prompt(orchestrator):
    """Test prompt normalization"""
    # Test dedent
    prompt = """
        This is a test prompt
        with indentation
    """
    
    normalized = orchestrator._normalize_prompt(prompt)
    assert normalized == "This is a test prompt\nwith indentation"
    
    # Test strip
    prompt = "  Test prompt  "
    normalized = orchestrator._normalize_prompt(prompt)
    assert normalized == "Test prompt"


@pytest.mark.asyncio
async def test_full_pipeline(orchestrator, mock_services):
    """Test complete orchestration pipeline"""
    # Setup all mocks
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    mock_services["semantic_cache"]._embed = AsyncMock(return_value=[0.1] * 1536)
    
    result = await orchestrator.orchestrate(
        prompt="What is the capital of France?",
        user_id="test-user",
        metadata={"source": "test"},
        max_output_tokens=200
    )
    
    # Verify all steps were executed
    assert result["cache_hit"] is False
    assert result["model_used"] == "gpt-4o-mini"
    assert result["complexity"] == 1
    assert result["tokens_in"] > 0
    assert result["tokens_out"] > 0
    assert "cost" in result
    assert "latency_ms" in result
    
    # Verify all services were called
    mock_services["semantic_cache"].lookup.assert_called_once()
    mock_services["prompt_compressor"].compress.assert_called_once()
    mock_services["overkill_detector"].score.assert_called_once()
    mock_services["routing_engine"].route.assert_called_once()
    mock_services["batch_queue"].enqueue.assert_called_once()
    mock_services["cost_calculator"].compute_savings.assert_called()
    mock_services["supabase_client"].insert_request_log.assert_called()


@pytest.mark.asyncio
async def test_fallback_model(orchestrator, mock_services):
    """Test fallback to default model when routing returns None"""
    # Setup cache miss
    mock_services["semantic_cache"].lookup = AsyncMock(return_value={"hit": False})
    
    # Setup routing to return None model
    mock_services["routing_engine"].route = AsyncMock(return_value={
        "model": None,
        "provider": None,
        "complexity": 1,
        "reason": "No models available"
    })
    
    result = await orchestrator.orchestrate(
        prompt="Test prompt with fallback",
        user_id="test-user"
    )
    
    # Should fallback to gpt-4o-mini
    assert result["model_used"] == "gpt-4o-mini"


def test_route_request_schema():
    """Test RouteRequest schema validation"""
    # Valid request
    request = RouteRequest(
        prompt="Test prompt",
        user_id="test-user",
        max_output_tokens=500
    )
    assert request.prompt == "Test prompt"
    assert request.user_id == "test-user"
    assert request.max_output_tokens == 500
    
    # Default values
    request = RouteRequest(prompt="Test")
    assert request.user_id is None
    assert request.max_output_tokens == 400


def test_route_response_schema():
    """Test RouteResponse schema validation"""
    response = RouteResponse(
        response="Test response",
        model_used="gpt-4o-mini",
        complexity=1,
        cache_hit=False,
        tokens_in=100,
        tokens_out=50,
        cost={
            "actual_cost": 0.00028,
            "baseline_cost": 0.00192,
            "absolute_savings": 0.00164,
            "savings_pct": 85.4
        },
        latency_ms=120.5
    )
    
    assert response.response == "Test response"
    assert response.model_used == "gpt-4o-mini"
    assert response.complexity == 1
    assert response.cache_hit is False
    assert response.tokens_in == 100
    assert response.tokens_out == 50
    assert response.cost.actual_cost == 0.00028
    assert response.latency_ms == 120.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

