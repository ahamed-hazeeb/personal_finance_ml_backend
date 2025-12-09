"""
Pydantic schemas for budget endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BudgetRecommendRequest(BaseModel):
    """Request schema for budget recommendations."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="List of financial goals")
    analysis_months: int = Field(3, description="Months of history to analyze", ge=1, le=12)


class BudgetAllocation(BaseModel):
    """Budget allocation details."""
    needs: float = Field(..., description="Budget for needs")
    wants: float = Field(..., description="Budget for wants")
    savings: float = Field(..., description="Budget for savings")
    needs_percentage: float = Field(..., description="Needs as percentage of income")
    wants_percentage: float = Field(..., description="Wants as percentage of income")
    savings_percentage: float = Field(..., description="Savings as percentage of income")


class CategoryRecommendation(BaseModel):
    """Category-specific budget recommendation."""
    category: str = Field(..., description="Category name")
    type: str = Field(..., description="Recommendation type: leakage, reduction, etc.")
    message: str = Field(..., description="Recommendation message")
    current_amount: Optional[float] = Field(None, description="Current spending amount")
    recommended_amount: Optional[float] = Field(None, description="Recommended amount")
    potential_savings: Optional[float] = Field(None, description="Potential savings")
    variance: Optional[float] = Field(None, description="Spending variance")


class BudgetRecommendResponse(BaseModel):
    """Response schema for budget recommendations."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    monthly_income: float = Field(..., description="Monthly income")
    recommended_budget: BudgetAllocation = Field(..., description="Recommended budget allocation")
    current_spending: BudgetAllocation = Field(..., description="Current spending allocation")
    adjustments_needed: Dict[str, float] = Field(..., description="Required adjustments")
    category_recommendations: List[CategoryRecommendation] = Field(..., description="Category-specific recommendations")
    calculated_at: str = Field(..., description="Calculation timestamp")


class BudgetAlertsRequest(BaseModel):
    """Request schema for budget alerts."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    budget: Dict[str, float] = Field(..., description="Budget with needs/wants/savings")


class BudgetAlert(BaseModel):
    """Individual budget alert."""
    type: str = Field(..., description="Alert type: projected_overspending, exceeded")
    category: str = Field(..., description="Category: needs, wants, savings")
    severity: str = Field(..., description="Severity: info, warning, alert")
    message: str = Field(..., description="Alert message")
    current_spending: float = Field(..., description="Current spending")
    budget: float = Field(..., description="Budget amount")
    projected_spending: Optional[float] = Field(None, description="Projected spending")
    days_remaining: Optional[int] = Field(None, description="Days remaining in month")


class BudgetAlertsResponse(BaseModel):
    """Response schema for budget alerts."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    alerts: List[BudgetAlert] = Field(..., description="List of budget alerts")
    alert_count: int = Field(..., description="Number of alerts")


class OptimizeRequest(BaseModel):
    """Request schema for budget optimization."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    target_savings_rate: float = Field(0.20, description="Target savings rate (0-1)", ge=0, le=0.5)


class OptimizationOpportunity(BaseModel):
    """Budget optimization opportunity."""
    category: str = Field(..., description="Category name")
    current_spending: float = Field(..., description="Current spending")
    suggested_reduction: float = Field(..., description="Suggested reduction amount")
    new_budget: float = Field(..., description="New budget after reduction")


class OptimizeResponse(BaseModel):
    """Response schema for budget optimization."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    current_savings_rate: float = Field(..., description="Current savings rate percentage")
    target_savings_rate: float = Field(..., description="Target savings rate percentage")
    monthly_savings_gap: Optional[float] = Field(None, description="Monthly savings gap")
    optimization_opportunities: List[OptimizationOpportunity] = Field(..., description="Optimization opportunities")
    projected_savings_rate: Optional[float] = Field(None, description="Projected savings rate after optimizations")
    status: Optional[str] = Field(None, description="Status message if target already met")
    message: Optional[str] = Field(None, description="Informational message")
