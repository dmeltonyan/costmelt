"""
Cost Melt - Batch Worker

Background worker that processes batched requests from Redis queue.
Groups requests by model and sends them as batches to LLM APIs.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Configuration (should match BatchQueue)
BATCH_WINDOW_MS = 10  # Max wait time before flushing batch
MAX_BATCH_SIZE = 16  # Max batch size
REDIS_QUEUE_PREFIX = "costmelt:batch:"
REDIS_PENDING_PREFIX = "costmelt:pending:"

# Models to process
SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "deepseek-chat",
    "llama-3",
    "llama3-70b-groq"
]


async def run_batch_worker(redis_client, llm_client):
    """
    Main batch worker loop.
    
    Continuously:
    - Check all model queues
    - If there are items, group into batch
    - Call llm_client.batch_generate()
    - Write back results
    
    Args:
        redis_client: Redis client instance
        llm_client: LLM client with batch_generate method
    """
    logger.info("Batch worker started")
    
    while True:
        try:
            # Process each model queue
            for model in SUPPORTED_MODELS:
                await _process_model_queue(redis_client, llm_client, model)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.001)  # 1ms
            
        except Exception as e:
            logger.error(f"Error in batch worker loop: {e}", exc_info=True)
            await asyncio.sleep(1)  # Wait 1s on error


async def _process_model_queue(
    redis_client,
    llm_client,
    model: str
):
    """
    Process batch queue for a specific model.
    
    Args:
        redis_client: Redis client
        llm_client: LLM client
        model: Model name
    """
    queue_key = f"{REDIS_QUEUE_PREFIX}{model}"
    
    # Check queue length
    queue_length = redis_client.llen(queue_key)
    
    if queue_length == 0:
        return  # No requests in queue
    
    # Determine batch size
    batch_size = min(queue_length, MAX_BATCH_SIZE)
    
    # Collect batch
    batch_start = time.time()
    requests = []
    
    # Pop requests from queue
    for _ in range(batch_size):
        request_json = redis_client.rpop(queue_key)
        if not request_json:
            break
        
        try:
            request = json.loads(request_json)
            requests.append(request)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing request from queue: {e}")
            continue
    
    if not requests:
        return  # No valid requests
    
    # Check if we should wait for more (if batch is small and window hasn't expired)
    if len(requests) < MAX_BATCH_SIZE:
        # Check age of oldest request
        oldest_timestamp = min(req.get("timestamp", time.time()) for req in requests)
        age_ms = (time.time() - oldest_timestamp) * 1000
        
        # If oldest request is still fresh, wait a bit more
        if age_ms < BATCH_WINDOW_MS:
            wait_time = (BATCH_WINDOW_MS - age_ms) / 1000
            await asyncio.sleep(wait_time)
            
            # Try to get more requests
            while len(requests) < MAX_BATCH_SIZE:
                request_json = redis_client.rpop(queue_key)
                if not request_json:
                    break
                
                try:
                    request = json.loads(request_json)
                    requests.append(request)
                except json.JSONDecodeError:
                    continue
    
    # Process batch
    if requests:
        await _process_batch(redis_client, llm_client, requests, model)


async def _process_batch(
    redis_client,
    llm_client,
    requests: List[Dict[str, Any]],
    model: str
):
    """
    Process a batch of requests.
    
    Args:
        redis_client: Redis client
        llm_client: LLM client with batch_generate method
        requests: List of request dictionaries
        model: Model name
    """
    batch_start = time.time()
    batch_size = len(requests)
    
    logger.info(f"Processing batch of {batch_size} requests for model {model}")
    
    try:
        # Extract prompts from requests
        prompts = [req.get("prompt", "") for req in requests]
        request_ids = [req.get("id") for req in requests]
        
        # Call LLM batch generate
        if hasattr(llm_client, 'batch_generate'):
            # Use batch_generate if available
            responses = await llm_client.batch_generate(
                model=model,
                prompts=prompts
            )
        else:
            # Fallback: process individually in parallel
            responses = await _process_individually(llm_client, requests, model)
        
        # Map responses back to requests
        batch_time = (time.time() - batch_start) * 1000
        
        for i, request_id in enumerate(request_ids):
            if i < len(responses):
                response_text = responses[i] if isinstance(responses[i], str) else responses[i].get("text", "")
                
                result = {
                    "status": "ok",
                    "response": response_text,
                    "error": None,
                    "model": model,
                    "batched": True,
                    "batch_size": batch_size
                }
            else:
                # Missing response - mark as error
                result = {
                    "status": "error",
                    "response": None,
                    "error": "Missing response in batch",
                    "model": model,
                    "batched": True
                }
            
            # Write result to pending key
            pending_key = f"{REDIS_PENDING_PREFIX}{request_id}"
            redis_client.set(pending_key, json.dumps(result))
            
            # Set TTL (clean up after 60 seconds)
            redis_client.expire(pending_key, 60)
        
        logger.info(
            f"Batch processed: {batch_size} requests for {model}, "
            f"time={batch_time:.2f}ms"
        )
        
    except Exception as e:
        logger.error(f"Error processing batch for {model}: {e}", exc_info=True)
        
        # Write error to all pending keys
        for req in requests:
            request_id = req.get("id")
            if request_id:
                result = {
                    "status": "error",
                    "response": None,
                    "error": str(e),
                    "model": model,
                    "batched": True
                }
                
                pending_key = f"{REDIS_PENDING_PREFIX}{request_id}"
                redis_client.set(pending_key, json.dumps(result))
                redis_client.expire(pending_key, 60)


async def _process_individually(
    llm_client,
    requests: List[Dict[str, Any]],
    model: str
) -> List[str]:
    """
    Process requests individually in parallel (fallback when batch_generate not available).
    
    Args:
        llm_client: LLM client
        requests: List of request dictionaries
        model: Model name
    
    Returns:
        List of response texts
    """
    async def process_one(req: Dict[str, Any]) -> str:
        """Process a single request"""
        try:
            # Get appropriate client for model
            client = _get_client_for_model(llm_client, model)
            
            if not client:
                return f"Error: No client for model {model}"
            
            response = await client.complete(
                prompt=req.get("prompt", ""),
                system_prompt=req.get("system_prompt"),
                model=model,
                temperature=req.get("temperature", 0.7),
                max_tokens=req.get("max_tokens", 1000)
            )
            
            return response.get("text", "")
        except Exception as e:
            logger.error(f"Error processing individual request: {e}")
            return f"Error: {str(e)}"
    
    # Process all requests in parallel
    tasks = [process_one(req) for req in requests]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error strings
    result = []
    for resp in responses:
        if isinstance(resp, Exception):
            result.append(f"Error: {str(resp)}")
        else:
            result.append(resp)
    
    return result


def _get_client_for_model(llm_client, model: str):
    """
    Get appropriate LLM client for a model.
    
    Args:
        llm_client: Base LLM client or client factory
        model: Model name
    
    Returns:
        LLM client instance
    """
    # If llm_client has a method to get client by model, use it
    if hasattr(llm_client, 'get_client_for_model'):
        return llm_client.get_client_for_model(model)
    
    # Otherwise, import clients directly
    from services.openai_client import OpenAIClient
    from services.anthropic_client import AnthropicClient
    from services.deepseek_client import DeepSeekClient
    from services.groq_client import GroqClient
    
    client_map = {
        "gpt-4o": OpenAIClient(),
        "gpt-4o-mini": OpenAIClient(),
        "claude-3-5-sonnet": AnthropicClient(),
        "claude-3-haiku": AnthropicClient(),
        "deepseek-chat": DeepSeekClient(),
        "llama-3": GroqClient(),
        "llama3-70b-groq": GroqClient()
    }
    
    return client_map.get(model)


# Main entry point for running worker
async def main():
    """Main entry point for batch worker"""
    import redis
    import os
    
    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    try:
        redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return
    
    # Initialize LLM client (placeholder - should be injected)
    # In production, this would be a proper LLM client factory
    llm_client = None  # Will use individual client fallback
    
    # Run worker
    await run_batch_worker(redis_client, llm_client)


if __name__ == "__main__":
    # Run worker
    # Usage: python -m workers.batch_worker
    # Or: uvicorn workers.batch_worker:main
    asyncio.run(main())
