"""
Preprocessing utilities for personal finance ML models.

This module provides functions for feature engineering, data validation,
and preprocessing for time-series financial data.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from datetime import datetime


# Constants
EPSILON = 1e-8  # Small value to avoid division by zero in normalization


def create_time_features(df: pd.DataFrame, date_column: str = 'year_month') -> pd.DataFrame:
    """
    Create time-based features from date column.
    
    Args:
        df: DataFrame with date column
        date_column: Name of the date column
        
    Returns:
        DataFrame with additional time features
    """
    df = df.copy()
    
    # Convert to period if not already
    if not isinstance(df[date_column].iloc[0], pd.Period):
        df[date_column] = pd.to_datetime(df[date_column]).dt.to_period('M')
    
    # Extract temporal features
    df['month'] = df[date_column].apply(lambda x: x.month)
    df['quarter'] = df[date_column].apply(lambda x: x.quarter)
    df['year'] = df[date_column].apply(lambda x: x.year)
    
    # Create cyclical features for month (sin/cos encoding)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    return df


def create_lag_features(
    df: pd.DataFrame,
    target_columns: List[str],
    lag_periods: List[int] = [1, 2, 3]
) -> pd.DataFrame:
    """
    Create lagged features for time-series prediction.
    
    Args:
        df: DataFrame with time-series data
        target_columns: Columns to create lags for
        lag_periods: List of lag periods (e.g., [1, 2, 3] for 1, 2, 3 months back)
        
    Returns:
        DataFrame with lag features
    """
    df = df.copy()
    
    for col in target_columns:
        for lag in lag_periods:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    
    return df


def create_rolling_features(
    df: pd.DataFrame,
    target_columns: List[str],
    windows: List[int] = [3, 6]
) -> pd.DataFrame:
    """
    Create rolling statistics features.
    
    Args:
        df: DataFrame with time-series data
        target_columns: Columns to create rolling features for
        windows: List of window sizes for rolling statistics
        
    Returns:
        DataFrame with rolling features
    """
    df = df.copy()
    
    for col in target_columns:
        for window in windows:
            # Rolling mean
            df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window=window, min_periods=1).mean()
            
            # Rolling std
            df[f'{col}_rolling_std_{window}'] = df[col].rolling(window=window, min_periods=1).std()
            # Fill NaN std values with 0 (happens with single value or constant values)
            df[f'{col}_rolling_std_{window}'] = df[f'{col}_rolling_std_{window}'].fillna(0)
            
            # Rolling trend (difference between current and rolling mean)
            df[f'{col}_trend_{window}'] = df[col] - df[f'{col}_rolling_mean_{window}']
    
    return df


def create_growth_features(
    df: pd.DataFrame,
    target_columns: List[str]
) -> pd.DataFrame:
    """
    Create growth rate and momentum features.
    
    Args:
        df: DataFrame with time-series data
        target_columns: Columns to create growth features for
        
    Returns:
        DataFrame with growth features
    """
    df = df.copy()
    
    for col in target_columns:
        # Month-over-month growth rate
        # Replace inf and -inf with NaN, then fill with 0
        growth = df[col].pct_change()
        growth = growth.replace([np.inf, -np.inf], np.nan)
        df[f'{col}_mom_growth'] = growth.fillna(0)
        
        # Year-over-year growth rate (if enough data)
        if len(df) > 12:
            yoy_growth = df[col].pct_change(periods=12)
            yoy_growth = yoy_growth.replace([np.inf, -np.inf], np.nan)
            df[f'{col}_yoy_growth'] = yoy_growth.fillna(0)
    
    return df


def engineer_features(
    df: pd.DataFrame,
    target_columns: List[str],
    date_column: str = 'year_month',
    lag_periods: List[int] = [1, 2, 3],
    rolling_windows: List[int] = [3, 6]
) -> pd.DataFrame:
    """
    Complete feature engineering pipeline for financial time-series data.
    
    Args:
        df: Input DataFrame
        target_columns: Columns to create features for
        date_column: Name of the date column
        lag_periods: Lag periods for lag features
        rolling_windows: Window sizes for rolling features
        
    Returns:
        DataFrame with engineered features
    """
    df = df.copy()
    
    # Time-based features
    df = create_time_features(df, date_column)
    
    # Lag features
    df = create_lag_features(df, target_columns, lag_periods)
    
    # Rolling features
    df = create_rolling_features(df, target_columns, rolling_windows)
    
    # Growth features
    df = create_growth_features(df, target_columns)
    
    return df


def prepare_train_test_split(
    df: pd.DataFrame,
    test_size: int = 3,
    feature_columns: List[str] = None,
    target_columns: List[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Time-series aware train-test split.
    
    Args:
        df: DataFrame with features and targets
        test_size: Number of recent periods to use for testing
        feature_columns: List of feature column names
        target_columns: List of target column names
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    # Split based on time order
    train_df = df.iloc[:-test_size]
    test_df = df.iloc[-test_size:]
    
    # Remove rows with NaN (from lag features)
    train_df = train_df.dropna()
    test_df = test_df.dropna()
    
    if feature_columns is None or target_columns is None:
        return train_df, test_df, None, None
    
    X_train = train_df[feature_columns]
    X_test = test_df[feature_columns]
    y_train = train_df[target_columns]
    y_test = test_df[target_columns]
    
    return X_train, X_test, y_train, y_test


def validate_data(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that DataFrame has required columns and proper data types.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If validation fails
    """
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        print(f"Warning: Found null values in columns: {null_cols}")
    
    return True


def normalize_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Normalize features using mean and std from training set.
    
    Args:
        X_train: Training features
        X_test: Test features (optional)
        
    Returns:
        Tuple of (X_train_normalized, X_test_normalized, normalization_params)
    """
    normalization_params = {
        'mean': X_train.mean(),
        'std': X_train.std()
    }
    
    X_train_norm = (X_train - normalization_params['mean']) / (normalization_params['std'] + EPSILON)
    
    X_test_norm = None
    if X_test is not None:
        X_test_norm = (X_test - normalization_params['mean']) / (normalization_params['std'] + EPSILON)
    
    return X_train_norm, X_test_norm, normalization_params
