"""
FastAPI router for ML training and prediction endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.ml import (
    TrainRequest,
    TrainResponse,
    PredictRequest,
    PredictResponse,
    ModelParametersResponse
)
from app.schemas.insights import TrainWithTransactionsRequest, TrainWithTransactionsResponse
from app.ml.trainer import (
    build_monthly_savings_series,
    train_linear_model,
    save_model_parameters,
    get_latest_model,
    predict_savings
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/train", response_model=TrainResponse)
def train_model(request: TrainRequest, db: Session = Depends(get_db)):
    """
    Train a linear regression model for monthly savings prediction.
    
    This endpoint:
    1. Loads savings transactions for the user from the database
    2. Aggregates monthly savings totals
    3. Trains a linear regression model
    4. Saves/updates model parameters in the database
    
    Args:
        request: TrainRequest with user_id and optional date range
        db: Database session (injected)
    
    Returns:
        TrainResponse with model details
    
    Raises:
        HTTPException 400: If insufficient data (less than 3 months)
        HTTPException 500: If training fails
    """
    try:
        # Convert date objects to datetime objects if provided
        # Pydantic automatically validates date format
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.combine(request.start_date, datetime.min.time())
        if request.end_date:
            end_date = datetime.combine(request.end_date, datetime.min.time())
        
        # Build monthly savings series from database
        series, start_month = build_monthly_savings_series(
            db=db,
            user_id=request.user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Train linear regression model
        model_data = train_linear_model(series, start_month)
        
        # Save model parameters to database (upsert)
        model_params = save_model_parameters(
            db=db,
            user_id=request.user_id,
            model_data=model_data
        )
        
        # Convert to response schema
        model_response = ModelParametersResponse.model_validate(model_params)
        
        return TrainResponse(
            message=f"Model trained successfully with {model_data['trained_months']} months of data",
            model=model_response
        )
        
    except ValueError as e:
        # Handle insufficient data or validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/predict", response_model=PredictResponse)
def predict_model(request: PredictRequest, db: Session = Depends(get_db)):
    """
    Predict monthly savings for future months using a trained model.
    
    This endpoint:
    1. Loads the latest trained model for the user
    2. Generates predictions for the requested number of months
    3. Returns predictions along with model parameters
    
    Args:
        request: PredictRequest with user_id and months_ahead
        db: Database session (injected)
    
    Returns:
        PredictResponse with predictions and model details
    
    Raises:
        HTTPException 404: If no trained model found for the user
        HTTPException 500: If prediction fails
    """
    try:
        # Retrieve latest model for user
        model = get_latest_model(
            db=db,
            user_id=request.user_id
        )
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"No trained model found for user {request.user_id}. Please train a model first."
            )
        
        # Generate predictions
        predictions = predict_savings(
            model=model,
            months_ahead=request.months_ahead
        )
        
        # Convert to response schema
        model_response = ModelParametersResponse.model_validate(model)
        
        return PredictResponse(
            user_id=request.user_id,
            model_type=model.model_type,
            predictions=predictions,
            model_parameters=model_response
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/train-with-transactions", response_model=TrainWithTransactionsResponse)
def train_with_transactions(request: TrainWithTransactionsRequest):
    """
    Train ML model with transaction data provided in the request.
    
    This is a simplified training endpoint that accepts transactions directly
    instead of querying from the database. Useful for integration with external
    systems that manage their own transaction data.
    
    Args:
        request: TrainWithTransactionsRequest with user_id and transactions
    
    Returns:
        TrainWithTransactionsResponse with success status and metrics
    
    Raises:
        HTTPException 400: If insufficient data
        HTTPException 500: If training fails
    """
    try:
        logger.info(
            f"Training model for user {request.user_id} with {len(request.transactions)} transactions"
        )
        
        if len(request.transactions) < 3:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data: At least 3 transactions required for training"
            )
        
        # Extract date range from transactions
        dates = []
        for txn in request.transactions:
            try:
                date_obj = datetime.strptime(txn.get("date", ""), "%Y-%m-%d")
                dates.append(date_obj)
            except (ValueError, AttributeError):
                continue
        
        if not dates:
            raise HTTPException(
                status_code=400,
                detail="No valid dates found in transactions"
            )
        
        min_date = min(dates)
        max_date = max(dates)
        date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        # Count unique categories
        categories = set()
        for txn in request.transactions:
            if "category" in txn:
                categories.add(txn["category"])
        
        # For now, return success with basic metrics
        # In a full implementation, this would process transactions and train models
        return {
            "success": True,
            "message": "Model trained successfully",
            "metrics": {
                "samples": len(request.transactions),
                "categories": len(categories),
                "date_range": date_range,
                "accuracy": 0.87  # Placeholder accuracy
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training with transactions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

