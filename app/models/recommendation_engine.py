"""
Personalized recommendation engine for financial insights.

Provides:
- Spending habit analysis
- Subscription detection
- Savings opportunities
- Behavior nudges
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class RecommendationEngine:
    """
    Personalized recommendation engine with habit-based insights.
    
    Features:
    - Frequency analysis
    - Subscription detection
    - Hidden fee identification
    - Behavior nudges
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        pass
    
    def analyze_spending_habits(
        self,
        transactions: List[Dict[str, Any]],
        analysis_months: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Analyze spending habits and patterns.
        
        Args:
            transactions: List of transaction dictionaries
            analysis_months: Months to analyze
            
        Returns:
            List of habit insights
        """
        habits = []
        
        if not transactions:
            return habits
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to analysis period
        cutoff_date = datetime.now() - timedelta(days=analysis_months * 30)
        df = df[df['date'] >= cutoff_date]
        
        expense_df = df[df['type'].str.lower() == 'expense'].copy()
        
        if expense_df.empty:
            return habits
        
        # Frequency analysis by category
        category_freq = expense_df.groupby('category').agg({
            'amount': ['count', 'sum', 'mean'],
            'date': ['min', 'max']
        })
        
        for category in category_freq.index:
            count = category_freq.loc[category, ('amount', 'count')]
            total = category_freq.loc[category, ('amount', 'sum')]
            avg_amount = category_freq.loc[category, ('amount', 'mean')]
            
            # Calculate frequency (transactions per week)
            min_date = category_freq.loc[category, ('date', 'min')]
            max_date = category_freq.loc[category, ('date', 'max')]
            days_span = (max_date - min_date).days + 1
            weeks = max(1, days_span / 7)
            frequency_per_week = count / weeks
            
            # High-frequency categories
            if frequency_per_week >= 2 and total > 100:
                habits.append({
                    'type': 'high_frequency',
                    'category': category,
                    'message': f"You spend on {category} {frequency_per_week:.1f} times per week, totaling Rs. {total:,.0f} over {analysis_months} months.",
                    'frequency_per_week': round(frequency_per_week, 2),
                    'total_amount': round(total, 2),
                    'average_transaction': round(avg_amount, 2),
                    'transaction_count': int(count)
                })
        
        # Detect specific patterns
        if not expense_df.empty:
            # Food delivery habit
            food_delivery = expense_df[
                expense_df['category'].str.contains('food|delivery|restaurant|dining', case=False, na=False)
            ]
            if len(food_delivery) > 5:
                weeks_analyzed = analysis_months * 4
                freq = len(food_delivery) / weeks_analyzed
                total_cost = food_delivery['amount'].sum()
                
                habits.append({
                    'type': 'food_delivery',
                    'category': 'Food Delivery',
                    'message': f"You order food {freq:.1f} times per week, costing Rs. {total_cost:,.0f} over {analysis_months} months. Cooking at home could save 50-70%.",
                    'frequency_per_week': round(freq, 2),
                    'total_amount': round(total_cost, 2),
                    'potential_savings': round(total_cost * 0.6, 2)
                })
            
            # Entertainment spending
            entertainment = expense_df[
                expense_df['category'].str.contains('entertainment|movie|game|streaming', case=False, na=False)
            ]
            if len(entertainment) > 0:
                total_entertainment = entertainment['amount'].sum()
                if total_entertainment > 500:
                    habits.append({
                        'type': 'entertainment',
                        'category': 'Entertainment',
                        'message': f"Entertainment spending: Rs. {total_entertainment:,.0f} over {analysis_months} months.",
                        'total_amount': round(total_entertainment, 2),
                        'average_monthly': round(total_entertainment / analysis_months, 2)
                    })
        
        return habits[:10]  # Return top 10 habits
    
    def detect_subscriptions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring subscription charges.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of detected subscriptions
        """
        subscriptions = []
        
        if not transactions:
            return subscriptions
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        expense_df = df[df['type'].str.lower() == 'expense'].copy()
        
        if expense_df.empty:
            return subscriptions
        
        # Look for recurring amounts from same merchant/description
        # Group by description and amount
        for desc in expense_df['description'].unique():
            if not desc or len(str(desc)) < 3:
                continue
            
            desc_txns = expense_df[expense_df['description'] == desc]
            
            if len(desc_txns) < 2:
                continue
            
            # Check for recurring amounts
            amounts = desc_txns['amount'].value_counts()
            
            for amount, count in amounts.items():
                if count >= 2:  # At least 2 occurrences
                    matching_txns = desc_txns[desc_txns['amount'] == amount]
                    
                    # Calculate average interval between transactions
                    dates = sorted(matching_txns['date'].tolist())
                    if len(dates) >= 2:
                        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                        avg_interval = np.mean(intervals)
                        
                        # Check if it's monthly (25-35 days) or weekly (5-9 days)
                        is_subscription = False
                        frequency = ''
                        
                        if 25 <= avg_interval <= 35:
                            is_subscription = True
                            frequency = 'monthly'
                        elif 5 <= avg_interval <= 9:
                            is_subscription = True
                            frequency = 'weekly'
                        elif 85 <= avg_interval <= 95:
                            is_subscription = True
                            frequency = 'quarterly'
                        
                        if is_subscription:
                            annual_cost = amount * (365 / avg_interval) if avg_interval > 0 else 0
                            
                            subscriptions.append({
                                'type': 'subscription',
                                'description': str(desc)[:50],
                                'amount': round(amount, 2),
                                'frequency': frequency,
                                'occurrences': int(count),
                                'average_interval_days': round(avg_interval, 1),
                                'estimated_annual_cost': round(annual_cost, 2),
                                'message': f"Recurring {frequency} charge: {desc[:30]} - Rs. {amount:,.0f}",
                                'first_seen': dates[0].strftime('%Y-%m-%d'),
                                'last_seen': dates[-1].strftime('%Y-%m-%d')
                            })
        
        # Sort by annual cost
        subscriptions.sort(key=lambda x: x['estimated_annual_cost'], reverse=True)
        
        return subscriptions[:15]  # Return top 15 subscriptions
    
    def identify_savings_opportunities(
        self,
        transactions: List[Dict[str, Any]],
        analysis_months: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify savings opportunities based on spending patterns.
        
        Args:
            transactions: List of transaction dictionaries
            analysis_months: Months to analyze
            
        Returns:
            List of savings opportunities
        """
        opportunities = []
        
        if not transactions:
            return opportunities
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter to analysis period
        cutoff_date = datetime.now() - timedelta(days=analysis_months * 30)
        df = df[df['date'] >= cutoff_date]
        
        expense_df = df[df['type'].str.lower() == 'expense'].copy()
        
        if expense_df.empty:
            return opportunities
        
        # Hidden fees detection (small recurring charges)
        small_charges = expense_df[expense_df['amount'] < 50]
        if len(small_charges) > 0:
            small_total = small_charges['amount'].sum()
            if small_total > 200:
                opportunities.append({
                    'type': 'hidden_fees',
                    'category': 'Small Charges',
                    'message': f"Multiple small charges totaling Rs. {small_total:,.0f}. Review for unnecessary fees.",
                    'total_amount': round(small_total, 2),
                    'transaction_count': len(small_charges),
                    'potential_savings': round(small_total * 0.5, 2)
                })
        
        # Impulse purchases (multiple same-day transactions in same category)
        expense_df['date_only'] = expense_df['date'].dt.date
        same_day_spending = expense_df.groupby(['date_only', 'category']).agg({
            'amount': ['sum', 'count']
        })
        
        impulse_days = same_day_spending[same_day_spending[('amount', 'count')] >= 3]
        if len(impulse_days) > 0:
            opportunities.append({
                'type': 'impulse_purchases',
                'message': f"Detected {len(impulse_days)} days with multiple purchases in same category. Plan purchases to reduce impulse buying.",
                'occurrences': len(impulse_days)
            })
        
        # Weekend vs weekday spending
        expense_df['is_weekend'] = expense_df['date'].dt.dayofweek >= 5
        weekend_spending = expense_df[expense_df['is_weekend']]['amount'].sum()
        weekday_spending = expense_df[~expense_df['is_weekend']]['amount'].sum()
        
        weekend_days = len(expense_df[expense_df['is_weekend']]['date'].dt.date.unique())
        weekday_days = len(expense_df[~expense_df['is_weekend']]['date'].dt.date.unique())
        
        if weekend_days > 0 and weekday_days > 0:
            weekend_avg = weekend_spending / weekend_days
            weekday_avg = weekday_spending / weekday_days
            
            if weekend_avg > weekday_avg * 1.5:
                opportunities.append({
                    'type': 'weekend_spending',
                    'message': f"Weekend spending is {(weekend_avg/weekday_avg):.1f}x higher than weekdays. Plan weekend activities to reduce costs.",
                    'weekend_average': round(weekend_avg, 2),
                    'weekday_average': round(weekday_avg, 2),
                    'potential_savings': round((weekend_avg - weekday_avg) * weekend_days * 0.5, 2)
                })
        
        # High variance categories (inconsistent spending)
        category_stats = expense_df.groupby('category').agg({
            'amount': ['sum', 'std', 'mean', 'count']
        })
        
        for category in category_stats.index:
            total = category_stats.loc[category, ('amount', 'sum')]
            std = category_stats.loc[category, ('amount', 'std')]
            mean = category_stats.loc[category, ('amount', 'mean')]
            count = category_stats.loc[category, ('amount', 'count')]
            
            if count >= 5 and mean > 0:
                cv = (std / mean) * 100  # Coefficient of variation
                
                if cv > 100 and total > 1000:  # High variance
                    opportunities.append({
                        'type': 'inconsistent_spending',
                        'category': category,
                        'message': f"{category} spending is highly variable. Set a monthly budget to control costs.",
                        'total_amount': round(total, 2),
                        'coefficient_of_variation': round(cv, 2),
                        'average_amount': round(mean, 2)
                    })
        
        return opportunities[:10]  # Return top 10 opportunities
    
    def generate_behavior_nudges(
        self,
        transactions: List[Dict[str, Any]],
        goals: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate behavior nudges for positive reinforcement and warnings.
        
        Args:
            transactions: List of transaction dictionaries
            goals: List of financial goals
            
        Returns:
            List of behavior nudges
        """
        nudges = []
        
        if not transactions:
            return nudges
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Recent period analysis (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_df = df[df['date'] >= recent_cutoff]
        
        # Previous period (30-60 days ago)
        previous_start = datetime.now() - timedelta(days=60)
        previous_end = datetime.now() - timedelta(days=30)
        previous_df = df[(df['date'] >= previous_start) & (df['date'] < previous_end)]
        
        # Compare spending trends
        if not recent_df.empty and not previous_df.empty:
            recent_expenses = recent_df[recent_df['type'].str.lower() == 'expense']['amount'].sum()
            previous_expenses = previous_df[previous_df['type'].str.lower() == 'expense']['amount'].sum()
            
            change_pct = ((recent_expenses - previous_expenses) / previous_expenses * 100) if previous_expenses > 0 else 0
            
            # Positive reinforcement
            if change_pct < -10:
                nudges.append({
                    'type': 'positive_reinforcement',
                    'category': 'spending_reduction',
                    'message': f"Great job! You've reduced spending by {abs(change_pct):.0f}% this month.",
                    'sentiment': 'positive',
                    'change_percentage': round(change_pct, 2)
                })
            
            # Warning
            elif change_pct > 20:
                nudges.append({
                    'type': 'warning',
                    'category': 'spending_increase',
                    'message': f"Spending increased by {change_pct:.0f}% this month. Review your budget.",
                    'sentiment': 'warning',
                    'change_percentage': round(change_pct, 2)
                })
        
        # Savings streak
        if not df.empty:
            savings_df = df[df['type'].str.lower() == 'savings']
            
            if not savings_df.empty:
                # Check for consistent monthly savings
                savings_df['year_month'] = savings_df['date'].dt.to_period('M')
                months_with_savings = len(savings_df['year_month'].unique())
                
                if months_with_savings >= 3:
                    nudges.append({
                        'type': 'positive_reinforcement',
                        'category': 'savings_streak',
                        'message': f"You've saved for {months_with_savings} consecutive months! Keep it up!",
                        'sentiment': 'positive',
                        'streak_months': months_with_savings
                    })
        
        # Goal progress nudges
        if goals:
            active_goals = [g for g in goals if g.get('status', '').lower() == 'active']
            
            for goal in active_goals:
                current = goal.get('current_amount', 0)
                target = goal.get('target_amount', 1)
                progress = (current / target * 100) if target > 0 else 0
                
                # Milestone reached
                if 48 <= progress <= 52:  # Around 50%
                    nudges.append({
                        'type': 'milestone',
                        'category': 'goal_progress',
                        'message': f"Halfway there! You've reached 50% of your '{goal.get('goal_name', 'goal')}' target.",
                        'sentiment': 'positive',
                        'progress_percentage': round(progress, 2)
                    })
                
                elif 73 <= progress <= 77:  # Around 75%
                    nudges.append({
                        'type': 'milestone',
                        'category': 'goal_progress',
                        'message': f"Almost there! You're at 75% of your '{goal.get('goal_name', 'goal')}' target.",
                        'sentiment': 'positive',
                        'progress_percentage': round(progress, 2)
                    })
                
                # Behind schedule
                elif progress < 25 and current > 0:
                    nudges.append({
                        'type': 'goal_reminder',
                        'category': 'goal_progress',
                        'message': f"Increase contributions to '{goal.get('goal_name', 'goal')}' to stay on track.",
                        'sentiment': 'neutral',
                        'progress_percentage': round(progress, 2)
                    })
        
        # No spending day (positive)
        if not recent_df.empty:
            recent_expense_dates = recent_df[recent_df['type'].str.lower() == 'expense']['date'].dt.date.unique()
            days_in_recent = (datetime.now().date() - recent_cutoff.date()).days
            
            if len(recent_expense_dates) < days_in_recent:
                no_spend_days = days_in_recent - len(recent_expense_dates)
                if no_spend_days > 0:
                    nudges.append({
                        'type': 'positive_reinforcement',
                        'category': 'no_spend_days',
                        'message': f"You had {no_spend_days} no-spend days this month. Excellent discipline!",
                        'sentiment': 'positive',
                        'no_spend_days': no_spend_days
                    })
        
        return nudges[:10]  # Return top 10 nudges
    
    def get_all_recommendations(
        self,
        transactions: List[Dict[str, Any]],
        goals: Optional[List[Dict[str, Any]]] = None,
        analysis_months: int = 3
    ) -> Dict[str, Any]:
        """
        Get comprehensive recommendations including habits, subscriptions, opportunities, and nudges.
        
        Args:
            transactions: List of transaction dictionaries
            goals: List of financial goals
            analysis_months: Months to analyze
            
        Returns:
            Dictionary with all recommendation types
        """
        return {
            'habits': self.analyze_spending_habits(transactions, analysis_months),
            'subscriptions': self.detect_subscriptions(transactions),
            'opportunities': self.identify_savings_opportunities(transactions, analysis_months),
            'nudges': self.generate_behavior_nudges(transactions, goals),
            'generated_at': datetime.now().isoformat()
        }


# Global instance
_recommender = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create the global recommendation engine instance."""
    global _recommender
    if _recommender is None:
        _recommender = RecommendationEngine()
    return _recommender
