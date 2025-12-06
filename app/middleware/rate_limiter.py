"""
Rate limiting middleware using slowapi.

This module provides rate limiting to prevent abuse and ensure fair usage.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_limiter() -> Limiter:
    """
    Create and configure rate limiter.
    
    Returns:
        Configured Limiter instance
    """
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}seconds"],
        enabled=settings.RATE_LIMIT_ENABLED,
        storage_uri=settings.get_redis_url() if settings.CACHE_ENABLED else "memory://",
        strategy="fixed-window"
    )
    
    return limiter


def register_rate_limiter(app):
    """
    Register rate limiter with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting is disabled")
        return
    
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info(
        f"Rate limiting enabled: {settings.RATE_LIMIT_REQUESTS} requests "
        f"per {settings.RATE_LIMIT_PERIOD} seconds"
    )
