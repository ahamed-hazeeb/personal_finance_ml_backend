"""
Pydantic schemas for recommendation endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationsRequest(BaseModel):
    """Base request schema for recommendations."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="List of financial goals")
    analysis_months: int = Field(3, description="Months of history to analyze", ge=1, le=12)


class SpendingHabit(BaseModel):
    """Spending habit insight."""
    type: str = Field(..., description="Habit type: high_frequency, food_delivery, etc.")
    category: str = Field(..., description="Category name")
    message: str = Field(..., description="Habit description")
    frequency_per_week: Optional[float] = Field(None, description="Frequency per week")
    total_amount: Optional[float] = Field(None, description="Total amount")
    average_transaction: Optional[float] = Field(None, description="Average transaction amount")
    transaction_count: Optional[int] = Field(None, description="Number of transactions")
    potential_savings: Optional[float] = Field(None, description="Potential savings")
    average_monthly: Optional[float] = Field(None, description="Average monthly amount")


class HabitsResponse(BaseModel):
    """Response schema for spending habits."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    habits: List[SpendingHabit] = Field(..., description="List of spending habits")
    habits_count: int = Field(..., description="Number of habits identified")
    analysis_period_months: int = Field(..., description="Months analyzed")


class Subscription(BaseModel):
    """Detected subscription."""
    type: str = Field(..., description="Type: subscription")
    description: str = Field(..., description="Subscription description")
    amount: float = Field(..., description="Subscription amount")
    frequency: str = Field(..., description="Frequency: monthly, weekly, quarterly")
    occurrences: int = Field(..., description="Number of occurrences detected")
    average_interval_days: float = Field(..., description="Average interval in days")
    estimated_annual_cost: float = Field(..., description="Estimated annual cost")
    message: str = Field(..., description="Subscription message")
    first_seen: str = Field(..., description="First transaction date")
    last_seen: str = Field(..., description="Last transaction date")


class SubscriptionsResponse(BaseModel):
    """Response schema for subscriptions."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    subscriptions: List[Subscription] = Field(..., description="List of detected subscriptions")
    subscription_count: int = Field(..., description="Number of subscriptions")
    total_monthly_cost: float = Field(..., description="Total monthly subscription cost")
    total_annual_cost: float = Field(..., description="Total annual subscription cost")


class SavingsOpportunity(BaseModel):
    """Savings opportunity insight."""
    type: str = Field(..., description="Opportunity type: hidden_fees, impulse_purchases, etc.")
    category: Optional[str] = Field(None, description="Category name")
    message: str = Field(..., description="Opportunity description")
    total_amount: Optional[float] = Field(None, description="Total amount")
    potential_savings: Optional[float] = Field(None, description="Potential savings")
    transaction_count: Optional[int] = Field(None, description="Number of transactions")
    occurrences: Optional[int] = Field(None, description="Number of occurrences")
    weekend_average: Optional[float] = Field(None, description="Weekend average spending")
    weekday_average: Optional[float] = Field(None, description="Weekday average spending")
    coefficient_of_variation: Optional[float] = Field(None, description="Coefficient of variation")
    average_amount: Optional[float] = Field(None, description="Average amount")


class OpportunitiesResponse(BaseModel):
    """Response schema for savings opportunities."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    opportunities: List[SavingsOpportunity] = Field(..., description="List of savings opportunities")
    opportunity_count: int = Field(..., description="Number of opportunities")
    total_potential_savings: float = Field(..., description="Total potential savings")


class BehaviorNudge(BaseModel):
    """Behavior nudge for positive reinforcement or warning."""
    type: str = Field(..., description="Nudge type: positive_reinforcement, warning, milestone, goal_reminder")
    category: str = Field(..., description="Category: spending_reduction, savings_streak, etc.")
    message: str = Field(..., description="Nudge message")
    sentiment: str = Field(..., description="Sentiment: positive, negative, neutral, warning")
    change_percentage: Optional[float] = Field(None, description="Change percentage")
    streak_months: Optional[int] = Field(None, description="Streak in months")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage")
    no_spend_days: Optional[int] = Field(None, description="Number of no-spend days")


class NudgesResponse(BaseModel):
    """Response schema for behavior nudges."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    nudges: List[BehaviorNudge] = Field(..., description="List of behavior nudges")
    nudge_count: int = Field(..., description="Number of nudges")
