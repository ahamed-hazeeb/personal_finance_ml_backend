"""
ML Trainer module for building monthly savings series and training linear regression models.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

from app.db import Transaction, ModelParameters


def build_monthly_savings_series(
    db: Session,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.Series:
    """
    Build a monthly savings time series from transactions table.
    
    Args:
        db: SQLAlchemy database session
        user_id: User ID to filter transactions
        start_date: Optional start date for filtering (defaults to 12 months ago)
        end_date: Optional end date for filtering (defaults to today)
    
    Returns:
        pandas.Series with monthly index (0..N-1) as index and total savings as values
    
    Raises:
        ValueError: If insufficient data (less than 3 months)
    """
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)  # Last 12 months
    
    # Query to aggregate monthly savings
    # Use date_trunc to group by month
    query = text("""
        SELECT 
            date_trunc('month', date) as month,
            SUM(amount) as total_savings
        FROM transactions
        WHERE user_id = :user_id
            AND type = 'savings'
            AND date >= :start_date
            AND date <= :end_date
        GROUP BY date_trunc('month', date)
        ORDER BY date_trunc('month', date) ASC
    """)
    
    result = db.execute(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    rows = result.fetchall()
    
    # Convert to DataFrame
    if not rows:
        raise ValueError(f"No savings transactions found for user {user_id} in the specified date range")
    
    df = pd.DataFrame(rows, columns=['month', 'total_savings'])
    
    # Validate minimum data requirement
    if len(df) < 3:
        raise ValueError(
            f"Insufficient data: found {len(df)} months, need at least 3 months for training"
        )
    
    # Create monthly index starting from 0
    df['month_index'] = range(len(df))
    
    # Store start month for metadata
    start_month = df['month'].iloc[0].strftime('%Y-%m')
    
    # Create Series with month_index as index
    series = pd.Series(
        data=df['total_savings'].values,
        index=df['month_index'].values,
        name='total_savings'
    )
    
    # Store start_month as attribute for later use
    series.start_month = start_month
    
    return series


def train_linear_model(series: pd.Series) -> Dict:
    """
    Train a linear regression model on monthly savings time series.
    
    Args:
        series: pandas Series with month index (0..N-1) and savings values
    
    Returns:
        Dictionary containing:
            - slope: Model slope (monthly savings trend)
            - intercept: Model intercept
            - r2_score: R² score of the model
            - trained_months: Number of months used for training
            - start_month: First month in the series (YYYY-MM format)
    """
    # Prepare data for sklearn
    X = series.index.values.reshape(-1, 1)  # Month indices
    y = series.values  # Savings values
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make predictions for R² calculation
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # Extract model parameters
    result = {
        'slope': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'r2_score': float(r2),
        'trained_months': len(series),
        'start_month': getattr(series, 'start_month', 'unknown')
    }
    
    return result


def save_model_parameters(
    db: Session,
    user_id: int,
    model_data: Dict,
    model_type: str = 'linear_regression',
    target_table: str = 'transactions_savings'
) -> ModelParameters:
    """
    Save or update model parameters in the database (upsert behavior).
    
    Args:
        db: SQLAlchemy database session
        user_id: User ID
        model_data: Dictionary with slope, intercept, r2_score, trained_months, start_month
        model_type: Type of model (default: 'linear_regression')
        target_table: Target table name (default: 'transactions_savings')
    
    Returns:
        ModelParameters object (created or updated)
    """
    # Try to find existing model
    existing_model = db.query(ModelParameters).filter(
        ModelParameters.user_id == user_id,
        ModelParameters.model_type == model_type,
        ModelParameters.target_table == target_table
    ).first()
    
    # Prepare parameters JSON (excluding slope and intercept which have dedicated columns)
    parameters_json = {
        'r2_score': model_data['r2_score'],
        'trained_months': model_data['trained_months'],
        'start_month': model_data['start_month']
    }
    
    if existing_model:
        # Update existing model
        existing_model.slope = model_data['slope']
        existing_model.intercept = model_data['intercept']
        existing_model.parameters = parameters_json
        existing_model.last_trained_date = datetime.now().date()
        db.commit()
        db.refresh(existing_model)
        return existing_model
    else:
        # Insert new model
        new_model = ModelParameters(
            user_id=user_id,
            model_type=model_type,
            target_table=target_table,
            slope=model_data['slope'],
            intercept=model_data['intercept'],
            parameters=parameters_json,
            last_trained_date=datetime.now().date()
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model


def get_latest_model(
    db: Session,
    user_id: int,
    model_type: str = 'linear_regression',
    target_table: str = 'transactions_savings'
) -> Optional[ModelParameters]:
    """
    Retrieve the latest model parameters for a user.
    
    Args:
        db: SQLAlchemy database session
        user_id: User ID
        model_type: Type of model (default: 'linear_regression')
        target_table: Target table name (default: 'transactions_savings')
    
    Returns:
        ModelParameters object or None if not found
    """
    model = db.query(ModelParameters).filter(
        ModelParameters.user_id == user_id,
        ModelParameters.model_type == model_type,
        ModelParameters.target_table == target_table
    ).first()
    
    return model


def predict_savings(
    model: ModelParameters,
    months_ahead: int
) -> list:
    """
    Predict monthly savings for future months using a trained linear model.
    
    Args:
        model: ModelParameters object with trained model
        months_ahead: Number of months to predict ahead
    
    Returns:
        List of predicted savings values for the next months_ahead months
    """
    # Extract parameters
    slope = float(model.slope)
    intercept = float(model.intercept)
    trained_months = model.parameters.get('trained_months', 0)
    
    # Generate predictions
    # Start from the next month after training (month index = trained_months)
    predictions = []
    for i in range(months_ahead):
        month_index = trained_months + i
        predicted_value = slope * month_index + intercept
        predictions.append(float(predicted_value))
    
    return predictions
