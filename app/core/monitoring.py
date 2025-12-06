"""
Monitoring and metrics collection for the Personal Finance ML Backend.

This module provides Prometheus metrics integration for tracking:
- API request metrics (count, latency, errors)
- Model performance metrics
- Cache hit rates
- Database connection pool metrics
"""
from typing import Callable
from functools import wraps
import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from fastapi import Response

from app.core.config import settings


# API Metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"]
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)

api_errors_total = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["method", "endpoint", "error_type"]
)

# Model Metrics
model_training_total = Counter(
    "model_training_total",
    "Total number of model training operations",
    ["user_id", "model_type", "status"]
)

model_training_duration_seconds = Histogram(
    "model_training_duration_seconds",
    "Model training duration in seconds",
    ["model_type"]
)

model_prediction_total = Counter(
    "model_prediction_total",
    "Total number of predictions",
    ["user_id", "model_type"]
)

model_prediction_duration_seconds = Histogram(
    "model_prediction_duration_seconds",
    "Model prediction duration in seconds",
    ["model_type"]
)

model_accuracy = Gauge(
    "model_accuracy",
    "Model accuracy (R² score)",
    ["user_id", "model_type"]
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"]
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"]
)

# Database Metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections"
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

db_errors_total = Counter(
    "db_errors_total",
    "Total number of database errors",
    ["error_type"]
)

# System Information
app_info = Info(
    "app",
    "Application information"
)

# Set application info
app_info.info({
    "version": settings.APP_VERSION,
    "environment": settings.ENVIRONMENT,
    "name": settings.APP_NAME
})


def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """
    Track API request metrics.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        duration: Request duration in seconds
    """
    if not settings.ENABLE_METRICS:
        return
    
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()
    
    api_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_error(method: str, endpoint: str, error_type: str):
    """
    Track API errors.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        error_type: Type of error
    """
    if not settings.ENABLE_METRICS:
        return
    
    api_errors_total.labels(
        method=method,
        endpoint=endpoint,
        error_type=error_type
    ).inc()


def track_model_training(user_id: int, model_type: str, duration: float, status: str = "success"):
    """
    Track model training metrics.
    
    Args:
        user_id: User ID
        model_type: Type of model
        duration: Training duration in seconds
        status: Training status (success/failure)
    """
    if not settings.ENABLE_METRICS:
        return
    
    model_training_total.labels(
        user_id=str(user_id),
        model_type=model_type,
        status=status
    ).inc()
    
    model_training_duration_seconds.labels(
        model_type=model_type
    ).observe(duration)


def track_prediction(user_id: int, model_type: str, duration: float):
    """
    Track prediction metrics.
    
    Args:
        user_id: User ID
        model_type: Type of model
        duration: Prediction duration in seconds
    """
    if not settings.ENABLE_METRICS:
        return
    
    model_prediction_total.labels(
        user_id=str(user_id),
        model_type=model_type
    ).inc()
    
    model_prediction_duration_seconds.labels(
        model_type=model_type
    ).observe(duration)


def update_model_accuracy(user_id: int, model_type: str, accuracy: float):
    """
    Update model accuracy metric.
    
    Args:
        user_id: User ID
        model_type: Type of model
        accuracy: Model accuracy (R² score)
    """
    if not settings.ENABLE_METRICS:
        return
    
    model_accuracy.labels(
        user_id=str(user_id),
        model_type=model_type
    ).set(accuracy)


def track_cache_hit(cache_type: str):
    """
    Track cache hit.
    
    Args:
        cache_type: Type of cache
    """
    if not settings.ENABLE_METRICS:
        return
    
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """
    Track cache miss.
    
    Args:
        cache_type: Type of cache
    """
    if not settings.ENABLE_METRICS:
        return
    
    cache_misses_total.labels(cache_type=cache_type).inc()


def track_db_query(query_type: str, duration: float):
    """
    Track database query metrics.
    
    Args:
        query_type: Type of query
        duration: Query duration in seconds
    """
    if not settings.ENABLE_METRICS:
        return
    
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def track_db_error(error_type: str):
    """
    Track database errors.
    
    Args:
        error_type: Type of error
    """
    if not settings.ENABLE_METRICS:
        return
    
    db_errors_total.labels(error_type=error_type).inc()


def metrics_middleware(app):
    """
    Middleware to track API request metrics.
    
    Args:
        app: FastAPI application
    """
    @app.middleware("http")
    async def track_requests(request, call_next):
        """Track incoming requests."""
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        track_request_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration
        )
        
        return response


def get_metrics() -> Response:
    """
    Get Prometheus metrics.
    
    Returns:
        Response with metrics in Prometheus format
    """
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


def measure_time(metric_name: str = None):
    """
    Decorator to measure execution time of a function.
    
    Args:
        metric_name: Name for the metric (optional)
    
    Usage:
        @measure_time("process_data")
        def process_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            name = metric_name or func.__name__
            # You can add custom metric tracking here if needed
            
            return result
        return wrapper
    return decorator
