"""
Structured logging configuration for the Personal Finance ML Backend.

This module provides JSON-formatted logging with contextual information
and integration with monitoring systems.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON objects with timestamp, level, message,
    and additional context fields.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        # Add any custom fields
        if hasattr(record, "custom_fields"):
            log_data.update(record.custom_fields)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom text formatter for human-readable logs.
    
    Formats log records as readable text with colors for different log levels.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as colored text.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format: [TIMESTAMP] LEVEL - module.function:line - MESSAGE
        log_message = (
            f"{color}[{datetime.utcnow().isoformat()}] "
            f"{record.levelname:<8}{self.RESET} - "
            f"{record.module}.{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message


def setup_logging() -> logging.Logger:
    """
    Setup application logging with appropriate formatter and handlers.
    
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Choose formatter based on settings
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if configured)
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that adds contextual information to log records.
    
    Usage:
        logger = LoggerAdapter(logging.getLogger(__name__), {"user_id": 123})
        logger.info("User action", extra={"action": "login"})
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the logging call to add contextual information.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (msg, kwargs) with added context
        """
        # Add context from adapter
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        kwargs["extra"].update(self.extra)
        
        return msg, kwargs


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **kwargs
):
    """
    Log performance metrics for an operation.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        success: Whether operation succeeded
        **kwargs: Additional context fields
    """
    extra = {
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
        "custom_fields": kwargs
    }
    
    if success:
        logger.info(f"{operation} completed successfully", extra=extra)
    else:
        logger.warning(f"{operation} failed", extra=extra)


def log_model_training(
    logger: logging.Logger,
    user_id: int,
    model_type: str,
    data_points: int,
    duration_ms: float,
    metrics: Dict[str, float]
):
    """
    Log model training metrics.
    
    Args:
        logger: Logger instance
        user_id: User ID
        model_type: Type of model trained
        data_points: Number of data points used
        duration_ms: Training duration in milliseconds
        metrics: Model performance metrics (e.g., R², MAE)
    """
    extra = {
        "user_id": user_id,
        "model_type": model_type,
        "data_points": data_points,
        "duration_ms": duration_ms,
        "custom_fields": metrics
    }
    
    logger.info(f"Model trained: {model_type}", extra=extra)


def log_prediction(
    logger: logging.Logger,
    user_id: int,
    model_type: str,
    prediction_type: str,
    duration_ms: float,
    cached: bool = False
):
    """
    Log prediction requests.
    
    Args:
        logger: Logger instance
        user_id: User ID
        model_type: Type of model used
        prediction_type: Type of prediction made
        duration_ms: Prediction duration in milliseconds
        cached: Whether result was served from cache
    """
    extra = {
        "user_id": user_id,
        "model_type": model_type,
        "prediction_type": prediction_type,
        "duration_ms": duration_ms,
        "cached": cached
    }
    
    logger.info(f"Prediction: {prediction_type}", extra=extra)


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log an error with context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context about the error
    """
    extra = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "custom_fields": context or {}
    }
    
    logger.error(f"Error: {str(error)}", exc_info=True, extra=extra)


# Initialize logging on module import
setup_logging()
