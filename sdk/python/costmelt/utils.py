"""
Cost Melt Python SDK - Utility Functions

Helper functions for retries, backoff, and JSON handling.
"""

import time
import random
from typing import Callable, TypeVar, Any
from functools import wraps

T = TypeVar('T')


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Callable:
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to delays
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        
                        # Add jitter if enabled
                        if jitter:
                            delay = delay * (0.5 + random.random() * 0.5)
                        
                        time.sleep(delay)
                    else:
                        # Last attempt failed, raise the exception
                        raise last_exception
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def parse_json_response(response_data: dict) -> dict:
    """
    Parse and validate JSON response.
    
    Args:
        response_data: Raw response dictionary
    
    Returns:
        Parsed response dictionary
    
    Raises:
        ValueError: If response is invalid
    """
    if not isinstance(response_data, dict):
        raise ValueError("Response must be a dictionary")
    
    return response_data


def is_retryable_error(status_code: int) -> bool:
    """
    Check if an HTTP status code indicates a retryable error.
    
    Args:
        status_code: HTTP status code
    
    Returns:
        True if error is retryable, False otherwise
    """
    # Retry on 5xx errors, 429 (rate limit), and 504 (timeout)
    return status_code >= 500 or status_code == 429 or status_code == 504


def calculate_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate backoff delay for retry attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter
    delay = delay * (0.5 + random.random() * 0.5)
    return delay

