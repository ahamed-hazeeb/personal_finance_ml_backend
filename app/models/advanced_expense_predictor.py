"""
Advanced expense forecasting using time-series models.

This module provides advanced forecasting capabilities using:
- Holt-Winters exponential smoothing for seasonal patterns (12+ months)
- ARIMA models for intermediate data (6-11 months)
- Linear fallback for limited data (<6 months)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

warnings.filterwarnings('ignore', category=ConvergenceWarning)


class AdvancedExpenseForecaster:
    """
    Advanced expense forecaster using time-series models.
    
    Automatically selects the best model based on data availability:
    - 12+ months: Holt-Winters exponential smoothing
    - 6-11 months: ARIMA
    - <6 months: Linear regression fallback
    """
    
    def __init__(self):
        """Initialize the advanced expense forecaster."""
        self.model = None
        self.model_type = None
        self.data_months = 0
        self.last_trained = None
    
    def select_model(
        self, 
        monthly_expenses: pd.Series, 
        months_available: int
    ) -> str:
        """
        Select the appropriate model based on data availability.
        
        Args:
            monthly_expenses: Time series of monthly expenses
            months_available: Number of months of data available
            
        Returns:
            Model type selected: 'holt_winters', 'arima', or 'linear'
        """
        if months_available >= 12:
            return 'holt_winters'
        elif months_available >= 6:
            return 'arima'
        else:
            return 'linear'
    
    def holt_winters_forecast(
        self, 
        monthly_expenses: pd.Series,
        forecast_periods: int = 1,
        seasonal_periods: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast using Holt-Winters exponential smoothing.
        
        Args:
            monthly_expenses: Time series of monthly expenses
            forecast_periods: Number of periods to forecast
            seasonal_periods: Seasonal period length (default 12 for monthly data)
            
        Returns:
            Dictionary with forecasts and confidence intervals
        """
        try:
            # Ensure we have enough data for seasonal decomposition
            if len(monthly_expenses) < 2 * seasonal_periods:
                seasonal_periods = max(4, len(monthly_expenses) // 2)
            
            # Fit Holt-Winters model with additive seasonality
            model = ExponentialSmoothing(
                monthly_expenses,
                seasonal_periods=seasonal_periods,
                trend='add',
                seasonal='add',
                initialization_method='estimated'
            )
            
            fitted_model = model.fit(optimized=True)
            self.model = fitted_model
            self.model_type = 'holt_winters'
            
            # Generate forecast
            forecast = fitted_model.forecast(steps=forecast_periods)
            
            # Calculate confidence intervals (approximate using residuals)
            residuals = fitted_model.fittedvalues - monthly_expenses
            std_residual = np.std(residuals)
            
            ci_lower = forecast - 1.96 * std_residual
            ci_upper = forecast + 1.96 * std_residual
            
            return {
                'model_type': 'holt_winters',
                'forecast': forecast.tolist(),
                'confidence_interval_lower': ci_lower.tolist(),
                'confidence_interval_upper': ci_upper.tolist(),
                'confidence_level': 0.95
            }
            
        except Exception as e:
            # Fallback to ARIMA if Holt-Winters fails
            return self.arima_forecast(monthly_expenses, forecast_periods)
    
    def arima_forecast(
        self, 
        monthly_expenses: pd.Series,
        forecast_periods: int = 1
    ) -> Dict[str, Any]:
        """
        Forecast using ARIMA model.
        
        Args:
            monthly_expenses: Time series of monthly expenses
            forecast_periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecasts and confidence intervals
        """
        try:
            # Use auto-ARIMA to find best parameters
            # For simplicity, use ARIMA(1,1,1) as default
            order = (1, 1, 1)
            
            # Try common ARIMA configurations
            best_aic = np.inf
            best_order = order
            
            for p in range(0, 3):
                for d in range(0, 2):
                    for q in range(0, 3):
                        try:
                            temp_model = ARIMA(monthly_expenses, order=(p, d, q))
                            temp_fitted = temp_model.fit()
                            if temp_fitted.aic < best_aic:
                                best_aic = temp_fitted.aic
                                best_order = (p, d, q)
                        except:
                            continue
            
            # Fit best ARIMA model
            model = ARIMA(monthly_expenses, order=best_order)
            fitted_model = model.fit()
            self.model = fitted_model
            self.model_type = 'arima'
            
            # Generate forecast with confidence intervals
            forecast_result = fitted_model.forecast(steps=forecast_periods, alpha=0.05)
            
            if hasattr(forecast_result, 'predicted_mean'):
                forecast = forecast_result.predicted_mean
            else:
                forecast = forecast_result
            
            # Get confidence intervals
            forecast_df = fitted_model.get_forecast(steps=forecast_periods)
            ci = forecast_df.conf_int(alpha=0.05)
            
            return {
                'model_type': 'arima',
                'order': best_order,
                'forecast': forecast.tolist() if hasattr(forecast, 'tolist') else [forecast],
                'confidence_interval_lower': ci.iloc[:, 0].tolist(),
                'confidence_interval_upper': ci.iloc[:, 1].tolist(),
                'confidence_level': 0.95
            }
            
        except Exception as e:
            # Fallback to linear if ARIMA fails
            return self.fallback_linear_forecast(monthly_expenses, forecast_periods)
    
    def fallback_linear_forecast(
        self, 
        monthly_expenses: pd.Series,
        forecast_periods: int = 1
    ) -> Dict[str, Any]:
        """
        Simple linear regression fallback for limited data.
        
        Args:
            monthly_expenses: Time series of monthly expenses
            forecast_periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecasts and confidence intervals
        """
        # Use simple linear trend
        X = np.arange(len(monthly_expenses)).reshape(-1, 1)
        y = monthly_expenses.values
        
        # Calculate linear regression manually
        X_mean = X.mean()
        y_mean = y.mean()
        
        slope = np.sum((X.flatten() - X_mean) * (y - y_mean)) / np.sum((X.flatten() - X_mean) ** 2)
        intercept = y_mean - slope * X_mean
        
        self.model_type = 'linear'
        
        # Generate forecasts
        future_X = np.arange(len(monthly_expenses), len(monthly_expenses) + forecast_periods)
        forecasts = slope * future_X + intercept
        
        # Calculate confidence intervals using residual standard error
        y_pred = slope * X.flatten() + intercept
        residuals = y - y_pred
        std_error = np.std(residuals)
        
        ci_lower = forecasts - 1.96 * std_error
        ci_upper = forecasts + 1.96 * std_error
        
        return {
            'model_type': 'linear',
            'forecast': forecasts.tolist(),
            'confidence_interval_lower': ci_lower.tolist(),
            'confidence_interval_upper': ci_upper.tolist(),
            'confidence_level': 0.95
        }
    
    def forecast(
        self, 
        transactions: List[Dict[str, Any]],
        forecast_months: int = 1
    ) -> Dict[str, Any]:
        """
        Main forecast method that selects and applies the appropriate model.
        
        Args:
            transactions: List of transaction dictionaries
            forecast_months: Number of months to forecast ahead
            
        Returns:
            Dictionary with forecasts, model info, and confidence intervals
        """
        # Convert transactions to monthly expense series
        df = pd.DataFrame(transactions)
        
        if df.empty or 'date' not in df.columns or 'amount' not in df.columns:
            return {
                'error': 'Invalid transaction data',
                'forecast': [0] * forecast_months
            }
        
        # Filter for expenses only
        expense_df = df[df['type'].str.lower() == 'expense'].copy()
        
        if expense_df.empty:
            return {
                'error': 'No expense data available',
                'forecast': [0] * forecast_months
            }
        
        # Convert date to datetime
        expense_df['date'] = pd.to_datetime(expense_df['date'])
        
        # Group by month and sum expenses
        expense_df['year_month'] = expense_df['date'].dt.to_period('M')
        monthly_expenses = expense_df.groupby('year_month')['amount'].sum().sort_index()
        
        # Determine number of months available
        months_available = len(monthly_expenses)
        self.data_months = months_available
        
        if months_available < 3:
            return {
                'error': 'Insufficient data (minimum 3 months required)',
                'forecast': [monthly_expenses.mean()] * forecast_months if len(monthly_expenses) > 0 else [0] * forecast_months
            }
        
        # Select and apply model
        model_type = self.select_model(monthly_expenses, months_available)
        
        if model_type == 'holt_winters':
            result = self.holt_winters_forecast(monthly_expenses, forecast_months)
        elif model_type == 'arima':
            result = self.arima_forecast(monthly_expenses, forecast_months)
        else:
            result = self.fallback_linear_forecast(monthly_expenses, forecast_months)
        
        # Add metadata
        result['months_of_data'] = months_available
        result['last_month_expense'] = float(monthly_expenses.iloc[-1])
        result['average_monthly_expense'] = float(monthly_expenses.mean())
        result['trained_at'] = datetime.now().isoformat()
        
        self.last_trained = datetime.now()
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the currently fitted model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            'model_type': self.model_type,
            'data_months': self.data_months,
            'last_trained': self.last_trained.isoformat() if self.last_trained else None,
            'is_fitted': self.model is not None
        }


# Global instance
_forecaster = None


def get_advanced_forecaster() -> AdvancedExpenseForecaster:
    """Get or create the global advanced forecaster instance."""
    global _forecaster
    if _forecaster is None:
        _forecaster = AdvancedExpenseForecaster()
    return _forecaster
