"""
Service for generating financial insights from transaction data.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from app.schemas.transactions import TransactionSchema
from app.schemas.insights import (
    InsightSchema, SpendingPatterns, CategorySpending, MonthlyAverage,
    PredictionSummary, Recommendation
)


class InsightService:
    """Service for analyzing transactions and generating insights."""
    
    def __init__(self):
        """Initialize the insight service."""
        pass
    
    def generate_insights(self, transactions: List[TransactionSchema]) -> Dict[str, Any]:
        """
        Generate comprehensive insights from transactions.
        
        Args:
            transactions: List of transaction objects
            
        Returns:
            Dictionary containing insights, patterns, predictions, and recommendations
        """
        if not transactions:
            return self._empty_insights()
        
        # Analyze spending patterns
        spending_patterns = self._analyze_spending_patterns(transactions)
        
        # Generate insights
        insights = []
        insights.extend(self._detect_high_spending(transactions, spending_patterns))
        insights.extend(self._find_savings_opportunities(transactions, spending_patterns))
        insights.extend(self._detect_anomalies(transactions))
        insights.extend(self._identify_trends(transactions))
        
        # Generate predictions
        predictions = self._generate_predictions(transactions, spending_patterns)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            transactions, spending_patterns, insights
        )
        
        return {
            "success": True,
            "insights": insights,
            "spending_patterns": spending_patterns,
            "predictions": predictions,
            "recommendations": recommendations
        }
    
    def _empty_insights(self) -> Dict[str, Any]:
        """Return empty insights structure."""
        return {
            "success": True,
            "insights": [],
            "spending_patterns": {
                "total_income": 0,
                "total_expenses": 0,
                "total_savings": 0,
                "savings_rate": 0,
                "top_categories": [],
                "monthly_average": {
                    "income": 0,
                    "expenses": 0,
                    "savings": 0
                }
            },
            "predictions": {
                "next_month_expense": 0,
                "next_month_income": 0,
                "confidence": 0
            },
            "recommendations": []
        }
    
    def _analyze_spending_patterns(
        self, transactions: List[TransactionSchema]
    ) -> Dict[str, Any]:
        """Analyze spending patterns from transactions."""
        total_income = 0
        total_expenses = 0
        total_savings = 0
        category_totals = defaultdict(float)
        
        # Calculate totals
        for txn in transactions:
            if txn.type.lower() == "income":
                total_income += txn.amount
            elif txn.type.lower() == "expense":
                total_expenses += txn.amount
                category_totals[txn.category] += txn.amount
            elif txn.type.lower() == "savings":
                total_savings += txn.amount
        
        # Calculate savings rate
        savings_rate = 0
        if total_income > 0:
            net_savings = total_income - total_expenses
            savings_rate = (net_savings / total_income) * 100
        
        # Get top categories
        top_categories = []
        if total_expenses > 0:
            sorted_categories = sorted(
                category_totals.items(), key=lambda x: x[1], reverse=True
            )
            for category, amount in sorted_categories[:5]:
                percentage = (amount / total_expenses) * 100
                top_categories.append({
                    "category": category,
                    "amount": amount,
                    "percentage": round(percentage, 2)
                })
        
        # Calculate monthly averages
        date_range = self._get_date_range(transactions)
        months = max(1, date_range)
        
        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "total_savings": round(total_savings, 2),
            "savings_rate": round(savings_rate, 2),
            "top_categories": top_categories,
            "monthly_average": {
                "income": round(total_income / months, 2),
                "expenses": round(total_expenses / months, 2),
                "savings": round((total_income - total_expenses) / months, 2)
            }
        }
    
    def _get_date_range(self, transactions: List[TransactionSchema]) -> int:
        """Calculate date range in months from transactions."""
        if not transactions:
            return 1
        
        dates = []
        for txn in transactions:
            try:
                date_obj = datetime.strptime(txn.date, "%Y-%m-%d")
                dates.append(date_obj)
            except (ValueError, AttributeError):
                continue
        
        if not dates:
            return 1
        
        min_date = min(dates)
        max_date = max(dates)
        
        # Calculate months
        months = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
        return max(1, months)
    
    def _detect_high_spending(
        self, transactions: List[TransactionSchema], patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect high spending categories."""
        insights = []
        threshold = 50  # Alert if category is > 50% of expenses
        
        for category_info in patterns["top_categories"]:
            if category_info["percentage"] > threshold:
                insights.append({
                    "type": "high_spending",
                    "category": category_info["category"],
                    "message": f"{category_info['category']} expenses are {category_info['percentage']:.1f}% of your total spending (Rs. {category_info['amount']:,.0f})",
                    "severity": "warning",
                    "amount": category_info["amount"],
                    "percentage": category_info["percentage"]
                })
        
        return insights
    
    def _find_savings_opportunities(
        self, transactions: List[TransactionSchema], patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find potential savings opportunities."""
        insights = []
        threshold = 15  # Look for categories > 15% of expenses
        
        for category_info in patterns["top_categories"]:
            if 15 < category_info["percentage"] < 50:
                potential_savings = category_info["amount"] * 0.2  # 20% reduction
                insights.append({
                    "type": "savings_opportunity",
                    "category": category_info["category"],
                    "message": f"Reducing {category_info['category']} by 20% could save Rs. {potential_savings:,.0f}/month",
                    "potential_savings": round(potential_savings, 2),
                    "severity": "info"
                })
        
        return insights
    
    def _detect_anomalies(self, transactions: List[TransactionSchema]) -> List[Dict[str, Any]]:
        """Detect unusual transactions using statistical methods."""
        insights = []
        
        # Group by category
        category_amounts = defaultdict(list)
        for txn in transactions:
            if txn.type.lower() == "expense":
                category_amounts[txn.category].append({
                    "amount": txn.amount,
                    "date": txn.date
                })
        
        # Detect anomalies per category
        for category, amounts_data in category_amounts.items():
            if len(amounts_data) < 3:
                continue
            
            amounts = [item["amount"] for item in amounts_data]
            mean = np.mean(amounts)
            std = np.std(amounts)
            
            if std == 0:
                continue
            
            # Find outliers (z-score > 2)
            for item in amounts_data:
                z_score = (item["amount"] - mean) / std
                if z_score > 2:
                    insights.append({
                        "type": "anomaly",
                        "category": category,
                        "message": f"Unusual high expense of Rs. {item['amount']:,.0f} detected in {category}",
                        "date": item["date"],
                        "amount": item["amount"],
                        "severity": "alert"
                    })
        
        return insights[:3]  # Return top 3 anomalies
    
    def _identify_trends(self, transactions: List[TransactionSchema]) -> List[Dict[str, Any]]:
        """Identify spending trends by comparing recent vs previous periods."""
        insights = []
        
        # Sort transactions by date
        sorted_txns = sorted(
            [t for t in transactions if t.type.lower() == "expense"],
            key=lambda x: x.date
        )
        
        if len(sorted_txns) < 10:
            return insights
        
        # Split into two halves
        mid = len(sorted_txns) // 2
        first_half = sorted_txns[:mid]
        second_half = sorted_txns[mid:]
        
        # Compare category spending
        first_totals = defaultdict(float)
        second_totals = defaultdict(float)
        
        for txn in first_half:
            first_totals[txn.category] += txn.amount
        
        for txn in second_half:
            second_totals[txn.category] += txn.amount
        
        # Find significant changes
        for category in second_totals:
            if category in first_totals and first_totals[category] > 0:
                change_pct = (
                    (second_totals[category] - first_totals[category]) /
                    first_totals[category]
                ) * 100
                
                if abs(change_pct) > 20:  # Significant change threshold
                    trend = "increasing" if change_pct > 0 else "decreasing"
                    insights.append({
                        "type": "trend",
                        "message": f"Your {category} expenses {trend} by {abs(change_pct):.0f}% compared to earlier period",
                        "category": category,
                        "trend": trend,
                        "change_percentage": round(change_pct, 2)
                    })
        
        return insights[:2]  # Return top 2 trends
    
    def _generate_predictions(
        self, transactions: List[TransactionSchema], patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate simple predictions for next month."""
        # Use monthly averages for predictions
        monthly_avg = patterns["monthly_average"]
        
        # Simple prediction with slight confidence adjustment
        confidence = 0.85 if len(transactions) > 20 else 0.70
        
        return {
            "next_month_expense": round(monthly_avg["expenses"], 2),
            "next_month_income": round(monthly_avg["income"], 2),
            "confidence": confidence
        }
    
    def _generate_recommendations(
        self, 
        transactions: List[TransactionSchema], 
        patterns: Dict[str, Any],
        insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Recommend budget for high spending categories
        for insight in insights:
            if insight.get("type") == "high_spending":
                recommendations.append({
                    "type": "budget_alert",
                    "message": f"Set a budget limit for {insight['category']} expenses (currently Rs. {insight['amount']:,.0f})",
                    "priority": "high"
                })
        
        # Recommend increasing savings rate
        if patterns["savings_rate"] < 20:
            target_savings = patterns["total_income"] * 0.2 if patterns["total_income"] > 0 else 0
            recommendations.append({
                "type": "savings_goal",
                "message": "Increase savings rate to 20% by reducing discretionary spending",
                "target_amount": round(target_savings, 2),
                "priority": "medium"
            })
        
        # Recommend tracking for uncategorized or inconsistent spending
        if len(patterns["top_categories"]) < 3 and patterns["total_expenses"] > 0:
            recommendations.append({
                "type": "tracking",
                "message": "Categorize your expenses better for more accurate insights",
                "priority": "low"
            })
        
        return recommendations[:5]  # Return top 5 recommendations


# Global instance
_insight_service = None


def get_insight_service() -> InsightService:
    """Get or create the global insight service instance."""
    global _insight_service
    if _insight_service is None:
        _insight_service = InsightService()
    return _insight_service
