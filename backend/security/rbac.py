"""
Cost Melt - Role-Based Access Control (RBAC)

Decorators and helpers for enforcing role-based permissions.
"""

from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, Request, status
import logging

logger = logging.getLogger(__name__)


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "read": 1,
    "write": 2,
    "admin": 3
}


def require_role(required_role: str):
    """
    Decorator to require a specific role or higher.
    
    Role hierarchy:
    - read: Can only view metrics (GET /dashboard/*)
    - write: Can call /v1/route and view metrics
    - admin: Full access including API key management
    
    Args:
        required_role: Minimum required role (read, write, or admin)
    
    Usage:
        @router.get("/dashboard/stats")
        @require_role("read")
        async def get_stats():
            ...
        
        @router.post("/auth/api-keys")
        @require_role("admin")
        async def create_api_key():
            ...
    """
    if required_role not in ROLE_HIERARCHY:
        raise ValueError(f"Invalid role: {required_role}. Must be read, write, or admin")
    
    required_level = ROLE_HIERARCHY[required_role]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get role from request state (set by auth middleware)
            user_role = getattr(request.state, "role", None)
            
            if not user_role:
                logger.warning("Role not found in request state - auth middleware may not be applied")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user role meets requirement
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            
            if user_level < required_level:
                logger.warning(f"Access denied: user role {user_role} < required {required_role}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}, your role: {user_role}"
                )
            
            # Role check passed, proceed
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(roles: List[str]):
    """
    Decorator to require any one of the specified roles.
    
    Args:
        roles: List of acceptable roles
    
    Usage:
        @router.get("/some-endpoint")
        @require_any_role(["write", "admin"])
        async def some_endpoint():
            ...
    """
    if not roles:
        raise ValueError("At least one role must be specified")
    
    for role in roles:
        if role not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {role}. Must be read, write, or admin")
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = getattr(request.state, "role", None)
            
            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if user_role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required one of: {roles}, your role: {user_role}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def is_admin(request: Request) -> bool:
    """
    Check if the current user has admin role.
    
    Args:
        request: FastAPI request object
    
    Returns:
        True if user is admin, False otherwise
    """
    role = getattr(request.state, "role", None)
    return role == "admin"


def is_write_or_admin(request: Request) -> bool:
    """
    Check if the current user has write or admin role.
    
    Args:
        request: FastAPI request object
    
    Returns:
        True if user is write or admin, False otherwise
    """
    role = getattr(request.state, "role", None)
    return role in ["write", "admin"]


def get_user_id(request: Request) -> Optional[str]:
    """
    Get user ID from request state.
    
    Args:
        request: FastAPI request object
    
    Returns:
        User ID string or None
    """
    return getattr(request.state, "user_id", None)


def get_project_id(request: Request) -> Optional[str]:
    """
    Get project ID from request state.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Project ID string or None
    """
    return getattr(request.state, "project_id", None)

