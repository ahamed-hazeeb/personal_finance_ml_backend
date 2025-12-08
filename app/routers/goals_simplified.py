"""
FastAPI router for simplified goal planning endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time

from app.schemas.goals import (
    CalculateTimelineRequest,
    CalculateTimelineResponse,
    ReversePlanRequest,
    ReversePlanResponse
)
from app.models.goal_planner import GoalPlanner
from app.core.logging import get_logger
from app.core.monitoring import track_prediction

logger = get_logger(__name__)

router = APIRouter(prefix="/goals", tags=["Goal Planning - Simplified"])

# Initialize goal planner
goal_planner = GoalPlanner()


@router.post("/timeline", response_model=CalculateTimelineResponse)
async def calculate_timeline(request: CalculateTimelineRequest):
    """
    Calculate timeline to reach a financial goal.
    
    Simplified endpoint path that matches Node.js backend expectations.
    Same functionality as /api/v1/goals/calculate-timeline.
    
    Args:
        request: CalculateTimelineRequest with goal parameters
    
    Returns:
        CalculateTimelineResponse with timeline and feasibility analysis
    """
    try:
        start_time = time.time()
        
        # Calculate timeline
        result = goal_planner.calculate_timeline(
            target_amount=request.target_amount,
            current_savings=request.current_savings,
            monthly_savings=request.monthly_savings
        )
        
        duration = time.time() - start_time
        
        # Track metrics
        track_prediction(
            user_id=0,
            model_type="goal_timeline",
            duration=duration
        )
        
        logger.info(
            f"Timeline calculated: {request.target_amount} in {result.get('months_needed', 0)} months",
            extra={"duration_ms": duration * 1000}
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid timeline request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Timeline calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.post("/reverse-plan", response_model=ReversePlanResponse)
async def reverse_plan(request: ReversePlanRequest):
    """
    Calculate required monthly savings to reach a goal by a target date.
    
    Simplified endpoint path that matches Node.js backend expectations.
    Same functionality as /api/v1/goals/reverse-plan.
    
    Args:
        request: ReversePlanRequest with goal parameters
    
    Returns:
        ReversePlanResponse with required savings and alternatives
    """
    try:
        start_time = time.time()
        
        # Calculate reverse plan
        result = goal_planner.reverse_plan(
            target_amount=request.target_amount,
            current_savings=request.current_savings,
            target_date=request.target_date
        )
        
        duration = time.time() - start_time
        
        # Track metrics
        track_prediction(
            user_id=0,
            model_type="goal_reverse_plan",
            duration=duration
        )
        
        logger.info(
            f"Reverse plan calculated: ${result.get('required_monthly_savings', 0)}/month needed",
            extra={"duration_ms": duration * 1000}
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid reverse plan request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reverse plan calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")
