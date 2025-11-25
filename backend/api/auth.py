"""
Cost Melt - Authentication API Endpoints

Endpoints for API key management: create, list, revoke, rotate.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, Field
import logging

from backend.security.api_key_manager import APIKeyManager
from backend.security.rbac import require_role, get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models
class CreateAPIKeyRequest(BaseModel):
    """Request model for creating API key"""
    project_id: str = Field(..., description="Project identifier")
    role: str = Field(default="write", description="Access role: admin, write, or read")
    expires_at: Optional[str] = Field(None, description="ISO format expiration date (optional)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class CreateAPIKeyResponse(BaseModel):
    """Response model for API key creation"""
    api_key: str = Field(..., description="Plaintext API key (shown once only)")
    prefix: str = Field(..., description="Key prefix for identification")
    key_id: str = Field(..., description="Database key ID")
    user_id: str = Field(..., description="User ID")
    project_id: str = Field(..., description="Project ID")
    role: str = Field(..., description="Access role")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")


class APIKeyInfo(BaseModel):
    """API key information (without plaintext)"""
    id: str
    prefix: str
    role: str
    status: str
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]
    project_id: str
    metadata: Dict[str, Any]


class ListAPIKeysResponse(BaseModel):
    """Response model for listing API keys"""
    keys: List[APIKeyInfo]
    total: int


class RotateAPIKeyResponse(BaseModel):
    """Response model for API key rotation"""
    api_key: str = Field(..., description="New plaintext API key")
    prefix: str
    key_id: str
    old_key_id: str
    created_at: str


class MeResponse(BaseModel):
    """Response model for /auth/me endpoint"""
    user_id: str
    project_id: str
    role: str
    rate_limit_remaining: int
    rate_limit_limit: int
    rate_limit_reset_at: int


def get_api_key_manager(request: Request) -> APIKeyManager:
    """Dependency to get API key manager from app state"""
    return request.app.state.api_key_manager


def get_rate_limit_middleware(request: Request):
    """Dependency to get rate limit middleware from app state"""
    return request.app.state.rate_limit_middleware


@router.post("/api-keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
@require_role("admin")
async def create_api_key(
    request: Request,
    body: CreateAPIKeyRequest,
    api_key_manager: APIKeyManager = Depends(get_api_key_manager)
):
    """
    Create a new API key.
    
    Requires admin role.
    
    The plaintext API key is returned ONCE and should be stored securely.
    It cannot be retrieved again after creation.
    """
    user_id = get_user_id(request)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found"
        )
    
    # Parse expiration date if provided
    expires_at = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid expires_at format. Use ISO 8601 format."
            )
    
    # Validate role
    if body.role not in ["admin", "write", "read"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be admin, write, or read"
        )
    
    try:
        result = await api_key_manager.create_api_key(
            user_id=user_id,
            project_id=body.project_id,
            role=body.role,
            expires_at=expires_at,
            metadata=body.metadata
        )
        
        logger.info(f"Created API key for user {user_id}, project {body.project_id}, role {body.role}")
        
        return CreateAPIKeyResponse(**result)
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/api-keys", response_model=ListAPIKeysResponse)
@require_role("admin")
async def list_api_keys(
    request: Request,
    project_id: Optional[str] = None,
    api_key_manager: APIKeyManager = Depends(get_api_key_manager)
):
    """
    List all API keys for the current user.
    
    Requires admin role.
    
    Plaintext keys are never returned - only metadata.
    """
    user_id = get_user_id(request)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found"
        )
    
    try:
        keys = await api_key_manager.list_api_keys(user_id, project_id)
        
        # Convert to APIKeyInfo models
        key_infos = [
            APIKeyInfo(
                id=key["id"],
                prefix=key["prefix"],
                role=key["role"],
                status=key["status"],
                created_at=key["created_at"],
                last_used_at=key.get("last_used_at"),
                expires_at=key.get("expires_at"),
                project_id=key["project_id"],
                metadata=key.get("metadata", {})
            )
            for key in keys
        ]
        
        return ListAPIKeysResponse(keys=key_infos, total=len(key_infos))
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role("admin")
async def revoke_api_key(
    request: Request,
    key_id: str,
    api_key_manager: APIKeyManager = Depends(get_api_key_manager)
):
    """
    Revoke an API key.
    
    Requires admin role.
    
    Revoked keys cannot be used for authentication.
    """
    user_id = get_user_id(request)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found"
        )
    
    try:
        success = await api_key_manager.revoke_api_key(key_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or doesn't belong to you"
            )
        
        logger.info(f"Revoked API key {key_id} for user {user_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.post("/api-keys/{key_id}/rotate", response_model=RotateAPIKeyResponse)
@require_role("admin")
async def rotate_api_key(
    request: Request,
    key_id: str,
    api_key_manager: APIKeyManager = Depends(get_api_key_manager)
):
    """
    Rotate an API key: revoke old key and create new one.
    
    Requires admin role.
    
    Returns the new plaintext API key (shown once).
    """
    user_id = get_user_id(request)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found"
        )
    
    try:
        result = await api_key_manager.rotate_api_key(key_id, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or doesn't belong to you"
            )
        
        logger.info(f"Rotated API key {key_id} for user {user_id}")
        
        return RotateAPIKeyResponse(
            api_key=result["api_key"],
            prefix=result["prefix"],
            key_id=result["key_id"],
            old_key_id=key_id,
            created_at=result["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate API key: {str(e)}"
        )


@router.get("/me", response_model=MeResponse)
async def get_current_user(
    request: Request,
    rate_limit_middleware = Depends(get_rate_limit_middleware)
):
    """
    Get current authenticated user information.
    
    Returns user ID, role, project ID, and rate limit status.
    """
    user_id = getattr(request.state, "user_id", None)
    project_id = getattr(request.state, "project_id", None)
    role = getattr(request.state, "role", None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Get rate limit status
    try:
        rate_limit_status = await rate_limit_middleware.get_rate_limit_status(user_id)
    except Exception as e:
        logger.warning(f"Error getting rate limit status: {e}")
        rate_limit_status = {
            "limit": 60,
            "remaining": 60,
            "reset_at": 0
        }
    
    return MeResponse(
        user_id=user_id,
        project_id=project_id or "",
        role=role or "read",
        rate_limit_remaining=rate_limit_status["remaining"],
        rate_limit_limit=rate_limit_status["limit"],
        rate_limit_reset_at=rate_limit_status["reset_at"]
    )

