"""
Base predictor class for personal finance ML models.

This module provides the base class with common functionality for all predictors,
including model training, evaluation, persistence, and prediction with confidence intervals.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
import joblib
import os


class BaseFinancePredictor:
    """
    Base class for personal finance predictors.
    
    Provides common functionality for training, evaluation, and prediction
    with confidence intervals. All specific predictors should inherit from this class.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
        **kwargs
    ):
        """
        Initialize the base predictor.
        
        Args:
            n_estimators: Number of trees in the random forest
            max_depth: Maximum depth of trees
            random_state: Random seed for reproducibility
            **kwargs: Additional parameters for RandomForestRegressor
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = None
        self.feature_names = None
        self.target_names = None
        self.training_residuals = None
        self.is_fitted = False
        self.model_params = kwargs
        
    def _create_model(self) -> RandomForestRegressor:
        """
        Create a RandomForestRegressor instance.
        
        Returns:
            RandomForestRegressor instance
        """
        return RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1,  # Use all available cores
            **self.model_params
        )
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train the model with optional validation.
        
        Args:
            X_train: Training features
            y_train: Training targets
            validation_split: Fraction of data to use for validation
            
        Returns:
            Dictionary with training metrics
        """
        # Store feature and target names
        self.feature_names = list(X_train.columns)
        if isinstance(y_train, pd.Series):
            self.target_names = [y_train.name]
            y_train = y_train.values.reshape(-1, 1)
        else:
            self.target_names = list(y_train.columns)
            y_train = y_train.values
        
        # Create and train model
        self.model = self._create_model()
        self.model.fit(X_train.values, y_train.ravel() if y_train.shape[1] == 1 else y_train)
        
        # Calculate training residuals for confidence intervals
        train_pred = self.model.predict(X_train.values)
        if y_train.shape[1] == 1:
            self.training_residuals = y_train.ravel() - train_pred
        else:
            self.training_residuals = y_train - train_pred
        
        self.is_fitted = True
        
        # Calculate training metrics
        from utils.metrics import calculate_regression_metrics
        
        if y_train.shape[1] == 1:
            metrics = calculate_regression_metrics(
                y_train.ravel(),
                train_pred,
                prefix='train_'
            )
        else:
            # For multi-output, calculate average metrics
            metrics = {}
            for i, target_name in enumerate(self.target_names):
                target_metrics = calculate_regression_metrics(
                    y_train[:, i],
                    train_pred[:, i],
                    prefix=f'train_{target_name}_'
                )
                metrics.update(target_metrics)
        
        return metrics
    
    def predict(
        self,
        X: pd.DataFrame,
        return_confidence_interval: bool = True,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Make predictions with optional confidence intervals.
        
        Args:
            X: Features for prediction
            return_confidence_interval: Whether to return confidence intervals
            confidence_level: Confidence level for intervals (default 0.95)
            
        Returns:
            Dictionary with predictions and optional confidence intervals
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before making predictions")
        
        # Ensure features match training
        if list(X.columns) != self.feature_names:
            X = X[self.feature_names]
        
        # Make predictions
        predictions = self.model.predict(X.values)
        
        result = {'predictions': predictions}
        
        # Calculate confidence intervals if requested
        if return_confidence_interval and self.training_residuals is not None:
            from utils.metrics import calculate_confidence_intervals
            
            if len(predictions.shape) == 1:
                lower, upper = calculate_confidence_intervals(
                    predictions,
                    self.training_residuals,
                    confidence_level
                )
            else:
                # For multi-output predictions
                lower = np.zeros_like(predictions)
                upper = np.zeros_like(predictions)
                for i in range(predictions.shape[1]):
                    lower[:, i], upper[:, i] = calculate_confidence_intervals(
                        predictions[:, i],
                        self.training_residuals[:, i],
                        confidence_level
                    )
            
            result['confidence_interval'] = (lower, upper)
        
        return result
    
    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Evaluate model performance on test data.
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary with evaluation metrics
        """
        from utils.metrics import calculate_regression_metrics
        
        # Make predictions
        pred_result = self.predict(X_test, return_confidence_interval=False)
        predictions = pred_result['predictions']
        
        # Calculate metrics
        if isinstance(y_test, pd.Series):
            y_test = y_test.values
        elif isinstance(y_test, pd.DataFrame):
            y_test = y_test.values
        
        if len(predictions.shape) == 1:
            metrics = calculate_regression_metrics(
                y_test.ravel(),
                predictions,
                prefix='test_'
            )
        else:
            # For multi-output, calculate metrics per target
            metrics = {}
            for i, target_name in enumerate(self.target_names):
                target_metrics = calculate_regression_metrics(
                    y_test[:, i],
                    predictions[:, i],
                    prefix=f'test_{target_name}_'
                )
                metrics.update(target_metrics)
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores.
        
        Returns:
            DataFrame with feature names and importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before getting feature importance")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save(self, filepath: str):
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path to save the model
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before saving")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'target_names': self.target_names,
            'training_residuals': self.training_residuals,
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'random_state': self.random_state,
            'model_params': self.model_params
        }
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to: {filepath}")
    
    def load(self, filepath: str):
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.target_names = model_data['target_names']
        self.training_residuals = model_data['training_residuals']
        self.n_estimators = model_data['n_estimators']
        self.max_depth = model_data['max_depth']
        self.random_state = model_data['random_state']
        self.model_params = model_data.get('model_params', {})
        self.is_fitted = True
        
        print(f"Model loaded from: {filepath}")
    
    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        n_splits: int = 3
    ) -> Dict[str, List[float]]:
        """
        Perform time-series cross-validation.
        
        Args:
            X: Features
            y: Targets
            n_splits: Number of splits for cross-validation
            
        Returns:
            Dictionary with cross-validation scores
        """
        from utils.metrics import calculate_regression_metrics
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        cv_scores = {
            'mae': [],
            'rmse': [],
            'mape': [],
            'r2': []
        }
        
        for train_idx, val_idx in tscv.split(X):
            X_train_cv = X.iloc[train_idx]
            X_val_cv = X.iloc[val_idx]
            y_train_cv = y.iloc[train_idx]
            y_val_cv = y.iloc[val_idx]
            
            # Train model
            temp_model = self._create_model()
            y_train_values = y_train_cv.values.ravel() if isinstance(y_train_cv, pd.Series) else y_train_cv.values
            temp_model.fit(X_train_cv.values, y_train_values)
            
            # Predict
            predictions = temp_model.predict(X_val_cv.values)
            y_val_values = y_val_cv.values.ravel() if isinstance(y_val_cv, pd.Series) else y_val_cv.values
            
            # Calculate metrics
            metrics = calculate_regression_metrics(y_val_values, predictions)
            cv_scores['mae'].append(metrics['mae'])
            cv_scores['rmse'].append(metrics['rmse'])
            cv_scores['mape'].append(metrics['mape'])
            cv_scores['r2'].append(metrics['r2'])
        
        return cv_scores
