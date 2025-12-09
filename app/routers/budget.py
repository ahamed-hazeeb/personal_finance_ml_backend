"""
FastAPI router for budget endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.budget import (
    BudgetRecommendRequest, BudgetRecommendResponse,
    BudgetAlertsRequest, BudgetAlertsResponse,
    OptimizeRequest, OptimizeResponse,
    BudgetAlert
)
from app.models.budget_optimizer import get_budget_optimizer
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/budget", tags=["Budget Management"])

# Get budget optimizer instance
optimizer = get_budget_optimizer()


@router.post("/recommend", response_model=BudgetRecommendResponse)
async def get_budget_recommendations(request: BudgetRecommendRequest):
    """
    Generate personalized budget recommendations using 50/30/20 rule.
    
    Analyzes:
    - Historical spending patterns (3-12 months)
    - Income patterns
    - Active financial goals
    - Category-wise spending
    
    Provides:
    - Recommended budget allocation (needs/wants/savings)
    - Current spending analysis
    - Required adjustments
    - Category-specific recommendations
    
    Args:
        request: Budget recommendation request
    
    Returns:
        BudgetRecommendResponse with personalized budget
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If generation fails
    """
    try:
        logger.info(f"Generating budget recommendations for user {request.user_id}")
        
        # Generate recommendations
        result = optimizer.generate_budget_recommendations(
            transactions=request.transactions,
            goals=request.goals,
            analysis_months=request.analysis_months
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        logger.info(f"Budget recommendations generated for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget recommendation generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Budget recommendation generation failed: {str(e)}"
        )


@router.post("/alerts", response_model=BudgetAlertsResponse)
async def get_budget_alerts(request: BudgetAlertsRequest):
    """
    Get real-time budget overspending alerts.
    
    Analyzes current month spending and provides:
    - Projected overspending alerts (based on current rate)
    - Already exceeded budget alerts
    - Days remaining in month
    
    Args:
        request: Budget alerts request with current budget
    
    Returns:
        BudgetAlertsResponse with active alerts
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If alert detection fails
    """
    try:
        logger.info(f"Checking budget alerts for user {request.user_id}")
        
        # Detect alerts
        alerts = optimizer.detect_overspending_alerts(
            transactions=request.transactions,
            budget=request.budget
        )
        
        logger.info(f"Found {len(alerts)} budget alerts for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            'alerts': alerts,
            'alert_count': len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Budget alert detection failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Budget alert detection failed: {str(e)}"
        )


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_budget(request: OptimizeRequest):
    """
    Provide budget optimization suggestions to reach target savings rate.
    
    Analyzes spending and suggests:
    - Categories to reduce
    - Specific reduction amounts
    - Projected savings rate after optimizations
    
    Args:
        request: Optimization request with target savings rate
    
    Returns:
        OptimizeResponse with optimization suggestions
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If optimization fails
    """
    try:
        logger.info(
            f"Optimizing budget for user {request.user_id} "
            f"with target savings rate {request.target_savings_rate * 100:.0f}%"
        )
        
        # Generate optimization suggestions
        result = optimizer.optimize_budget(
            transactions=request.transactions,
            target_savings_rate=request.target_savings_rate
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        logger.info(f"Budget optimization complete for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget optimization failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Budget optimization failed: {str(e)}"
        )
