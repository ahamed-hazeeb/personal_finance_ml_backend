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
from app.ml.trainer import (
    build_monthly_savings_series,
    train_linear_model,
    save_model_parameters,
    get_latest_model,
    predict_savings
)

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
        # Parse dates if provided
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        if request.end_date:
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # Build monthly savings series from database
        series = build_monthly_savings_series(
            db=db,
            user_id=request.user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Train linear regression model
        model_data = train_linear_model(series)
        
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
