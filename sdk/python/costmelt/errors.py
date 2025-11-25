"""
Cost Melt Python SDK - Custom Exceptions

Custom exception classes for Cost Melt API errors.
"""


class CostMeltError(Exception):
    """Base exception for all Cost Melt errors"""
    
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(self.message)
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class RouteError(CostMeltError):
    """Error during request routing"""
    pass


class APIConnectionError(CostMeltError):
    """Error connecting to Cost Melt API"""
    pass


class RateLimitError(CostMeltError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message, code=429)
        self.retry_after = retry_after


class ServerError(CostMeltError):
    """Server-side error (5xx)"""
    pass


class TimeoutError(CostMeltError):
    """Request timeout"""
    pass


class ValidationError(CostMeltError):
    """Invalid request parameters"""
    pass

