"""
Training pipeline for personal finance ML models.

This script provides a complete training pipeline with feature engineering,
time-series cross-validation, model training, evaluation, and persistence.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import ExpenseForecaster, CategorySpendingPredictor, SavingsForecaster
from utils.preprocessing import engineer_features, prepare_train_test_split
from utils.metrics import (
    calculate_regression_metrics,
    evaluate_category_predictions,
    format_prediction_report
)


def load_data(data_path: str) -> pd.DataFrame:
    """
    Load monthly financial data from CSV.
    
    Args:
        data_path: Path to the CSV file
        
    Returns:
        DataFrame with monthly data
    """
    df = pd.read_csv(data_path)
    
    # Convert year_month to period if it's a string
    if 'year_month' in df.columns and df['year_month'].dtype == 'object':
        df['year_month'] = pd.to_datetime(df['year_month']).dt.to_period('M')
    
    return df


def train_expense_forecaster(
    monthly_df: pd.DataFrame,
    model_save_path: str = None,
    test_size: int = 3
) -> ExpenseForecaster:
    """
    Train the monthly expense forecasting model.
    
    Args:
        monthly_df: DataFrame with monthly financial data
        model_save_path: Path to save the trained model
        test_size: Number of months to use for testing
        
    Returns:
        Trained ExpenseForecaster
    """
    print("\n" + "="*60)
    print("TRAINING EXPENSE FORECASTER")
    print("="*60)
    
    # Initialize model
    model = ExpenseForecaster(n_estimators=100, max_depth=10, random_state=42)
    
    # Prepare data
    print("\nPreparing data...")
    X, y = model.prepare_data(monthly_df, target_column='total_expense')
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = prepare_train_test_split(
        pd.concat([X, y], axis=1),
        test_size=test_size,
        feature_columns=list(X.columns),
        target_columns=[y.name]
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Train model
    print("\nTraining model...")
    train_metrics = model.train(X_train, y_train)
    
    print("\nTraining Metrics:")
    for metric, value in train_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_metrics = model.evaluate(X_test, y_test)
    
    print("\nTest Metrics:")
    for metric, value in test_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Cross-validation
    print("\nPerforming cross-validation...")
    cv_scores = model.cross_validate(X, y, n_splits=3)
    
    print("\nCross-Validation Scores:")
    for metric, scores in cv_scores.items():
        print(f"  {metric}: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})")
    
    # Feature importance
    print("\nTop 10 Important Features:")
    importance_df = model.get_feature_importance()
    print(importance_df.head(10).to_string(index=False))
    
    # Save model
    if model_save_path:
        model.save(model_save_path)
    
    return model


def train_category_predictor(
    monthly_df: pd.DataFrame,
    model_save_path: str = None,
    test_size: int = 3
) -> CategorySpendingPredictor:
    """
    Train the category-wise spending prediction model.
    
    Args:
        monthly_df: DataFrame with monthly financial data
        model_save_path: Path to save the trained model
        test_size: Number of months to use for testing
        
    Returns:
        Trained CategorySpendingPredictor
    """
    print("\n" + "="*60)
    print("TRAINING CATEGORY SPENDING PREDICTOR")
    print("="*60)
    
    # Initialize model
    model = CategorySpendingPredictor(n_estimators=100, max_depth=10, random_state=42)
    
    # Prepare data
    print("\nPreparing data...")
    X, y = model.prepare_data(monthly_df)
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Categories: {list(y.columns)}")
    
    # Split data
    X_train, X_test, y_train, y_test = prepare_train_test_split(
        pd.concat([X, y], axis=1),
        test_size=test_size,
        feature_columns=list(X.columns),
        target_columns=list(y.columns)
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Train model
    print("\nTraining model...")
    train_metrics = model.train(X_train, y_train)
    
    print("\nTraining Metrics (sample):")
    sample_metrics = list(train_metrics.items())[:5]
    for metric, value in sample_metrics:
        print(f"  {metric}: {value:.4f}")
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_metrics = model.evaluate(X_test, y_test)
    
    print("\nTest Metrics (sample):")
    sample_metrics = list(test_metrics.items())[:5]
    for metric, value in sample_metrics:
        print(f"  {metric}: {value:.4f}")
    
    # Category-wise evaluation
    print("\nCategory-wise Performance:")
    pred_result = model.predict(X_test, return_confidence_interval=False)
    y_pred_df = pd.DataFrame(pred_result['predictions'], columns=model.category_columns)
    
    category_metrics = evaluate_category_predictions(
        y_test.reset_index(drop=True),
        y_pred_df,
        model.category_columns
    )
    print(category_metrics.to_string(index=False))
    
    # Feature importance (for first output)
    print("\nTop 10 Important Features (overall):")
    # For MultiOutputRegressor, we can get importance from individual estimators
    if hasattr(model.model, 'estimators_'):
        avg_importance = np.mean([est.feature_importances_ for est in model.model.estimators_], axis=0)
        importance_df = pd.DataFrame({
            'feature': model.feature_names,
            'importance': avg_importance
        }).sort_values('importance', ascending=False)
        print(importance_df.head(10).to_string(index=False))
    
    # Save model
    if model_save_path:
        model.save(model_save_path)
    
    return model


def train_savings_forecaster(
    monthly_df: pd.DataFrame,
    model_save_path: str = None,
    test_size: int = 3
) -> SavingsForecaster:
    """
    Train the savings trajectory forecasting model.
    
    Args:
        monthly_df: DataFrame with monthly financial data
        model_save_path: Path to save the trained model
        test_size: Number of months to use for testing
        
    Returns:
        Trained SavingsForecaster
    """
    print("\n" + "="*60)
    print("TRAINING SAVINGS FORECASTER")
    print("="*60)
    
    # Initialize model
    model = SavingsForecaster(n_estimators=100, max_depth=10, random_state=42)
    
    # Prepare data
    print("\nPreparing data...")
    X, y = model.prepare_data(monthly_df, target_column='savings')
    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = prepare_train_test_split(
        pd.concat([X, y], axis=1),
        test_size=test_size,
        feature_columns=list(X.columns),
        target_columns=[y.name]
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Train model
    print("\nTraining model...")
    train_metrics = model.train(X_train, y_train)
    
    print("\nTraining Metrics:")
    for metric, value in train_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_metrics = model.evaluate(X_test, y_test)
    
    print("\nTest Metrics:")
    for metric, value in test_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Cross-validation
    print("\nPerforming cross-validation...")
    cv_scores = model.cross_validate(X, y, n_splits=3)
    
    print("\nCross-Validation Scores:")
    for metric, scores in cv_scores.items():
        print(f"  {metric}: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})")
    
    # Feature importance
    print("\nTop 10 Important Features:")
    importance_df = model.get_feature_importance()
    print(importance_df.head(10).to_string(index=False))
    
    # Save model
    if model_save_path:
        model.save(model_save_path)
    
    return model


def main():
    """
    Main training pipeline execution.
    """
    parser = argparse.ArgumentParser(description='Train personal finance ML models')
    parser.add_argument(
        '--data',
        type=str,
        default='./data/sample_monthly_data.csv',
        help='Path to monthly data CSV file'
    )
    parser.add_argument(
        '--models-dir',
        type=str,
        default='./models/saved',
        help='Directory to save trained models'
    )
    parser.add_argument(
        '--test-size',
        type=int,
        default=3,
        help='Number of months to use for testing'
    )
    parser.add_argument(
        '--model-type',
        type=str,
        choices=['expense', 'category', 'savings', 'all'],
        default='all',
        help='Type of model to train'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PERSONAL FINANCE ML TRAINING PIPELINE")
    print("="*60)
    print(f"Data path: {args.data}")
    print(f"Models directory: {args.models_dir}")
    print(f"Test size: {args.test_size} months")
    print(f"Model type: {args.model_type}")
    
    # Create models directory
    os.makedirs(args.models_dir, exist_ok=True)
    
    # Load data
    print("\nLoading data...")
    monthly_df = load_data(args.data)
    print(f"Loaded {len(monthly_df)} months of data")
    print(f"Date range: {monthly_df['year_month'].min()} to {monthly_df['year_month'].max()}")
    
    # Train models
    if args.model_type in ['expense', 'all']:
        expense_model = train_expense_forecaster(
            monthly_df,
            model_save_path=f"{args.models_dir}/expense_forecaster.pkl",
            test_size=args.test_size
        )
    
    if args.model_type in ['category', 'all']:
        category_model = train_category_predictor(
            monthly_df,
            model_save_path=f"{args.models_dir}/category_predictor.pkl",
            test_size=args.test_size
        )
    
    if args.model_type in ['savings', 'all']:
        savings_model = train_savings_forecaster(
            monthly_df,
            model_save_path=f"{args.models_dir}/savings_forecaster.pkl",
            test_size=args.test_size
        )
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"\nModels saved to: {args.models_dir}")


if __name__ == "__main__":
    main()
