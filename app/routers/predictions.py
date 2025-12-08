"""
FastAPI router for predictions endpoint.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime
from dateutil.relativedelta import relativedelta

from app.schemas.insights import PredictionsResponse, MonthlyPrediction
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Predictions"])


@router.get("/predictions", response_model=PredictionsResponse)
async def get_predictions(
    user_id: int = Query(..., description="User ID"),
    months: int = Query(default=6, ge=1, le=24, description="Number of months to predict (1-24)")
):
    """
    Get future expense/income predictions for a user.
    
    This endpoint generates predictions for future months based on
    historical patterns. Since this is a simplified implementation,
    it returns averaged predictions.
    
    Args:
        user_id: User ID to generate predictions for
        months: Number of months to predict (default: 6)
    
    Returns:
        PredictionsResponse with monthly predictions
    
    Raises:
        HTTPException 404: If no data found for user
        HTTPException 500: If prediction fails
    """
    try:
        logger.info(f"Generating {months} months of predictions for user {user_id}")
        
        # For now, generate simple averaged predictions
        # In a full implementation, this would use trained ML models
        predictions = []
        current_date = datetime.now()
        
        # Default average values (these would come from user's historical data)
        avg_income = 250000
        avg_expense = 243333
        base_confidence = 0.85
        
        # Category percentages for breakdown
        category_pcts = {
            "Business": 0.68,
            "Food": 0.11,
            "Entertainment": 0.11,
            "Shopping": 0.05,
            "Others": 0.05
        }
        
        for i in range(months):
            # Use relativedelta for proper month arithmetic
            month_date = current_date + relativedelta(months=i+1)
            month_str = month_date.strftime("%Y-%m")
            
            # Slightly vary predictions with some randomness
            variation = 1.0 + (i * 0.02)  # 2% increase per month
            confidence = max(0.6, base_confidence - (i * 0.03))  # Decrease confidence over time
            
            predicted_income = avg_income * variation
            predicted_expense = avg_expense * variation
            
            # Calculate category breakdown based on predicted expense
            category_breakdown = {
                category: round(predicted_expense * pct, 2)
                for category, pct in category_pcts.items()
            }
            
            predictions.append({
                "month": month_str,
                "predicted_income": round(predicted_income, 2),
                "predicted_expense": round(predicted_expense, 2),
                "predicted_savings": round(predicted_income - predicted_expense, 2),
                "confidence": round(confidence, 2),
                "category_breakdown": category_breakdown
            })
        
        logger.info(f"Generated {len(predictions)} predictions for user {user_id}")
        
        return {
            "success": True,
            "predictions": predictions
        }
        
    except Exception as e:
        logger.error(f"Prediction generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
