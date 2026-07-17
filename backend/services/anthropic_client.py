"""
Cost Melt - Anthropic Client

Unified client for Anthropic Claude API calls.
"""

import asyncio
from typing import Dict, Any, Optional
import anthropic
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class AnthropicClient:
    """
    Client for Anthropic Claude API interactions.
    
    Supports:
    - Claude 3.5 Sonnet
    - Claude 3 Haiku
    """
    
    def __init__(self):
        """Initialize Anthropic client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Complete a chat request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (claude-3-5-sonnet-20241022, claude-3-haiku-20240307)
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with 'text' and 'tokens_used'
        """
        if not self.client:
            raise Exception("Anthropic client not initialized (missing API key)")
        
        try:
            # Map model names
            model_map = {
                "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
                "claude-3-haiku": "claude-3-haiku-20240307"
            }
            actual_model = model_map.get(model, model)
            
            # anthropic.Anthropic is a synchronous client; offload to a
            # thread so this call doesn't block the event loop (see
            # openai_client.py for the full rationale).
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=actual_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else None,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            text = response.content[0].text
            # Anthropic doesn't always return input tokens, estimate
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return {
                "text": text,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            raise

