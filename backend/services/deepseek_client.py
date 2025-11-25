"""
Cost Melt - DeepSeek Client

Unified client for DeepSeek API calls.
"""

from typing import Dict, Any, Optional
import openai
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class DeepSeekClient:
    """
    Client for DeepSeek API interactions.
    
    DeepSeek uses OpenAI-compatible API.
    """
    
    def __init__(self):
        """Initialize DeepSeek client"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = "https://api.deepseek.com"
        
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not set")
            self.client = None
        else:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Complete a chat request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (deepseek-chat)
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with 'text' and 'tokens_used'
        """
        if not self.client:
            raise Exception("DeepSeek client not initialized (missing API key)")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
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
            logger.error(f"DeepSeek API error: {e}", exc_info=True)
            raise

