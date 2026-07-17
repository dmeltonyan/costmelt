"""
Cost Melt - OpenAI Client

Unified client for OpenAI API calls (GPT-4o, GPT-4o-mini, embeddings).
"""

import asyncio
from typing import Dict, Any, Optional
import openai
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class OpenAIClient:
    """
    Client for OpenAI API interactions.
    
    Supports:
    - Chat completions (GPT-4o, GPT-4o-mini)
    - Embeddings (text-embedding-3-small)
    """
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set")
        self.client = openai.OpenAI(api_key=api_key) if api_key else None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Complete a chat request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (gpt-4o, gpt-4o-mini)
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with 'text' and 'tokens_used'
        """
        if not self.client:
            raise Exception("OpenAI client not initialized (missing API key)")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # openai.OpenAI is a synchronous client; calling it directly
            # from this async function would block the event loop for the
            # entire request (freezing every other in-flight request on
            # this worker). asyncio.to_thread offloads it to a thread pool.
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
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
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise
    
    async def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """
        Get embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Dict with 'embedding' (list of floats)
        """
        if not self.client:
            raise Exception("OpenAI client not initialized (missing API key)")
        
        try:
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model=model,
                input=text
            )

            embedding = response.data[0].embedding
            
            return {
                "embedding": embedding
            }
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}", exc_info=True)
            raise

