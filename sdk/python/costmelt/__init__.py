"""
Cost Melt Python SDK

Official Python client library for Cost Melt - LLM routing, caching, batching, and cost-optimization proxy.
"""

from costmelt.client import CostMeltClient
from costmelt.errors import (
    CostMeltError,
    RouteError,
    APIConnectionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from costmelt.types import (
    RouteRequest,
    RouteResponse,
    CostSummary,
)

__version__ = "0.1.0"
__all__ = [
    "CostMeltClient",
    "CostMeltError",
    "RouteError",
    "APIConnectionError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "RouteRequest",
    "RouteResponse",
    "CostSummary",
]
