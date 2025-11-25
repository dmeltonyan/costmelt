"""
Cost Melt - Authentication Middleware

Validates API keys on all /v1/* and /dashboard/* routes.
Attaches user information to request.state for downstream use.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging

from backend.security.api_key_manager import APIKeyManager

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate requests using API keys.
    
    Accepts API keys in:
    - Authorization: Bearer <key>
    - x-api-key: <key>
    
    Public endpoints (no auth required):
    - /health
    - /docs
    - /openapi.json
    - /redoc
    """
    
    def __init__(self, app, api_key_manager: APIKeyManager):
        """
        Initialize auth middleware.
        
        Args:
            app: FastAPI application
            api_key_manager: APIKeyManager instance
        """
        super().__init__(app)
        self.api_key_manager = api_key_manager
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate API key.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        # Check if endpoint requires authentication
        path = request.url.path
        
        # Public endpoints (no auth required)
        public_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
        
        if any(path.startswith(public) for public in public_paths):
            return await call_next(request)
        
        # Protected endpoints require API key
        protected_paths = ["/v1/", "/dashboard/", "/auth/"]
        
        if any(path.startswith(protected) for protected in protected_paths):
            # Extract API key from headers
            api_key = self._extract_api_key(request)
            
            if not api_key:
                logger.warning(f"Missing API key for {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Authentication required",
                        "code": 401,
                        "message": "API key is required. Provide it via 'Authorization: Bearer <key>' or 'x-api-key: <key>' header"
                    }
                )
            
            # Verify API key
            auth_result = await self.api_key_manager.verify_api_key(api_key)
            
            if not auth_result or not auth_result.get("valid"):
                logger.warning(f"Invalid API key for {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid API key",
                        "code": 401,
                        "message": "The provided API key is invalid, expired, or revoked"
                    }
                )
            
            # Attach auth info to request state
            request.state.user_id = auth_result["user_id"]
            request.state.project_id = auth_result["project_id"]
            request.state.role = auth_result["role"]
            request.state.key_id = auth_result["key_id"]
            
            logger.debug(f"Authenticated request: user={auth_result['user_id']}, role={auth_result['role']}, path={path}")
        
        # Continue to next middleware/handler
        response = await call_next(request)
        return response
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from request headers.
        
        Checks:
        1. Authorization: Bearer <key>
        2. x-api-key: <key>
        
        Args:
            request: FastAPI request
        
        Returns:
            API key string or None
        """
        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()  # Remove "Bearer " prefix
        
        # Check x-api-key header
        api_key_header = request.headers.get("x-api-key")
        if api_key_header:
            return api_key_header.strip()
        
        return None

