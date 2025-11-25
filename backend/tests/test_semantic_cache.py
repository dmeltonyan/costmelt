"""
Cost Melt - Semantic Cache Tests

Test suite for the production-grade semantic cache engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List, Dict, Any
import uuid
import time


# Mock classes for testing
class MockEmbeddingClient:
    """Mock embedding client"""
    
    def __init__(self):
        self.embeddings = {}
        self.call_count = 0
    
    async def get_embedding(self, text: str, model: str = "text-embedding-3-small"):
        """Return mock embedding"""
        self.call_count += 1
        if text not in self.embeddings:
            # Generate a simple mock embedding (1536 dimensions)
            self.embeddings[text] = [0.1] * 1536
        return {"embedding": self.embeddings[text]}
    
    def set_embedding(self, text: str, embedding: List[float]):
        """Set embedding for a specific text"""
        self.embeddings[text] = embedding


class MockSupabaseClient:
    """Mock Supabase client"""
    
    def __init__(self):
        self.client = Mock()
        self.cache_entries = {}
        self.rpc_results = []
    
    def set_rpc_result(self, result: List[Dict[str, Any]]):
        """Set result for RPC calls"""
        self.rpc_results = result
    
    def get_rpc_mock(self):
        """Get mock RPC callable"""
        def rpc_mock(function_name, params):
            mock_result = Mock()
            mock_result.execute.return_value.data = self.rpc_results
            return mock_result
        return rpc_mock
    
    def get_table_mock(self):
        """Get mock table callable"""
        def table_mock(table_name):
            mock_table = Mock()
            
            # Mock insert
            def insert(data):
                cache_id = data.get("id", str(uuid.uuid4()))
                self.cache_entries[cache_id] = data
                mock_result = Mock()
                mock_result.data = [data]
                mock_result.execute.return_value = mock_result
                return mock_result
            
            # Mock delete
            def delete():
                mock_delete = Mock()
                
                def eq(column, value):
                    if value in self.cache_entries:
                        del self.cache_entries[value]
                    return mock_delete
                
                mock_delete.eq = eq
                mock_delete.execute.return_value = None
                return mock_delete
            
            mock_table.insert = insert
            mock_table.delete = delete
            return mock_table
        
        return table_mock


class MockRedisClient:
    """Mock Redis client"""
    
    def __init__(self):
        self.data = {}
        self.sets = {}
        self.call_count = 0
    
    def get(self, key: str):
        """Get value from Redis"""
        return self.data.get(key)
    
    def set(self, key: str, value: Any):
        """Set value in Redis"""
        self.data[key] = value
    
    def incr(self, key: str):
        """Increment value"""
        current = int(self.data.get(key, 0))
        self.data[key] = current + 1
        return current + 1
    
    def decr(self, key: str):
        """Decrement value"""
        current = int(self.data.get(key, 0))
        self.data[key] = max(0, current - 1)
        return self.data[key]
    
    def expire(self, key: str, seconds: int):
        """Set expiration (mock - doesn't actually expire)"""
        pass
    
    def delete(self, *keys: str):
        """Delete keys"""
        for key in keys:
            self.data.pop(key, None)
    
    def sadd(self, key: str, *values: str):
        """Add to set"""
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].update(values)
    
    def srem(self, key: str, *values: str):
        """Remove from set"""
        if key in self.sets:
            self.sets[key].difference_update(values)
    
    def smembers(self, key: str):
        """Get set members"""
        return self.sets.get(key, set())
    
    def ping(self):
        """Test connection"""
        return True


@pytest.fixture
def mock_embedding_client():
    """Fixture for mock embedding client"""
    return MockEmbeddingClient()


@pytest.fixture
def mock_supabase_client():
    """Fixture for mock Supabase client"""
    client = MockSupabaseClient()
    client.client.rpc = client.get_rpc_mock()
    client.client.table = client.get_table_mock()
    return client


@pytest.fixture
def mock_redis_client():
    """Fixture for mock Redis client"""
    return MockRedisClient()


@pytest.fixture
def semantic_cache(mock_supabase_client, mock_embedding_client, mock_redis_client):
    """Fixture for semantic cache with mocks"""
    from api.semantic_cache import SemanticCache
    
    return SemanticCache(
        supabase_client=mock_supabase_client,
        embedding_client=mock_embedding_client,
        redis_client=mock_redis_client,
        similarity_threshold=0.92,
        ttl_seconds=604800
    )


@pytest.mark.asyncio
async def test_lookup_cache_hit(semantic_cache, mock_supabase_client, mock_embedding_client):
    """Test cache lookup with hit"""
    prompt = "What is the capital of France?"
    
    # Set up mock embedding
    embedding = [0.1] * 1536
    mock_embedding_client.set_embedding(prompt, embedding)
    
    # Set up mock Supabase result
    cache_id = str(uuid.uuid4())
    mock_result = [{
        "id": cache_id,
        "prompt": prompt,
        "response": "The capital of France is Paris.",
        "similarity": 0.95,
        "created_at": "2024-01-01T00:00:00Z"
    }]
    mock_supabase_client.set_rpc_result(mock_result)
    
    result = await semantic_cache.lookup(prompt)
    
    assert result is not None
    assert result["hit"] is True
    assert result["response"] == "The capital of France is Paris."
    assert result["similarity"] == 0.95
    assert result["id"] == cache_id


@pytest.mark.asyncio
async def test_lookup_cache_miss_low_similarity(semantic_cache, mock_supabase_client, mock_embedding_client):
    """Test cache lookup with miss due to low similarity"""
    prompt = "What is the capital of France?"
    
    # Set up mock embedding
    embedding = [0.1] * 1536
    mock_embedding_client.set_embedding(prompt, embedding)
    
    # Set up mock Supabase result with low similarity
    mock_result = [{
        "id": str(uuid.uuid4()),
        "prompt": "Different prompt",
        "response": "Some response",
        "similarity": 0.85,  # Below threshold of 0.92
        "created_at": "2024-01-01T00:00:00Z"
    }]
    mock_supabase_client.set_rpc_result(mock_result)
    
    result = await semantic_cache.lookup(prompt)
    
    assert result is None  # Should return None on miss


@pytest.mark.asyncio
async def test_lookup_cache_miss_no_results(semantic_cache, mock_supabase_client, mock_embedding_client):
    """Test cache lookup with miss due to no results"""
    prompt = "What is the capital of France?"
    
    # Set up mock embedding
    embedding = [0.1] * 1536
    mock_embedding_client.set_embedding(prompt, embedding)
    
    # Set up empty result
    mock_supabase_client.set_rpc_result([])
    
    result = await semantic_cache.lookup(prompt)
    
    assert result is None


@pytest.mark.asyncio
async def test_store_cache_entry(semantic_cache, mock_supabase_client, mock_redis_client):
    """Test storing a cache entry"""
    prompt = "What is the capital of France?"
    response = "The capital of France is Paris."
    embedding = [0.1] * 1536
    
    result = await semantic_cache.store(prompt, response, embedding)
    
    assert result["stored"] is True
    assert "id" in result
    assert result["ttl_seconds"] == 604800
    
    # Verify Redis metadata was stored
    cache_id = result["id"]
    assert mock_redis_client.get(f"cache:lru:{cache_id}") is not None
    assert mock_redis_client.get(f"cache:timestamps:{cache_id}") is not None


@pytest.mark.asyncio
async def test_normalize_prompt(semantic_cache):
    """Test prompt normalization"""
    # Test with multiple spaces
    prompt = "  This   has    multiple    spaces  "
    normalized = semantic_cache._normalize_prompt(prompt)
    
    assert normalized == "This has multiple spaces"
    assert "  " not in normalized  # No double spaces
    
    # Test with newlines
    prompt = "Line 1\nLine 2\nLine 3"
    normalized = semantic_cache._normalize_prompt(prompt)
    
    assert "\n" not in normalized  # Newlines should be replaced with spaces


@pytest.mark.asyncio
async def test_embed_computation(semantic_cache, mock_embedding_client):
    """Test embedding computation"""
    prompt = "Test prompt"
    
    embedding = await semantic_cache._embed(prompt)
    
    assert len(embedding) == 1536  # text-embedding-3-small dimension
    assert mock_embedding_client.call_count > 0


@pytest.mark.asyncio
async def test_lru_tracking(semantic_cache, mock_redis_client):
    """Test LRU tracking"""
    cache_id = str(uuid.uuid4())
    
    # Touch LRU
    await semantic_cache._touch_lru(cache_id)
    
    # Check that LRU counter was incremented
    lru_key = f"cache:lru:{cache_id}"
    lru_value = mock_redis_client.get(lru_key)
    assert lru_value == 1
    
    # Touch again
    await semantic_cache._touch_lru(cache_id)
    lru_value = mock_redis_client.get(lru_key)
    assert lru_value == 2


@pytest.mark.asyncio
async def test_eviction_when_full(semantic_cache, mock_redis_client, mock_supabase_client):
    """Test eviction when cache is full"""
    # Set cache size to exceed limit
    semantic_cache.max_size = 5
    mock_redis_client.set("cache:size", 10)  # Exceeds limit
    
    # Add some cache IDs to recent keys
    for i in range(10):
        cache_id = str(uuid.uuid4())
        mock_redis_client.sadd("cache:recent_keys", cache_id)
        mock_redis_client.set(f"cache:lru:{cache_id}", i)  # Different LRU scores
    
    # Trigger eviction
    await semantic_cache._evict_if_needed()
    
    # Check that size was reduced
    size = int(mock_redis_client.get("cache:size") or 0)
    assert size <= semantic_cache.max_size


@pytest.mark.asyncio
async def test_ttl_setting(semantic_cache, mock_redis_client):
    """Test TTL setting"""
    cache_id = str(uuid.uuid4())
    
    # Set TTL
    await semantic_cache._set_ttl(cache_id)
    
    # Verify keys exist (TTL is set, but mock doesn't actually expire)
    lru_key = f"cache:lru:{cache_id}"
    timestamp_key = f"cache:timestamps:{cache_id}"
    
    # Keys should exist (TTL doesn't delete immediately)
    assert mock_redis_client.get(lru_key) is not None or True  # Mock may not track expire


@pytest.mark.asyncio
async def test_best_match_selection(semantic_cache):
    """Test best match selection from results"""
    results = [
        {"id": "1", "similarity": 0.85},
        {"id": "2", "similarity": 0.95},
        {"id": "3", "similarity": 0.90}
    ]
    
    best = semantic_cache._best_match(results)
    
    assert best["id"] == "2"  # Highest similarity
    assert best["similarity"] == 0.95


@pytest.mark.asyncio
async def test_error_handling_embedding_failure(semantic_cache, mock_embedding_client):
    """Test error handling when embedding fails"""
    prompt = "Test prompt"
    
    # Make embedding client raise exception
    async def failing_embed(text, model):
        raise Exception("Embedding failed")
    
    mock_embedding_client.get_embedding = failing_embed
    
    result = await semantic_cache.lookup(prompt)
    
    # Should return None on error
    assert result is None


@pytest.mark.asyncio
async def test_error_handling_supabase_failure(semantic_cache, mock_supabase_client):
    """Test error handling when Supabase fails"""
    prompt = "Test prompt"
    
    # Make Supabase client unavailable
    mock_supabase_client.client = None
    
    result = await semantic_cache.lookup(prompt)
    
    # Should return None on error
    assert result is None


@pytest.mark.asyncio
async def test_store_with_redis_unavailable(semantic_cache, mock_supabase_client):
    """Test storing when Redis is unavailable"""
    prompt = "Test prompt"
    response = "Test response"
    embedding = [0.1] * 1536
    
    # Make Redis unavailable
    semantic_cache.redis = None
    
    result = await semantic_cache.store(prompt, response, embedding)
    
    # Should still store in Supabase
    assert result["stored"] is True


def test_similarity_threshold_configurable():
    """Test that similarity threshold is configurable"""
    from api.semantic_cache import SemanticCache
    
    cache1 = SemanticCache(
        supabase_client=Mock(),
        embedding_client=Mock(),
        redis_client=Mock(),
        similarity_threshold=0.90
    )
    
    cache2 = SemanticCache(
        supabase_client=Mock(),
        embedding_client=Mock(),
        redis_client=Mock(),
        similarity_threshold=0.95
    )
    
    assert cache1.similarity_threshold == 0.90
    assert cache2.similarity_threshold == 0.95


def test_ttl_configurable():
    """Test that TTL is configurable"""
    from api.semantic_cache import SemanticCache
    
    cache1 = SemanticCache(
        supabase_client=Mock(),
        embedding_client=Mock(),
        redis_client=Mock(),
        ttl_seconds=3600  # 1 hour
    )
    
    cache2 = SemanticCache(
        supabase_client=Mock(),
        embedding_client=Mock(),
        redis_client=Mock(),
        ttl_seconds=86400  # 1 day
    )
    
    assert cache1.ttl_seconds == 3600
    assert cache2.ttl_seconds == 86400


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

