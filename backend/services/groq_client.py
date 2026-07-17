"""
Cost Melt - Groq Client

Unified client for Groq API calls (Llama 3).
"""

import asyncio
from typing import Dict, Any, Optional
from groq import Groq
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class GroqClient:
    """
    Client for Groq API interactions.
    
    Supports:
    - Llama 3 models
    """
    
    def __init__(self):
        """Initialize Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key) if api_key else None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "llama-3-8b-8192",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Complete a chat request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (llama-3-8b-8192, llama-3-70b-8192)
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with 'text' and 'tokens_used'
        """
        if not self.client:
            raise Exception("Groq client not initialized (missing API key)")
        
        try:
            # Map model names
            model_map = {
                "llama-3": "llama-3-8b-8192"
            }
            actual_model = model_map.get(model, model)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # groq.Groq is a synchronous client; offload to a thread so
            # this call doesn't block the event loop (see
            # openai_client.py for the full rationale).
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=actual_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return {
                "text": text,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"Groq API error: {e}", exc_info=True)
            raise

