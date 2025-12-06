"""
Expense forecasting model for predicting monthly total expenses.

This module provides a predictor for forecasting total monthly expenses
based on historical spending patterns with confidence intervals.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_predictor import BaseFinancePredictor


class ExpenseForecaster(BaseFinancePredictor):
    """
    Predictor for monthly total expense forecasting.
    
    Uses historical expense data with time-series features to predict
    next month's total expense with confidence intervals.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
        **kwargs
    ):
        """
        Initialize the expense forecaster.
        
        Args:
            n_estimators: Number of trees in the random forest
            max_depth: Maximum depth of trees
            random_state: Random seed for reproducibility
            **kwargs: Additional parameters for RandomForestRegressor
        """
        super().__init__(n_estimators, max_depth, random_state, **kwargs)
    
    def prepare_data(
        self,
        monthly_df: pd.DataFrame,
        target_column: str = 'total_expense'
    ) -> tuple:
        """
        Prepare data for expense forecasting.
        
        Args:
            monthly_df: DataFrame with monthly financial data
            target_column: Name of the target column
            
        Returns:
            Tuple of (features_df, target_series)
        """
        from utils.preprocessing import engineer_features
        
        # Create features
        df = monthly_df.copy()
        
        # Engineer features
        feature_cols = [target_column, 'total_income', 'savings']
        df_engineered = engineer_features(
            df,
            target_columns=feature_cols,
            lag_periods=[1, 2, 3],
            rolling_windows=[3, 6]
        )
        
        # Drop rows with NaN (from lag features)
        df_engineered = df_engineered.dropna()
        
        # Select features (exclude original target and date)
        exclude_cols = ['year_month', target_column, 'total_income', 'savings']
        feature_columns = [col for col in df_engineered.columns if col not in exclude_cols]
        
        X = df_engineered[feature_columns]
        y = df_engineered[target_column]
        
        return X, y
    
    def forecast_next_month(
        self,
        monthly_df: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Forecast next month's total expense.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            confidence_level: Confidence level for prediction interval
            
        Returns:
            Dictionary with forecast and confidence interval
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before forecasting")
        
        # Prepare the last available data point
        X, _ = self.prepare_data(monthly_df)
        X_latest = X.iloc[[-1]]  # Get the most recent data
        
        # Make prediction
        result = self.predict(X_latest, return_confidence_interval=True, confidence_level=confidence_level)
        
        prediction = result['predictions'][0]
        ci_lower, ci_upper = result['confidence_interval'][0][0], result['confidence_interval'][1][0]
        
        forecast = {
            'predicted_expense': round(prediction, 2),
            'confidence_interval': (round(ci_lower, 2), round(ci_upper, 2)),
            'confidence_level': confidence_level
        }
        
        return forecast
