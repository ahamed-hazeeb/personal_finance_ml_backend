"""
Global error handler middleware for the Personal Finance ML Backend.

This module provides centralized error handling with user-friendly messages
and proper logging of exceptions.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Union

from app.core.logging import get_logger, log_error
from app.core.config import settings

logger = get_logger(__name__)


class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(AppError):
    """Not found error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)


class InsufficientDataError(AppError):
    """Insufficient data error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


class ModelTrainingError(AppError):
    """Model training error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=500, details=details)


class PredictionError(AppError):
    """Prediction error exception."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=500, details=details)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle application-specific errors.
    
    Args:
        request: FastAPI request object
        exc: Application error exception
        
    Returns:
        JSON response with error details
    """
    log_error(logger, exc, context={
        "endpoint": str(request.url),
        "method": request.method,
        "status_code": exc.status_code
    })
    
    response = {
        "error": {
            "type": type(exc).__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    }
    
    # Add details if available and not in production
    if exc.details and (settings.DEBUG or not settings.is_production()):
        response["error"]["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation error exception
        
    Returns:
        JSON response with validation error details
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error["loc"]])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url}", extra={
        "endpoint": str(request.url),
        "method": request.method,
        "errors": errors
    })
    
    response = {
        "error": {
            "type": "ValidationError",
            "message": "Invalid input data",
            "status_code": 422,
            "details": errors
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSON response with error details
    """
    response = {
        "error": {
            "type": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected errors.
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    log_error(logger, exc, context={
        "endpoint": str(request.url),
        "method": request.method
    })
    
    # In production, hide implementation details
    if settings.is_production():
        message = "An unexpected error occurred. Please try again later."
        details = None
    else:
        message = str(exc)
        details = {
            "traceback": traceback.format_exc()
        }
    
    response = {
        "error": {
            "type": "InternalServerError",
            "message": message,
            "status_code": 500
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(ValidationError, app_error_handler)
    app.add_exception_handler(NotFoundError, app_error_handler)
    app.add_exception_handler(InsufficientDataError, app_error_handler)
    app.add_exception_handler(ModelTrainingError, app_error_handler)
    app.add_exception_handler(PredictionError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, general_error_handler)
