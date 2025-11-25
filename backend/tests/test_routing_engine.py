"""
Cost Melt - Routing Engine Tests

Test suite for the production-grade routing engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from api.routing_engine import RoutingEngine, MODEL_COSTS, ROUTING_RULES
from utils.provider_health import ProviderHealth


# Mock classes for testing
class MockEmbeddingClient:
    """Mock embedding client"""
    
    def __init__(self):
        self.embeddings = {}
    
    async def get_embedding(self, text: str, model: str = "text-embedding-3-small"):
        """Return mock embedding"""
        if text not in self.embeddings:
            # Generate a simple mock embedding (1536 dimensions for text-embedding-3-small)
            self.embeddings[text] = [0.1] * 1536
        return {"embedding": self.embeddings[text]}


class MockOverkillDetector:
    """Mock overkill detector"""
    
    def __init__(self, default_complexity: int = 1):
        self.default_complexity = default_complexity
        self.complexity_map = {}
    
    async def score(self, prompt: str) -> int:
        """Return mock complexity score"""
        return self.complexity_map.get(prompt, self.default_complexity)
    
    async def detect_complexity(self, prompt: str) -> int:
        """Alias for score"""
        return await self.score(prompt)
    
    def set_complexity(self, prompt: str, complexity: int):
        """Set complexity for a specific prompt"""
        self.complexity_map[prompt] = complexity


class MockProviderHealth:
    """Mock provider health checker"""
    
    def __init__(self):
        self.health_status = {
            "openai": True,
            "anthropic": True,
            "groq": True,
            "deepseek": True
        }
    
    def is_healthy(self, provider: str) -> bool:
        """Return mock health status"""
        return self.health_status.get(provider, True)
    
    def mark_unhealthy(self, provider: str):
        """Mark provider as unhealthy"""
        self.health_status[provider] = False
    
    def mark_healthy(self, provider: str):
        """Mark provider as healthy"""
        self.health_status[provider] = True


@pytest.fixture
def mock_embedding_client():
    """Fixture for mock embedding client"""
    return MockEmbeddingClient()


@pytest.fixture
def mock_overkill_detector():
    """Fixture for mock overkill detector"""
    return MockOverkillDetector()


@pytest.fixture
def mock_health_checker():
    """Fixture for mock health checker"""
    return MockProviderHealth()


@pytest.fixture
def routing_engine(mock_embedding_client, mock_overkill_detector, mock_health_checker):
    """Fixture for routing engine with mocks"""
    return RoutingEngine(
        embedding_client=mock_embedding_client,
        overkill_detector=mock_overkill_detector,
        health_checker=mock_health_checker
    )


@pytest.mark.asyncio
async def test_route_simple_prompt(routing_engine, mock_overkill_detector):
    """Test routing for simple prompt"""
    prompt = "What is the capital of France?"
    mock_overkill_detector.set_complexity(prompt, 0)
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    assert result["model"] is not None
    assert result["complexity"] == 0
    assert result["provider"] is not None
    assert result["reason"] is not None
    # Simple prompts should route to cheapest models
    assert result["model"] in ROUTING_RULES[0]


@pytest.mark.asyncio
async def test_route_medium_prompt(routing_engine, mock_overkill_detector):
    """Test routing for medium complexity prompt"""
    prompt = "Explain how SQL joins work with examples"
    mock_overkill_detector.set_complexity(prompt, 1)
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    assert result["model"] is not None
    assert result["complexity"] == 1
    assert result["model"] in ROUTING_RULES[1]


@pytest.mark.asyncio
async def test_route_complex_prompt(routing_engine, mock_overkill_detector):
    """Test routing for complex prompt"""
    prompt = "Design a distributed system architecture for handling 1M requests per second"
    mock_overkill_detector.set_complexity(prompt, 2)
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    assert result["model"] is not None
    assert result["complexity"] == 2
    assert result["model"] in ROUTING_RULES[2]


@pytest.mark.asyncio
async def test_provider_health_fallback(routing_engine, mock_overkill_detector, mock_health_checker):
    """Test fallback when provider is unhealthy"""
    prompt = "Simple question"
    mock_overkill_detector.set_complexity(prompt, 0)
    
    # Mark groq as unhealthy (first choice for simple prompts)
    mock_health_checker.mark_unhealthy("groq")
    mock_health_checker.mark_unhealthy("deepseek")
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    # Should fallback to gpt-4o-mini (still in simple list)
    assert result["model"] is not None
    assert result["model"] == "gpt-4o-mini"  # Should be cheapest available


@pytest.mark.asyncio
async def test_cost_aware_selection(routing_engine, mock_overkill_detector):
    """Test that cheapest model is selected when multiple available"""
    prompt = "Simple prompt"
    mock_overkill_detector.set_complexity(prompt, 0)
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    # Should select cheapest from complexity 0 models
    selected_cost = MODEL_COSTS.get(result["model"], float('inf'))
    other_costs = [MODEL_COSTS.get(m, float('inf')) for m in ROUTING_RULES[0]]
    
    # Selected model should be among the cheapest
    assert selected_cost <= min(other_costs)


@pytest.mark.asyncio
async def test_normalize_prompt(routing_engine):
    """Test prompt normalization"""
    prompt = "  This   has    multiple    spaces  "
    normalized = routing_engine._normalize_prompt(prompt)
    
    assert normalized == "This has multiple spaces"
    assert "  " not in normalized  # No double spaces


@pytest.mark.asyncio
async def test_embedding_caching(routing_engine, mock_embedding_client):
    """Test that embeddings are cached"""
    prompt = "Test prompt for caching"
    
    # First call
    embedding1 = await routing_engine._get_embedding(prompt)
    
    # Second call should use cache
    embedding2 = await routing_engine._get_embedding(prompt)
    
    assert embedding1 == embedding2
    # Verify only one call was made (check mock if needed)


@pytest.mark.asyncio
async def test_heuristic_complexity_fallback(routing_engine):
    """Test heuristic complexity when detector fails"""
    # Test simple prompt
    simple_prompt = "Hello world"
    complexity = routing_engine._heuristic_complexity(simple_prompt)
    assert complexity == 0
    
    # Test medium prompt
    medium_prompt = "Explain how this works"
    complexity = routing_engine._heuristic_complexity(medium_prompt)
    assert complexity == 1
    
    # Test complex prompt
    complex_prompt = "Analyze and compare these algorithms"
    complexity = routing_engine._heuristic_complexity(complex_prompt)
    assert complexity == 2


@pytest.mark.asyncio
async def test_error_handling(routing_engine, mock_overkill_detector):
    """Test error handling when routing fails"""
    prompt = "Test prompt"
    
    # Make overkill detector raise exception
    async def failing_score(p):
        raise Exception("Detector failed")
    
    mock_overkill_detector.score = failing_score
    
    # Should still return a result (with heuristic fallback)
    result = await routing_engine.route(prompt, user_id="test_user")
    
    assert result["model"] is not None  # Should have fallback
    assert result["complexity"] in [0, 1, 2]


@pytest.mark.asyncio
async def test_all_providers_unhealthy(routing_engine, mock_overkill_detector, mock_health_checker):
    """Test behavior when all providers are unhealthy"""
    prompt = "Test prompt"
    mock_overkill_detector.set_complexity(prompt, 0)
    
    # Mark all providers as unhealthy
    for provider in ["openai", "anthropic", "groq", "deepseek"]:
        mock_health_checker.mark_unhealthy(provider)
    
    result = await routing_engine.route(prompt, user_id="test_user")
    
    # Should attempt fallback, but if all unhealthy, might return error
    # The implementation should handle this gracefully
    assert "model" in result
    # Model might be None if truly no providers available


def test_model_costs_defined():
    """Test that all models have cost definitions"""
    all_models = []
    for models in ROUTING_RULES.values():
        all_models.extend(models)
    
    for model in set(all_models):
        assert model in MODEL_COSTS, f"Model {model} missing cost definition"


def test_provider_mapping_complete():
    """Test that all models have provider mappings"""
    from api.routing_engine import MODEL_TO_PROVIDER
    
    all_models = []
    for models in ROUTING_RULES.values():
        all_models.extend(models)
    
    for model in set(all_models):
        assert model in MODEL_TO_PROVIDER, f"Model {model} missing provider mapping"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

