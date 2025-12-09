"""
Financial health scoring system (0-100).

Calculates comprehensive financial health score based on:
- Savings rate (30%)
- Expense consistency (25%)
- Emergency fund (20%)
- Debt to income ratio (15%)
- Goal progress (10%)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class FinancialHealthScorer:
    """
    Calculate and track financial health scores.
    
    Components with weights:
    - Savings rate: 30%
    - Expense consistency: 25%
    - Emergency fund: 20%
    - Debt to income: 15%
    - Goal progress: 10%
    """
    
    # Weight configuration
    HEALTH_SCORE_WEIGHTS = {
        'savings_rate': 0.30,
        'expense_consistency': 0.25,
        'emergency_fund': 0.20,
        'debt_to_income': 0.15,
        'goal_progress': 0.10
    }
    
    def __init__(self):
        """Initialize the financial health scorer."""
        pass
    
    def calculate_savings_rate_score(
        self, 
        total_income: float, 
        total_expenses: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate savings rate score (0-100).
        
        Scoring:
        - 0-5% savings: 0-30 points
        - 5-10%: 30-50 points
        - 10-20%: 50-70 points
        - 20-30%: 70-90 points
        - 30%+: 90-100 points
        
        Args:
            total_income: Total income amount
            total_expenses: Total expense amount
            
        Returns:
            Tuple of (score, details_dict)
        """
        if total_income <= 0:
            return 0, {'savings_rate': 0, 'status': 'insufficient_income'}
        
        savings = max(0, total_income - total_expenses)
        savings_rate = (savings / total_income) * 100
        
        # Calculate score based on savings rate
        if savings_rate >= 30:
            score = 100
        elif savings_rate >= 20:
            score = 70 + (savings_rate - 20) * 2  # 70-90 range
        elif savings_rate >= 10:
            score = 50 + (savings_rate - 10) * 2  # 50-70 range
        elif savings_rate >= 5:
            score = 30 + (savings_rate - 5) * 4  # 30-50 range
        else:
            score = savings_rate * 6  # 0-30 range
        
        details = {
            'savings_rate': round(savings_rate, 2),
            'monthly_savings': round(savings, 2),
            'score': round(score, 2),
            'status': self._get_savings_status(savings_rate)
        }
        
        return round(score, 2), details
    
    def calculate_expense_consistency_score(
        self, 
        monthly_expenses: List[float]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate expense consistency score (0-100).
        
        Lower variance = higher score (more predictable spending)
        
        Args:
            monthly_expenses: List of monthly expense amounts
            
        Returns:
            Tuple of (score, details_dict)
        """
        if not monthly_expenses or len(monthly_expenses) < 2:
            return 50, {'status': 'insufficient_data', 'score': 50}
        
        mean_expense = np.mean(monthly_expenses)
        std_expense = np.std(monthly_expenses)
        
        if mean_expense == 0:
            return 100, {'cv': 0, 'score': 100, 'status': 'excellent'}
        
        # Calculate coefficient of variation (CV)
        cv = (std_expense / mean_expense) * 100
        
        # Score based on CV
        # CV < 10%: Excellent (90-100 points)
        # CV 10-20%: Good (70-90 points)
        # CV 20-30%: Fair (50-70 points)
        # CV 30-50%: Poor (30-50 points)
        # CV > 50%: Very Poor (0-30 points)
        
        if cv < 10:
            score = 100 - cv
        elif cv < 20:
            score = 90 - (cv - 10) * 2
        elif cv < 30:
            score = 70 - (cv - 20) * 2
        elif cv < 50:
            score = 50 - (cv - 30) * 1
        else:
            score = max(0, 30 - (cv - 50) * 0.5)
        
        details = {
            'coefficient_of_variation': round(cv, 2),
            'mean_expense': round(mean_expense, 2),
            'std_deviation': round(std_expense, 2),
            'score': round(score, 2),
            'status': self._get_consistency_status(cv)
        }
        
        return round(score, 2), details
    
    def calculate_emergency_fund_score(
        self, 
        emergency_savings: float,
        monthly_expenses: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate emergency fund score (0-100).
        
        Target: 3-6 months of expenses
        
        Args:
            emergency_savings: Total emergency fund amount
            monthly_expenses: Average monthly expenses
            
        Returns:
            Tuple of (score, details_dict)
        """
        if monthly_expenses <= 0:
            return 0, {'months_covered': 0, 'score': 0, 'status': 'no_data'}
        
        months_covered = emergency_savings / monthly_expenses
        
        # Scoring
        # 0 months: 0 points
        # 1 month: 30 points
        # 2 months: 50 points
        # 3 months: 70 points
        # 4 months: 85 points
        # 5 months: 95 points
        # 6+ months: 100 points
        
        if months_covered >= 6:
            score = 100
        elif months_covered >= 5:
            score = 95 + (months_covered - 5) * 5
        elif months_covered >= 4:
            score = 85 + (months_covered - 4) * 10
        elif months_covered >= 3:
            score = 70 + (months_covered - 3) * 15
        elif months_covered >= 2:
            score = 50 + (months_covered - 2) * 20
        elif months_covered >= 1:
            score = 30 + (months_covered - 1) * 20
        else:
            score = months_covered * 30
        
        details = {
            'months_covered': round(months_covered, 2),
            'emergency_fund': round(emergency_savings, 2),
            'monthly_expenses': round(monthly_expenses, 2),
            'target_fund': round(monthly_expenses * 6, 2),
            'score': round(score, 2),
            'status': self._get_emergency_status(months_covered)
        }
        
        return round(score, 2), details
    
    def calculate_debt_to_income_score(
        self, 
        monthly_debt_payment: float,
        monthly_income: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate debt-to-income ratio score (0-100).
        
        Lower ratio = higher score
        
        Args:
            monthly_debt_payment: Total monthly debt payments
            monthly_income: Monthly income
            
        Returns:
            Tuple of (score, details_dict)
        """
        if monthly_income <= 0:
            return 0, {'debt_ratio': 0, 'score': 0, 'status': 'no_income'}
        
        debt_ratio = (monthly_debt_payment / monthly_income) * 100
        
        # Scoring
        # 0-10%: 90-100 points (excellent)
        # 10-20%: 70-90 points (good)
        # 20-35%: 50-70 points (fair)
        # 35-50%: 30-50 points (poor)
        # 50%+: 0-30 points (critical)
        
        if debt_ratio <= 10:
            score = 100 - debt_ratio
        elif debt_ratio <= 20:
            score = 90 - (debt_ratio - 10) * 2
        elif debt_ratio <= 35:
            score = 70 - (debt_ratio - 20) * 1.33
        elif debt_ratio <= 50:
            score = 50 - (debt_ratio - 35) * 1.33
        else:
            score = max(0, 30 - (debt_ratio - 50) * 0.6)
        
        details = {
            'debt_to_income_ratio': round(debt_ratio, 2),
            'monthly_debt': round(monthly_debt_payment, 2),
            'monthly_income': round(monthly_income, 2),
            'score': round(score, 2),
            'status': self._get_debt_status(debt_ratio)
        }
        
        return round(score, 2), details
    
    def calculate_goal_progress_score(
        self, 
        goals: List[Dict[str, Any]]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate goal progress score (0-100).
        
        Based on percentage of active goals on track
        
        Args:
            goals: List of goal dictionaries with progress info
            
        Returns:
            Tuple of (score, details_dict)
        """
        if not goals:
            return 50, {'active_goals': 0, 'score': 50, 'status': 'no_goals'}
        
        active_goals = [g for g in goals if g.get('status', '').lower() == 'active']
        
        if not active_goals:
            return 50, {'active_goals': 0, 'score': 50, 'status': 'no_active_goals'}
        
        # Calculate progress for each goal
        on_track_count = 0
        total_progress = 0
        
        for goal in active_goals:
            current = goal.get('current_amount', 0)
            target = goal.get('target_amount', 1)
            progress_pct = (current / target) * 100 if target > 0 else 0
            total_progress += progress_pct
            
            # Consider on track if progress > 25%
            if progress_pct > 25:
                on_track_count += 1
        
        avg_progress = total_progress / len(active_goals)
        on_track_ratio = on_track_count / len(active_goals)
        
        # Score based on average progress and on-track ratio
        score = (avg_progress * 0.6) + (on_track_ratio * 100 * 0.4)
        score = min(100, score)
        
        details = {
            'active_goals': len(active_goals),
            'goals_on_track': on_track_count,
            'average_progress': round(avg_progress, 2),
            'score': round(score, 2),
            'status': self._get_goal_status(avg_progress)
        }
        
        return round(score, 2), details
    
    def calculate_overall_score(
        self,
        transactions: List[Dict[str, Any]],
        emergency_savings: float = 0,
        monthly_debt_payment: float = 0,
        goals: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate overall financial health score.
        
        Args:
            transactions: List of transaction dictionaries
            emergency_savings: Emergency fund amount
            monthly_debt_payment: Monthly debt payment amount
            goals: List of financial goals
            
        Returns:
            Dictionary with overall score and component scores
        """
        if not transactions:
            return {
                'overall_score': 0,
                'error': 'No transaction data provided'
            }
        
        # Convert transactions to DataFrame
        df = pd.DataFrame(transactions)
        
        # Calculate monthly aggregates
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Income and expenses
        income_df = df[df['type'].str.lower() == 'income']
        expense_df = df[df['type'].str.lower() == 'expense']
        
        monthly_income = income_df.groupby('year_month')['amount'].sum()
        monthly_expenses = expense_df.groupby('year_month')['amount'].sum()
        
        if monthly_income.empty or monthly_expenses.empty:
            return {
                'overall_score': 0,
                'error': 'Insufficient income or expense data'
            }
        
        total_income = monthly_income.sum()
        total_expenses = monthly_expenses.sum()
        avg_monthly_income = monthly_income.mean()
        avg_monthly_expense = monthly_expenses.mean()
        
        # Calculate component scores
        savings_score, savings_details = self.calculate_savings_rate_score(
            total_income, total_expenses
        )
        
        consistency_score, consistency_details = self.calculate_expense_consistency_score(
            monthly_expenses.tolist()
        )
        
        emergency_score, emergency_details = self.calculate_emergency_fund_score(
            emergency_savings, avg_monthly_expense
        )
        
        debt_score, debt_details = self.calculate_debt_to_income_score(
            monthly_debt_payment, avg_monthly_income
        )
        
        goal_score, goal_details = self.calculate_goal_progress_score(
            goals or []
        )
        
        # Calculate weighted overall score
        overall_score = (
            savings_score * self.HEALTH_SCORE_WEIGHTS['savings_rate'] +
            consistency_score * self.HEALTH_SCORE_WEIGHTS['expense_consistency'] +
            emergency_score * self.HEALTH_SCORE_WEIGHTS['emergency_fund'] +
            debt_score * self.HEALTH_SCORE_WEIGHTS['debt_to_income'] +
            goal_score * self.HEALTH_SCORE_WEIGHTS['goal_progress']
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            savings_details, consistency_details, emergency_details,
            debt_details, goal_details
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'grade': self._get_grade(overall_score),
            'component_scores': {
                'savings_rate': {
                    'score': savings_score,
                    'weight': self.HEALTH_SCORE_WEIGHTS['savings_rate'],
                    'details': savings_details
                },
                'expense_consistency': {
                    'score': consistency_score,
                    'weight': self.HEALTH_SCORE_WEIGHTS['expense_consistency'],
                    'details': consistency_details
                },
                'emergency_fund': {
                    'score': emergency_score,
                    'weight': self.HEALTH_SCORE_WEIGHTS['emergency_fund'],
                    'details': emergency_details
                },
                'debt_to_income': {
                    'score': debt_score,
                    'weight': self.HEALTH_SCORE_WEIGHTS['debt_to_income'],
                    'details': debt_details
                },
                'goal_progress': {
                    'score': goal_score,
                    'weight': self.HEALTH_SCORE_WEIGHTS['goal_progress'],
                    'details': goal_details
                }
            },
            'recommendations': recommendations,
            'calculated_at': datetime.now().isoformat()
        }
    
    def _get_savings_status(self, savings_rate: float) -> str:
        """Get status label for savings rate."""
        if savings_rate >= 30:
            return 'excellent'
        elif savings_rate >= 20:
            return 'good'
        elif savings_rate >= 10:
            return 'fair'
        elif savings_rate >= 5:
            return 'needs_improvement'
        else:
            return 'critical'
    
    def _get_consistency_status(self, cv: float) -> str:
        """Get status label for expense consistency."""
        if cv < 10:
            return 'excellent'
        elif cv < 20:
            return 'good'
        elif cv < 30:
            return 'fair'
        elif cv < 50:
            return 'poor'
        else:
            return 'very_poor'
    
    def _get_emergency_status(self, months: float) -> str:
        """Get status label for emergency fund."""
        if months >= 6:
            return 'excellent'
        elif months >= 3:
            return 'good'
        elif months >= 2:
            return 'fair'
        elif months >= 1:
            return 'needs_improvement'
        else:
            return 'critical'
    
    def _get_debt_status(self, ratio: float) -> str:
        """Get status label for debt ratio."""
        if ratio <= 10:
            return 'excellent'
        elif ratio <= 20:
            return 'good'
        elif ratio <= 35:
            return 'fair'
        elif ratio <= 50:
            return 'poor'
        else:
            return 'critical'
    
    def _get_goal_status(self, progress: float) -> str:
        """Get status label for goal progress."""
        if progress >= 75:
            return 'excellent'
        elif progress >= 50:
            return 'good'
        elif progress >= 25:
            return 'fair'
        else:
            return 'needs_improvement'
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(
        self,
        savings_details: Dict[str, Any],
        consistency_details: Dict[str, Any],
        emergency_details: Dict[str, Any],
        debt_details: Dict[str, Any],
        goal_details: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on scores."""
        recommendations = []
        
        # Savings recommendations
        if savings_details.get('status') in ['needs_improvement', 'critical']:
            recommendations.append({
                'category': 'savings_rate',
                'priority': 'high',
                'message': f"Your savings rate is {savings_details.get('savings_rate', 0):.1f}%. Try to save at least 20% of your income."
            })
        
        # Consistency recommendations
        if consistency_details.get('status') in ['poor', 'very_poor']:
            recommendations.append({
                'category': 'expense_consistency',
                'priority': 'medium',
                'message': "Your spending varies significantly month-to-month. Create a budget to stabilize expenses."
            })
        
        # Emergency fund recommendations
        if emergency_details.get('status') in ['needs_improvement', 'critical']:
            months_needed = max(0, 6 - emergency_details.get('months_covered', 0))
            target_amount = emergency_details.get('target_fund', 0)
            recommendations.append({
                'category': 'emergency_fund',
                'priority': 'high',
                'message': f"Build your emergency fund to cover {months_needed:.1f} more months of expenses (target: Rs. {target_amount:,.0f})."
            })
        
        # Debt recommendations
        if debt_details.get('status') in ['poor', 'critical']:
            recommendations.append({
                'category': 'debt_to_income',
                'priority': 'high',
                'message': f"Your debt-to-income ratio is {debt_details.get('debt_to_income_ratio', 0):.1f}%. Consider debt reduction strategies."
            })
        
        # Goal recommendations
        if goal_details.get('status') == 'needs_improvement':
            recommendations.append({
                'category': 'goal_progress',
                'priority': 'medium',
                'message': "Review your financial goals and increase contributions to stay on track."
            })
        
        return recommendations


# Global instance
_scorer = None


def get_health_scorer() -> FinancialHealthScorer:
    """Get or create the global health scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = FinancialHealthScorer()
    return _scorer
