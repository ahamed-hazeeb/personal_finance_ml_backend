"""
FastAPI router for goal planning endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.schemas.goals import (
    CalculateTimelineRequest,
    CalculateTimelineResponse,
    ReversePlanRequest,
    ReversePlanResponse
)
from app.models.goal_planner import GoalPlanner
from app.core.logging import get_logger
from app.core.monitoring import track_prediction
import time

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/goals", tags=["Goal Planning"])

# Initialize goal planner
goal_planner = GoalPlanner()


@router.post("/calculate-timeline", response_model=CalculateTimelineResponse)
async def calculate_timeline(request: CalculateTimelineRequest):
    """
    Calculate timeline to reach a financial goal.
    
    This endpoint:
    1. Takes target amount, current savings, and monthly savings
    2. Calculates months needed to reach the goal
    3. Provides feasibility analysis
    4. Generates milestone checkpoints
    
    Args:
        request: CalculateTimelineRequest with goal parameters
    
    Returns:
        CalculateTimelineResponse with timeline and feasibility analysis
    
    Raises:
        HTTPException 400: If parameters are invalid
        HTTPException 500: If calculation fails
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
            user_id=0,  # No user_id in request, use placeholder
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
    
    This endpoint:
    1. Takes target amount, current savings, and target date
    2. Calculates required monthly savings
    3. Provides feasibility analysis
    4. Suggests alternative timelines
    
    Args:
        request: ReversePlanRequest with goal parameters
    
    Returns:
        ReversePlanResponse with required savings and alternatives
    
    Raises:
        HTTPException 400: If parameters are invalid
        HTTPException 500: If calculation fails
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
            user_id=0,  # No user_id in request, use placeholder
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
