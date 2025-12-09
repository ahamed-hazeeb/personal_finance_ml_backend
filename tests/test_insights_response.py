"""
Test insights response to ensure all required fields are present.

This test validates that the insight generator produces insights with all
required fields including 'type', 'message', and 'severity' for all insight types.
"""
import pytest
from datetime import datetime, timedelta
from app.services.insight_service import get_insight_service
from app.schemas.transactions import TransactionSchema


# Constants for validation
VALID_SEVERITIES = ["info", "warning", "alert"]
VALID_INSIGHT_TYPES = ["high_spending", "savings_opportunity", "anomaly", "trend"]
REQUIRED_INSIGHT_FIELDS = ["type", "message", "severity"]


def generate_synthetic_transactions_with_trends():
    """
    Generate synthetic transactions that will produce trend insights.
    
    Creates two periods of transactions with different spending patterns
    to trigger the trend detection logic.
    """
    transactions = []
    base_date = datetime.now() - timedelta(days=60)
    
    # First period (30 days ago): Lower spending in "Food" category
    for i in range(15):
        date = base_date + timedelta(days=i)
        transactions.append(
            TransactionSchema(
                id=i + 1,
                user_id=1,
                date=date.strftime("%Y-%m-%d"),
                amount=50.0,  # Lower amount
                type="expense",
                category="Food",
                description=f"Grocery shopping {i+1}"
            )
        )
    
    # Second period (recent 30 days): Higher spending in "Food" category (50% increase)
    for i in range(15):
        date = base_date + timedelta(days=30 + i)
        transactions.append(
            TransactionSchema(
                id=i + 16,
                user_id=1,
                date=date.strftime("%Y-%m-%d"),
                amount=75.0,  # Higher amount to trigger trend
                type="expense",
                category="Food",
                description=f"Grocery shopping {i+16}"
            )
        )
    
    # Add some income transactions
    for i in range(2):
        date = base_date + timedelta(days=i * 30)
        transactions.append(
            TransactionSchema(
                id=i + 31,
                user_id=1,
                date=date.strftime("%Y-%m-%d"),
                amount=2000.0,
                type="income",
                category="Salary",
                description=f"Monthly salary {i+1}"
            )
        )
    
    return transactions


def test_all_insights_have_required_fields():
    """
    Test that all insights have required fields: type, message, and severity.
    
    This is the main test to ensure the fix prevents ResponseValidationError.
    """
    # Get insight service
    service = get_insight_service()
    
    # Generate synthetic transactions that produce trend insights
    transactions = generate_synthetic_transactions_with_trends()
    
    # Generate insights
    result = service.generate_insights(transactions)
    
    # Assert result structure
    assert result is not None
    assert "success" in result
    assert result["success"] is True
    assert "insights" in result
    assert isinstance(result["insights"], list)
    
    # Ensure we have insights to test
    insights = result["insights"]
    assert len(insights) > 0, "Should generate at least one insight"
    
    # Check each insight for required fields
    for i, insight in enumerate(insights):
        for field in REQUIRED_INSIGHT_FIELDS:
            assert field in insight, f"Insight {i} missing required field '{field}': {insight}"
            assert insight[field] is not None, f"Insight {i} field '{field}' is None: {insight}"
            assert insight[field] != "", f"Insight {i} field '{field}' is empty: {insight}"
        
        # Validate severity is one of the expected values
        assert insight["severity"] in VALID_SEVERITIES, \
            f"Insight {i} has invalid severity '{insight['severity']}', expected one of {VALID_SEVERITIES}"
        
        # Validate type is one of the expected values
        assert insight["type"] in VALID_INSIGHT_TYPES, \
            f"Insight {i} has invalid type '{insight['type']}', expected one of {VALID_INSIGHT_TYPES}"


def test_trend_insights_have_severity():
    """
    Specifically test that trend insights include the severity field.
    
    This was the original bug - trend insights were missing severity.
    """
    # Get insight service
    service = get_insight_service()
    
    # Generate transactions that will produce trend insights
    transactions = generate_synthetic_transactions_with_trends()
    
    # Generate insights
    result = service.generate_insights(transactions)
    
    # Find trend insights
    trend_insights = [i for i in result["insights"] if i.get("type") == "trend"]
    
    # We should have at least one trend insight with our synthetic data
    assert len(trend_insights) > 0, "Should generate at least one trend insight"
    
    # Check each trend insight has severity
    for trend in trend_insights:
        assert "severity" in trend, f"Trend insight missing severity field: {trend}"
        assert trend["severity"] is not None, f"Trend insight severity is None: {trend}"
        assert trend["severity"] != "", f"Trend insight severity is empty: {trend}"
        assert trend["severity"] == "info", f"Trend insight should have 'info' severity, got '{trend['severity']}'"


def test_other_insight_types_have_severity():
    """
    Test that other insight types also have severity field.
    
    Ensures we didn't break existing insights while fixing trend insights.
    """
    # Get insight service
    service = get_insight_service()
    
    # Generate synthetic transactions for various insight types
    transactions = []
    base_date = datetime.now() - timedelta(days=30)
    
    # High spending in one category (should trigger high_spending insight)
    for i in range(20):
        date = base_date + timedelta(days=i)
        transactions.append(
            TransactionSchema(
                id=i + 1,
                user_id=1,
                date=date.strftime("%Y-%m-%d"),
                amount=500.0,  # High amount
                type="expense",
                category="Entertainment",
                description=f"Entertainment expense {i+1}"
            )
        )
    
    # Add minimal spending in other categories
    for i in range(5):
        date = base_date + timedelta(days=i)
        transactions.append(
            TransactionSchema(
                id=i + 21,
                user_id=1,
                date=date.strftime("%Y-%m-%d"),
                amount=20.0,
                type="expense",
                category="Transport",
                description=f"Transport expense {i+1}"
            )
        )
    
    # Add income
    transactions.append(
        TransactionSchema(
            id=26,
            user_id=1,
            date=base_date.strftime("%Y-%m-%d"),
            amount=1000.0,
            type="income",
            category="Salary",
            description="Monthly salary"
        )
    )
    
    # Generate insights
    result = service.generate_insights(transactions)
    
    # Check all insights have severity
    for insight in result["insights"]:
        assert "severity" in insight, f"Insight missing severity: {insight}"
        assert insight["severity"] in VALID_SEVERITIES, \
            f"Invalid severity value: {insight['severity']}"
        
        # Verify expected severity based on type
        if insight["type"] == "high_spending":
            assert insight["severity"] == "warning", \
                f"high_spending should have 'warning' severity, got '{insight['severity']}'"
        elif insight["type"] == "anomaly":
            assert insight["severity"] == "alert", \
                f"anomaly should have 'alert' severity, got '{insight['severity']}'"
        elif insight["type"] in ["savings_opportunity", "trend"]:
            assert insight["severity"] == "info", \
                f"{insight['type']} should have 'info' severity, got '{insight['severity']}'"


def test_empty_transactions_returns_valid_structure():
    """
    Test that even with empty transactions, the response has valid structure.
    """
    service = get_insight_service()
    
    # Generate insights with empty list
    result = service.generate_insights([])
    
    # Should still return valid structure
    assert result["success"] is True
    assert isinstance(result["insights"], list)
    assert len(result["insights"]) == 0
    
    # Other fields should be present
    assert "spending_patterns" in result
    assert "predictions" in result
    assert "recommendations" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
