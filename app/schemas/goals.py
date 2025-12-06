"""
Pydantic schemas for goal planning endpoints.
"""
from datetime import date as date_type
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class CalculateTimelineRequest(BaseModel):
    """Request schema for calculate timeline endpoint."""
    target_amount: float = Field(..., description="Target goal amount", gt=0)
    current_savings: float = Field(..., description="Current savings amount", ge=0)
    monthly_savings: float = Field(..., description="Monthly savings amount", gt=0)


class ReversePlanRequest(BaseModel):
    """Request schema for reverse plan endpoint."""
    target_amount: float = Field(..., description="Target goal amount", gt=0)
    current_savings: float = Field(..., description="Current savings amount", ge=0)
    target_date: date_type = Field(..., description="Desired target date")


class MilestoneResponse(BaseModel):
    """Milestone response schema."""
    percentage: int
    amount: float
    months_from_start: int
    expected_date: str


class AlternativeScenarioResponse(BaseModel):
    """Alternative scenario response schema."""
    scenario: str
    monthly_savings: float
    months_needed: int
    target_date: str
    description: str


class CalculateTimelineResponse(BaseModel):
    """Response schema for calculate timeline endpoint."""
    feasible: bool
    target_amount: float
    current_savings: float
    amount_needed: float
    monthly_savings: float
    months_needed: int
    target_date: str
    progress_percentage: float
    feasibility_rating: str
    feasibility_message: str
    milestones: List[MilestoneResponse]


class ReversePlanResponse(BaseModel):
    """Response schema for reverse plan endpoint."""
    feasible: bool
    target_amount: float
    current_savings: float
    amount_needed: float
    target_date: str
    months_available: int
    required_monthly_savings: float
    feasibility_score: int
    feasibility_rating: str
    feasibility_message: str
    alternatives: List[AlternativeScenarioResponse]
    milestones: List[MilestoneResponse]
