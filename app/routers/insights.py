"""
FastAPI router for insights endpoint.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.transactions import TransactionSchema, TransactionListRequest
from app.schemas.insights import InsightsResponse
from app.services.insight_service import get_insight_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Insights"])

# Get insight service instance
insight_service = get_insight_service()


@router.post("/insights", response_model=InsightsResponse)
async def get_insights(request: TransactionListRequest):
    """
    Analyze user transactions and return AI-powered insights.
    
    This endpoint:
    1. Analyzes spending patterns across categories
    2. Detects anomalies and unusual transactions
    3. Identifies spending trends
    4. Finds savings opportunities
    5. Generates predictions for future expenses
    6. Provides actionable recommendations
    
    Args:
        request: TransactionListRequest with user_id and transaction list
    
    Returns:
        InsightsResponse with insights, patterns, predictions, and recommendations
    
    Raises:
        HTTPException 400: If transaction data is invalid
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            f"Generating insights for user {request.user_id} with {len(request.transactions)} transactions"
        )
        
        # Generate insights
        result = insight_service.generate_insights(request.transactions)
        
        # Defensive normalization: ensure all insights have a severity field
        normalized_count = 0
        for insight in result['insights']:
            if not insight.get('severity') or insight.get('severity') == '':
                insight['severity'] = 'info'
                normalized_count += 1
                logger.debug(
                    f"Normalized insight missing severity: type={insight.get('type')}, "
                    f"message={insight.get('message', '')[:50]}"
                )
        
        if normalized_count > 0:
            logger.debug(f"Normalized {normalized_count} insights with missing severity field")
        
        logger.info(
            f"Generated {len(result['insights'])} insights for user {request.user_id}"
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid insights request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Insights generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")
