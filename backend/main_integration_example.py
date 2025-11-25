"""
Cost Melt - Main FastAPI Application with Security Integration

This is an example of how to integrate the authentication and security
middleware into the main FastAPI application.

Copy the relevant parts into your main.py file.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Existing imports
from api.gateway import router as gateway_router
from api.dashboard import router as dashboard_router
from api.auth import router as auth_router
from utils.logger import setup_logger

# Security imports
from backend.security.api_key_manager import APIKeyManager
from backend.middleware.auth_middleware import AuthMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware

# Database and Redis clients (adjust imports based on your setup)
from db.supabase_client import SupabaseClient
import redis.asyncio as redis

# Initialize logger
logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cost Melt API",
    description="LLM Proxy that automatically cuts token costs by routing, caching, batching, and compressing prompts",
    version="1.0.0"
)

# Initialize clients (adjust based on your setup)
supabase_client = SupabaseClient()
redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)

# Initialize API key manager
api_key_manager = APIKeyManager(supabase_client)

# Store in app state for dependency injection
app.state.api_key_manager = api_key_manager
app.state.redis_client = redis_client

# Configure CORS (update for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware (must be before rate limiting)
app.add_middleware(
    AuthMiddleware,
    api_key_manager=api_key_manager
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_client,
    default_limit=60,  # 60 requests per minute
    window_seconds=60
)

# Store rate limit middleware in app state for /auth/me endpoint
app.state.rate_limit_middleware = app.user_middleware[-1]  # Get the middleware instance

# Register routers
app.include_router(gateway_router, prefix="/v1", tags=["gateway"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(auth_router, tags=["authentication"])

@app.get("/health")
async def health_check():
    """Health check endpoint (public, no auth required)"""
    return {"status": "healthy", "service": "costmelt-backend"}

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
        port=8000,
        reload=True,
        log_level="info"
    )

