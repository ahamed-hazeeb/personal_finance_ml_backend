"""
Main FastAPI application for Personal Finance ML Backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ml, goals, insights, predictions, goals_simplified
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.monitoring import metrics_middleware, get_metrics
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limiter import register_rate_limiter

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered predictive analytics backend for personal finance management",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Register error handlers
register_error_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware
if settings.ENABLE_METRICS:
    metrics_middleware(app)

# Register rate limiter
if settings.RATE_LIMIT_ENABLED:
    register_rate_limiter(app)

# Include routers
app.include_router(insights.router)  # POST /insights
app.include_router(predictions.router)  # GET /predictions
app.include_router(goals_simplified.router)  # POST /goals/timeline, POST /goals/reverse-plan
app.include_router(ml.router)  # POST /ml/train, POST /ml/predict
app.include_router(goals.router)  # POST /api/v1/goals/calculate-timeline, POST /api/v1/goals/reverse-plan

logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Debug mode: {settings.DEBUG}")


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "insights": "POST /insights - Get AI-powered spending insights from transactions",
            "predictions": "GET /predictions?user_id=X&months=6 - Get future expense predictions",
            "goals_timeline": "POST /goals/timeline - Calculate goal achievement timeline",
            "goals_reverse_plan": "POST /goals/reverse-plan - Calculate required savings for goal",
            "ml_train": "POST /ml/train - Train a linear regression model for monthly savings",
            "ml_predict": "POST /ml/predict - Predict monthly savings for future months",
            "goals_calculate_timeline": "POST /api/v1/goals/calculate-timeline - Calculate goal timeline (detailed)",
            "goals_reverse_plan_v1": "POST /api/v1/goals/reverse-plan - Calculate required savings (detailed)",
            "health": "GET /health - Health check endpoint",
            "metrics": "GET /metrics - Prometheus metrics (if enabled)",
            "docs": "GET /docs - Interactive API documentation"
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns system health status and basic metrics.
    """
    from app.services.cache_service import get_cache_service
    
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }
    
    # Add cache status if enabled
    if settings.CACHE_ENABLED:
        cache_service = get_cache_service()
        cache_stats = cache_service.get_stats()
        health_status["cache"] = {
            "enabled": cache_stats.get("enabled", False),
            "hit_rate": cache_stats.get("hit_rate", 0)
        }
    
    return health_status


@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for monitoring.
    """
    if not settings.ENABLE_METRICS:
        return {"error": "Metrics are disabled"}
    
    return get_metrics()


@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    logger.info("Application startup complete")
    logger.info(f"API documentation available at /docs")
    logger.info(f"Health check available at /health")
    
    if settings.ENABLE_METRICS:
        logger.info(f"Metrics available at /metrics")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    logger.info("Application shutting down gracefully")

