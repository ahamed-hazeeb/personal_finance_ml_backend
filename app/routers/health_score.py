"""
FastAPI router for financial health score endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.schemas.health_score import (
    HealthScoreRequest, HealthScoreResponse, TrendsResponse, 
    BenchmarkResponse, BenchmarkData, HealthScoreTrend
)
from app.models.financial_health_scorer import get_health_scorer
from app.db import get_db, FinancialHealthHistory, UserBenchmarks
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/insights", tags=["Financial Health"])

# Get health scorer instance
health_scorer = get_health_scorer()


@router.post("/health-score", response_model=HealthScoreResponse)
async def calculate_health_score(
    request: HealthScoreRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate comprehensive financial health score (0-100).
    
    Analyzes:
    - Savings rate (30%)
    - Expense consistency (25%)
    - Emergency fund (20%)
    - Debt-to-income ratio (15%)
    - Goal progress (10%)
    
    Args:
        request: Health score calculation request
        db: Database session
    
    Returns:
        HealthScoreResponse with overall score, components, and recommendations
    
    Raises:
        HTTPException 400: If request data is invalid
        HTTPException 500: If calculation fails
    """
    try:
        logger.info(f"Calculating health score for user {request.user_id}")
        
        # Calculate health score
        result = health_scorer.calculate_overall_score(
            transactions=request.transactions,
            emergency_savings=request.emergency_savings,
            monthly_debt_payment=request.monthly_debt_payment,
            goals=request.goals
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Save to database
        try:
            health_record = FinancialHealthHistory(
                user_id=request.user_id,
                score=int(result['overall_score']),
                savings_rate_score=result['component_scores']['savings_rate']['score'],
                expense_consistency_score=result['component_scores']['expense_consistency']['score'],
                emergency_fund_score=result['component_scores']['emergency_fund']['score'],
                debt_ratio_score=result['component_scores']['debt_to_income']['score'],
                goal_progress_score=result['component_scores']['goal_progress']['score'],
                grade=result['grade'],
                recommendations=result['recommendations'],
                calculated_at=datetime.fromisoformat(result['calculated_at'])
            )
            db.add(health_record)
            db.commit()
            logger.info(f"Saved health score record for user {request.user_id}")
        except Exception as db_error:
            logger.warning(f"Failed to save health score to database: {str(db_error)}")
            db.rollback()
        
        return {
            'success': True,
            'user_id': request.user_id,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health score calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health score calculation failed: {str(e)}")


@router.get("/trends/{user_id}", response_model=TrendsResponse)
async def get_health_trends(
    user_id: int,
    months: int = 6,
    db: Session = Depends(get_db)
):
    """
    Get historical health score trends for a user.
    
    Provides:
    - Historical score data
    - Month-over-month change
    - Quarter-over-quarter change
    
    Args:
        user_id: User ID
        months: Number of months of history to return (default 6)
        db: Database session
    
    Returns:
        TrendsResponse with historical trend data and changes
    
    Raises:
        HTTPException 404: If no data found for user
        HTTPException 500: If retrieval fails
    """
    try:
        logger.info(f"Fetching health trends for user {user_id}")
        
        # Query historical data
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        
        records = db.query(FinancialHealthHistory).filter(
            FinancialHealthHistory.user_id == user_id,
            FinancialHealthHistory.calculated_at >= cutoff_date
        ).order_by(FinancialHealthHistory.calculated_at.asc()).all()
        
        if not records:
            raise HTTPException(
                status_code=404, 
                detail=f"No health score history found for user {user_id}"
            )
        
        # Convert to trend data
        trend_data = [
            HealthScoreTrend(
                score=float(record.score),
                grade=record.grade,
                calculated_at=record.calculated_at.isoformat()
            )
            for record in records
        ]
        
        # Calculate changes
        current_score = float(records[-1].score)
        
        # Month-over-month change
        mom_change = None
        if len(records) >= 2:
            one_month_ago = datetime.now() - timedelta(days=30)
            older_records = [r for r in records if r.calculated_at < one_month_ago]
            if older_records:
                old_score = float(older_records[-1].score)
                mom_change = ((current_score - old_score) / old_score) * 100 if old_score > 0 else 0
        
        # Quarter-over-quarter change
        qoq_change = None
        if len(records) >= 2:
            three_months_ago = datetime.now() - timedelta(days=90)
            older_records = [r for r in records if r.calculated_at < three_months_ago]
            if older_records:
                old_score = float(older_records[-1].score)
                qoq_change = ((current_score - old_score) / old_score) * 100 if old_score > 0 else 0
        
        return {
            'success': True,
            'user_id': user_id,
            'current_score': current_score,
            'trend_data': trend_data,
            'month_over_month_change': round(mom_change, 2) if mom_change is not None else None,
            'quarter_over_quarter_change': round(qoq_change, 2) if qoq_change is not None else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve health trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")


@router.get("/benchmark/{user_id}", response_model=BenchmarkResponse)
async def get_benchmark_comparison(
    user_id: int,
    age_group: Optional[str] = None,
    income_bracket: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare user's health score against peer benchmarks.
    
    Provides anonymized comparison with users in similar:
    - Age group (e.g., '25-30', '31-35')
    - Income bracket (e.g., '50-75k', '75-100k')
    
    Args:
        user_id: User ID
        age_group: User's age group (optional)
        income_bracket: User's income bracket (optional)
        db: Database session
    
    Returns:
        BenchmarkResponse with peer comparison data
    
    Raises:
        HTTPException 404: If no user data or benchmark data found
        HTTPException 500: If comparison fails
    """
    try:
        logger.info(f"Fetching benchmark comparison for user {user_id}")
        
        # Get user's most recent score
        user_record = db.query(FinancialHealthHistory).filter(
            FinancialHealthHistory.user_id == user_id
        ).order_by(FinancialHealthHistory.calculated_at.desc()).first()
        
        if not user_record:
            raise HTTPException(
                status_code=404,
                detail=f"No health score found for user {user_id}"
            )
        
        user_score = float(user_record.score)
        
        # Get benchmark data
        benchmark_query = db.query(UserBenchmarks)
        
        if age_group:
            benchmark_query = benchmark_query.filter(UserBenchmarks.age_group == age_group)
        if income_bracket:
            benchmark_query = benchmark_query.filter(UserBenchmarks.income_bracket == income_bracket)
        
        benchmark = benchmark_query.first()
        
        if not benchmark:
            # No exact match, get overall average
            logger.warning(f"No exact benchmark match for age_group={age_group}, income_bracket={income_bracket}")
            all_benchmarks = db.query(UserBenchmarks).all()
            
            if not all_benchmarks:
                # Create synthetic benchmark if no data exists
                peer_average = 65.0  # Default benchmark
                logger.info("Using default synthetic benchmark")
            else:
                # Calculate weighted average
                total_samples = sum(b.sample_size or 1 for b in all_benchmarks)
                peer_average = sum(
                    (b.avg_health_score or 65.0) * (b.sample_size or 1) 
                    for b in all_benchmarks
                ) / total_samples if total_samples > 0 else 65.0
        else:
            peer_average = float(benchmark.avg_health_score or 65.0)
        
        # Calculate percentile (simplified)
        if user_score > peer_average:
            percentile = 50 + min(50, (user_score - peer_average) / peer_average * 100)
        else:
            percentile = 50 - min(50, (peer_average - user_score) / peer_average * 100)
        
        # Generate comparison message
        diff = user_score - peer_average
        if abs(diff) < 5:
            comparison = "Your score is similar to your peer group average"
        elif diff > 0:
            comparison = f"Your score is {abs(diff):.1f} points above your peer group average"
        else:
            comparison = f"Your score is {abs(diff):.1f} points below your peer group average"
        
        return {
            'success': True,
            'user_id': user_id,
            'age_group': age_group,
            'income_bracket': income_bracket,
            'benchmark': BenchmarkData(
                user_score=user_score,
                peer_average=round(peer_average, 2),
                percentile=round(percentile, 2),
                comparison=comparison
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Benchmark comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark comparison failed: {str(e)}")
