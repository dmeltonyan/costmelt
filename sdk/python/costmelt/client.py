"""
Cost Melt Python SDK - Main Client

Production-ready Python client for Cost Melt API.
"""

import os
import time
import random
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter

from costmelt.types import RouteRequest, RouteResponse
from costmelt.errors import (
    CostMeltError,
    RouteError,
    APIConnectionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class CostMeltClient:
    """
    Official Python client for Cost Melt API.
    
    Provides a simple interface for routing LLM requests through Cost Melt's
    optimization pipeline with automatic retries and error handling.
    
    Example:
        >>> from costmelt import CostMeltClient
        >>> client = CostMeltClient()
        >>> response = client.route("Explain binary search.")
        >>> print(response["response"])
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize Cost Melt client.
        
        Args:
            api_key: API key for authentication (optional in dev mode)
            base_url: Base URL for Cost Melt API (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.api_key = api_key or os.getenv("COSTMELT_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create session. Retries are handled entirely by the manual loop
        # in _make_request (which needs per-status-code control — e.g. it
        # must NOT retry 429 the way it retries 5xx/504). Mounting a
        # urllib3 Retry adapter here too would retry those same status
        # codes a second, hidden time underneath _make_request, silently
        # multiplying the actual attempt count and defeating the "don't
        # retry rate limits" behavior below.
        self.session = requests.Session()
        adapter = HTTPAdapter()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"costmelt-python-sdk/0.1.0"
        })
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    def route(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_output_tokens: Optional[int] = 400
    ) -> RouteResponse:
        """
        Route an LLM request through Cost Melt's optimization pipeline.
        
        This method sends a prompt to Cost Melt, which automatically:
        - Compresses the prompt to reduce tokens
        - Checks semantic cache for similar prompts
        - Routes to the optimal model based on complexity
        - Batches requests when possible
        - Calculates cost and savings
        
        Args:
            prompt: The user prompt to process (required)
            user_id: User identifier for analytics (optional)
            metadata: Additional metadata dictionary (optional)
            max_output_tokens: Maximum output tokens (optional, default: 400)
        
        Returns:
            RouteResponse dictionary with:
            - response: LLM-generated response text
            - model_used: Model that processed the request
            - complexity: Complexity classification (0, 1, or 2)
            - cache_hit: Whether response came from cache
            - tokens_in: Number of input tokens
            - tokens_out: Number of output tokens
            - cost: Cost breakdown (actual_cost, baseline_cost, savings)
            - latency_ms: Request latency in milliseconds
        
        Raises:
            ValidationError: If prompt is invalid
            APIConnectionError: If connection to API fails
            RateLimitError: If rate limit is exceeded
            ServerError: If server returns 5xx error
            RouteError: For other routing errors
        """
        if not prompt or not prompt.strip():
            raise ValidationError("Prompt cannot be empty", code=400)
        
        # Build request payload
        payload: RouteRequest = {
            "prompt": prompt.strip(),
        }
        
        if user_id:
            payload["user_id"] = user_id
        
        if metadata:
            payload["metadata"] = metadata
        
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        
        # Make request with retries
        return self._make_request(
            method="POST",
            endpoint="/v1/route",
            payload=payload
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get global statistics from dashboard.
        
        Returns:
            Dictionary with total requests, tokens, costs, savings, cache hit rate
        """
        return self._make_request("GET", "/dashboard/stats")
    
    def get_usage(self) -> Dict[str, Any]:
        """
        Get usage breakdown by model.
        
        Returns:
            Dictionary with models list containing usage statistics
        """
        return self._make_request("GET", "/dashboard/usage")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.
        
        Returns:
            Dictionary with cache hits, misses, hit rate, recent hits
        """
        return self._make_request("GET", "/dashboard/cache")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing complexity and model distribution.
        
        Returns:
            Dictionary with complexity_distribution and model_distribution
        """
        return self._make_request("GET", "/dashboard/routing")
    
    def get_daily_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get daily timeseries metrics.
        
        Args:
            days: Number of days to look back (default: 30)
        
        Returns:
            Dictionary with days list containing daily metrics
        """
        return self._make_request("GET", f"/dashboard/daily?days={days}")
    
    def get_models_stats(self) -> Dict[str, Any]:
        """
        Get model usage and cost comparison.
        
        Returns:
            Dictionary with entries list containing model statistics
        """
        return self._make_request("GET", "/dashboard/models")
    
    def get_savings_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get historical savings over time.
        
        Args:
            days: Number of days to look back (default: 30)
        
        Returns:
            Dictionary with savings_over_time list
        """
        return self._make_request("GET", f"/dashboard/savings?days={days}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Dictionary with status information
        """
        return self._make_request("GET", "/health")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Cost Melt API with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            payload: Request payload (for POST requests)
        
        Returns:
            Response dictionary
        
        Raises:
            Various CostMeltError subclasses based on error type
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                if method == "POST":
                    response = self.session.post(
                        url,
                        json=payload,
                        timeout=self.timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        timeout=self.timeout
                    )
                
                # Handle successful response
                if response.status_code == 200:
                    return response.json()
                
                # Handle error responses
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", error_data.get("error", "Unknown error"))
                error_code = error_data.get("code", response.status_code)
                
                # Rate limit error
                if response.status_code == 429:
                    retry_after = error_data.get("retry_after")
                    raise RateLimitError(error_message, retry_after=retry_after)
                
                # Server errors (retryable)
                if 500 <= response.status_code < 600:
                    if attempt < self.max_retries - 1:
                        # Calculate backoff delay
                        delay = min(1.0 * (2 ** attempt), 60.0)
                        delay = delay * (0.5 + random.random() * 0.5)
                        time.sleep(delay)
                        continue
                    raise ServerError(error_message, code=error_code)
                
                # Timeout error
                if response.status_code == 504:
                    if attempt < self.max_retries - 1:
                        delay = min(1.0 * (2 ** attempt), 60.0)
                        time.sleep(delay)
                        continue
                    raise TimeoutError(error_message, code=error_code)
                
                # Client errors (don't retry)
                if 400 <= response.status_code < 500:
                    if response.status_code == 400:
                        raise ValidationError(error_message, code=error_code)
                    raise RouteError(error_message, code=error_code)
                
                # Unknown status code
                raise CostMeltError(error_message, code=error_code)
            
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    delay = min(1.0 * (2 ** attempt), 60.0)
                    time.sleep(delay)
                    continue
                raise TimeoutError("Request timed out", code=504)
            
            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    delay = min(1.0 * (2 ** attempt), 60.0)
                    time.sleep(delay)
                    continue
                raise APIConnectionError(f"Failed to connect to API: {str(e)}", code=0)
            
            except (RateLimitError, ValidationError, RouteError):
                # Don't retry these errors
                raise
            
            except Exception as e:
                if isinstance(e, CostMeltError):
                    raise
                
                if attempt < self.max_retries - 1:
                    delay = min(1.0 * (2 ** attempt), 60.0)
                    time.sleep(delay)
                    continue
                
                raise APIConnectionError(f"Unexpected error: {str(e)}", code=0)

        # Every branch above raises on the final attempt; this is unreachable.
        raise APIConnectionError("Failed to make request after retries", code=0)

