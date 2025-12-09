"""
Smart budget optimizer with 50/30/20 rule.

Implements personalized budgeting based on:
- Historical spending patterns
- Income analysis
- Active financial goals
- Real-time overspending detection
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class BudgetOptimizer:
    """
    Smart budget optimizer using 50/30/20 rule with personalization.
    
    Default allocation:
    - 50% Needs (essential expenses)
    - 30% Wants (discretionary)
    - 20% Savings (financial goals)
    """
    
    # Category classifications
    NEEDS_CATEGORIES = [
        'Rent', 'Mortgage', 'Utilities', 'Groceries', 'Healthcare', 
        'Insurance', 'Transportation', 'Loan Payment', 'Education'
    ]
    
    WANTS_CATEGORIES = [
        'Entertainment', 'Dining Out', 'Shopping', 'Travel', 'Hobbies',
        'Food Delivery', 'Subscriptions', 'Fitness', 'Personal Care'
    ]
    
    # Default budget ratios
    DEFAULT_NEEDS_RATIO = 0.50
    DEFAULT_WANTS_RATIO = 0.30
    DEFAULT_SAVINGS_RATIO = 0.20
    
    def __init__(self):
        """Initialize the budget optimizer."""
        pass
    
    def classify_category(self, category: str) -> str:
        """
        Classify a category as 'needs', 'wants', or 'savings'.
        
        Args:
            category: Category name
            
        Returns:
            Classification: 'needs', 'wants', or 'savings'
        """
        category_upper = category.upper() if category else ''
        
        for needs_cat in self.NEEDS_CATEGORIES:
            if needs_cat.upper() in category_upper:
                return 'needs'
        
        for wants_cat in self.WANTS_CATEGORIES:
            if wants_cat.upper() in category_upper:
                return 'wants'
        
        if 'SAVING' in category_upper or 'INVESTMENT' in category_upper:
            return 'savings'
        
        # Default to needs for unclassified essential-sounding categories
        return 'needs'
    
    def analyze_spending_patterns(
        self, 
        transactions: List[Dict[str, Any]],
        months: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze historical spending patterns.
        
        Args:
            transactions: List of transaction dictionaries
            months: Number of recent months to analyze
            
        Returns:
            Dictionary with spending analysis
        """
        if not transactions:
            return {
                'total_needs': 0,
                'total_wants': 0,
                'total_savings': 0,
                'category_breakdown': {},
                'months_analyzed': 0
            }
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to recent months
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        df = df[df['date'] >= cutoff_date]
        
        # Classify expenses
        expenses_df = df[df['type'].str.lower() == 'expense'].copy()
        
        if expenses_df.empty:
            return {
                'total_needs': 0,
                'total_wants': 0,
                'total_savings': 0,
                'category_breakdown': {},
                'months_analyzed': 0
            }
        
        expenses_df['classification'] = expenses_df['category'].apply(
            self.classify_category
        )
        
        # Calculate totals
        total_needs = expenses_df[expenses_df['classification'] == 'needs']['amount'].sum()
        total_wants = expenses_df[expenses_df['classification'] == 'wants']['amount'].sum()
        
        # Savings from transactions
        savings_df = df[df['type'].str.lower() == 'savings']
        total_savings = savings_df['amount'].sum() if not savings_df.empty else 0
        
        # Category breakdown
        category_breakdown = {}
        for category in expenses_df['category'].unique():
            cat_df = expenses_df[expenses_df['category'] == category]
            category_breakdown[category] = {
                'total': float(cat_df['amount'].sum()),
                'average_monthly': float(cat_df['amount'].sum() / max(1, months)),
                'classification': self.classify_category(category),
                'transaction_count': len(cat_df),
                'variance': float(cat_df.groupby(pd.Grouper(key='date', freq='M'))['amount'].sum().std())
            }
        
        return {
            'total_needs': round(total_needs, 2),
            'total_wants': round(total_wants, 2),
            'total_savings': round(total_savings, 2),
            'category_breakdown': category_breakdown,
            'months_analyzed': months
        }
    
    def calculate_income(
        self, 
        transactions: List[Dict[str, Any]],
        months: int = 3
    ) -> float:
        """
        Calculate average monthly income.
        
        Args:
            transactions: List of transaction dictionaries
            months: Number of recent months to analyze
            
        Returns:
            Average monthly income
        """
        if not transactions:
            return 0
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to recent months
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        df = df[df['date'] >= cutoff_date]
        
        income_df = df[df['type'].str.lower() == 'income']
        
        if income_df.empty:
            return 0
        
        total_income = income_df['amount'].sum()
        return round(total_income / max(1, months), 2)
    
    def generate_budget_recommendations(
        self,
        transactions: List[Dict[str, Any]],
        goals: Optional[List[Dict[str, Any]]] = None,
        analysis_months: int = 3
    ) -> Dict[str, Any]:
        """
        Generate personalized budget recommendations.
        
        Args:
            transactions: List of transaction dictionaries
            goals: List of financial goals
            analysis_months: Months of history to analyze
            
        Returns:
            Dictionary with budget recommendations
        """
        # Analyze current spending
        spending_analysis = self.analyze_spending_patterns(transactions, analysis_months)
        monthly_income = self.calculate_income(transactions, analysis_months)
        
        if monthly_income <= 0:
            return {
                'error': 'Unable to determine income',
                'recommendations': []
            }
        
        # Calculate baseline 50/30/20 budget
        baseline_needs = monthly_income * self.DEFAULT_NEEDS_RATIO
        baseline_wants = monthly_income * self.DEFAULT_WANTS_RATIO
        baseline_savings = monthly_income * self.DEFAULT_SAVINGS_RATIO
        
        # Adjust for goals
        required_savings = baseline_savings
        if goals:
            goal_savings = self._calculate_goal_requirements(goals, monthly_income)
            required_savings = max(baseline_savings, goal_savings)
        
        # Adjust wants/needs if savings requirement increased
        if required_savings > baseline_savings:
            difference = required_savings - baseline_savings
            # Reduce wants first, then needs if necessary
            adjusted_wants = max(baseline_wants - difference, monthly_income * 0.15)
            
            if adjusted_wants < baseline_wants:
                adjusted_needs = baseline_needs
            else:
                remaining_diff = difference - (baseline_wants - adjusted_wants)
                adjusted_needs = baseline_needs - remaining_diff
            
            baseline_wants = adjusted_wants
            baseline_needs = adjusted_needs
            baseline_savings = required_savings
        
        # Current spending vs recommended
        current_needs = spending_analysis['total_needs'] / analysis_months
        current_wants = spending_analysis['total_wants'] / analysis_months
        current_savings = spending_analysis['total_savings'] / analysis_months
        
        # Generate category-specific recommendations
        category_recommendations = []
        for category, data in spending_analysis['category_breakdown'].items():
            avg_monthly = data['average_monthly']
            classification = data['classification']
            
            # High variance indicates leakage
            if data['variance'] > avg_monthly * 0.5 and avg_monthly > 100:
                category_recommendations.append({
                    'category': category,
                    'type': 'leakage',
                    'message': f"High variance in {category} spending. Consider setting a fixed budget.",
                    'current_amount': round(avg_monthly, 2),
                    'variance': round(data['variance'], 2)
                })
            
            # Overspending in wants
            if classification == 'wants' and avg_monthly > baseline_wants * 0.3:
                reduction_amount = avg_monthly * 0.2  # Suggest 20% reduction
                category_recommendations.append({
                    'category': category,
                    'type': 'reduction',
                    'message': f"Consider reducing {category} spending by 20%.",
                    'current_amount': round(avg_monthly, 2),
                    'recommended_amount': round(avg_monthly - reduction_amount, 2),
                    'potential_savings': round(reduction_amount, 2)
                })
        
        return {
            'monthly_income': monthly_income,
            'recommended_budget': {
                'needs': round(baseline_needs, 2),
                'wants': round(baseline_wants, 2),
                'savings': round(baseline_savings, 2),
                'needs_percentage': round((baseline_needs / monthly_income) * 100, 1),
                'wants_percentage': round((baseline_wants / monthly_income) * 100, 1),
                'savings_percentage': round((baseline_savings / monthly_income) * 100, 1)
            },
            'current_spending': {
                'needs': round(current_needs, 2),
                'wants': round(current_wants, 2),
                'savings': round(current_savings, 2),
                'needs_percentage': round((current_needs / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                'wants_percentage': round((current_wants / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                'savings_percentage': round((current_savings / monthly_income) * 100, 1) if monthly_income > 0 else 0
            },
            'adjustments_needed': {
                'needs': round(baseline_needs - current_needs, 2),
                'wants': round(baseline_wants - current_wants, 2),
                'savings': round(baseline_savings - current_savings, 2)
            },
            'category_recommendations': category_recommendations[:10],  # Top 10
            'calculated_at': datetime.now().isoformat()
        }
    
    def detect_overspending_alerts(
        self,
        transactions: List[Dict[str, Any]],
        budget: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Detect real-time overspending against budget.
        
        Args:
            transactions: List of transaction dictionaries
            budget: Budget dictionary with 'needs', 'wants', 'savings'
            
        Returns:
            List of overspending alerts
        """
        alerts = []
        
        if not transactions:
            return alerts
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Current month transactions
        current_month_start = datetime.now().replace(day=1)
        current_month_df = df[df['date'] >= current_month_start]
        
        if current_month_df.empty:
            return alerts
        
        # Classify and sum current month spending
        expenses_df = current_month_df[current_month_df['type'].str.lower() == 'expense'].copy()
        
        if expenses_df.empty:
            return alerts
        
        expenses_df['classification'] = expenses_df['category'].apply(
            self.classify_category
        )
        
        current_needs = expenses_df[expenses_df['classification'] == 'needs']['amount'].sum()
        current_wants = expenses_df[expenses_df['classification'] == 'wants']['amount'].sum()
        
        # Check against budget
        needs_budget = budget.get('needs', 0)
        wants_budget = budget.get('wants', 0)
        
        # Calculate days into month
        days_in_month = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_in_month = days_in_month.day
        current_day = datetime.now().day
        days_remaining = days_in_month - current_day
        
        # Projected spending
        if current_day > 0:
            daily_needs_rate = current_needs / current_day
            daily_wants_rate = current_wants / current_day
            
            projected_needs = current_needs + (daily_needs_rate * days_remaining)
            projected_wants = current_wants + (daily_wants_rate * days_remaining)
            
            # Generate alerts
            if projected_needs > needs_budget:
                overage_pct = ((projected_needs - needs_budget) / needs_budget) * 100
                alerts.append({
                    'type': 'projected_overspending',
                    'category': 'needs',
                    'severity': 'warning',
                    'message': f"At current rate, you'll exceed Needs budget by {overage_pct:.0f}% ({projected_needs - needs_budget:.0f} Rs.)",
                    'current_spending': round(current_needs, 2),
                    'projected_spending': round(projected_needs, 2),
                    'budget': needs_budget,
                    'days_remaining': days_remaining
                })
            
            if projected_wants > wants_budget:
                overage_pct = ((projected_wants - wants_budget) / wants_budget) * 100
                alerts.append({
                    'type': 'projected_overspending',
                    'category': 'wants',
                    'severity': 'warning',
                    'message': f"At current rate, you'll exceed Wants budget by {overage_pct:.0f}% ({projected_wants - wants_budget:.0f} Rs.)",
                    'current_spending': round(current_wants, 2),
                    'projected_spending': round(projected_wants, 2),
                    'budget': wants_budget,
                    'days_remaining': days_remaining
                })
        
        # Already exceeded
        if current_needs > needs_budget:
            alerts.append({
                'type': 'exceeded',
                'category': 'needs',
                'severity': 'alert',
                'message': f"You've exceeded your Needs budget by {current_needs - needs_budget:.0f} Rs.",
                'current_spending': round(current_needs, 2),
                'budget': needs_budget
            })
        
        if current_wants > wants_budget:
            alerts.append({
                'type': 'exceeded',
                'category': 'wants',
                'severity': 'alert',
                'message': f"You've exceeded your Wants budget by {current_wants - wants_budget:.0f} Rs.",
                'current_spending': round(current_wants, 2),
                'budget': wants_budget
            })
        
        return alerts
    
    def optimize_budget(
        self,
        transactions: List[Dict[str, Any]],
        target_savings_rate: float = 0.20
    ) -> Dict[str, Any]:
        """
        Provide optimization suggestions to reach target savings rate.
        
        Args:
            transactions: List of transaction dictionaries
            target_savings_rate: Target savings rate (0-1)
            
        Returns:
            Dictionary with optimization suggestions
        """
        spending_analysis = self.analyze_spending_patterns(transactions)
        monthly_income = self.calculate_income(transactions)
        
        if monthly_income <= 0:
            return {'error': 'Unable to determine income'}
        
        current_total = (
            spending_analysis['total_needs'] + 
            spending_analysis['total_wants']
        ) / spending_analysis['months_analyzed']
        
        current_savings = spending_analysis['total_savings'] / spending_analysis['months_analyzed']
        current_savings_rate = current_savings / monthly_income if monthly_income > 0 else 0
        
        target_savings = monthly_income * target_savings_rate
        savings_gap = target_savings - current_savings
        
        if savings_gap <= 0:
            return {
                'status': 'target_met',
                'message': f"You're already saving {current_savings_rate * 100:.1f}%, which meets or exceeds the target of {target_savings_rate * 100:.0f}%.",
                'current_savings_rate': round(current_savings_rate * 100, 2)
            }
        
        # Find optimization opportunities
        opportunities = []
        
        # Sort categories by potential savings (high spend + high variance)
        category_list = []
        for category, data in spending_analysis['category_breakdown'].items():
            if data['classification'] == 'wants':
                score = data['average_monthly'] * (1 + data['variance'] / data['average_monthly'])
                category_list.append({
                    'category': category,
                    'current_spend': data['average_monthly'],
                    'score': score
                })
        
        category_list.sort(key=lambda x: x['score'], reverse=True)
        
        remaining_gap = savings_gap
        for cat_data in category_list[:5]:  # Top 5 opportunities
            if remaining_gap <= 0:
                break
            
            # Suggest 30% reduction
            reduction = min(cat_data['current_spend'] * 0.3, remaining_gap)
            opportunities.append({
                'category': cat_data['category'],
                'current_spending': round(cat_data['current_spend'], 2),
                'suggested_reduction': round(reduction, 2),
                'new_budget': round(cat_data['current_spend'] - reduction, 2)
            })
            remaining_gap -= reduction
        
        return {
            'current_savings_rate': round(current_savings_rate * 100, 2),
            'target_savings_rate': round(target_savings_rate * 100, 2),
            'monthly_savings_gap': round(savings_gap, 2),
            'optimization_opportunities': opportunities,
            'projected_savings_rate': round(
                ((current_savings + sum(o['suggested_reduction'] for o in opportunities)) / monthly_income) * 100, 
                2
            )
        }
    
    def _calculate_goal_requirements(
        self, 
        goals: List[Dict[str, Any]],
        monthly_income: float
    ) -> float:
        """Calculate monthly savings required for goals."""
        total_required = 0
        
        for goal in goals:
            if goal.get('status', '').lower() != 'active':
                continue
            
            target = goal.get('target_amount', 0)
            current = goal.get('current_amount', 0)
            remaining = target - current
            
            # Assume 12 months if no target date
            monthly_contribution = goal.get('monthly_contribution')
            if monthly_contribution:
                total_required += monthly_contribution
            else:
                # Assume 12-month timeframe
                total_required += remaining / 12
        
        # Cap at 40% of income (reasonable maximum)
        return min(total_required, monthly_income * 0.40)


# Global instance
_optimizer = None


def get_budget_optimizer() -> BudgetOptimizer:
    """Get or create the global budget optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = BudgetOptimizer()
    return _optimizer
