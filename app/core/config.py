"""
Configuration management for the Personal Finance ML Backend.

This module provides centralized configuration management with support for
different environments (dev, staging, production) and secure handling of secrets.
"""
import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    For example, DATABASE_URL can be set via the DATABASE_URL env var.
    """
    
    # Application
    APP_NAME: str = "Personal Finance ML Backend"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/personal_finance",
        description="PostgreSQL connection string"
    )
    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Maximum overflow connections")
    
    # Redis Cache
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    CACHE_TTL_SECONDS: int = Field(default=86400, description="Default cache TTL (24 hours)")
    CACHE_TTL_HEALTH_SCORE: int = Field(default=86400, description="Health score cache TTL")
    CACHE_TTL_BENCHMARKS: int = Field(default=604800, description="Benchmarks cache TTL (7 days)")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend")
    
    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT encoding"
    )
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Max requests per time window")
    RATE_LIMIT_PERIOD: int = Field(default=3600, description="Rate limit time window in seconds (1 hour)")
    
    # Model Configuration
    MIN_TRAINING_MONTHS: int = Field(default=3, description="Minimum months required for training")
    MAX_TRAINING_MONTHS: int = Field(default=24, description="Maximum months to use for training")
    CONFIDENCE_LEVEL: float = Field(default=0.95, description="Confidence level for predictions")
    MODEL_SAVE_DIR: str = Field(default="./models/saved", description="Directory to save trained models")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics endpoint port")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    
    # Feature Flags
    ENABLE_ADVANCED_FORECASTING: bool = Field(default=True, description="Enable Holt-Winters/ARIMA")
    ENABLE_GOAL_PLANNING: bool = Field(default=True, description="Enable goal planning features")
    ENABLE_BUDGET_OPTIMIZER: bool = Field(default=True, description="Enable budget optimizer")
    ENABLE_RECOMMENDATIONS: bool = Field(default=True, description="Enable recommendations engine")
    ENABLE_CASHFLOW_PREDICTOR: bool = Field(default=False, description="Enable cashflow predictor (Phase 2)")
    ENABLE_DEBT_OPTIMIZER: bool = Field(default=False, description="Enable debt optimizer (Phase 2)")
    ENABLE_INVESTMENT_ANALYZER: bool = Field(default=False, description="Enable investment analyzer (Phase 2)")
    
    # Prediction Settings
    DEFAULT_FORECAST_MONTHS: int = Field(default=6, description="Default number of months to forecast")
    MAX_FORECAST_MONTHS: int = Field(default=24, description="Maximum number of months to forecast")
    ANOMALY_THRESHOLD: float = Field(default=1.5, description="Anomaly detection threshold (std dev)")
    
    # Budget Settings
    BUDGET_SAFETY_MARGIN: float = Field(default=0.1, description="Budget safety margin (10%)")
    OVERSPENDING_THRESHOLD: float = Field(default=1.2, description="Overspending threshold (20% above avg)")
    
    # Health Score Weights
    HEALTH_SCORE_WEIGHT_SAVINGS_RATE: float = Field(default=0.30, description="Savings rate weight")
    HEALTH_SCORE_WEIGHT_EXPENSE_CONSISTENCY: float = Field(default=0.25, description="Expense consistency weight")
    HEALTH_SCORE_WEIGHT_EMERGENCY_FUND: float = Field(default=0.20, description="Emergency fund weight")
    HEALTH_SCORE_WEIGHT_DEBT_RATIO: float = Field(default=0.15, description="Debt-to-income ratio weight")
    HEALTH_SCORE_WEIGHT_GOAL_PROGRESS: float = Field(default=0.10, description="Goal progress weight")
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @field_validator("CONFIDENCE_LEVEL")
    @classmethod
    def validate_confidence_level(cls, v):
        """Validate confidence level."""
        if not 0 < v < 1:
            raise ValueError("CONFIDENCE_LEVEL must be between 0 and 1")
        return v
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    This function can be used as a FastAPI dependency.
    
    Returns:
        Settings instance
    """
    return settings
