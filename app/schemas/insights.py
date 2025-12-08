"""
Pydantic schemas for insights and analysis responses.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InsightSchema(BaseModel):
    """Schema for individual insight."""
    type: str = Field(..., description="Insight type: high_spending, savings_opportunity, anomaly, trend")
    message: str = Field(..., description="Human-readable insight message")
    severity: str = Field(..., description="Severity level: info, warning, alert")
    category: Optional[str] = Field(None, description="Related category")
    amount: Optional[float] = Field(None, description="Related amount")
    percentage: Optional[float] = Field(None, description="Percentage value")
    potential_savings: Optional[float] = Field(None, description="Potential savings amount")
    date: Optional[str] = Field(None, description="Related date")
    trend: Optional[str] = Field(None, description="Trend direction: increasing, decreasing, stable")
    change_percentage: Optional[float] = Field(None, description="Percentage change")


class CategorySpending(BaseModel):
    """Schema for category spending breakdown."""
    category: str = Field(..., description="Category name")
    amount: float = Field(..., description="Total amount")
    percentage: float = Field(..., description="Percentage of total")


class MonthlyAverage(BaseModel):
    """Schema for monthly averages."""
    income: float = Field(..., description="Average monthly income")
    expenses: float = Field(..., description="Average monthly expenses")
    savings: float = Field(..., description="Average monthly savings")


class SpendingPatterns(BaseModel):
    """Schema for spending patterns analysis."""
    total_income: float = Field(..., description="Total income")
    total_expenses: float = Field(..., description="Total expenses")
    total_savings: float = Field(..., description="Total savings")
    savings_rate: float = Field(..., description="Savings rate percentage")
    top_categories: List[CategorySpending] = Field(..., description="Top spending categories")
    monthly_average: MonthlyAverage = Field(..., description="Monthly averages")


class PredictionSummary(BaseModel):
    """Schema for prediction summary."""
    next_month_expense: float = Field(..., description="Predicted next month expenses")
    next_month_income: float = Field(..., description="Predicted next month income")
    confidence: float = Field(..., description="Confidence score 0-1")


class Recommendation(BaseModel):
    """Schema for recommendations."""
    type: str = Field(..., description="Recommendation type")
    message: str = Field(..., description="Recommendation message")
    priority: str = Field(..., description="Priority level: low, medium, high")
    target_amount: Optional[float] = Field(None, description="Target amount")


class InsightsResponse(BaseModel):
    """Response schema for insights endpoint."""
    success: bool = Field(default=True, description="Success status")
    insights: List[InsightSchema] = Field(..., description="List of insights")
    spending_patterns: SpendingPatterns = Field(..., description="Spending patterns analysis")
    predictions: PredictionSummary = Field(..., description="Future predictions")
    recommendations: List[Recommendation] = Field(..., description="Actionable recommendations")


class CategoryBreakdown(BaseModel):
    """Schema for category-wise breakdown in predictions."""
    category: str = Field(..., description="Category name")
    amount: float = Field(..., description="Predicted amount")


class MonthlyPrediction(BaseModel):
    """Schema for monthly prediction."""
    month: str = Field(..., description="Month in YYYY-MM format")
    predicted_income: float = Field(..., description="Predicted income")
    predicted_expense: float = Field(..., description="Predicted expenses")
    predicted_savings: float = Field(..., description="Predicted savings")
    confidence: float = Field(..., description="Confidence score")
    category_breakdown: Optional[Dict[str, float]] = Field(None, description="Category-wise breakdown")


class PredictionsResponse(BaseModel):
    """Response schema for predictions endpoint."""
    success: bool = Field(default=True, description="Success status")
    predictions: List[MonthlyPrediction] = Field(..., description="Monthly predictions")


class TrainWithTransactionsRequest(BaseModel):
    """Request schema for training with transaction data."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")


class TrainWithTransactionsResponse(BaseModel):
    """Response schema for training with transactions."""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Training status message")
    metrics: Dict[str, Any] = Field(..., description="Training metrics")
