"""
Savings trajectory forecasting model.

This module provides a predictor for projecting user's savings over
3, 6, and 12 months with confidence intervals on growth trends.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from .base_predictor import BaseFinancePredictor


class SavingsForecaster(BaseFinancePredictor):
    """
    Predictor for savings trajectory forecasting.
    
    Projects future savings based on historical income, expense, and savings patterns.
    Provides confidence intervals for short-term (3m), medium-term (6m), and long-term (12m) forecasts.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
        **kwargs
    ):
        """
        Initialize the savings forecaster.
        
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
        target_column: str = 'savings'
    ) -> tuple:
        """
        Prepare data for savings forecasting.
        
        Args:
            monthly_df: DataFrame with monthly financial data
            target_column: Name of the target column (default 'savings')
            
        Returns:
            Tuple of (features_df, target_series)
        """
        from utils.preprocessing import engineer_features
        
        # Create features
        df = monthly_df.copy()
        
        # Engineer features
        feature_cols = ['savings', 'total_income', 'total_expense']
        df_engineered = engineer_features(
            df,
            target_columns=feature_cols,
            lag_periods=[1, 2, 3],
            rolling_windows=[3, 6]
        )
        
        # Drop rows with NaN
        df_engineered = df_engineered.dropna()
        
        # Select features
        exclude_cols = ['year_month', target_column, 'total_income', 'total_expense']
        feature_columns = [col for col in df_engineered.columns if col not in exclude_cols]
        
        X = df_engineered[feature_columns]
        y = df_engineered[target_column]
        
        return X, y
    
    def forecast_trajectory(
        self,
        monthly_df: pd.DataFrame,
        periods: List[int] = [3, 6, 12],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Forecast savings trajectory for multiple future periods.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            periods: List of periods to forecast (in months)
            confidence_level: Confidence level for prediction intervals
            
        Returns:
            Dictionary with trajectory forecasts and confidence intervals
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before forecasting")
        
        # Get current savings (cumulative)
        current_savings = monthly_df['savings'].cumsum().iloc[-1]
        
        # Prepare features for prediction
        X, _ = self.prepare_data(monthly_df)
        
        trajectory = {}
        
        # Forecast for each period
        for period in periods:
            # For simplicity, we'll use iterative prediction
            # In practice, you might want to use more sophisticated methods
            
            # Use the most recent data
            X_pred = X.iloc[[-1]].copy()
            
            # Predict monthly savings
            result = self.predict(X_pred, return_confidence_interval=True, confidence_level=confidence_level)
            monthly_savings_pred = result['predictions'][0]
            
            # Extract confidence intervals: result['confidence_interval'] is (lower_array, upper_array)
            ci_lower_array, ci_upper_array = result['confidence_interval']
            ci_lower = ci_lower_array[0]  # First element of lower bound array
            ci_upper = ci_upper_array[0]  # First element of upper bound array
            
            # Project cumulative savings
            projected_cumulative = current_savings + (monthly_savings_pred * period)
            ci_cumulative_lower = current_savings + (ci_lower * period)
            ci_cumulative_upper = current_savings + (ci_upper * period)
            
            trajectory[f'{period}_months'] = {
                'projected_savings': round(projected_cumulative, 2),
                'monthly_savings_rate': round(monthly_savings_pred, 2),
                'confidence_interval': (round(ci_cumulative_lower, 2), round(ci_cumulative_upper, 2)),
                'growth_from_current': round(projected_cumulative - current_savings, 2)
            }
        
        trajectory['current_savings'] = round(current_savings, 2)
        
        return trajectory
    
    def calculate_savings_metrics(
        self,
        monthly_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate various savings metrics from historical data.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            
        Returns:
            Dictionary with savings metrics
        """
        savings = monthly_df['savings']
        income = monthly_df['total_income']
        
        metrics = {
            'avg_monthly_savings': round(savings.mean(), 2),
            'savings_rate': round((savings.mean() / income.mean()) * 100, 2),  # as percentage
            'savings_volatility': round(savings.std(), 2),
            'total_cumulative_savings': round(savings.sum(), 2),
            'max_monthly_savings': round(savings.max(), 2),
            'min_monthly_savings': round(savings.min(), 2),
            'months_positive_savings': int((savings > 0).sum()),
            'months_negative_savings': int((savings < 0).sum())
        }
        
        # Calculate trend (linear regression slope)
        if len(savings) > 1:
            x = np.arange(len(savings))
            coeffs = np.polyfit(x, savings, 1)
            metrics['savings_trend'] = round(coeffs[0], 2)  # slope
        
        return metrics
    
    def assess_financial_health(
        self,
        monthly_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Assess overall financial health based on savings patterns.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            
        Returns:
            Dictionary with financial health assessment
        """
        metrics = self.calculate_savings_metrics(monthly_df)
        trajectory = self.forecast_trajectory(monthly_df)
        
        # Determine health status
        savings_rate = metrics['savings_rate']
        if savings_rate >= 20:
            health_status = 'Excellent'
            health_message = 'You are saving a healthy percentage of your income.'
        elif savings_rate >= 10:
            health_status = 'Good'
            health_message = 'Your savings rate is reasonable. Consider increasing it if possible.'
        elif savings_rate >= 5:
            health_status = 'Fair'
            health_message = 'Your savings rate is low. Try to reduce expenses or increase income.'
        else:
            health_status = 'Poor'
            health_message = 'Your savings rate is very low. Urgent attention needed to improve financial health.'
        
        assessment = {
            'status': health_status,
            'message': health_message,
            'current_metrics': metrics,
            'projected_trajectory': trajectory,
            'recommendations': []
        }
        
        # Add recommendations
        if metrics['savings_rate'] < 15:
            assessment['recommendations'].append('Aim to save at least 15-20% of your income')
        
        if metrics['savings_volatility'] > metrics['avg_monthly_savings'] * 0.5:
            assessment['recommendations'].append('Work on stabilizing your monthly savings')
        
        if metrics['months_negative_savings'] > 0:
            assessment['recommendations'].append(
                f'You had {metrics["months_negative_savings"]} month(s) with negative savings. '
                'Focus on building an emergency fund.'
            )
        
        return assessment
