"""
Cost Melt - Security Module

Authentication, authorization, and security utilities.
"""

from security.api_key_manager import APIKeyManager
from security.rbac import (
    require_role,
    require_any_role,
    is_admin,
    is_write_or_admin,
    get_user_id,
    get_project_id,
)

__all__ = [
    "APIKeyManager",
    "require_role",
    "require_any_role",
    "is_admin",
    "is_write_or_admin",
    "get_user_id",
    "get_project_id",
]

