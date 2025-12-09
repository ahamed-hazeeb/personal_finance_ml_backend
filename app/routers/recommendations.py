"""
FastAPI router for recommendation endpoints.
"""
from fastapi import APIRouter, HTTPException

from app.schemas.recommendations import (
    RecommendationsRequest, HabitsResponse, SubscriptionsResponse,
    OpportunitiesResponse, NudgesResponse
)
from app.models.recommendation_engine import get_recommendation_engine
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])

# Get recommendation engine instance
recommender = get_recommendation_engine()


@router.get("/habits/{user_id}", response_model=HabitsResponse)
@router.post("/habits", response_model=HabitsResponse)
async def get_spending_habits(
    user_id: int = None,
    request: RecommendationsRequest = None
):
    """
    Analyze spending habits and patterns.
    
    Identifies:
    - High-frequency spending categories
    - Food delivery habits
    - Entertainment spending patterns
    - Frequency per week analysis
    
    Args:
        user_id: User ID (GET request)
        request: Recommendations request (POST request)
    
    Returns:
        HabitsResponse with spending habit insights
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If analysis fails
    """
    try:
        if request:
            user_id = request.user_id
            transactions = request.transactions
            analysis_months = request.analysis_months
        else:
            raise HTTPException(status_code=400, detail="Request body required for POST")
        
        logger.info(f"Analyzing spending habits for user {user_id}")
        
        # Analyze habits
        habits = recommender.analyze_spending_habits(
            transactions=transactions,
            analysis_months=analysis_months
        )
        
        logger.info(f"Found {len(habits)} spending habits for user {user_id}")
        
        return {
            'success': True,
            'user_id': user_id,
            'habits': habits,
            'habits_count': len(habits),
            'analysis_period_months': analysis_months
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spending habits analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Spending habits analysis failed: {str(e)}"
        )


@router.post("/subscriptions", response_model=SubscriptionsResponse)
async def detect_subscriptions(request: RecommendationsRequest):
    """
    Detect recurring subscription charges.
    
    Identifies:
    - Monthly subscriptions
    - Weekly subscriptions
    - Quarterly subscriptions
    - Estimated annual costs
    
    Args:
        request: Recommendations request
    
    Returns:
        SubscriptionsResponse with detected subscriptions
    
    Raises:
        HTTPException 500: If detection fails
    """
    try:
        logger.info(f"Detecting subscriptions for user {request.user_id}")
        
        # Detect subscriptions
        subscriptions = recommender.detect_subscriptions(
            transactions=request.transactions
        )
        
        # Calculate totals
        total_monthly = sum(
            sub['amount'] if sub['frequency'] == 'monthly' else
            sub['amount'] * 4 if sub['frequency'] == 'weekly' else
            sub['amount'] / 3 if sub['frequency'] == 'quarterly' else 0
            for sub in subscriptions
        )
        
        total_annual = sum(sub['estimated_annual_cost'] for sub in subscriptions)
        
        logger.info(f"Found {len(subscriptions)} subscriptions for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            'subscriptions': subscriptions,
            'subscription_count': len(subscriptions),
            'total_monthly_cost': round(total_monthly, 2),
            'total_annual_cost': round(total_annual, 2)
        }
        
    except Exception as e:
        logger.error(f"Subscription detection failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Subscription detection failed: {str(e)}"
        )


@router.post("/opportunities", response_model=OpportunitiesResponse)
async def get_savings_opportunities(request: RecommendationsRequest):
    """
    Identify savings opportunities based on spending patterns.
    
    Identifies:
    - Hidden fees (small recurring charges)
    - Impulse purchases
    - Weekend vs weekday spending patterns
    - High variance categories
    
    Args:
        request: Recommendations request
    
    Returns:
        OpportunitiesResponse with savings opportunities
    
    Raises:
        HTTPException 500: If identification fails
    """
    try:
        logger.info(f"Identifying savings opportunities for user {request.user_id}")
        
        # Identify opportunities
        opportunities = recommender.identify_savings_opportunities(
            transactions=request.transactions,
            analysis_months=request.analysis_months
        )
        
        # Calculate total potential savings
        total_savings = sum(
            opp.get('potential_savings', 0) 
            for opp in opportunities 
            if opp.get('potential_savings')
        )
        
        logger.info(f"Found {len(opportunities)} savings opportunities for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            'opportunities': opportunities,
            'opportunity_count': len(opportunities),
            'total_potential_savings': round(total_savings, 2)
        }
        
    except Exception as e:
        logger.error(f"Savings opportunity identification failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Savings opportunity identification failed: {str(e)}"
        )


@router.post("/nudges", response_model=NudgesResponse)
async def get_behavior_nudges(request: RecommendationsRequest):
    """
    Generate behavior nudges for positive reinforcement and warnings.
    
    Provides:
    - Positive reinforcement (spending reduction, savings streak)
    - Warnings (spending increase)
    - Milestone celebrations (50%, 75% goal progress)
    - Goal reminders
    - No-spend day recognition
    
    Args:
        request: Recommendations request
    
    Returns:
        NudgesResponse with behavior nudges
    
    Raises:
        HTTPException 500: If generation fails
    """
    try:
        logger.info(f"Generating behavior nudges for user {request.user_id}")
        
        # Generate nudges
        nudges = recommender.generate_behavior_nudges(
            transactions=request.transactions,
            goals=request.goals
        )
        
        logger.info(f"Generated {len(nudges)} behavior nudges for user {request.user_id}")
        
        return {
            'success': True,
            'user_id': request.user_id,
            'nudges': nudges,
            'nudge_count': len(nudges)
        }
        
    except Exception as e:
        logger.error(f"Behavior nudge generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Behavior nudge generation failed: {str(e)}"
        )
