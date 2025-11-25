"""
Cost Melt - API Key Manager

Production-ready API key creation, verification, revocation, and rotation.
Uses bcrypt for secure hashing and prefix-based lookup for performance.
"""

import secrets
import bcrypt
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages API key lifecycle: creation, verification, revocation, rotation.
    
    Security features:
    - bcrypt hashing (cost factor 12)
    - Prefix-based lookup for performance
    - Expiration support
    - Role-based access control
    - Usage tracking
    """
    
    def __init__(self, supabase_client):
        """
        Initialize API key manager.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self.bcrypt_rounds = 12  # Production-grade bcrypt cost factor
    
    def generate_api_key(self, length: int = 48) -> str:
        """
        Generate a cryptographically secure API key.
        
        Format: cm_live_<random_base64>
        Total length: ~48 characters
        
        Args:
            length: Length of random bytes (default: 48)
        
        Returns:
            API key string in format: cm_live_<base64>
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(length)
        # Encode to base64url (URL-safe)
        key_suffix = secrets.token_urlsafe(length)[:length]
        # Format: cm_live_<random>
        api_key = f"cm_live_{key_suffix}"
        return api_key
    
    def hash_key(self, api_key: str) -> str:
        """
        Hash API key using bcrypt.
        
        Args:
            api_key: Plaintext API key
        
        Returns:
            bcrypt hash string
        """
        # Encode to bytes for bcrypt
        key_bytes = api_key.encode('utf-8')
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        key_hash = bcrypt.hashpw(key_bytes, salt)
        return key_hash.decode('utf-8')
    
    def verify_hash(self, api_key: str, key_hash: str) -> bool:
        """
        Verify API key against stored hash.
        
        Args:
            api_key: Plaintext API key to verify
            key_hash: Stored bcrypt hash
        
        Returns:
            True if key matches hash, False otherwise
        """
        try:
            key_bytes = api_key.encode('utf-8')
            hash_bytes = key_hash.encode('utf-8')
            return bcrypt.checkpw(key_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Error verifying key hash: {e}")
            return False
    
    def extract_prefix(self, api_key: str) -> str:
        """
        Extract prefix (first 8 characters after 'cm_live_') for lookup.
        
        Args:
            api_key: Full API key
        
        Returns:
            Prefix string (8 characters)
        """
        # Format: cm_live_<prefix><rest>
        if api_key.startswith("cm_live_"):
            prefix_part = api_key[8:]  # After "cm_live_"
            return prefix_part[:8]
        # Fallback: use first 8 chars
        return api_key[:8]
    
    async def create_api_key(
        self,
        user_id: str,
        project_id: str,
        role: str = "write",
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            role: Access role (admin, write, read)
            expires_at: Optional expiration datetime
            metadata: Optional metadata dictionary
        
        Returns:
            Dictionary with:
            - api_key: Plaintext key (shown once)
            - prefix: Key prefix
            - key_id: Database ID
            - created_at: Creation timestamp
        
        Raises:
            ValueError: If role is invalid
        """
        if role not in ["admin", "write", "read"]:
            raise ValueError(f"Invalid role: {role}. Must be admin, write, or read")
        
        # Generate new API key
        api_key = self.generate_api_key()
        key_hash = self.hash_key(api_key)
        prefix = self.extract_prefix(api_key)
        
        # Prepare database record
        record = {
            "user_id": user_id,
            "project_id": project_id,
            "key_hash": key_hash,
            "prefix": prefix,
            "role": role,
            "status": "active",
            "metadata": metadata or {}
        }
        
        if expires_at:
            record["expires_at"] = expires_at.isoformat()
        
        # Insert into database
        try:
            result = self.supabase.table("api_keys").insert(record).execute()
            if not result.data:
                raise Exception("Failed to create API key")
            
            key_record = result.data[0]
            
            logger.info(f"Created API key for user {user_id}, project {project_id}, role {role}")
            
            return {
                "api_key": api_key,  # Plaintext - shown once only
                "prefix": prefix,
                "key_id": key_record["id"],
                "user_id": user_id,
                "project_id": project_id,
                "role": role,
                "created_at": key_record["created_at"],
                "expires_at": key_record.get("expires_at")
            }
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            raise
    
    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an API key and return user information.
        
        Args:
            api_key: Plaintext API key to verify
        
        Returns:
            Dictionary with validation result:
            - valid: bool
            - user_id: str
            - project_id: str
            - role: str
            - key_id: str
        
            Returns None if key is invalid
        """
        # Validate format
        if not api_key or not api_key.startswith("cm_live_"):
            logger.warning("Invalid API key format")
            return None
        
        # Extract prefix for lookup
        prefix = self.extract_prefix(api_key)
        
        # Query database for keys with matching prefix
        try:
            result = self.supabase.table("api_keys").select("*").eq("prefix", prefix).eq("status", "active").execute()
            
            if not result.data:
                logger.warning(f"No active keys found with prefix {prefix}")
                return None
            
            # Check expiration
            now = datetime.now(timezone.utc)
            
            # Try each key with matching prefix (rare collision, but possible)
            for key_record in result.data:
                # Check expiration
                if key_record.get("expires_at"):
                    expires_at = datetime.fromisoformat(key_record["expires_at"].replace("Z", "+00:00"))
                    if expires_at < now:
                        logger.warning(f"API key {key_record['id']} has expired")
                        continue
                
                # Verify hash
                stored_hash = key_record["key_hash"]
                if self.verify_hash(api_key, stored_hash):
                    # Key matches! Update last_used_at
                    key_id = key_record["id"]
                    try:
                        self.supabase.table("api_keys").update({
                            "last_used_at": now.isoformat()
                        }).eq("id", key_id).execute()
                    except Exception as e:
                        logger.warning(f"Failed to update last_used_at: {e}")
                    
                    logger.info(f"Verified API key for user {key_record['user_id']}")
                    
                    return {
                        "valid": True,
                        "user_id": key_record["user_id"],
                        "project_id": key_record["project_id"],
                        "role": key_record["role"],
                        "key_id": key_id
                    }
            
            # No matching hash found
            logger.warning(f"API key hash verification failed for prefix {prefix}")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return None
    
    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """
        Revoke an API key (soft delete).
        
        Args:
            key_id: API key UUID
            user_id: User ID (for authorization check)
        
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            # Verify key belongs to user
            result = self.supabase.table("api_keys").select("*").eq("id", key_id).eq("user_id", user_id).execute()
            
            if not result.data:
                logger.warning(f"API key {key_id} not found or doesn't belong to user {user_id}")
                return False
            
            # Update status to revoked
            self.supabase.table("api_keys").update({
                "status": "revoked"
            }).eq("id", key_id).execute()
            
            logger.info(f"Revoked API key {key_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False
    
    async def list_api_keys(self, user_id: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all API keys for a user.
        
        Args:
            user_id: User identifier
            project_id: Optional project filter
        
        Returns:
            List of API key records (without plaintext keys)
        """
        try:
            query = self.supabase.table("api_keys").select("*").eq("user_id", user_id)
            
            if project_id:
                query = query.eq("project_id", project_id)
            
            result = query.order("created_at", desc=True).execute()
            
            # Remove sensitive data
            keys = []
            for key in result.data:
                keys.append({
                    "id": key["id"],
                    "prefix": key["prefix"],
                    "role": key["role"],
                    "status": key["status"],
                    "created_at": key["created_at"],
                    "last_used_at": key.get("last_used_at"),
                    "expires_at": key.get("expires_at"),
                    "project_id": key["project_id"],
                    "metadata": key.get("metadata", {})
                })
            
            return keys
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    async def rotate_api_key(self, key_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Rotate an API key: revoke old, create new.
        
        Args:
            key_id: Old API key UUID
            user_id: User ID (for authorization)
        
        Returns:
            New API key information (same format as create_api_key)
            Returns None if rotation fails
        """
        try:
            # Get old key info
            result = self.supabase.table("api_keys").select("*").eq("id", key_id).eq("user_id", user_id).execute()
            
            if not result.data:
                logger.warning(f"API key {key_id} not found for rotation")
                return None
            
            old_key = result.data[0]
            
            # Revoke old key
            await self.revoke_api_key(key_id, user_id)
            
            # Create new key with same parameters
            expires_at = None
            if old_key.get("expires_at"):
                expires_at = datetime.fromisoformat(old_key["expires_at"].replace("Z", "+00:00"))
            
            new_key = await self.create_api_key(
                user_id=old_key["user_id"],
                project_id=old_key["project_id"],
                role=old_key["role"],
                expires_at=expires_at,
                metadata=old_key.get("metadata", {})
            )
            
            logger.info(f"Rotated API key {key_id} for user {user_id}")
            return new_key
            
        except Exception as e:
            logger.error(f"Error rotating API key: {e}")
            return None

