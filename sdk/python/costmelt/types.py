"""
Cost Melt Python SDK - Type Definitions

Type definitions for requests and responses.
"""

from typing import TypedDict, Optional, Dict, Any


class CostSummary(TypedDict):
    """Cost breakdown for a request"""
    actual_cost: float
    baseline_cost: float
    absolute_savings: float
    savings_pct: float


class RouteRequest(TypedDict, total=False):
    """Request payload for /v1/route endpoint"""
    prompt: str
    user_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    max_output_tokens: Optional[int]


class RouteResponse(TypedDict):
    """Response from /v1/route endpoint"""
    response: str
    model_used: str
    complexity: int
    cache_hit: bool
    tokens_in: int
    tokens_out: int
    cost: CostSummary
    latency_ms: float


class ErrorResponse(TypedDict):
    """Error response structure"""
    error: str
    code: int
    message: str

