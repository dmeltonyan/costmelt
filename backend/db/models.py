"""
Cost Melt - Database Models

SQLAlchemy ORM models for database tables.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class RequestLog(Base):
    """
    ORM model for request logs table.
    
    Stores all LLM requests with metadata for analytics.
    """
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False)
    compressed = Column(Boolean, default=False)
    user_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    @classmethod
    async def create(
        cls,
        prompt: str,
        response: str,
        model_used: str,
        tokens_used: int,
        cost: float,
        cache_hit: bool = False,
        compressed: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new request log entry.
        
        Note: This is a placeholder. In production, use async SQLAlchemy session.
        """
        # TODO: Implement actual database insertion
        # This would use an async session manager
        return {
            "id": 1,
            "prompt": prompt,
            "response": response,
            "model_used": model_used,
            "tokens_used": tokens_used,
            "cost": cost,
            "cache_hit": cache_hit,
            "compressed": compressed,
            "user_id": user_id,
            "created_at": datetime.now()
        }


class CacheEntry(Base):
    """
    ORM model for cache entries table.
    
    Stores cached prompt-response pairs with vector embeddings.
    """
    __tablename__ = "cache"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    embedding = Column(Text)  # pgvector type - stored as text representation
    model_used = Column(String(50), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, server_default=func.now())


class User(Base):
    """
    ORM model for users table.
    
    Extends Supabase Auth with additional metadata.
    """
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)  # Supabase Auth UUID
    email = Column(String(255), unique=True, nullable=False)
    plan = Column(String(50), default="free")
    api_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class APIKey(Base):
    """
    ORM model for API keys table.
    
    Stores API keys for authentication.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_used = Column(DateTime, nullable=True)

