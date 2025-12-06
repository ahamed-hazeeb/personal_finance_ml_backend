"""
Goal Planning Intelligence Module.

This module provides intelligent goal planning features including:
- Timeline calculation for financial goals
- Reverse goal planning
- Goal adjustment recommendations
- Feasibility analysis
"""
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np

from app.core.logging import get_logger
from app.utils.validators import validate_goal_data, validate_amount

logger = get_logger(__name__)


class GoalPlanner:
    """
    Goal planning engine for financial goals.
    
    Provides calculations for goal timelines, required savings,
    and feasibility analysis.
    """
    
    def __init__(self):
        """Initialize the goal planner."""
        pass
    
    def calculate_timeline(
        self,
        target_amount: float,
        current_savings: float,
        monthly_savings: float,
        current_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate timeline to reach a financial goal.
        
        Args:
            target_amount: Target goal amount
            current_savings: Current savings amount
            monthly_savings: Monthly savings amount
            current_date: Current date (defaults to today)
            
        Returns:
            Dictionary with timeline calculation and feasibility
        """
        # Validate inputs
        validated = validate_goal_data(
            target_amount=target_amount,
            current_savings=current_savings,
            monthly_savings=monthly_savings
        )
        
        target_amount = validated["target_amount"]
        current_savings = validated["current_savings"]
        monthly_savings = validated["monthly_savings"]
        
        if current_date is None:
            current_date = date.today()
        
        # Calculate required amount
        amount_needed = target_amount - current_savings
        
        # Calculate months needed
        if monthly_savings <= 0:
            return {
                "feasible": False,
                "message": "Goal is not feasible with zero or negative monthly savings",
                "amount_needed": amount_needed,
                "monthly_savings": monthly_savings
            }
        
        months_needed = np.ceil(amount_needed / monthly_savings)
        
        # Calculate target date
        target_date = current_date + relativedelta(months=int(months_needed))
        
        # Calculate progress percentage
        progress_percentage = (current_savings / target_amount) * 100
        
        # Feasibility analysis
        feasibility = self._analyze_feasibility(months_needed, monthly_savings)
        
        return {
            "feasible": True,
            "target_amount": target_amount,
            "current_savings": current_savings,
            "amount_needed": amount_needed,
            "monthly_savings": monthly_savings,
            "months_needed": int(months_needed),
            "target_date": target_date.isoformat(),
            "progress_percentage": round(progress_percentage, 2),
            "feasibility_rating": feasibility["rating"],
            "feasibility_message": feasibility["message"],
            "milestones": self._generate_milestones(
                current_savings,
                target_amount,
                monthly_savings,
                current_date
            )
        }
    
    def reverse_plan(
        self,
        target_amount: float,
        current_savings: float,
        target_date: date,
        current_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate required monthly savings to reach a goal by a target date.
        
        Args:
            target_amount: Target goal amount
            current_savings: Current savings amount
            target_date: Desired target date
            current_date: Current date (defaults to today)
            
        Returns:
            Dictionary with required monthly savings and feasibility
        """
        # Validate inputs
        validated = validate_goal_data(
            target_amount=target_amount,
            current_savings=current_savings,
            goal_date=target_date
        )
        
        target_amount = validated["target_amount"]
        current_savings = validated["current_savings"]
        target_date = validated["goal_date"]
        
        if current_date is None:
            current_date = date.today()
        
        # Calculate months available
        months_available = self._calculate_months_between(current_date, target_date)
        
        if months_available <= 0:
            return {
                "feasible": False,
                "message": "Target date is in the past or too soon",
                "target_date": target_date.isoformat()
            }
        
        # Calculate required amount
        amount_needed = target_amount - current_savings
        
        # Calculate required monthly savings
        required_monthly_savings = amount_needed / months_available
        
        # Feasibility analysis
        feasibility = self._analyze_feasibility(months_available, required_monthly_savings)
        
        # Generate alternative timelines
        alternatives = self._generate_alternative_timelines(
            amount_needed,
            required_monthly_savings,
            current_date
        )
        
        return {
            "feasible": True,
            "target_amount": target_amount,
            "current_savings": current_savings,
            "amount_needed": amount_needed,
            "target_date": target_date.isoformat(),
            "months_available": months_available,
            "required_monthly_savings": round(required_monthly_savings, 2),
            "feasibility_score": feasibility["score"],
            "feasibility_rating": feasibility["rating"],
            "feasibility_message": feasibility["message"],
            "alternatives": alternatives,
            "milestones": self._generate_milestones(
                current_savings,
                target_amount,
                required_monthly_savings,
                current_date
            )
        }
    
    def _calculate_months_between(self, start_date: date, end_date: date) -> int:
        """Calculate number of months between two dates."""
        delta = relativedelta(end_date, start_date)
        return delta.years * 12 + delta.months
    
    def _analyze_feasibility(self, months_needed: int, monthly_savings: float) -> Dict[str, Any]:
        """Analyze feasibility of a goal."""
        if months_needed <= 12 and monthly_savings < 1000:
            score = 85
            rating = "Excellent"
            message = "This goal is highly achievable with your current savings plan"
        elif months_needed <= 24 and monthly_savings < 2000:
            score = 70
            rating = "Good"
            message = "This goal is achievable with consistent savings"
        elif months_needed <= 36:
            score = 55
            rating = "Moderate"
            message = "This goal requires commitment but is achievable"
        elif months_needed <= 60:
            score = 40
            rating = "Challenging"
            message = "This is an ambitious goal that will require dedication"
        else:
            score = 25
            rating = "Very Challenging"
            message = "Consider breaking this into smaller milestones"
        
        return {
            "score": score,
            "rating": rating,
            "message": message
        }
    
    def _generate_milestones(
        self,
        current_savings: float,
        target_amount: float,
        monthly_savings: float,
        start_date: date
    ) -> List[Dict[str, Any]]:
        """Generate milestone checkpoints for a goal."""
        milestones = []
        amount_needed = target_amount - current_savings
        
        # Generate milestones at 25%, 50%, 75%, and 100%
        percentages = [25, 50, 75, 100]
        
        for pct in percentages:
            milestone_amount = current_savings + (amount_needed * (pct / 100))
            months_to_milestone = np.ceil((milestone_amount - current_savings) / monthly_savings) if monthly_savings > 0 else 0
            milestone_date = start_date + relativedelta(months=int(months_to_milestone))
            
            milestones.append({
                "percentage": pct,
                "amount": round(milestone_amount, 2),
                "months_from_start": int(months_to_milestone),
                "expected_date": milestone_date.isoformat()
            })
        
        return milestones
    
    def _generate_alternative_timelines(
        self,
        amount_needed: float,
        base_monthly_savings: float,
        start_date: date
    ) -> List[Dict[str, Any]]:
        """Generate alternative timeline scenarios."""
        alternatives = []
        
        # Aggressive (1.5x monthly savings)
        aggressive_monthly = base_monthly_savings * 1.5
        aggressive_months = np.ceil(amount_needed / aggressive_monthly)
        aggressive_date = start_date + relativedelta(months=int(aggressive_months))
        
        alternatives.append({
            "scenario": "Aggressive",
            "monthly_savings": round(aggressive_monthly, 2),
            "months_needed": int(aggressive_months),
            "target_date": aggressive_date.isoformat(),
            "description": "Reach your goal faster with increased savings"
        })
        
        # Conservative (0.75x monthly savings)
        conservative_monthly = base_monthly_savings * 0.75
        conservative_months = np.ceil(amount_needed / conservative_monthly)
        conservative_date = start_date + relativedelta(months=int(conservative_months))
        
        alternatives.append({
            "scenario": "Conservative",
            "monthly_savings": round(conservative_monthly, 2),
            "months_needed": int(conservative_months),
            "target_date": conservative_date.isoformat(),
            "description": "More flexible timeline with lower monthly commitment"
        })
        
        return alternatives
