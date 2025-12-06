"""
Authentication middleware for API key-based authentication.

This module provides simple API key authentication for securing endpoints.
For production, consider using JWT tokens or OAuth2.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# API Key header
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # In development mode, skip authentication if DEBUG is True
    if settings.DEBUG and settings.is_development():
        logger.debug("Skipping API key verification in development mode")
        return "dev_key"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={settings.API_KEY_HEADER: "Required"}
        )
    
    # TODO: In production, validate against database of API keys
    # For now, we'll use a simple check against SECRET_KEY
    # This is a placeholder - implement proper API key management
    
    # Example: Check if API key matches expected format
    # In production, you would:
    # 1. Query database for valid API keys
    # 2. Check expiration dates
    # 3. Check rate limits per key
    # 4. Track usage per key
    
    # Placeholder validation
    if api_key != settings.SECRET_KEY:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


def get_current_user_id(api_key: str = Security(verify_api_key)) -> int:
    """
    Extract user ID from API key.
    
    Args:
        api_key: Validated API key
        
    Returns:
        User ID associated with the API key
    """
    # TODO: In production, look up user ID from API key in database
    # For now, return a placeholder
    return 1
