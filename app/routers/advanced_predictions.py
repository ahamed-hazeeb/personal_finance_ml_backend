"""
FastAPI router for advanced predictions endpoint.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from app.models.advanced_expense_predictor import get_advanced_forecaster
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["Advanced Predictions"])

# Get forecaster instance
forecaster = get_advanced_forecaster()


class AdvancedExpenseRequest(BaseModel):
    """Request schema for advanced expense prediction."""
    user_id: int = Field(..., description="User ID")
    transactions: List[Dict[str, Any]] = Field(..., description="List of transactions")
    forecast_months: int = Field(1, description="Number of months to forecast (1-12)", ge=1, le=12)


class AdvancedExpenseResponse(BaseModel):
    """Response schema for advanced expense prediction."""
    success: bool = Field(default=True, description="Success status")
    user_id: int = Field(..., description="User ID")
    model_type: str = Field(..., description="Model used: holt_winters, arima, or linear")
    forecast: List[float] = Field(..., description="Forecasted expenses")
    confidence_interval_lower: List[float] = Field(..., description="Lower confidence bound")
    confidence_interval_upper: List[float] = Field(..., description="Upper confidence bound")
    confidence_level: float = Field(..., description="Confidence level (0.95)")
    months_of_data: int = Field(..., description="Months of historical data used")
    last_month_expense: float = Field(..., description="Most recent month expense")
    average_monthly_expense: float = Field(..., description="Average monthly expense")
    trained_at: str = Field(..., description="Training timestamp")


@router.post("/expense/advanced", response_model=AdvancedExpenseResponse)
async def get_advanced_expense_forecast(request: AdvancedExpenseRequest):
    """
    Get advanced expense forecasts using time-series models.
    
    Automatically selects the best model:
    - 12+ months: Holt-Winters exponential smoothing (seasonal patterns)
    - 6-11 months: ARIMA (trend-based forecasting)
    - 3-5 months: Linear regression (simple trend)
    
    Provides confidence intervals for uncertainty quantification.
    
    Args:
        request: Advanced expense prediction request
    
    Returns:
        AdvancedExpenseResponse with forecasts and confidence intervals
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If prediction fails
    """
    try:
        logger.info(
            f"Generating advanced expense forecast for user {request.user_id} "
            f"for {request.forecast_months} months"
        )
        
        # Generate forecast
        result = forecaster.forecast(
            transactions=request.transactions,
            forecast_months=request.forecast_months
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        logger.info(
            f"Advanced forecast complete for user {request.user_id} "
            f"using {result.get('model_type')} model"
        )
        
        return {
            'success': True,
            'user_id': request.user_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced expense forecast failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Advanced expense forecast failed: {str(e)}"
        )
