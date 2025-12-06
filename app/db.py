"""
Database configuration and session management for PostgreSQL.
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/personal_finance")

# Create engine
engine = create_engine(DATABASE_URL)

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
    date = Column(Date, nullable=False)
    amount = Column(Numeric, nullable=False)
    type = Column(String, nullable=False)  # 'expense', 'income', 'savings'
    category = Column(String)
    description = Column(String)


class ModelParameters(Base):
    """Model parameters table for storing trained ML model metadata."""
    __tablename__ = "model_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    model_type = Column(String, nullable=False)  # 'linear_regression'
    target_table = Column(String, nullable=False)  # 'transactions_savings'
    slope = Column(Numeric, nullable=True)
    intercept = Column(Numeric, nullable=True)
    parameters = Column(JSON, nullable=True)  # Additional parameters as JSON
    last_trained_date = Column(Date, nullable=False)
    
    __table_args__ = (
        Index('idx_user_model_target', 'user_id', 'model_type', 'target_table'),
    )


# Dependency to get DB session
def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
