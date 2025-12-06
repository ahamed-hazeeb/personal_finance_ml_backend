"""
Pydantic schemas for ML training and prediction endpoints.
"""
from datetime import date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    """Request schema for training endpoint."""
    user_id: int = Field(..., description="User ID to train model for")
    start_date: Optional[str] = Field(None, description="Start date for training data (YYYY-MM-DD format)")
    end_date: Optional[str] = Field(None, description="End date for training data (YYYY-MM-DD format)")


class ModelParametersResponse(BaseModel):
    """Response schema for model parameters."""
    id: int
    user_id: int
    model_type: str
    target_table: str
    slope: float
    intercept: float
    parameters: Dict
    last_trained_date: date
    
    class Config:
        from_attributes = True


class TrainResponse(BaseModel):
    """Response schema for training endpoint."""
    message: str
    model: ModelParametersResponse


class PredictRequest(BaseModel):
    """Request schema for prediction endpoint."""
    user_id: int = Field(..., description="User ID to predict for")
    months_ahead: int = Field(..., description="Number of months to predict ahead", gt=0)


class PredictResponse(BaseModel):
    """Response schema for prediction endpoint."""
    user_id: int
    model_type: str
    predictions: List[float]
    model_parameters: ModelParametersResponse
