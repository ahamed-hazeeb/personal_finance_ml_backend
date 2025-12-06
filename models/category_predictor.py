"""
Category-wise spending prediction model.

This module provides a predictor for forecasting expenses per spending category
with risk detection and budget recommendations using MultiOutputRegressor.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from .base_predictor import BaseFinancePredictor


class CategorySpendingPredictor(BaseFinancePredictor):
    """
    Predictor for category-wise spending forecasting.
    
    Uses MultiOutputRegressor to predict expenses for multiple categories
    simultaneously, enabling cross-category pattern learning.
    """
    
    def __init__(
        self,
        category_columns: List[str] = None,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
        **kwargs
    ):
        """
        Initialize the category spending predictor.
        
        Args:
            category_columns: List of spending category column names
            n_estimators: Number of trees in the random forest
            max_depth: Maximum depth of trees
            random_state: Random seed for reproducibility
            **kwargs: Additional parameters for RandomForestRegressor
        """
        super().__init__(n_estimators, max_depth, random_state, **kwargs)
        self.category_columns = category_columns
    
    def _create_model(self) -> MultiOutputRegressor:
        """
        Create a MultiOutputRegressor instance.
        
        Returns:
            MultiOutputRegressor with RandomForestRegressor
        """
        base_estimator = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1,
            **self.model_params
        )
        return MultiOutputRegressor(base_estimator, n_jobs=-1)
    
    def prepare_data(
        self,
        monthly_df: pd.DataFrame,
        category_columns: List[str] = None
    ) -> tuple:
        """
        Prepare data for category-wise prediction.
        
        Args:
            monthly_df: DataFrame with monthly financial data
            category_columns: List of category columns to predict
            
        Returns:
            Tuple of (features_df, targets_df)
        """
        from utils.preprocessing import engineer_features
        
        if category_columns is None:
            if self.category_columns is None:
                # Auto-detect category columns
                exclude = ['year_month', 'total_income', 'total_expense', 'savings']
                category_columns = [col for col in monthly_df.columns if col not in exclude]
            else:
                category_columns = self.category_columns
        
        self.category_columns = category_columns
        
        # Create features
        df = monthly_df.copy()
        
        # Engineer features for each category
        feature_cols = category_columns + ['total_income', 'total_expense']
        df_engineered = engineer_features(
            df,
            target_columns=feature_cols,
            lag_periods=[1, 2, 3],
            rolling_windows=[3, 6]
        )
        
        # Drop rows with NaN
        df_engineered = df_engineered.dropna()
        
        # Select features (exclude original targets and date)
        exclude_cols = ['year_month'] + category_columns + ['total_income', 'total_expense', 'savings']
        feature_columns = [col for col in df_engineered.columns if col not in exclude_cols]
        
        X = df_engineered[feature_columns]
        y = df_engineered[category_columns]
        
        return X, y
    
    def forecast_categories(
        self,
        monthly_df: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> Dict[str, Dict[str, Any]]:
        """
        Forecast next month's expenses for all categories.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            confidence_level: Confidence level for prediction intervals
            
        Returns:
            Dictionary with forecasts per category
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before forecasting")
        
        # Prepare the last available data point
        X, _ = self.prepare_data(monthly_df)
        X_latest = X.iloc[[-1]]
        
        # Make prediction
        result = self.predict(X_latest, return_confidence_interval=True, confidence_level=confidence_level)
        
        predictions = result['predictions'][0]
        ci_lower, ci_upper = result['confidence_interval'][0][0], result['confidence_interval'][1][0]
        
        # Format results per category
        forecasts = {}
        for i, category in enumerate(self.category_columns):
            forecasts[category] = {
                'predicted': round(predictions[i], 2),
                'confidence_interval': (round(ci_lower[i], 2), round(ci_upper[i], 2))
            }
        
        return forecasts
    
    def detect_overspending_risks(
        self,
        monthly_df: pd.DataFrame,
        threshold: float = 1.2
    ) -> Dict[str, Dict]:
        """
        Detect categories at risk of overspending.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            threshold: Risk threshold (1.2 = 20% above historical average)
            
        Returns:
            Dictionary with risk analysis per category
        """
        from utils.metrics import detect_overspending_risk
        
        # Get category forecasts
        forecasts = self.forecast_categories(monthly_df)
        
        # Create DataFrame of predictions
        predicted_expenses = pd.DataFrame({
            cat: [info['predicted']] for cat, info in forecasts.items()
        })
        
        # Calculate historical averages
        historical_avg = monthly_df[self.category_columns].mean()
        
        # Detect risks
        risk_report = detect_overspending_risk(
            predicted_expenses,
            historical_avg,
            threshold
        )
        
        return risk_report
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get average feature importance across all category predictors.
        
        Returns:
            DataFrame with feature names and average importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before getting feature importance")
        
        # For MultiOutputRegressor, average importance across all estimators
        if hasattr(self.model, 'estimators_'):
            avg_importance = np.mean([est.feature_importances_ for est in self.model.estimators_], axis=0)
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': avg_importance
            }).sort_values('importance', ascending=False)
            return importance_df
        else:
            # Fallback to parent class implementation
            return super().get_feature_importance()
    
    def generate_budget_recommendations(
        self,
        monthly_df: pd.DataFrame,
        total_budget: float,
        safety_margin: float = 0.1
    ) -> Dict[str, float]:
        """
        Generate optimal budget recommendations per category.
        
        Args:
            monthly_df: DataFrame with historical monthly data
            total_budget: Total available monthly budget
            safety_margin: Safety margin percentage (default 10%)
            
        Returns:
            Dictionary with recommended budget per category
        """
        from utils.metrics import generate_budget_recommendations
        
        # Get forecasts
        forecasts = self.forecast_categories(monthly_df)
        predicted_expenses = pd.DataFrame({
            cat: [info['predicted']] for cat, info in forecasts.items()
        })
        
        # Historical expenses
        historical_expenses = monthly_df[self.category_columns]
        
        # Generate recommendations
        recommendations = generate_budget_recommendations(
            predicted_expenses,
            historical_expenses,
            total_budget,
            safety_margin
        )
        
        return recommendations
