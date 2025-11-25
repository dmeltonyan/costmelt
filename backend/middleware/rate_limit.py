"""
Cost Melt - Rate Limiting Middleware

Redis-based token bucket rate limiting.
Limits requests per user to prevent abuse.
"""

import time
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis token bucket algorithm.
    
    Rate limits:
    - Default: 60 requests/minute
    - Pro: 600 requests/minute
    - Enterprise: Custom (stored in database)
    
    Uses Redis key: ratelimit:{user_id}
    """
    
    def __init__(
        self,
        app,
        redis_client,
        default_limit: int = 60,
        window_seconds: int = 60
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            redis_client: Redis client (aioredis or redis)
            default_limit: Default requests per window (default: 60)
            window_seconds: Time window in seconds (default: 60)
        """
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_seconds = window_seconds
    
    async def dispatch(self, request: Request, call_next):
        """
        Check rate limit before processing request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
        
        Returns:
            Response or 429 if rate limited
        """
        # Skip rate limiting for public endpoints
        path = request.url.path
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        
        if any(path.startswith(public) for public in public_paths):
            return await call_next(request)
        
        # Get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        if not user_id:
            # No user ID means auth middleware didn't run or user is anonymous
            # For protected routes, this shouldn't happen, but handle gracefully
            return await call_next(request)
        
        # Check rate limit
        rate_limit_result = await self._check_rate_limit(user_id)
        
        if not rate_limit_result["allowed"]:
            retry_after = rate_limit_result.get("retry_after", self.window_seconds)
            
            logger.warning(f"Rate limit exceeded for user {user_id}: {rate_limit_result['remaining']}/{rate_limit_result['limit']}")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "code": 429,
                    "message": f"Too many requests. Limit: {rate_limit_result['limit']} per {self.window_seconds} seconds",
                    "retry_after": retry_after,
                    "limit": rate_limit_result["limit"],
                    "remaining": rate_limit_result["remaining"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                    "X-RateLimit-Reset": str(rate_limit_result.get("reset_at", int(time.time()) + retry_after)),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Rate limit check passed
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result.get("reset_at", int(time.time()) + self.window_seconds))
        
        return response
    
    async def _check_rate_limit(self, user_id: str) -> dict:
        """
        Check rate limit for user using token bucket algorithm.
        
        Redis structure:
        Key: ratelimit:{user_id}
        Value: current token count
        TTL: window_seconds
        
        Algorithm:
        1. Get current token count
        2. If count > 0, decrement and allow
        3. If count == 0, deny
        4. Refill tokens when TTL expires
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with:
            - allowed: bool
            - limit: int
            - remaining: int
            - retry_after: int (seconds)
            - reset_at: int (timestamp)
        """
        redis_key = f"ratelimit:{user_id}"
        limit = await self._get_user_limit(user_id)
        
        try:
            # Get current count (async redis)
            current = await self.redis.get(redis_key)
            
            if current is None:
                # First request or TTL expired - initialize with limit-1
                await self.redis.setex(redis_key, self.window_seconds, limit - 1)
                remaining = limit - 1
                reset_at = int(time.time()) + self.window_seconds
            else:
                current = int(current)
                
                if current > 0:
                    # Decrement token
                    await self.redis.decr(redis_key)
                    remaining = current - 1
                    # Get TTL for reset_at
                    ttl = await self.redis.ttl(redis_key)
                    reset_at = int(time.time()) + (ttl if ttl > 0 else self.window_seconds)
                else:
                    # No tokens remaining
                    ttl = await self.redis.ttl(redis_key)
                    retry_after = ttl if ttl > 0 else self.window_seconds
                    return {
                        "allowed": False,
                        "limit": limit,
                        "remaining": 0,
                        "retry_after": retry_after,
                        "reset_at": int(time.time()) + retry_after
                    }
            
            return {
                "allowed": True,
                "limit": limit,
                "remaining": remaining,
                "reset_at": reset_at
            }
            
        except Exception as e:
            # If Redis is unavailable, log error but allow request (fail open)
            logger.error(f"Rate limit check failed (Redis error): {e}")
            return {
                "allowed": True,  # Fail open for availability
                "limit": limit,
                "remaining": limit - 1,
                "reset_at": int(time.time()) + self.window_seconds
            }
    
    async def _get_user_limit(self, user_id: str) -> int:
        """
        Get rate limit for user.
        
        In the future, this can check database for custom limits per user/project.
        For now, returns default limit.
        
        Args:
            user_id: User identifier
        
        Returns:
            Requests per window
        """
        # TODO: Check database for custom limits
        # For now, return default
        return self.default_limit
    
    async def get_rate_limit_status(self, user_id: str) -> dict:
        """
        Get current rate limit status for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with limit, remaining, reset_at
        """
        redis_key = f"ratelimit:{user_id}"
        limit = await self._get_user_limit(user_id)
        
        try:
            # Get current status (async redis)
            current = await self.redis.get(redis_key)
            remaining = int(current) if current else limit
            
            ttl = await self.redis.ttl(redis_key)
            reset_at = int(time.time()) + (ttl if ttl > 0 else self.window_seconds)
            
            return {
                "limit": limit,
                "remaining": remaining,
                "reset_at": reset_at
            }
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {
                "limit": limit,
                "remaining": limit,
                "reset_at": int(time.time()) + self.window_seconds
            }

