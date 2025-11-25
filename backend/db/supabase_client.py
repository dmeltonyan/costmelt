"""
Cost Melt - Supabase Client

Client for interacting with Supabase PostgreSQL database.
Handles vector embeddings, cache storage, and request logging.
"""

from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class SupabaseClient:
    """
    Supabase client for database operations.
    
    Handles:
    - Request logging
    - Cache storage and retrieval
    - User management
    - API key management
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not set")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(url, key)
            logger.info("Connected to Supabase")
    
    async def insert_request_log(
        self,
        prompt: str,
        response: str,
        model_used: str,
        tokens_used: int,
        cost: float,
        cache_hit: bool,
        compressed: bool,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert a request log entry.
        
        Args:
            prompt: Original prompt
            response: LLM response
            model_used: Model that generated response
            tokens_used: Number of tokens used
            cost: Cost of the request
            cache_hit: Whether cache was hit
            compressed: Whether prompt was compressed
            user_id: Optional user ID
        
        Returns:
            Inserted record
        """
        if not self.client:
            logger.warning("Supabase not available, skipping log")
            return {}
        
        try:
            data = {
                "prompt": prompt,
                "response": response,
                "model_used": model_used,
                "tokens_used": tokens_used,
                "cost": cost,
                "cache_hit": cache_hit,
                "compressed": compressed,
                "user_id": user_id
            }
            
            result = self.client.table("requests").insert(data).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting request log: {e}", exc_info=True)
            return {}
    
    async def insert_cache_entry(
        self,
        prompt: str,
        response: str,
        embedding: List[float],
        model_used: str,
        tokens_used: int,
        cost: float
    ) -> Dict[str, Any]:
        """
        Insert a cache entry with embedding.
        
        Args:
            prompt: Original prompt
            response: Cached response
            embedding: Vector embedding of the prompt
            model_used: Model that generated response
            tokens_used: Number of tokens used
            cost: Cost of the original request
        
        Returns:
            Inserted record
        """
        if not self.client:
            logger.warning("Supabase not available, skipping cache storage")
            return {}
        
        try:
            data = {
                "prompt": prompt,
                "response": response,
                "embedding": embedding,  # pgvector will handle this
                "model_used": model_used,
                "tokens_used": tokens_used,
                "cost": cost
            }
            
            result = self.client.table("cache").insert(data).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting cache entry: {e}", exc_info=True)
            return {}
    
    async def search_similar_embeddings(
        self,
        embedding: List[float],
        threshold: float = 0.92,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity threshold
            limit: Maximum number of results
        
        Returns:
            List of matching cache entries with similarity scores
        """
        if not self.client:
            logger.warning("Supabase not available, returning empty results")
            return []
        
        try:
            # Use Supabase RPC for vector similarity search
            # This requires a custom function in Supabase
            result = self.client.rpc(
                "search_similar_cache",
                {
                    "query_embedding": embedding,
                    "similarity_threshold": threshold,
                    "match_limit": limit
                }
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error searching embeddings: {e}", exc_info=True)
            # Fallback: return empty if RPC not available
            return []
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with user statistics
        """
        if not self.client:
            return {}
        
        try:
            # Get request count, total cost, cache hit rate, etc.
            result = self.client.table("requests").select("*").eq("user_id", user_id).execute()
            
            requests = result.data if result.data else []
            total_cost = sum(r.get("cost", 0) for r in requests)
            cache_hits = sum(1 for r in requests if r.get("cache_hit", False))
            cache_hit_rate = cache_hits / len(requests) if requests else 0
            
            return {
                "total_requests": len(requests),
                "total_cost": total_cost,
                "cache_hit_rate": cache_hit_rate,
                "cache_hits": cache_hits
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            return {}

