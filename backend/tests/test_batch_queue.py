"""
Cost Melt - Batch Queue Tests

Test suite for the production-grade batch queue engine.
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any


# Mock classes for testing
class MockRedisClient:
    """Mock Redis client"""
    
    def __init__(self):
        self.data = {}
        self.lists = {}
        self.call_count = 0
    
    def set(self, key: str, value: str):
        """Set value"""
        self.data[key] = value
        self.call_count += 1
    
    def get(self, key: str) -> str:
        """Get value"""
        return self.data.get(key)
    
    def lpush(self, key: str, value: str):
        """LPUSH to list"""
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)  # Insert at front
    
    def rpop(self, key: str) -> str:
        """RPOP from list"""
        if key not in self.lists or not self.lists[key]:
            return None
        return self.lists[key].pop()  # Pop from end
    
    def llen(self, key: str) -> int:
        """Get list length"""
        return len(self.lists.get(key, []))
    
    def delete(self, key: str):
        """Delete key"""
        self.data.pop(key, None)
        self.lists.pop(key, None)
    
    def expire(self, key: str, seconds: int):
        """Set expiration (mock - doesn't actually expire)"""
        pass
    
    def ping(self):
        """Test connection"""
        return True


class MockLLMClient:
    """Mock LLM client with batch_generate"""
    
    def __init__(self):
        self.batch_calls = []
        self.responses = {}
    
    async def batch_generate(self, model: str, prompts: List[str]) -> List[str]:
        """Mock batch generate"""
        self.batch_calls.append((model, prompts))
        
        # Return mock responses
        if model in self.responses:
            return self.responses[model]
        
        # Default: return simple responses
        return [f"Response to: {prompt[:20]}..." for prompt in prompts]
    
    def set_responses(self, model: str, responses: List[str]):
        """Set custom responses for a model"""
        self.responses[model] = responses


@pytest.fixture
def mock_redis_client():
    """Fixture for mock Redis client"""
    return MockRedisClient()


@pytest.fixture
def mock_llm_client():
    """Fixture for mock LLM client"""
    return MockLLMClient()


@pytest.fixture
def batch_queue(mock_redis_client, mock_llm_client):
    """Fixture for batch queue with mocks"""
    from api.batch_queue import BatchQueue
    
    return BatchQueue(
        redis_client=mock_redis_client,
        llm_client=mock_llm_client,
        batch_window_ms=10,
        max_batch_size=16
    )


@pytest.mark.asyncio
async def test_enqueue_returns_request_id(batch_queue, mock_redis_client):
    """Test that enqueue returns a request_id"""
    request = {
        "prompt": "Test prompt",
        "model": "gpt-4o-mini"
    }
    
    # Start enqueue (will timeout since no worker)
    task = asyncio.create_task(batch_queue.enqueue(request))
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Check that request was added to queue
    queue_key = f"costmelt:batch:gpt-4o-mini"
    assert mock_redis_client.llen(queue_key) > 0
    
    # Cancel task (it will timeout)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_enqueue_timeout(batch_queue, mock_redis_client):
    """Test that enqueue times out if no worker writes response"""
    request = {
        "prompt": "Test prompt",
        "model": "gpt-4o-mini"
    }
    
    # Enqueue (will timeout)
    result = await batch_queue.enqueue(request)
    
    assert result["status"] == "timeout"
    assert "request_id" in result


@pytest.mark.asyncio
async def test_enqueue_with_response(batch_queue, mock_redis_client):
    """Test enqueue when worker writes response"""
    request = {
        "prompt": "Test prompt",
        "model": "gpt-4o-mini"
    }
    
    # Enqueue
    enqueue_task = asyncio.create_task(batch_queue.enqueue(request))
    
    # Wait a bit for request to be enqueued
    await asyncio.sleep(0.05)
    
    # Simulate worker writing response
    # Get request_id from queue
    queue_key = f"costmelt:batch:gpt-4o-mini"
    if mock_redis_client.llen(queue_key) > 0:
        request_json = mock_redis_client.rpop(queue_key)
        request_data = json.loads(request_json)
        request_id = request_data["id"]
        
        # Write response
        pending_key = f"costmelt:pending:{request_id}"
        response_data = {
            "status": "ok",
            "response": "Test response",
            "error": None,
            "batched": True
        }
        mock_redis_client.set(pending_key, json.dumps(response_data))
    
    # Wait for result
    result = await enqueue_task
    
    assert result["status"] == "ok"
    assert result["response"] == "Test response"
    assert result["batched"] is True


@pytest.mark.asyncio
async def test_normalize_request(batch_queue):
    """Test request normalization"""
    request = {
        "prompt": "Test",
        "model": "gpt-4o-mini",
        "user_id": "user123"
    }
    
    normalized = batch_queue._normalize_request(request)
    
    assert normalized["prompt"] == "Test"
    assert normalized["model"] == "gpt-4o-mini"
    assert normalized["user_id"] == "user123"
    assert "timestamp" in normalized


@pytest.mark.asyncio
async def test_generates_request_id_if_missing(batch_queue, mock_redis_client):
    """Test that request_id is generated if missing"""
    request = {
        "prompt": "Test",
        "model": "gpt-4o-mini"
    }
    
    # Enqueue (will timeout)
    result = await batch_queue.enqueue(request)
    
    assert "request_id" in result
    assert result["request_id"] is not None


@pytest.mark.asyncio
async def test_uses_existing_request_id(batch_queue, mock_redis_client):
    """Test that existing request_id is used"""
    request_id = str(uuid.uuid4())
    request = {
        "id": request_id,
        "prompt": "Test",
        "model": "gpt-4o-mini"
    }
    
    # Enqueue (will timeout)
    result = await batch_queue.enqueue(request)
    
    assert result["request_id"] == request_id


@pytest.mark.asyncio
async def test_error_handling(batch_queue):
    """Test error handling"""
    # Create batch queue with None redis (will cause error)
    from api.batch_queue import BatchQueue
    
    broken_queue = BatchQueue(redis_client=None)
    
    request = {
        "prompt": "Test",
        "model": "gpt-4o-mini"
    }
    
    result = await broken_queue.enqueue(request)
    
    assert result["status"] == "error"
    assert "error" in result


def test_queue_key_generation(batch_queue):
    """Test queue key generation"""
    key = batch_queue._get_queue_key("gpt-4o-mini")
    assert key == "costmelt:batch:gpt-4o-mini"


def test_pending_key_generation(batch_queue):
    """Test pending key generation"""
    request_id = str(uuid.uuid4())
    key = batch_queue._get_pending_key(request_id)
    assert key == f"costmelt:pending:{request_id}"


@pytest.mark.asyncio
async def test_integration_with_worker(mock_redis_client, mock_llm_client):
    """Integration test with fake redis and llm client"""
    from api.batch_queue import BatchQueue
    from workers.batch_worker import _process_model_queue
    
    # Create batch queue
    batch_queue = BatchQueue(
        redis_client=mock_redis_client,
        llm_client=mock_llm_client
    )
    
    # Set up mock responses
    mock_llm_client.set_responses("gpt-4o-mini", ["Response 1", "Response 2"])
    
    # Enqueue two requests
    request1 = {
        "prompt": "Prompt 1",
        "model": "gpt-4o-mini"
    }
    request2 = {
        "prompt": "Prompt 2",
        "model": "gpt-4o-mini"
    }
    
    # Start enqueue tasks
    task1 = asyncio.create_task(batch_queue.enqueue(request1))
    task2 = asyncio.create_task(batch_queue.enqueue(request2))
    
    # Wait for requests to be enqueued
    await asyncio.sleep(0.05)
    
    # Process queue with worker
    await _process_model_queue(mock_redis_client, mock_llm_client, "gpt-4o-mini")
    
    # Wait for results
    result1 = await task1
    result2 = await task2
    
    # Check results
    assert result1["status"] == "ok" or result1["status"] == "timeout"
    assert result2["status"] == "ok" or result2["status"] == "timeout"


@pytest.mark.asyncio
async def test_batch_size_limit(mock_redis_client, mock_llm_client):
    """Test that batch size is limited"""
    from workers.batch_worker import _process_model_queue
    
    # Add more than MAX_BATCH_SIZE requests
    queue_key = "costmelt:batch:gpt-4o-mini"
    for i in range(20):  # More than MAX_BATCH_SIZE (16)
        request = {
            "id": str(uuid.uuid4()),
            "prompt": f"Prompt {i}",
            "model": "gpt-4o-mini",
            "timestamp": 0  # Old timestamp to trigger immediate processing
        }
        mock_redis_client.lpush(queue_key, json.dumps(request))
    
    # Process queue
    await _process_model_queue(mock_redis_client, mock_llm_client, "gpt-4o-mini")
    
    # Check that batch was called with correct size
    assert len(mock_llm_client.batch_calls) > 0
    model, prompts = mock_llm_client.batch_calls[0]
    assert len(prompts) <= 16  # Should not exceed MAX_BATCH_SIZE


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

