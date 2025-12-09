"""
Tests for advanced expense predictor.
"""
import pytest
from datetime import datetime, timedelta
from app.models.advanced_expense_predictor import AdvancedExpenseForecaster


def generate_test_transactions(months: int, base_amount: float = 1000.0):
    """Generate synthetic transaction data for testing."""
    transactions = []
    base_date = datetime.now() - timedelta(days=months * 30)
    
    for month in range(months):
        # Generate 10-15 transactions per month
        for day in range(1, 16):
            date = base_date + timedelta(days=month * 30 + day)
            
            # Add some variation and seasonal pattern
            seasonal_factor = 1.0 + 0.1 * (month % 12) / 12
            variation = base_amount * 0.2 * (0.5 - (day % 10) / 20)
            amount = base_amount * seasonal_factor + variation
            
            transactions.append({
                'id': len(transactions) + 1,
                'user_id': 1,
                'date': date.strftime('%Y-%m-%d'),
                'amount': round(amount, 2),
                'type': 'expense',
                'category': 'General',
                'description': f'Test expense {len(transactions) + 1}'
            })
    
    return transactions


def test_forecaster_initialization():
    """Test that forecaster initializes correctly."""
    forecaster = AdvancedExpenseForecaster()
    assert forecaster is not None
    assert forecaster.model is None
    assert forecaster.model_type is None


def test_model_selection_logic():
    """Test that correct model is selected based on data availability."""
    forecaster = AdvancedExpenseForecaster()
    
    # Mock series (actual data doesn't matter for selection logic)
    import pandas as pd
    mock_series = pd.Series([1000] * 15)
    
    # Test Holt-Winters selection (12+ months)
    model = forecaster.select_model(mock_series, 15)
    assert model == 'holt_winters'
    
    # Test ARIMA selection (6-11 months)
    model = forecaster.select_model(mock_series, 8)
    assert model == 'arima'
    
    # Test linear fallback (<6 months)
    model = forecaster.select_model(mock_series, 4)
    assert model == 'linear'


def test_forecast_with_insufficient_data():
    """Test forecast with insufficient data."""
    forecaster = AdvancedExpenseForecaster()
    
    # Only 2 months of data
    transactions = generate_test_transactions(2)
    result = forecaster.forecast(transactions, forecast_months=1)
    
    assert 'error' in result
    assert 'Insufficient data' in result['error']


def test_forecast_with_linear_model():
    """Test forecast using linear fallback (3-5 months)."""
    forecaster = AdvancedExpenseForecaster()
    
    # 4 months of data - should use linear model
    transactions = generate_test_transactions(4)
    result = forecaster.forecast(transactions, forecast_months=1)
    
    assert 'error' not in result
    assert result['model_type'] == 'linear'
    assert len(result['forecast']) == 1
    assert 'confidence_interval_lower' in result
    assert 'confidence_interval_upper' in result
    assert result['months_of_data'] == 4


def test_forecast_with_arima_model():
    """Test forecast using ARIMA model (6-11 months)."""
    forecaster = AdvancedExpenseForecaster()
    
    # 8 months of data - should use ARIMA
    transactions = generate_test_transactions(8)
    result = forecaster.forecast(transactions, forecast_months=2)
    
    assert 'error' not in result
    assert result['model_type'] in ['arima', 'linear']  # May fallback if ARIMA fails
    assert len(result['forecast']) == 2
    assert result['months_of_data'] == 8


def test_forecast_with_holt_winters():
    """Test forecast using Holt-Winters (12+ months)."""
    forecaster = AdvancedExpenseForecaster()
    
    # 15 months of data - should use Holt-Winters
    transactions = generate_test_transactions(15)
    result = forecaster.forecast(transactions, forecast_months=3)
    
    assert 'error' not in result
    assert result['model_type'] in ['holt_winters', 'arima', 'linear']  # May fallback
    assert len(result['forecast']) == 3
    assert result['months_of_data'] == 15


def test_forecast_metadata():
    """Test that forecast includes proper metadata."""
    forecaster = AdvancedExpenseForecaster()
    
    transactions = generate_test_transactions(6)
    result = forecaster.forecast(transactions, forecast_months=1)
    
    assert 'months_of_data' in result
    assert 'last_month_expense' in result
    assert 'average_monthly_expense' in result
    assert 'trained_at' in result
    assert 'confidence_level' in result


def test_confidence_intervals():
    """Test that confidence intervals are reasonable."""
    forecaster = AdvancedExpenseForecaster()
    
    transactions = generate_test_transactions(6, base_amount=1000.0)
    result = forecaster.forecast(transactions, forecast_months=1)
    
    assert len(result['confidence_interval_lower']) == 1
    assert len(result['confidence_interval_upper']) == 1
    
    # Lower bound should be less than forecast
    assert result['confidence_interval_lower'][0] < result['forecast'][0]
    
    # Upper bound should be greater than forecast
    assert result['confidence_interval_upper'][0] > result['forecast'][0]


def test_forecast_empty_transactions():
    """Test forecast with empty transactions."""
    forecaster = AdvancedExpenseForecaster()
    
    result = forecaster.forecast([], forecast_months=1)
    
    assert 'error' in result


def test_forecast_no_expenses():
    """Test forecast with no expense transactions."""
    forecaster = AdvancedExpenseForecaster()
    
    # Only income transactions
    transactions = [
        {
            'id': 1,
            'user_id': 1,
            'date': '2024-01-01',
            'amount': 5000,
            'type': 'income',
            'category': 'Salary',
            'description': 'Monthly salary'
        }
    ]
    
    result = forecaster.forecast(transactions, forecast_months=1)
    
    assert 'error' in result
    assert 'No expense data' in result['error']


def test_get_model_info():
    """Test model info retrieval."""
    forecaster = AdvancedExpenseForecaster()
    
    # Before training
    info = forecaster.get_model_info()
    assert info['is_fitted'] is False
    assert info['model_type'] is None
    
    # After training
    transactions = generate_test_transactions(6)
    forecaster.forecast(transactions, forecast_months=1)
    
    info = forecaster.get_model_info()
    assert info['is_fitted'] is True
    assert info['model_type'] in ['linear', 'arima', 'holt_winters']
    assert info['data_months'] == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
