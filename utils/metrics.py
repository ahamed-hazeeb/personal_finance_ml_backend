"""
Metrics and evaluation utilities for personal finance ML models.

This module provides functions for evaluating model performance,
calculating confidence intervals, and generating prediction reports.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prefix: str = ""
) -> Dict[str, float]:
    """
    Calculate standard regression metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        prefix: Prefix for metric names
        
    Returns:
        Dictionary of metrics
    """
    metrics = {
        f'{prefix}mae': mean_absolute_error(y_true, y_pred),
        f'{prefix}rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        f'{prefix}mape': calculate_mape(y_true, y_pred),
        f'{prefix}r2': r2_score(y_true, y_pred)
    }
    
    return metrics


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-10) -> float:
    """
    Calculate Mean Absolute Percentage Error.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        epsilon: Small value to avoid division by zero
        
    Returns:
        MAPE value
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / (y_true + epsilon))) * 100


def calculate_confidence_intervals(
    predictions: np.ndarray,
    residuals: np.ndarray,
    confidence_level: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate prediction confidence intervals based on residuals.
    
    Args:
        predictions: Model predictions
        residuals: Training residuals (y_true - y_pred)
        confidence_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    # Calculate standard error from residuals
    std_error = np.std(residuals)
    
    # Z-score for confidence level
    z_score = stats.norm.ppf((1 + confidence_level) / 2)
    
    # Calculate intervals
    margin = z_score * std_error
    lower_bound = predictions - margin
    upper_bound = predictions + margin
    
    return lower_bound, upper_bound


def evaluate_category_predictions(
    y_true: pd.DataFrame,
    y_pred: pd.DataFrame,
    category_columns: List[str]
) -> pd.DataFrame:
    """
    Evaluate predictions for each spending category.
    
    Args:
        y_true: True values for all categories
        y_pred: Predicted values for all categories
        category_columns: List of category column names
        
    Returns:
        DataFrame with metrics per category
    """
    results = []
    
    for category in category_columns:
        if category not in y_true.columns or category not in y_pred.columns:
            continue
            
        metrics = calculate_regression_metrics(
            y_true[category].values,
            y_pred[category].values
        )
        
        metrics['category'] = category
        results.append(metrics)
    
    return pd.DataFrame(results)


def detect_overspending_risk(
    predicted_expenses: pd.DataFrame,
    historical_avg: pd.DataFrame,
    threshold: float = 1.2
) -> Dict[str, Dict]:
    """
    Detect categories at risk of overspending.
    
    Args:
        predicted_expenses: Predicted expenses per category
        historical_avg: Historical average expenses per category
        threshold: Risk threshold (1.2 = 20% above average)
        
    Returns:
        Dictionary with overspending risk information per category
    """
    risk_report = {}
    
    for category in predicted_expenses.columns:
        if category in historical_avg.index:
            predicted = predicted_expenses[category].iloc[0]
            avg = historical_avg[category]
            ratio = predicted / (avg + 1e-10)
            
            risk_report[category] = {
                'predicted': predicted,
                'historical_avg': avg,
                'ratio': ratio,
                'at_risk': ratio >= threshold,
                'excess_amount': max(0, predicted - avg * threshold)
            }
    
    return risk_report


def generate_budget_recommendations(
    predicted_expenses: pd.DataFrame,
    historical_expenses: pd.DataFrame,
    total_budget: float,
    safety_margin: float = 0.1
) -> Dict[str, float]:
    """
    Generate optimal budget recommendations per category.
    
    Args:
        predicted_expenses: Predicted expenses per category
        historical_expenses: Historical expenses (for trend analysis)
        total_budget: Total available budget
        safety_margin: Safety margin percentage (default 10%)
        
    Returns:
        Dictionary with recommended budget per category
    """
    # Calculate historical averages and trends
    historical_avg = historical_expenses.mean()
    recent_avg = historical_expenses.iloc[-3:].mean()  # Last 3 months
    
    # Weight: 60% recent trend, 40% historical average
    base_allocation = 0.6 * recent_avg + 0.4 * historical_avg
    
    # Normalize to fit total budget with safety margin
    available_budget = total_budget * (1 - safety_margin)
    total_base = base_allocation.sum()
    
    recommendations = {}
    for category in base_allocation.index:
        recommended = (base_allocation[category] / total_base) * available_budget
        recommendations[category] = round(recommended, 2)
    
    # Add safety buffer
    recommendations['Emergency_Buffer'] = round(total_budget * safety_margin, 2)
    
    return recommendations


def calculate_savings_trajectory_metrics(
    projected_savings: List[float],
    confidence_intervals: List[Tuple[float, float]],
    current_savings: float
) -> Dict:
    """
    Calculate metrics for savings trajectory.
    
    Args:
        projected_savings: List of projected savings for future periods
        confidence_intervals: List of (lower, upper) bounds for each period
        current_savings: Current savings amount
        
    Returns:
        Dictionary with trajectory metrics
    """
    if not projected_savings:
        return {}
    
    metrics = {
        'current_savings': current_savings,
        'projected_3m': projected_savings[0] if len(projected_savings) > 0 else None,
        'projected_6m': projected_savings[1] if len(projected_savings) > 1 else None,
        'projected_12m': projected_savings[2] if len(projected_savings) > 2 else None,
        'total_growth': projected_savings[-1] - current_savings if projected_savings else 0,
        'growth_rate': ((projected_savings[-1] / current_savings) - 1) * 100 if current_savings > 0 else 0,
        'confidence_intervals': confidence_intervals
    }
    
    return metrics


def format_prediction_report(
    predictions: Dict,
    metrics: Dict = None,
    risk_analysis: Dict = None
) -> str:
    """
    Format prediction results into a readable report.
    
    Args:
        predictions: Dictionary with prediction results
        metrics: Optional dictionary with evaluation metrics
        risk_analysis: Optional dictionary with risk analysis
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("PERSONAL FINANCE PREDICTION REPORT")
    report.append("=" * 60)
    
    # Predictions
    if 'monthly_expense' in predictions:
        report.append("\n📊 Monthly Expense Forecast:")
        pred = predictions['monthly_expense']
        report.append(f"  Predicted: ${pred['predicted']:.2f}")
        if 'confidence_interval' in pred:
            ci = pred['confidence_interval']
            report.append(f"  95% CI: [${ci[0]:.2f}, ${ci[1]:.2f}]")
    
    if 'category_expenses' in predictions:
        report.append("\n📈 Category-wise Predictions:")
        for cat, amount in predictions['category_expenses'].items():
            report.append(f"  {cat}: ${amount:.2f}")
    
    if 'savings_trajectory' in predictions:
        report.append("\n💰 Savings Trajectory:")
        traj = predictions['savings_trajectory']
        for period, value in traj.items():
            report.append(f"  {period}: ${value:.2f}")
    
    # Risk Analysis
    if risk_analysis:
        report.append("\n⚠️  Overspending Risk Analysis:")
        at_risk = [cat for cat, info in risk_analysis.items() if info.get('at_risk', False)]
        if at_risk:
            report.append(f"  Categories at risk: {', '.join(at_risk)}")
            for cat in at_risk:
                excess = risk_analysis[cat]['excess_amount']
                report.append(f"    - {cat}: ${excess:.2f} over recommended budget")
        else:
            report.append("  No categories at risk of overspending")
    
    # Metrics
    if metrics:
        report.append("\n📉 Model Performance:")
        for metric_name, value in metrics.items():
            if isinstance(value, float):
                report.append(f"  {metric_name}: {value:.4f}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)
