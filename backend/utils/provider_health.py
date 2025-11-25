"""
Cost Melt - Provider Health Checker

Monitors health status of LLM providers and models.
"""

from typing import Dict, Optional
import time
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProviderHealth:
    """
    Health checker for LLM providers.
    
    Tracks provider availability and health status.
    """
    
    def __init__(self):
        """Initialize provider health checker"""
        # Health status cache: provider -> (is_healthy, last_check_time)
        self._health_cache: Dict[str, tuple[bool, float]] = {}
        self._cache_ttl = 60  # Cache health status for 60 seconds
    
    def is_healthy(self, provider: str) -> bool:
        """
        Check if a provider is healthy.
        
        Args:
            provider: Provider name (e.g., "openai", "anthropic", "groq", "deepseek")
        
        Returns:
            True if provider is healthy, False otherwise
        """
        # Check cache first
        if provider in self._health_cache:
            is_healthy, last_check = self._health_cache[provider]
            if time.time() - last_check < self._cache_ttl:
                return is_healthy
        
        # Default: assume healthy (can be enhanced with actual health checks)
        # In production, this could ping the provider's health endpoint
        is_healthy = True
        
        # Update cache
        self._health_cache[provider] = (is_healthy, time.time())
        
        return is_healthy
    
    def mark_unhealthy(self, provider: str):
        """Mark a provider as unhealthy"""
        self._health_cache[provider] = (False, time.time())
        logger.warning(f"Marked provider {provider} as unhealthy")
    
    def mark_healthy(self, provider: str):
        """Mark a provider as healthy"""
        self._health_cache[provider] = (True, time.time())
        logger.info(f"Marked provider {provider} as healthy")
    
    def get_provider_for_model(self, model: str) -> Optional[str]:
        """
        Get provider name for a model.
        
        Args:
            model: Model name (e.g., "gpt-4o", "claude-3-haiku")
        
        Returns:
            Provider name or None
        """
        provider_map = {
            "gpt-4o": "openai",
            "gpt-4o-mini": "openai",
            "claude-3-5-sonnet": "anthropic",
            "claude-3-haiku": "anthropic",
            "llama3-70b-groq": "groq",
            "llama-3": "groq",
            "deepseek-chat": "deepseek"
        }
        
        return provider_map.get(model)

