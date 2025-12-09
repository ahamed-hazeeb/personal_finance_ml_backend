"""
Tests for financial health scorer.
"""
import pytest
from datetime import datetime, timedelta
from app.models.financial_health_scorer import FinancialHealthScorer


def generate_balanced_transactions(months: int = 6):
    """Generate balanced transactions (good financial health)."""
    transactions = []
    base_date = datetime.now() - timedelta(days=months * 30)
    
    for month in range(months):
        month_date = base_date + timedelta(days=month * 30)
        
        # Income: 5000/month
        transactions.append({
            'id': len(transactions) + 1,
            'user_id': 1,
            'date': month_date.strftime('%Y-%m-%d'),
            'amount': 5000,
            'type': 'income',
            'category': 'Salary',
            'description': 'Monthly salary'
        })
        
        # Consistent expenses: 3500/month
        for day in range(1, 8):
            transactions.append({
                'id': len(transactions) + 1,
                'user_id': 1,
                'date': (month_date + timedelta(days=day * 4)).strftime('%Y-%m-%d'),
                'amount': 500,
                'type': 'expense',
                'category': 'General',
                'description': f'Expense {day}'
            })
    
    return transactions


def test_scorer_initialization():
    """Test that scorer initializes correctly."""
    scorer = FinancialHealthScorer()
    assert scorer is not None
    assert scorer.HEALTH_SCORE_WEIGHTS['savings_rate'] == 0.30


def test_savings_rate_score_excellent():
    """Test savings rate scoring with excellent rate (30%+)."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_savings_rate_score(5000, 3000)
    
    assert score >= 90  # 40% savings rate should be excellent
    assert details['savings_rate'] == 40.0
    assert details['status'] == 'excellent'


def test_savings_rate_score_poor():
    """Test savings rate scoring with poor rate (<5%)."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_savings_rate_score(5000, 4900)
    
    assert score < 30  # 2% savings rate should be poor
    assert details['savings_rate'] == 2.0
    assert details['status'] in ['critical', 'needs_improvement']


def test_expense_consistency_excellent():
    """Test expense consistency with low variance."""
    scorer = FinancialHealthScorer()
    
    # Very consistent expenses
    monthly_expenses = [1000, 1020, 1010, 1015, 1005, 1012]
    score, details = scorer.calculate_expense_consistency_score(monthly_expenses)
    
    assert score >= 90  # Low CV should score high
    assert details['status'] == 'excellent'


def test_expense_consistency_poor():
    """Test expense consistency with high variance."""
    scorer = FinancialHealthScorer()
    
    # Highly variable expenses
    monthly_expenses = [500, 2000, 800, 1800, 600, 2200]
    score, details = scorer.calculate_expense_consistency_score(monthly_expenses)
    
    assert score < 70  # High CV should score lower
    assert details['status'] in ['fair', 'poor', 'very_poor']


def test_emergency_fund_score_excellent():
    """Test emergency fund with 6+ months coverage."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_emergency_fund_score(
        emergency_savings=30000,
        monthly_expenses=5000
    )
    
    assert score == 100  # 6 months coverage = perfect score
    assert details['months_covered'] == 6.0
    assert details['status'] == 'excellent'


def test_emergency_fund_score_critical():
    """Test emergency fund with minimal coverage."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_emergency_fund_score(
        emergency_savings=2000,
        monthly_expenses=5000
    )
    
    assert score < 50  # Less than 1 month coverage
    assert details['status'] in ['critical', 'needs_improvement']


def test_debt_to_income_score_excellent():
    """Test debt-to-income with low ratio."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_debt_to_income_score(
        monthly_debt_payment=500,
        monthly_income=10000
    )
    
    assert score >= 90  # 5% ratio is excellent
    assert details['debt_to_income_ratio'] == 5.0
    assert details['status'] == 'excellent'


def test_debt_to_income_score_critical():
    """Test debt-to-income with high ratio."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_debt_to_income_score(
        monthly_debt_payment=3000,
        monthly_income=5000
    )
    
    assert score < 50  # 60% ratio is critical
    assert details['status'] == 'critical'


def test_goal_progress_score_no_goals():
    """Test goal progress with no goals."""
    scorer = FinancialHealthScorer()
    
    score, details = scorer.calculate_goal_progress_score([])
    
    assert score == 50  # Neutral score for no goals
    assert details['status'] == 'no_goals'


def test_goal_progress_score_good():
    """Test goal progress with good progress."""
    scorer = FinancialHealthScorer()
    
    goals = [
        {
            'status': 'active',
            'current_amount': 30000,
            'target_amount': 50000  # 60% progress
        },
        {
            'status': 'active',
            'current_amount': 20000,
            'target_amount': 40000  # 50% progress
        }
    ]
    
    score, details = scorer.calculate_goal_progress_score(goals)
    
    assert score > 50  # Good progress
    assert details['active_goals'] == 2
    assert details['goals_on_track'] == 2


def test_overall_score_calculation():
    """Test overall score calculation with all components."""
    scorer = FinancialHealthScorer()
    
    transactions = generate_balanced_transactions(6)
    
    result = scorer.calculate_overall_score(
        transactions=transactions,
        emergency_savings=15000,  # 3 months
        monthly_debt_payment=500,  # 10% of income
        goals=[
            {
                'status': 'active',
                'current_amount': 25000,
                'target_amount': 50000
            }
        ]
    )
    
    assert 'overall_score' in result
    assert 0 <= result['overall_score'] <= 100
    assert 'grade' in result
    assert result['grade'] in ['A', 'B', 'C', 'D', 'F']
    assert 'component_scores' in result
    assert 'recommendations' in result


def test_overall_score_components():
    """Test that all component scores are present."""
    scorer = FinancialHealthScorer()
    
    transactions = generate_balanced_transactions(3)
    result = scorer.calculate_overall_score(transactions=transactions)
    
    components = result['component_scores']
    
    assert 'savings_rate' in components
    assert 'expense_consistency' in components
    assert 'emergency_fund' in components
    assert 'debt_to_income' in components
    assert 'goal_progress' in components
    
    # Each component should have score, weight, and details
    for component in components.values():
        assert 'score' in component
        assert 'weight' in component
        assert 'details' in component


def test_grade_assignment():
    """Test grade assignment based on score."""
    scorer = FinancialHealthScorer()
    
    assert scorer._get_grade(95) == 'A'
    assert scorer._get_grade(85) == 'B'
    assert scorer._get_grade(75) == 'C'
    assert scorer._get_grade(65) == 'D'
    assert scorer._get_grade(50) == 'F'


def test_recommendations_generation():
    """Test that recommendations are generated for low scores."""
    scorer = FinancialHealthScorer()
    
    # Create transactions with poor financial health
    transactions = []
    base_date = datetime.now() - timedelta(days=180)
    
    for month in range(6):
        month_date = base_date + timedelta(days=month * 30)
        
        # Income: 5000/month
        transactions.append({
            'id': len(transactions) + 1,
            'user_id': 1,
            'date': month_date.strftime('%Y-%m-%d'),
            'amount': 5000,
            'type': 'income',
            'category': 'Salary',
            'description': 'Monthly salary'
        })
        
        # High expenses: 4800/month (low savings)
        transactions.append({
            'id': len(transactions) + 1,
            'user_id': 1,
            'date': (month_date + timedelta(days=15)).strftime('%Y-%m-%d'),
            'amount': 4800,
            'type': 'expense',
            'category': 'General',
            'description': 'High expenses'
        })
    
    result = scorer.calculate_overall_score(
        transactions=transactions,
        emergency_savings=500,  # Very low
        monthly_debt_payment=1500  # High debt
    )
    
    recommendations = result['recommendations']
    
    assert len(recommendations) > 0
    
    # Should have recommendations for multiple issues
    categories = [r['category'] for r in recommendations]
    assert 'savings_rate' in categories or 'emergency_fund' in categories


def test_empty_transactions():
    """Test handling of empty transactions."""
    scorer = FinancialHealthScorer()
    
    result = scorer.calculate_overall_score(transactions=[])
    
    assert 'error' in result
    assert result['overall_score'] == 0


def test_insufficient_data():
    """Test handling of insufficient transaction data."""
    scorer = FinancialHealthScorer()
    
    # Only income, no expenses
    transactions = [
        {
            'id': 1,
            'user_id': 1,
            'date': '2024-01-01',
            'amount': 5000,
            'type': 'income',
            'category': 'Salary',
            'description': 'Salary'
        }
    ]
    
    result = scorer.calculate_overall_score(transactions=transactions)
    
    # Should handle gracefully
    assert 'error' in result or 'overall_score' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
