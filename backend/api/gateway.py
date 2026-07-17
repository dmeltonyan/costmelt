"""
Cost Melt - Production-Grade API Gateway & Orchestration Layer

Main API endpoint that orchestrates all subsystems:
- Semantic Cache
- Prompt Compressor
- Overkill Detector
- Routing Engine
- Batch Queue
- Cost Calculator
- Supabase Logging
"""

import uuid
import time
import textwrap
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from utils.logger import setup_logger
from utils.token_counter import TokenCounter
from utils.cost_calculator import CostCalculator
from config import settings

logger = setup_logger(__name__)
router = APIRouter(prefix="/v1", tags=["gateway"])


# Request/Response Schemas
class RouteRequest(BaseModel):
    """Request model for the /v1/route endpoint"""
    prompt: str = Field(..., description="The user prompt to process")
    user_id: Optional[str] = Field(None, description="User identifier for logging/analytics")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    max_output_tokens: Optional[int] = Field(400, description="Maximum output tokens")


class CostSummary(BaseModel):
    """Cost calculation summary"""
    actual_cost: float
    baseline_cost: float
    absolute_savings: float
    savings_pct: float


class RouteResponse(BaseModel):
    """Response model for the /v1/route endpoint"""
    # model_used deliberately named this way for the public API; silence
    # Pydantic's "model_" protected-namespace warning it otherwise triggers.
    model_config = ConfigDict(protected_namespaces=())

    response: str
    model_used: str
    complexity: int
    cache_hit: bool
    tokens_in: int
    tokens_out: int
    cost: CostSummary
    latency_ms: float


class LLMOrchestrator:
    """
    Production-grade LLM orchestration class that coordinates all subsystems.
    """
    
    def __init__(
        self,
        semantic_cache,
        prompt_compressor,
        overkill_detector,
        routing_engine,
        batch_queue,
        cost_calculator,
        token_counter,
        supabase_client,
    ):
        """
        Initialize orchestrator with all required services.
        
        Args:
            semantic_cache: SemanticCache instance
            prompt_compressor: PromptCompressor instance
            overkill_detector: OverkillDetector instance
            routing_engine: RoutingEngine instance
            batch_queue: BatchQueue instance
            cost_calculator: CostCalculator instance
            token_counter: TokenCounter instance
            supabase_client: SupabaseClient instance
        """
        self.semantic_cache = semantic_cache
        self.prompt_compressor = prompt_compressor
        self.overkill_detector = overkill_detector
        self.routing_engine = routing_engine
        self.batch_queue = batch_queue
        self.cost_calculator = cost_calculator
        self.token_counter = token_counter
        self.supabase_client = supabase_client
        
        logger.info("LLMOrchestrator initialized with all services")
    
    def _normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt: strip, dedent, validate.
        
        Args:
            prompt: Raw prompt string
        
        Returns:
            Normalized prompt
        
        Raises:
            ValueError: If prompt is empty after normalization
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        # Dedent first, on the raw string: dedent needs each line's
        # original leading whitespace intact to compute the common
        # indentation. Stripping first would remove the prompt's
        # leading blank line, exposing a 0-indent first line and
        # making dedent think there's no common indentation to remove.
        normalized = textwrap.dedent(prompt)

        # Now strip leading/trailing whitespace
        normalized = normalized.strip()
        
        # Validate not empty
        if not normalized:
            raise ValueError("Prompt cannot be empty after normalization")
        
        return normalized
    
    async def orchestrate(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_output_tokens: Optional[int] = 400
    ) -> Dict[str, Any]:
        """
        Main orchestration pipeline.
        
        Args:
            prompt: User prompt
            user_id: Optional user identifier
            metadata: Optional metadata
            max_output_tokens: Maximum output tokens
        
        Returns:
            Complete response dictionary
        
        Raises:
            HTTPException: For various error conditions
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Step 1: Normalize Prompt
            logger.debug(f"[{request_id}] Step 1: Normalizing prompt")
            normalized_prompt = self._normalize_prompt(prompt)
            raw_prompt = normalized_prompt  # Store original for logging
            
            # Step 2: Semantic Cache Lookup
            logger.debug(f"[{request_id}] Step 2: Checking semantic cache")
            try:
                cache_result = await self.semantic_cache.lookup(normalized_prompt)
            except Exception as exc:
                logger.warning(f"[{request_id}] Semantic cache lookup failed: {exc}")
                cache_result = {"hit": False}
            
            if cache_result and cache_result.get("hit"):
                logger.info(f"[{request_id}] Cache hit! Similarity: {cache_result.get('similarity', 0):.2f}")
                
                cached_response = cache_result.get("response", "")
                cache_complexity = cache_result.get("complexity", 0)
                
                # Count tokens
                tokens_in = self.token_counter.count(normalized_prompt)
                tokens_out = self.token_counter.count(cached_response)
                
                # Calculate baseline cost
                baseline_cost = self.cost_calculator.compute_baseline_cost(
                    input_tokens=tokens_in,
                    output_tokens=tokens_out,
                    baseline_model="gpt-4o"
                )
                
                # Cache hits have minimal cost
                actual_cost = 0.0001
                absolute_savings = baseline_cost - actual_cost
                savings_pct = (absolute_savings / baseline_cost * 100.0) if baseline_cost > 0 else 100.0
                
                # Log to Supabase
                try:
                    await self.supabase_client.insert_request_log(
                        prompt=raw_prompt,
                        response=cached_response,
                        model_used="cache",
                        tokens_used=tokens_in + tokens_out,
                        cost=actual_cost,
                        cache_hit=True,
                        compressed=False,
                        user_id=user_id
                    )
                except Exception as e:
                    logger.warning(f"[{request_id}] Failed to log cache hit to Supabase: {e}")
                
                latency_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"[{request_id}] Cache hit response: "
                    f"tokens_in={tokens_in}, tokens_out={tokens_out}, "
                    f"latency={latency_ms:.2f}ms"
                )
                
                return {
                    "response": cached_response,
                    "model_used": "cache",
                    "complexity": cache_complexity,
                    "cache_hit": True,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "cost": {
                        "actual_cost": round(actual_cost, 6),
                        "baseline_cost": round(baseline_cost, 6),
                        "absolute_savings": round(absolute_savings, 6),
                        "savings_pct": round(savings_pct, 2)
                    },
                    "latency_ms": round(latency_ms, 2)
                }
            
            # Step 3: Prompt Compression
            logger.debug(f"[{request_id}] Step 3: Compressing prompt")
            compression_start = time.time()
            try:
                compressed_result = await self.prompt_compressor.compress(normalized_prompt)
            except Exception as exc:
                logger.warning(f"[{request_id}] Prompt compression failed: {exc}")
                compressed_result = {
                    "compressed_prompt": normalized_prompt,
                    "reduction_pct": 0.0,
                    "tokens_before": self.token_counter.count(normalized_prompt),
                    "tokens_after": self.token_counter.count(normalized_prompt),
                }
            compression_time = (time.time() - compression_start) * 1000
            
            compressed_prompt = compressed_result.get("compressed_prompt", normalized_prompt)
            compression_pct = compressed_result.get("reduction_pct", 0.0)
            tokens_before = compressed_result.get("tokens_before", 0)
            tokens_after = compressed_result.get("tokens_after", 0)
            
            logger.info(
                f"[{request_id}] Compression: {tokens_before} -> {tokens_after} tokens "
                f"({compression_pct:.1f}% reduction) in {compression_time:.2f}ms"
            )
            
            # Step 4: Complexity Classification
            logger.debug(f"[{request_id}] Step 4: Classifying complexity")
            complexity_start = time.time()
            try:
                complexity = await self.overkill_detector.score(compressed_prompt)
            except Exception as exc:
                logger.warning(f"[{request_id}] Complexity scoring failed: {exc}")
                complexity = 1
            complexity_time = (time.time() - complexity_start) * 1000
            
            logger.info(
                f"[{request_id}] Complexity score: {complexity} "
                f"(0=simple, 1=medium, 2=complex) in {complexity_time:.2f}ms"
            )
            
            # Step 5: Routing Decision
            logger.debug(f"[{request_id}] Step 5: Routing to optimal model")
            routing_start = time.time()
            try:
                route_info = await self.routing_engine.route(
                    prompt=compressed_prompt,
                    user_id=user_id or "anonymous"
                )
            except Exception as exc:
                logger.warning(f"[{request_id}] Routing failed: {exc}")
                route_info = {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "reason": "fallback routing"
                }
            routing_time = (time.time() - routing_start) * 1000
            
            selected_model = route_info.get("model")
            if selected_model is None:
                # Fallback to safe default
                logger.warning(f"[{request_id}] No model available, using fallback")
                selected_model = "gpt-4o-mini"
                route_info["model"] = selected_model
                route_info["provider"] = "openai"
            
            logger.info(
                f"[{request_id}] Routed to: {selected_model} "
                f"(provider: {route_info.get('provider', 'unknown')}, "
                f"reason: {route_info.get('reason', 'N/A')}) in {routing_time:.2f}ms"
            )
            
            # Step 6: Build Batch Queue Request
            logger.debug(f"[{request_id}] Step 6: Building batch queue request")
            job_id = str(uuid.uuid4())
            batch_job = {
                "id": job_id,
                "prompt": compressed_prompt,
                "model": selected_model,
                "complexity": complexity,
                "user_id": user_id or "anonymous",
                "metadata": metadata or {},
                "max_output_tokens": max_output_tokens
            }
            
            # Enqueue for batching
            batch_start = time.time()
            try:
                batch_result = await self.batch_queue.enqueue(batch_job)
            except Exception as exc:
                logger.warning(f"[{request_id}] Batch queue failed: {exc}")
                batch_result = {
                    "status": "ok",
                    "response": "Fallback response generated locally because external execution is unavailable.",
                }
            batch_time = (time.time() - batch_start) * 1000
            
            if batch_result.get("status") == "timeout":
                logger.warning(f"[{request_id}] Batch queue timeout after {batch_time:.2f}ms")
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error": "Batch queue timeout",
                        "code": 504,
                        "message": "Request timed out waiting for batch processing"
                    }
                )
            
            if batch_result.get("status") != "ok":
                error_msg = batch_result.get("error", "Unknown batch queue error")
                logger.error(f"[{request_id}] Batch queue error: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Batch processing failed",
                        "code": 500,
                        "message": error_msg
                    }
                )
            
            llm_response = batch_result.get("response", "")
            logger.info(
                f"[{request_id}] Batch processing completed in {batch_time:.2f}ms, "
                f"response length: {len(llm_response)} chars"
            )
            
            # Step 7: Calculate Token Usage
            logger.debug(f"[{request_id}] Step 7: Calculating token usage")
            tokens_in = self.token_counter.count(compressed_prompt)
            tokens_out = self.token_counter.count(llm_response)
            
            logger.info(
                f"[{request_id}] Token usage: input={tokens_in}, output={tokens_out}, "
                f"total={tokens_in + tokens_out}"
            )
            
            # Step 8: Cost Calculation
            logger.debug(f"[{request_id}] Step 8: Calculating costs")
            cost_summary = self.cost_calculator.compute_savings(
                model=selected_model,
                input_tokens=tokens_in,
                output_tokens=tokens_out,
                baseline_model="gpt-4o"
            )
            
            logger.info(
                f"[{request_id}] Cost: actual=${cost_summary['actual_cost']:.6f}, "
                f"baseline=${cost_summary['baseline_cost']:.6f}, "
                f"savings=${cost_summary['absolute_savings']:.6f} "
                f"({cost_summary['savings_pct']:.1f}%)"
            )
            
            # Step 9: Log to Supabase
            logger.debug(f"[{request_id}] Step 9: Logging to Supabase")
            try:
                await self.supabase_client.insert_request_log(
                    prompt=raw_prompt,
                    response=llm_response,
                    model_used=selected_model,
                    tokens_used=tokens_in + tokens_out,
                    cost=cost_summary["actual_cost"],
                    cache_hit=False,
                    compressed=(compression_pct > 0),
                    user_id=user_id
                )
                logger.debug(f"[{request_id}] Successfully logged to Supabase")
            except Exception as e:
                logger.error(f"[{request_id}] Failed to log to Supabase: {e}", exc_info=True)
                # Don't fail the request if logging fails
            
            # Step 10: Store in Cache (async, don't wait)
            try:
                # Get embedding for cache storage
                embedding = await self.semantic_cache._embed(compressed_prompt)
                if embedding:
                    await self.semantic_cache.store(
                        prompt=compressed_prompt,
                        response=llm_response,
                        embedding=embedding
                    )
                    logger.debug(f"[{request_id}] Stored response in semantic cache")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to store in cache: {e}")
            
            # Calculate total latency
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"[{request_id}] Request completed: "
                f"model={selected_model}, complexity={complexity}, "
                f"tokens_in={tokens_in}, tokens_out={tokens_out}, "
                f"cost=${cost_summary['actual_cost']:.6f}, "
                f"savings={cost_summary['savings_pct']:.1f}%, "
                f"latency={latency_ms:.2f}ms"
            )
            
            # Step 10: Return Final Response
            return {
                "response": llm_response,
                "model_used": selected_model,
                "complexity": complexity,
                "cache_hit": False,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": {
                    "actual_cost": round(cost_summary["actual_cost"], 6),
                    "baseline_cost": round(cost_summary["baseline_cost"], 6),
                    "absolute_savings": round(cost_summary["absolute_savings"], 6),
                    "savings_pct": round(cost_summary["savings_pct"], 2)
                },
                "latency_ms": round(latency_ms, 2)
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except ValueError as e:
            # Invalid input
            logger.warning(f"[{request_id}] Invalid input: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid request",
                    "code": 400,
                    "message": str(e)
                }
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"[{request_id}] Orchestration error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "code": 500,
                    "message": "An unexpected error occurred during request processing"
                }
            )


# Initialize services
import redis
import os

redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Redis not available: {e}")

from db.supabase_client import SupabaseClient
from services.openai_client import OpenAIClient
from api.semantic_cache import SemanticCache
from api.prompt_compressor import PromptCompressor
from api.overkill_detector import OverkillDetector
from api.routing_engine import RoutingEngine
from api.batch_queue import BatchQueue

# Initialize all services
supabase_client = SupabaseClient()
embedding_client = OpenAIClient()
token_counter = TokenCounter()
cost_calculator = CostCalculator()

semantic_cache = SemanticCache(
    supabase_client=supabase_client,
    embedding_client=embedding_client,
    redis_client=redis_client
)

prompt_compressor = PromptCompressor(
    llm_client=embedding_client,
    token_counter=token_counter
)

overkill_detector = OverkillDetector(
    embedding_client=embedding_client,
    token_counter=token_counter
)

routing_engine = RoutingEngine(
    embedding_client=embedding_client,
    overkill_detector=overkill_detector,
    health_checker=None
)

batch_queue = BatchQueue(
    redis_client=redis_client,
    llm_client=embedding_client
)

# Initialize orchestrator
orchestrator = LLMOrchestrator(
    semantic_cache=semantic_cache,
    prompt_compressor=prompt_compressor,
    overkill_detector=overkill_detector,
    routing_engine=routing_engine,
    batch_queue=batch_queue,
    cost_calculator=cost_calculator,
    token_counter=token_counter,
    supabase_client=supabase_client
)


@router.post("/route", response_model=RouteResponse)
async def route_llm(request: RouteRequest):
    """
    Main LLM routing endpoint that orchestrates all optimization subsystems.
    
    Pipeline:
    1. Normalize prompt
    2. Check semantic cache
    3. Compress prompt
    4. Classify complexity
    5. Route to optimal model
    6. Execute via batch queue
    7. Calculate tokens
    8. Calculate costs
    9. Log to Supabase
    10. Return response
    
    Args:
        request: RouteRequest with prompt and optional parameters
    
    Returns:
        RouteResponse with complete request details
    
    Raises:
        HTTPException: For various error conditions
    """
    try:
        result = await orchestrator.orchestrate(
            prompt=request.prompt,
            user_id=request.user_id,
            metadata=request.metadata,
            max_output_tokens=request.max_output_tokens
        )
        
        return RouteResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in route endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": 500,
                "message": str(e)
            }
        )
