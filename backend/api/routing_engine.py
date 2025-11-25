"""
Cost Melt - Production-Grade Routing Engine

Intelligently routes requests to the most cost-effective LLM model based on:
- Prompt complexity
- Cost efficiency
- Semantic type
- Required reasoning depth
- Prompt length
- Overkill detection
- Provider availability
- Fallback support
"""

import re
import time
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import setup_logger
from utils.provider_health import ProviderHealth

logger = setup_logger(__name__)


# Model cost per 1K tokens (input + output average)
MODEL_COSTS = {
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "claude-3-haiku": 0.00025,
    "claude-3-5-sonnet": 0.003,
    "llama3-70b-groq": 0.00006,
    "llama-3": 0.00006,  # Alias
    "deepseek-chat": 0.00002
}

# Model to provider mapping
MODEL_TO_PROVIDER = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "claude-3-haiku": "anthropic",
    "claude-3-5-sonnet": "anthropic",
    "llama3-70b-groq": "groq",
    "llama-3": "groq",
    "deepseek-chat": "deepseek"
}

# Routing rules by complexity
ROUTING_RULES = {
    0: [  # Simple prompts
        "llama3-70b-groq",
        "deepseek-chat",
        "gpt-4o-mini"
    ],
    1: [  # Medium prompts
        "claude-3-haiku",
        "gpt-4o-mini",
        "deepseek-chat"
    ],
    2: [  # Complex prompts
        "gpt-4o",
        "claude-3-5-sonnet"
    ]
}


class RoutingEngine:
    """
    Production-grade routing engine that selects optimal LLM model.
    
    Pipeline:
    1. Normalize prompt
    2. Compute embeddings
    3. Get complexity score
    4. Apply routing rules
    5. Provider health check
    6. Cost-aware selection
    7. Build routing decision
    """
    
    def __init__(
        self,
        embedding_client=None,
        overkill_detector=None,
        health_checker: Optional[ProviderHealth] = None
    ):
        """
        Initialize routing engine.
        
        Args:
            embedding_client: Client for computing embeddings (OpenAIClient)
            overkill_detector: OverkillDetector instance
            health_checker: ProviderHealth instance
        """
        # Lazy imports to avoid circular dependencies
        if embedding_client is None:
            from services.openai_client import OpenAIClient
            self.embedding_client = OpenAIClient()
        else:
            self.embedding_client = embedding_client
        
        if overkill_detector is None:
            from api.overkill_detector import OverkillDetector
            self.overkill_detector = OverkillDetector()
        else:
            self.overkill_detector = overkill_detector
        
        if health_checker is None:
            self.health_checker = ProviderHealth()
        else:
            self.health_checker = health_checker
        
        # Cache for embeddings (optional optimization)
        self._embedding_cache: Dict[str, List[float]] = {}
    
    async def route(self, prompt: str, user_id: str) -> Dict[str, Any]:
        """
        Route request to optimal model based on comprehensive analysis.
        
        Args:
            prompt: User prompt text
            user_id: User identifier for logging/analytics
        
        Returns:
            Dict with:
            {
                "model": "gpt-4o-mini",
                "complexity": 1,
                "reason": "medium complexity with code patterns",
                "provider": "openai"
            }
        """
        routing_start = time.time()
        
        try:
            # Step 1: Normalize prompt
            normalized_prompt = self._normalize_prompt(prompt)
            prompt_length = len(normalized_prompt)
            
            logger.info(f"Routing request for user {user_id}, prompt length: {prompt_length}")
            
            # Step 2: Compute embeddings (for cache and semantic analysis)
            embedding_start = time.time()
            embedding = await self._get_embedding(normalized_prompt)
            embedding_time = (time.time() - embedding_start) * 1000
            
            # Step 3: Get complexity score
            complexity = await self._get_complexity_score(normalized_prompt)
            
            logger.info(f"Complexity score: {complexity}, embedding time: {embedding_time:.2f}ms")
            
            # Step 4: Apply routing rules
            candidate_models = self._select_model(complexity)
            
            if not candidate_models:
                logger.error(f"No candidate models for complexity {complexity}")
                return self._build_error_response(complexity, "no_candidates_for_complexity")
            
            # Step 5: Provider health check and filter
            healthy_models = self._filter_healthy_models(candidate_models)
            
            if not healthy_models:
                logger.warning("No healthy providers available, attempting fallback")
                # Try fallback: use any available model from any complexity level
                fallback_models = self._fallback()
                if not fallback_models:
                    return self._build_error_response(complexity, "no_healthy_providers_available")
                healthy_models = fallback_models
            
            # Step 6: Cost-aware selection
            selected_model = self._cheapest(healthy_models)
            
            # Step 7: Build response
            provider = MODEL_TO_PROVIDER.get(selected_model, "unknown")
            reason = self._build_reason(complexity, normalized_prompt, selected_model)
            
            routing_time = (time.time() - routing_start) * 1000
            
            logger.info(
                f"Routing decision: model={selected_model}, complexity={complexity}, "
                f"reason={reason}, provider={provider}, time={routing_time:.2f}ms"
            )
            
            return self._build_response(
                model=selected_model,
                complexity=complexity,
                reason=reason,
                provider=provider
            )
            
        except Exception as e:
            logger.error(f"Error in routing engine: {e}", exc_info=True)
            # Return error response with best-effort complexity
            try:
                complexity = await self._get_complexity_score(prompt)
            except:
                complexity = 1  # Default to medium
            
            return self._build_error_response(complexity, f"routing_error: {str(e)}")
    
    def _normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt: trim, clean whitespace, detect content type.
        
        Args:
            prompt: Raw prompt text
        
        Returns:
            Normalized prompt string
        """
        # Trim whitespace
        normalized = prompt.strip()
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Detect content type (for future semantic routing)
        # This could be used for specialized routing (e.g., code -> code-specialized models)
        # For now, we just normalize
        
        return normalized
    
    async def _get_embedding(self, prompt: str) -> List[float]:
        """
        Get embedding vector for prompt.
        
        Uses OpenAI text-embedding-3-small.
        Caches embeddings to avoid redundant API calls.
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Embedding vector (list of floats)
        """
        # Check cache first
        if prompt in self._embedding_cache:
            return self._embedding_cache[prompt]
        
        try:
            # Get embedding from OpenAI
            result = await self.embedding_client.get_embedding(
                text=prompt,
                model="text-embedding-3-small"
            )
            
            embedding = result["embedding"]
            
            # Cache embedding (limit cache size to prevent memory issues)
            if len(self._embedding_cache) < 1000:
                self._embedding_cache[prompt] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}", exc_info=True)
            # Return empty embedding on error (routing can still proceed)
            return []
    
    async def _get_complexity_score(self, prompt: str) -> int:
        """
        Get complexity score from OverkillDetector.
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Complexity score: 0 (simple), 1 (medium), or 2 (complex)
        """
        try:
            # Use OverkillDetector's detect_complexity method
            # If it has a score() method, use that instead
            if hasattr(self.overkill_detector, 'score'):
                complexity = await self.overkill_detector.score(prompt)
            else:
                complexity = await self.overkill_detector.detect_complexity(prompt)
            
            # Ensure complexity is in valid range
            if complexity not in [0, 1, 2]:
                logger.warning(f"Invalid complexity score {complexity}, defaulting to 1")
                complexity = 1
            
            return complexity
            
        except Exception as e:
            logger.error(f"Error getting complexity score: {e}", exc_info=True)
            # Fallback: use heuristic
            return self._heuristic_complexity(prompt)
    
    def _heuristic_complexity(self, prompt: str) -> int:
        """
        Fallback heuristic complexity detection.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Complexity score (0, 1, or 2)
        """
        prompt_lower = prompt.lower()
        
        # Complex indicators
        complex_patterns = [
            r'\b(analyze|compare|evaluate|synthesize|create|design|architecture|algorithm|proof|theorem)\b',
            r'\b(chain.of.thought|reasoning|step.by.step|multi.step)\b',
            r'\{.*\}|\[.*\]|\(.*\)',  # Code-like structures
            r'SELECT.*FROM|CREATE TABLE|INSERT INTO',  # SQL
        ]
        
        # Medium indicators
        medium_patterns = [
            r'\b(explain|describe|summarize|list|how|what|why)\b',
            r'\b(code|function|class|method|variable)\b',
        ]
        
        # Check for complex patterns
        for pattern in complex_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return 2
        
        # Check for medium patterns
        for pattern in medium_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return 1
        
        # Default to simple
        return 0
    
    def _select_model(self, complexity: int) -> List[str]:
        """
        Select candidate models based on complexity.
        
        Args:
            complexity: Complexity score (0, 1, or 2)
        
        Returns:
            List of candidate model names (ordered by preference)
        """
        return ROUTING_RULES.get(complexity, ROUTING_RULES[1])
    
    def _filter_healthy_models(self, models: List[str]) -> List[str]:
        """
        Filter models to only include those with healthy providers.
        
        Args:
            models: List of candidate model names
        
        Returns:
            List of healthy model names
        """
        healthy = []
        
        for model in models:
            provider = MODEL_TO_PROVIDER.get(model)
            if provider and self.health_checker.is_healthy(provider):
                healthy.append(model)
            elif not provider:
                # If provider mapping not found, assume healthy (for unknown models)
                logger.warning(f"No provider mapping for model {model}, assuming healthy")
                healthy.append(model)
        
        return healthy
    
    def _fallback(self) -> List[str]:
        """
        Get fallback models when primary routing fails.
        
        Returns:
            List of fallback model names (all available models, ordered by cost)
        """
        # Get all models, ordered by cost (cheapest first)
        all_models = [
            "deepseek-chat",
            "llama3-70b-groq",
            "gpt-4o-mini",
            "claude-3-haiku",
            "claude-3-5-sonnet",
            "gpt-4o"
        ]
        
        # Filter to healthy providers
        return self._filter_healthy_models(all_models)
    
    def _cheapest(self, models: List[str]) -> str:
        """
        Select cheapest model from list.
        
        Args:
            models: List of model names
        
        Returns:
            Cheapest model name
        """
        if not models:
            raise ValueError("Empty model list")
        
        # Sort by cost
        sorted_models = sorted(
            models,
            key=lambda m: MODEL_COSTS.get(m, float('inf'))
        )
        
        return sorted_models[0]
    
    def _build_reason(
        self,
        complexity: int,
        prompt: str,
        model: str
    ) -> str:
        """
        Build human-readable routing reason.
        
        Args:
            complexity: Complexity score
            prompt: Prompt text
            model: Selected model
        
        Returns:
            Reason string
        """
        # Detect prompt characteristics
        prompt_lower = prompt.lower()
        
        has_code = bool(re.search(r'\{|\}|def |class |function|SELECT|CREATE', prompt_lower))
        has_sql = bool(re.search(r'SELECT|INSERT|UPDATE|DELETE|CREATE TABLE', prompt_lower, re.IGNORECASE))
        is_long = len(prompt) > 500
        
        complexity_names = {0: "simple", 1: "medium", 2: "complex"}
        complexity_name = complexity_names.get(complexity, "medium")
        
        reason_parts = [f"{complexity_name} complexity"]
        
        if has_code:
            reason_parts.append("with code patterns")
        if has_sql:
            reason_parts.append("with SQL")
        if is_long:
            reason_parts.append("long prompt")
        
        reason_parts.append(f"→ {model}")
        
        return " ".join(reason_parts)
    
    def _build_response(
        self,
        model: str,
        complexity: int,
        reason: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Build routing decision response.
        
        Args:
            model: Selected model name
            complexity: Complexity score
            reason: Routing reason
            provider: Provider name
        
        Returns:
            Routing decision dict
        """
        return {
            "model": model,
            "complexity": complexity,
            "reason": reason,
            "provider": provider
        }
    
    def _build_error_response(
        self,
        complexity: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Build error response when routing fails.
        
        Args:
            complexity: Complexity score (if available)
            reason: Error reason
        
        Returns:
            Error response dict
        """
        return {
            "model": None,
            "complexity": complexity,
            "reason": reason,
            "provider": None
        }
