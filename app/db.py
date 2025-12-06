"""
Database configuration and session management for PostgreSQL.
"""
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, JSON, Index, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.config import settings

# Create engine with configuration from settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database Models
class Transaction(Base):
    """Transaction model matching the transactions table schema."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric, nullable=False)
    type = Column(String, nullable=False)  # 'expense', 'income', 'savings'
    category = Column(String, index=True)
    description = Column(String)


class ModelParameters(Base):
    """Model parameters table for storing trained ML model metadata."""
    __tablename__ = "model_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    model_type = Column(String, nullable=False)  # 'linear_regression', 'expense_forecast', etc.
    target_table = Column(String, nullable=False)  # 'transactions_savings'
    slope = Column(Numeric, nullable=True)
    intercept = Column(Numeric, nullable=True)
    parameters = Column(JSON, nullable=True)  # Additional parameters as JSON
    last_trained_date = Column(Date, nullable=False)
    
    __table_args__ = (
        Index('idx_user_model_target', 'user_id', 'model_type', 'target_table'),
    )


class PredictionCache(Base):
    """Cache for prediction results to improve performance."""
    __tablename__ = "prediction_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    prediction_type = Column(String(50), nullable=False, index=True)
    input_hash = Column(String(64), nullable=False, index=True)  # MD5 hash of input parameters
    result = Column(JSON, nullable=False)  # Prediction result as JSON
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_user_type_hash', 'user_id', 'prediction_type', 'input_hash'),
        Index('idx_expires', 'expires_at'),
    )


class ModelPerformanceMetrics(Base):
    """Track model performance over time."""
    __tablename__ = "model_performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, nullable=False, index=True)  # References model_parameters.id
    actual_value = Column(Numeric, nullable=True)
    predicted_value = Column(Numeric, nullable=True)
    error_percentage = Column(Numeric, nullable=True)
    mae = Column(Numeric, nullable=True)  # Mean Absolute Error
    rmse = Column(Numeric, nullable=True)  # Root Mean Squared Error
    r2_score = Column(Numeric, nullable=True)  # R² Score
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_model_recorded', 'model_id', 'recorded_at'),
    )


class UserBenchmarks(Base):
    """Anonymized user benchmarks for comparison."""
    __tablename__ = "user_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String(20), nullable=False, index=True)  # '20-30', '30-40', etc.
    income_bracket = Column(String(20), nullable=False, index=True)  # '0-30k', '30-50k', etc.
    avg_savings_rate = Column(Numeric, nullable=True)  # Average savings rate
    avg_expense_ratio = Column(Numeric, nullable=True)  # Average expense ratio
    avg_health_score = Column(Numeric, nullable=True)  # Average financial health score
    sample_size = Column(Integer, nullable=True)  # Number of users in this group
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_age_income', 'age_group', 'income_bracket'),
    )


class RecommendationsHistory(Base):
    """Track recommendations provided to users."""
    __tablename__ = "recommendations_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    recommendation_type = Column(String(50), nullable=False)  # 'habit', 'opportunity', 'nudge', etc.
    category = Column(String(50), nullable=True)
    recommendation = Column(Text, nullable=False)  # The actual recommendation text
    context = Column(JSON, nullable=True)  # Additional context data
    accepted = Column(Boolean, nullable=True)  # Whether user acted on it
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_type', 'user_id', 'recommendation_type'),
        Index('idx_created', 'created_at'),
    )


class FinancialGoals(Base):
    """User financial goals."""
    __tablename__ = "financial_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    goal_name = Column(String(200), nullable=False)
    target_amount = Column(Numeric, nullable=False)
    current_amount = Column(Numeric, nullable=False, default=0)
    target_date = Column(Date, nullable=True)
    monthly_contribution = Column(Numeric, nullable=True)
    status = Column(String(20), nullable=False, default='active')  # 'active', 'completed', 'abandoned'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
    )


# Dependency to get DB session
def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Function to create all tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Function to drop all tables (use with caution!)
def drop_tables():
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)
