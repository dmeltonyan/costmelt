"""
Cost Melt - Main FastAPI Application Entry Point

This is the main entry point for the Cost Melt backend service.
It initializes the FastAPI app, sets up middleware, and registers all API routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import redis.asyncio as redis_asyncio

from api.gateway import router as gateway_router
from api.dashboard import router as dashboard_router
from api.auth import router as auth_router
from db.supabase_client import SupabaseClient
from security.api_key_manager import APIKeyManager
from middleware.auth_middleware import AuthMiddleware
from middleware.rate_limit import RateLimiter, RateLimitMiddleware
from utils.logger import setup_logger
from config import settings

# Initialize logger
logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cost Melt API",
    description="LLM Proxy that automatically cuts token costs by routing, caching, batching, and compressing prompts",
    version="1.0.0"
)

# Shared auth/rate-limit services. APIKeyManager talks to the raw Supabase
# client (SupabaseClient.client), not the SupabaseClient wrapper itself.
supabase_client = SupabaseClient()
api_key_manager = APIKeyManager(supabase_client.client)
rate_limit_redis = redis_asyncio.from_url(settings.redis_url, decode_responses=True)
rate_limiter = RateLimiter(rate_limit_redis, default_limit=60, window_seconds=60)

app.state.api_key_manager = api_key_manager
app.state.rate_limiter = rate_limiter

# Middleware order matters: Starlette runs the LAST-added middleware
# FIRST on the way in. We add them innermost-first so the effective
# request flow is CORS -> Auth -> RateLimit -> route handler. CORS must
# be outermost so browsers can still read 401/429 error bodies; Auth
# must run before RateLimit so request.state.user_id is populated.
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
app.add_middleware(AuthMiddleware, api_key_manager=api_key_manager)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers. gateway_router and dashboard_router already declare
# their own prefixes ("/v1", "/dashboard") internally — don't add another
# one here or routes end up double-prefixed (e.g. /v1/v1/route).
app.include_router(gateway_router, tags=["gateway"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(auth_router, tags=["authentication"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "costmelt-backend",
        "mode": "local-ready",
        "cors_origins": settings.cors_allow_origins,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness endpoint for deployment and local startup checks."""
    return {
        "status": "ready",
        "service": "costmelt-backend",
        "dependencies": {
            "redis": True,
            "supabase": False,
            "openai": False,
        },
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True,
        log_level="info"
    )

