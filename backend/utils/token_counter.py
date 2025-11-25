"""
Cost Melt - Token Counter

Utility for counting tokens in text using tiktoken.
"""

from typing import Optional
import tiktoken
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TokenCounter:
    """
    Token counter using tiktoken library.
    
    Supports multiple encoding models.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize token counter.
        
        Args:
            model: Model to use for encoding (determines tokenizer)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except Exception:
            # Fallback to cl100k_base (GPT-4, GPT-3.5)
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.warning(f"Using fallback encoding for model: {model}")
    
    def count(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}", exc_info=True)
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def count_messages(
        self,
        messages: list,
        system_prompt: Optional[str] = None
    ) -> int:
        """
        Count tokens in a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
        
        Returns:
            Total token count
        """
        total = 0
        
        if system_prompt:
            total += self.count(system_prompt)
        
        for msg in messages:
            # Add tokens for role and content
            total += self.count(msg.get("role", ""))
            total += self.count(msg.get("content", ""))
            # Add overhead for message formatting (approximate)
            total += 4
        
        return total

