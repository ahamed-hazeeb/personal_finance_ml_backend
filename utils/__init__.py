"""
Utility functions for personal finance ML models.
"""

from .preprocessing import (
    create_time_features,
    create_lag_features,
    create_rolling_features,
    create_growth_features,
    engineer_features,
    prepare_train_test_split,
    validate_data,
    normalize_features
)

from .metrics import (
    calculate_regression_metrics,
    calculate_mape,
    calculate_confidence_intervals,
    evaluate_category_predictions,
    detect_overspending_risk,
    generate_budget_recommendations,
    calculate_savings_trajectory_metrics,
    format_prediction_report
)

__all__ = [
    # Preprocessing
    'create_time_features',
    'create_lag_features',
    'create_rolling_features',
    'create_growth_features',
    'engineer_features',
    'prepare_train_test_split',
    'validate_data',
    'normalize_features',
    # Metrics
    'calculate_regression_metrics',
    'calculate_mape',
    'calculate_confidence_intervals',
    'evaluate_category_predictions',
    'detect_overspending_risk',
    'generate_budget_recommendations',
    'calculate_savings_trajectory_metrics',
    'format_prediction_report'
]
