"""
Cost Melt - Logger Utility

Centralized logging configuration.
"""

import logging
import sys
from typing import Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Setup a logger with consistent configuration.
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level (defaults to INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.INFO)
    
    return logger

