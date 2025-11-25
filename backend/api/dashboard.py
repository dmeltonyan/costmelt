"""
Cost Melt - Production-Grade Dashboard Backend API

FastAPI routes for dashboard analytics, usage metrics, cost savings,
routing distributions, cache performance, and timeseries data.
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from db.supabase_client import SupabaseClient
from utils.cost_calculator import CostCalculator
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router with prefix
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize dependencies
supabase = SupabaseClient()
cost_calculator = CostCalculator()


@router.get("/stats")
async def get_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get top-level summary statistics.
    
    Returns:
        Dict with:
        - total_requests: Total number of requests
        - total_tokens_in: Sum of input tokens
        - total_tokens_out: Sum of output tokens
        - total_actual_cost: Total actual cost
        - total_baseline_cost: Total baseline cost (if all used GPT-4o)
        - total_savings: Absolute savings
        - savings_pct: Savings percentage
        - cache_hit_rate: Cache hit rate percentage
    """
    stats_start = time.time()
    
    try:
        if not supabase.client:
            return {
                "total_requests": 0,
                "total_tokens_in": 0,
                "total_tokens_out": 0,
                "total_actual_cost": 0.0,
                "total_baseline_cost": 0.0,
                "total_savings": 0.0,
                "savings_pct": 0.0,
                "cache_hit_rate": 0.0
            }
        
        # Query all requests
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for stats")
        
        # Calculate stats
        stats = _calculate_stats(requests)
        
        stats_time = (time.time() - stats_start) * 1000
        logger.info(f"Stats calculated in {stats_time:.2f}ms")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_usage(user_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get usage breakdown by model.
    
    Returns:
        Dict with "models" list containing:
        - model: Model name
        - count: Number of requests
        - input_tokens: Total input tokens
        - output_tokens: Total output tokens
        - actual_cost: Total actual cost
    """
    usage_start = time.time()
    
    try:
        if not supabase.client:
            return {"models": []}
        
        # Query all requests
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for usage breakdown")
        
        # Calculate model breakdown
        models = _calculate_model_breakdown(requests)
        
        usage_time = (time.time() - usage_start) * 1000
        logger.info(f"Usage breakdown calculated in {usage_time:.2f}ms")
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Error getting usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache")
async def get_cache(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get cache performance metrics.
    
    Returns:
        Dict with:
        - cache_hits: Number of cache hits
        - cache_misses: Number of cache misses
        - hit_rate: Cache hit rate percentage
        - recent_hits: List of recent cache hits with prompt/response info
    """
    cache_start = time.time()
    
    try:
        if not supabase.client:
            return {
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate": 0.0,
                "recent_hits": []
            }
        
        # Query all requests
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for cache stats")
        
        # Calculate cache metrics
        cache_metrics = _calculate_cache_metrics(requests)
        
        cache_time = (time.time() - cache_start) * 1000
        logger.info(f"Cache metrics calculated in {cache_time:.2f}ms")
        
        return cache_metrics
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing")
async def get_routing(user_id: Optional[str] = None) -> Dict[str, Dict[str, int]]:
    """
    Get routing complexity and model-choice breakdown.
    
    Returns:
        Dict with:
        - complexity_distribution: Counts by complexity level (0, 1, 2)
        - model_distribution: Counts by model name
    """
    routing_start = time.time()
    
    try:
        if not supabase.client:
            return {
                "complexity_distribution": {"0": 0, "1": 0, "2": 0},
                "model_distribution": {}
            }
        
        # Query all requests
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for routing stats")
        
        # Calculate routing breakdown
        complexity_dist = {}
        model_dist = {}
        
        for req in requests:
            # Complexity distribution
            complexity = req.get("complexity")
            if complexity is not None:
                complexity_str = str(int(complexity))
                complexity_dist[complexity_str] = complexity_dist.get(complexity_str, 0) + 1
            
            # Model distribution
            model = req.get("model_used") or req.get("model_selected", "unknown")
            model_dist[model] = model_dist.get(model, 0) + 1
        
        # Ensure all complexity levels are present
        for level in ["0", "1", "2"]:
            if level not in complexity_dist:
                complexity_dist[level] = 0
        
        routing_time = (time.time() - routing_start) * 1000
        logger.info(f"Routing breakdown calculated in {routing_time:.2f}ms")
        
        return {
            "complexity_distribution": complexity_dist,
            "model_distribution": model_dist
        }
        
    except Exception as e:
        logger.error(f"Error getting routing stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily")
async def get_daily(
    days: int = Query(30, description="Number of days to look back"),
    user_id: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get daily timeseries metrics for charts.
    
    Args:
        days: Number of days to look back
        user_id: Optional user ID filter
    
    Returns:
        Dict with "days" list containing daily stats:
        - date: Date string (YYYY-MM-DD)
        - requests: Number of requests
        - tokens_in: Total input tokens
        - tokens_out: Total output tokens
        - actual_cost: Total actual cost
        - baseline_cost: Total baseline cost
        - savings: Total savings
    """
    daily_start = time.time()
    
    try:
        if not supabase.client:
            return {"days": []}
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query requests in date range
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.gte("created_at", start_date.isoformat()).execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for daily stats (last {days} days)")
        
        # Group by day
        days_data = _group_by_day(requests)
        
        daily_time = (time.time() - daily_start) * 1000
        logger.info(f"Daily stats calculated in {daily_time:.2f}ms, {len(days_data)} days")
        
        return {"days": days_data}
        
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models(user_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get model usage and cost comparison table.
    
    Returns:
        Dict with "entries" list containing:
        - model: Model name
        - requests: Number of requests
        - actual_cost: Total actual cost
        - baseline_cost: Total baseline cost
        - savings_pct: Savings percentage
    """
    models_start = time.time()
    
    try:
        if not supabase.client:
            return {"entries": []}
        
        # Query all requests
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for models breakdown")
        
        # Group by model
        model_data = {}
        
        for req in requests:
            model = req.get("model_used") or req.get("model_selected", "unknown")
            
            if model not in model_data:
                model_data[model] = {
                    "model": model,
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            
            model_data[model]["requests"] += 1
            model_data[model]["input_tokens"] += req.get("tokens_in", 0) or req.get("tokens_used", 0) // 2
            model_data[model]["output_tokens"] += req.get("tokens_out", 0) or req.get("tokens_used", 0) // 2
        
        # Calculate costs for each model
        entries = []
        for model, data in model_data.items():
            # Compute actual cost
            actual_cost = cost_calculator.compute_request_cost(
                model=model,
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"]
            )
            
            # Compute baseline cost
            baseline_cost = cost_calculator.compute_baseline_cost(
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"]
            )
            
            # Compute savings
            savings = cost_calculator.compute_savings(
                model=model,
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"]
            )
            
            entries.append({
                "model": model,
                "requests": data["requests"],
                "actual_cost": round(actual_cost, 6),
                "baseline_cost": round(baseline_cost, 6),
                "savings_pct": savings["savings_pct"]
            })
        
        # Sort by requests (descending)
        entries.sort(key=lambda x: x["requests"], reverse=True)
        
        models_time = (time.time() - models_start) * 1000
        logger.info(f"Models breakdown calculated in {models_time:.2f}ms, {len(entries)} models")
        
        return {"entries": entries}
        
    except Exception as e:
        logger.error(f"Error getting models stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/savings")
async def get_savings(
    days: int = Query(30, description="Number of days to look back"),
    user_id: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get global savings over time (graph-friendly).
    
    Args:
        days: Number of days to look back
        user_id: Optional user ID filter
    
    Returns:
        Dict with "savings_over_time" list containing:
        - date: Date string (YYYY-MM-DD)
        - saved: Savings amount for that day
    """
    savings_start = time.time()
    
    try:
        if not supabase.client:
            return {"savings_over_time": []}
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query requests in date range
        query = supabase.client.table("requests").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.gte("created_at", start_date.isoformat()).execute()
        requests = result.data if result.data else []
        
        logger.info(f"Fetched {len(requests)} requests for savings timeseries (last {days} days)")
        
        # Calculate savings timeseries
        savings_data = _calculate_savings_timeseries(requests)
        
        savings_time = (time.time() - savings_start) * 1000
        logger.info(f"Savings timeseries calculated in {savings_time:.2f}ms, {len(savings_data)} days")
        
        return {"savings_over_time": savings_data}
        
    except Exception as e:
        logger.error(f"Error getting savings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _calculate_stats(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate top-level statistics from request records.
    
    Args:
        requests: List of request records
    
    Returns:
        Dict with aggregated statistics
    """
    if not requests:
        return {
            "total_requests": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_actual_cost": 0.0,
            "total_baseline_cost": 0.0,
            "total_savings": 0.0,
            "savings_pct": 0.0,
            "cache_hit_rate": 0.0
        }
    
    total_requests = len(requests)
    total_tokens_in = 0
    total_tokens_out = 0
    total_actual_cost = 0.0
    total_baseline_cost = 0.0
    cache_hits = 0
    
    # Aggregate from requests
    for req in requests:
        # Tokens
        tokens_in = req.get("tokens_in", 0) or (req.get("tokens_used", 0) // 2)
        tokens_out = req.get("tokens_out", 0) or (req.get("tokens_used", 0) // 2)
        
        total_tokens_in += tokens_in
        total_tokens_out += tokens_out
        
        # Model
        model = req.get("model_used") or req.get("model_selected", "unknown")
        
        # Actual cost
        actual_cost = cost_calculator.compute_request_cost(
            model=model,
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )
        total_actual_cost += actual_cost
        
        # Baseline cost
        baseline_cost = cost_calculator.compute_baseline_cost(
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )
        total_baseline_cost += baseline_cost
        
        # Cache hits
        if req.get("cache_hit", False):
            cache_hits += 1
    
    # Calculate savings
    total_savings = max(total_baseline_cost - total_actual_cost, 0.0)
    savings_pct = (total_savings / total_baseline_cost * 100.0) if total_baseline_cost > 0 else 0.0
    
    # Cache hit rate
    cache_hit_rate = (cache_hits / total_requests * 100.0) if total_requests > 0 else 0.0
    
    return {
        "total_requests": total_requests,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_actual_cost": round(total_actual_cost, 6),
        "total_baseline_cost": round(total_baseline_cost, 6),
        "total_savings": round(total_savings, 6),
        "savings_pct": round(savings_pct, 2),
        "cache_hit_rate": round(cache_hit_rate, 2)
    }


def _calculate_model_breakdown(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate usage breakdown by model.
    
    Args:
        requests: List of request records
    
    Returns:
        List of model usage dicts
    """
    model_data = {}
    
    for req in requests:
        model = req.get("model_used") or req.get("model_selected", "unknown")
        
        if model not in model_data:
            model_data[model] = {
                "model": model,
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        model_data[model]["count"] += 1
        model_data[model]["input_tokens"] += req.get("tokens_in", 0) or (req.get("tokens_used", 0) // 2)
        model_data[model]["output_tokens"] += req.get("tokens_out", 0) or (req.get("tokens_used", 0) // 2)
    
    # Calculate costs
    result = []
    for model, data in model_data.items():
        actual_cost = cost_calculator.compute_request_cost(
            model=model,
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"]
        )
        
        result.append({
            "model": model,
            "count": data["count"],
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "actual_cost": round(actual_cost, 6)
        })
    
    # Sort by count (descending)
    result.sort(key=lambda x: x["count"], reverse=True)
    
    return result


def _calculate_cache_metrics(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate cache performance metrics.
    
    Args:
        requests: List of request records
    
    Returns:
        Dict with cache metrics
    """
    cache_hits = 0
    cache_misses = 0
    recent_hits = []
    
    for req in requests:
        if req.get("cache_hit", False):
            cache_hits += 1
            
            # Add to recent hits (limit to 10 most recent)
            if len(recent_hits) < 10:
                prompt = req.get("prompt", "") or req.get("raw_prompt", "")
                response = req.get("response", "")
                recent_hits.append({
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "response_length": len(response)
                })
        else:
            cache_misses += 1
    
    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total * 100.0) if total > 0 else 0.0
    
    return {
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_rate": round(hit_rate, 2),
        "recent_hits": recent_hits
    }


def _group_by_day(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group requests by day and calculate daily metrics.
    
    Args:
        requests: List of request records
    
    Returns:
        List of daily stats, sorted by date
    """
    daily_data = {}
    
    for req in requests:
        # Extract date from created_at
        created_at = req.get("created_at", "")
        if not created_at:
            continue
        
        date_str = created_at[:10]  # YYYY-MM-DD
        
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "requests": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "actual_cost": 0.0,
                "baseline_cost": 0.0,
                "savings": 0.0
            }
        
        daily_data[date_str]["requests"] += 1
        
        # Tokens
        tokens_in = req.get("tokens_in", 0) or (req.get("tokens_used", 0) // 2)
        tokens_out = req.get("tokens_out", 0) or (req.get("tokens_used", 0) // 2)
        
        daily_data[date_str]["tokens_in"] += tokens_in
        daily_data[date_str]["tokens_out"] += tokens_out
        
        # Model
        model = req.get("model_used") or req.get("model_selected", "unknown")
        
        # Costs
        actual_cost = cost_calculator.compute_request_cost(
            model=model,
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )
        daily_data[date_str]["actual_cost"] += actual_cost
        
        baseline_cost = cost_calculator.compute_baseline_cost(
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )
        daily_data[date_str]["baseline_cost"] += baseline_cost
        
        daily_data[date_str]["savings"] += max(baseline_cost - actual_cost, 0.0)
    
    # Convert to list and sort
    result = []
    for date_str, data in daily_data.items():
        result.append({
            "date": date_str,
            "requests": data["requests"],
            "tokens_in": data["tokens_in"],
            "tokens_out": data["tokens_out"],
            "actual_cost": round(data["actual_cost"], 6),
            "baseline_cost": round(data["baseline_cost"], 6),
            "savings": round(data["savings"], 6)
        })
    
    result.sort(key=lambda x: x["date"])
    
    return result


def _calculate_savings_timeseries(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate savings over time.
    
    Args:
        requests: List of request records
    
    Returns:
        List of daily savings, sorted by date
    """
    daily_savings = {}
    
    for req in requests:
        # Extract date
        created_at = req.get("created_at", "")
        if not created_at:
            continue
        
        date_str = created_at[:10]
        
        if date_str not in daily_savings:
            daily_savings[date_str] = 0.0
        
        # Calculate savings for this request
        tokens_in = req.get("tokens_in", 0) or (req.get("tokens_used", 0) // 2)
        tokens_out = req.get("tokens_out", 0) or (req.get("tokens_used", 0) // 2)
        model = req.get("model_used") or req.get("model_selected", "unknown")
        
        savings = cost_calculator.compute_savings(
            model=model,
            input_tokens=tokens_in,
            output_tokens=tokens_out
        )
        
        daily_savings[date_str] += savings["absolute_savings"]
    
    # Convert to list
    result = [
        {
            "date": date_str,
            "saved": round(saved, 6)
        }
        for date_str, saved in daily_savings.items()
    ]
    
    result.sort(key=lambda x: x["date"])
    
    return result
