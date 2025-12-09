"""
Database configuration and session management for PostgreSQL.

This module defines the complete database schema aligned with the production database,
including all tables for users, transactions, bills, budgets, and ML model metadata.
"""
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, JSON, Index, DateTime, Text, Boolean, Float, ForeignKey, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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


# Core Tables

class User(Base):
    """User model for authentication and user management."""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    fcm_token = Column(Text, nullable=True)  # Firebase Cloud Messaging token for notifications
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Account(Base):
    """User accounts for tracking different financial accounts."""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    account_type = Column(Text, nullable=False)  # 'checking', 'savings', 'credit', etc.
    balance = Column(Numeric, nullable=False, default=0.00)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Category(Base):
    """Transaction categories (user-specific or global)."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True, index=True)  # NULL for global categories
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # 'income', 'expense', 'savings'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_categories_user_id', 'user_id'),
        Index('idx_categories_unique', 'user_id', 'name', 'type', unique=True),
    )


class PaymentMethod(Base):
    """Payment methods for users."""
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    method_name = Column(Text, nullable=False)  # 'credit_card', 'debit_card', 'upi', 'cash', etc.
    details = Column(JSON, nullable=True)  # Card last 4 digits, UPI ID, etc.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bill(Base):
    """Bills and recurring payments."""
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    bill_name = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric, nullable=False)
    status = Column(Text, nullable=False, default='unpaid')  # 'unpaid', 'paid', 'overdue'
    reminder_sent = Column(Integer, nullable=False, default=0)
    payment_reference = Column(Text, nullable=True)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id', ondelete='SET NULL'), nullable=True)
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_frequency = Column(Text, nullable=True)  # 'monthly', 'quarterly', 'yearly'
    reminder_enabled = Column(Boolean, nullable=False, default=False)
    reminder_days_before = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    """Transaction model matching the transactions table schema."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    amount = Column(Numeric, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    type = Column(Text, nullable=False)  # 'expense', 'income', 'savings'
    date = Column(Date, nullable=False, index=True)
    note = Column(Text, nullable=True, default='')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    receiver_name = Column(Text, nullable=True)
    payment_method = Column(Text, nullable=True)
    bill_id = Column(Integer, ForeignKey('bills.id', ondelete='SET NULL'), nullable=True, index=True)


class Budget(Base):
    """Budget planning and tracking."""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    amount = Column(Numeric, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Text, nullable=False, default='active')  # 'active', 'completed', 'cancelled'
    model_parameters_id = Column(Integer, ForeignKey('model_parameters.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class FuturePlan(Base):
    """Future financial plans and goals (legacy table, use FinancialGoals for new features)."""
    __tablename__ = "future_plans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    goal_name = Column(Text, nullable=False)
    target_amount = Column(Numeric, nullable=False)
    current_savings = Column(Numeric, nullable=False, default=0.00)
    target_date = Column(Date, nullable=False)
    monthly_savings = Column(Numeric, nullable=False)
    model_parameters_id = Column(Integer, ForeignKey('model_parameters.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    """Reminders for bills and financial events."""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(Text, nullable=False)
    reminder_date = Column(Date, nullable=False)
    reminder_time = Column(Time, nullable=True)
    days_before = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default='pending')  # 'pending', 'sent', 'dismissed'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ML and Analytics Tables

class ModelParameters(Base):
    """Model parameters table for storing trained ML model metadata."""
    __tablename__ = "model_parameters"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    model_type = Column(Text, nullable=False)  # 'linear_regression', 'expense_forecast', etc.
    slope = Column(Numeric, nullable=True)
    intercept = Column(Numeric, nullable=True)
    parameters = Column(JSON, nullable=True)  # Additional parameters as JSON
    last_trained_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    target_table = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_model_parameters_user_id', 'user_id'),
    )


class PredictionCache(Base):
    """Cache for prediction results to improve performance."""
    __tablename__ = "prediction_cache"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
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
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey('model_parameters.id'), nullable=False, index=True)
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
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
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
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
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
    """User financial goals (new implementation for Phase 2-4 features)."""
    __tablename__ = "financial_goals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
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


class FinancialHealthHistory(Base):
    """Financial health score history tracking (Phase 2-4 feature)."""
    __tablename__ = "financial_health_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Integer, nullable=False)  # Overall score 0-100
    savings_rate_score = Column(Numeric, nullable=True)
    expense_consistency_score = Column(Numeric, nullable=True)
    emergency_fund_score = Column(Numeric, nullable=True)
    debt_ratio_score = Column(Numeric, nullable=True)
    goal_progress_score = Column(Numeric, nullable=True)
    grade = Column(String(2), nullable=True)  # A, B, C, D, F
    recommendations = Column(JSON, nullable=True)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_calculated', 'user_id', 'calculated_at'),
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
