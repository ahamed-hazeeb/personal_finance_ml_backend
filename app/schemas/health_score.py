"""
Pydantic schemas for financial health score endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ComponentScoreDetails(BaseModel):
    """Details for a component score."""
    score: float = Field(..., description="Component score (0-100)")
    weight: float = Field(..., description="Weight in overall score")
    details: Dict[str, Any] = Field(..., description="Detailed metrics")


class HealthScoreRecommendation(BaseModel):
    """Individual recommendation for improvement."""
    category: str = Field(..., description="Category: savings_rate, emergency_fund, etc.")
    priority: str = Field(..., description="Priority: high, medium, low")
    message: str = Field(..., description="Recommendation message")


class HealthScoreRequest(BaseModel):
    """Request schema for calculating health score."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    emergency_savings: float = Field(0, description="Emergency fund amount")
    monthly_debt_payment: float = Field(0, description="Monthly debt payment")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="List of financial goals")


class HealthScoreResponse(BaseModel):
    """Response schema for health score calculation."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    overall_score: float = Field(..., description="Overall health score (0-100)")
    grade: str = Field(..., description="Letter grade: A, B, C, D, F")
    component_scores: Dict[str, ComponentScoreDetails] = Field(..., description="Individual component scores")
    recommendations: List[HealthScoreRecommendation] = Field(..., description="Improvement recommendations")
    calculated_at: str = Field(..., description="Calculation timestamp")


class HealthScoreTrend(BaseModel):
    """Historical health score data point."""
    score: float = Field(..., description="Health score")
    grade: str = Field(..., description="Letter grade")
    calculated_at: str = Field(..., description="Calculation date")


class TrendsResponse(BaseModel):
    """Response schema for trends endpoint."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    current_score: Optional[float] = Field(None, description="Current score")
    trend_data: List[HealthScoreTrend] = Field(..., description="Historical trend data")
    month_over_month_change: Optional[float] = Field(None, description="MoM change percentage")
    quarter_over_quarter_change: Optional[float] = Field(None, description="QoQ change percentage")


class BenchmarkData(BaseModel):
    """Benchmark comparison data."""
    user_score: float = Field(..., description="User's score")
    peer_average: float = Field(..., description="Peer group average score")
    percentile: float = Field(..., description="User's percentile rank")
    comparison: str = Field(..., description="Comparison message")


class BenchmarkResponse(BaseModel):
    """Response schema for benchmark comparison."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    age_group: Optional[str] = Field(None, description="User's age group")
    income_bracket: Optional[str] = Field(None, description="User's income bracket")
    benchmark: BenchmarkData = Field(..., description="Benchmark comparison data")
