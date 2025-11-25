"""
Cost Melt - Main FastAPI Application Entry Point

This is the main entry point for the Cost Melt backend service.
It initializes the FastAPI app, sets up middleware, and registers all API routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.gateway import router as gateway_router
from api.dashboard import router as dashboard_router
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cost Melt API",
    description="LLM Proxy that automatically cuts token costs by routing, caching, batching, and compressing prompts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(gateway_router, prefix="/v1", tags=["gateway"])
app.include_router(dashboard_router, tags=["dashboard"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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

