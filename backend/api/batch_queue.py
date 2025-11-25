"""
Cost Melt - Production-Grade Batch Queue Engine

Micro-batching layer using Redis for collecting and grouping requests,
then sending them as batches to LLM models to reduce latency and cost.
"""

import json
import uuid
import time
import asyncio
from typing import Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Redis key prefixes
REDIS_QUEUE_PREFIX = "costmelt:batch:"
REDIS_PENDING_PREFIX = "costmelt:pending:"

# Default configuration
DEFAULT_BATCH_WINDOW_MS = 10  # Max wait time before flushing batch
DEFAULT_MAX_BATCH_SIZE = 16  # Max batch size
DEFAULT_POLL_INTERVAL = 0.01  # Poll interval in seconds (10ms)
DEFAULT_TIMEOUT = 5.0  # Timeout in seconds


class BatchQueue:
    """
    Production-grade batch queue for micro-batching LLM requests.
    
    Features:
    - Redis-based queue per model
    - Async polling for responses
    - Timeout handling
    - Error handling and retries
    """
    
    def __init__(
        self,
        redis_client,
        llm_client=None,
        batch_window_ms: int = DEFAULT_BATCH_WINDOW_MS,
        max_batch_size: int = DEFAULT_MAX_BATCH_SIZE
    ):
        """
        Initialize batch queue.
        
        Args:
            redis_client: Redis client (sync or async-compatible)
            llm_client: LLM client with batch_generate method (optional, for fallback)
            batch_window_ms: Max wait time before flushing batch
            max_batch_size: Maximum requests per batch
        """
        self.redis = redis_client
        self.llm_client = llm_client
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        
        logger.info(
            f"BatchQueue initialized: window={batch_window_ms}ms, "
            f"max_size={max_batch_size}"
        )
    
    async def enqueue(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enqueue a request for batch processing.
        
        Args:
            request: Request dict with:
                {
                    "id": "<uuid>",  # Optional, will be generated
                    "prompt": "...",
                    "model": "gpt-4o-mini",
                    "complexity": 1,
                    "user_id": "<user-id>",
                    "metadata": {...}
                }
        
        Returns:
            Dict with response:
                {
                    "request_id": "...",
                    "status": "ok",
                    "response": "...",
                    "from_cache": false,
                    "batched": true
                }
                OR
                {
                    "request_id": "...",
                    "status": "timeout"
                }
        """
        enqueue_start = time.time()
        
        try:
            # Step 1: Normalize request
            normalized_request = self._normalize_request(request)
            
            # Step 2: Generate request_id if missing
            request_id = normalized_request.get("id")
            if not request_id:
                request_id = str(uuid.uuid4())
                normalized_request["id"] = request_id
            
            model = normalized_request.get("model", "gpt-4o-mini")
            
            logger.info(f"Enqueuing request {request_id} for model {model}")
            
            # Step 3: Store placeholder result
            pending_key = self._get_pending_key(request_id)
            placeholder = {
                "status": "pending",
                "response": None,
                "error": None,
                "request_id": request_id,
                "model": model
            }
            
            self._set_redis_value(pending_key, json.dumps(placeholder))
            
            # Step 4: Push request into model queue
            queue_key = self._get_queue_key(model)
            request_json = json.dumps(normalized_request)
            
            # Use LPUSH to add to front of queue (FIFO)
            self._lpush_redis(queue_key, request_json)
            
            logger.debug(f"Pushed request {request_id} to queue {queue_key}")
            
            # Step 5: Poll for response
            poll_start = time.time()
            max_attempts = int(DEFAULT_TIMEOUT / DEFAULT_POLL_INTERVAL)
            
            for attempt in range(max_attempts):
                # Check for response
                result = self._get_redis_value(pending_key)
                
                if result:
                    try:
                        result_data = json.loads(result)
                        status = result_data.get("status")
                        
                        if status != "pending":
                            # Response received!
                            total_time = (time.time() - enqueue_start) * 1000
                            poll_time = (time.time() - poll_start) * 1000
                            
                            logger.info(
                                f"Request {request_id} completed: status={status}, "
                                f"total_time={total_time:.2f}ms, poll_time={poll_time:.2f}ms"
                            )
                            
                            # Clean up pending key
                            self._delete_redis_key(pending_key)
                            
                            return {
                                "request_id": request_id,
                                "status": status,
                                "response": result_data.get("response"),
                                "error": result_data.get("error"),
                                "from_cache": result_data.get("from_cache", False),
                                "batched": result_data.get("batched", True),
                                "model": model
                            }
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing result for {request_id}: {e}")
                
                # Wait before next poll
                await asyncio.sleep(DEFAULT_POLL_INTERVAL)
            
            # Timeout
            total_time = (time.time() - enqueue_start) * 1000
            logger.warning(
                f"Request {request_id} timed out after {total_time:.2f}ms "
                f"(model={model})"
            )
            
            # Clean up
            self._delete_redis_key(pending_key)
            
            return {
                "request_id": request_id,
                "status": "timeout",
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Error enqueuing request: {e}", exc_info=True)
            # Return error response
            request_id = request.get("id", str(uuid.uuid4()))
            return {
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "batched": False
            }
    
    def _normalize_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize incoming request.
        
        Args:
            request: Raw request dict
        
        Returns:
            Normalized request dict
        """
        normalized = {
            "id": request.get("id"),
            "prompt": request.get("prompt", ""),
            "model": request.get("model", "gpt-4o-mini"),
            "complexity": request.get("complexity", 1),
            "user_id": request.get("user_id"),
            "metadata": request.get("metadata", {}),
            "timestamp": time.time()
        }
        
        # Add optional fields if present
        if "system_prompt" in request:
            normalized["system_prompt"] = request["system_prompt"]
        if "temperature" in request:
            normalized["temperature"] = request["temperature"]
        if "max_tokens" in request:
            normalized["max_tokens"] = request["max_tokens"]
        
        return normalized
    
    def _get_queue_key(self, model: str) -> str:
        """
        Get Redis queue key for a model.
        
        Args:
            model: Model name
        
        Returns:
            Redis key string
        """
        return f"{REDIS_QUEUE_PREFIX}{model}"
    
    def _get_pending_key(self, request_id: str) -> str:
        """
        Get Redis pending result key for a request.
        
        Args:
            request_id: Request UUID
        
        Returns:
            Redis key string
        """
        return f"{REDIS_PENDING_PREFIX}{request_id}"
    
    def _set_redis_value(self, key: str, value: str):
        """Set Redis value (sync wrapper)"""
        try:
            self.redis.set(key, value)
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            raise
    
    def _get_redis_value(self, key: str) -> Optional[str]:
        """Get Redis value (sync wrapper)"""
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None
    
    def _lpush_redis(self, key: str, value: str):
        """LPUSH to Redis list (sync wrapper)"""
        try:
            self.redis.lpush(key, value)
        except Exception as e:
            logger.error(f"Error LPUSH to Redis key {key}: {e}")
            raise
    
    def _rpop_redis(self, key: str) -> Optional[str]:
        """RPOP from Redis list (sync wrapper)"""
        try:
            return self.redis.rpop(key)
        except Exception as e:
            logger.error(f"Error RPOP from Redis key {key}: {e}")
            return None
    
    def _llen_redis(self, key: str) -> int:
        """Get length of Redis list (sync wrapper)"""
        try:
            return self.redis.llen(key) or 0
        except Exception as e:
            logger.error(f"Error LLEN Redis key {key}: {e}")
            return 0
    
    def _delete_redis_key(self, key: str):
        """Delete Redis key (sync wrapper)"""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
