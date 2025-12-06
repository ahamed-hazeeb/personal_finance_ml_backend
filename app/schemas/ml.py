"""
Pydantic schemas for ML training and prediction endpoints.
"""
from datetime import date as date_type
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    """Request schema for training endpoint."""
    user_id: int = Field(..., description="User ID to train model for")
    start_date: Optional[date_type] = Field(None, description="Start date for training data")
    end_date: Optional[date_type] = Field(None, description="End date for training data")


class ModelParametersResponse(BaseModel):
    """Response schema for model parameters."""
    id: int
    user_id: int
    model_type: str
    target_table: str
    slope: float
    intercept: float
    parameters: Dict
    last_trained_date: date_type
    
    class Config:
        from_attributes = True  # Pydantic v2 syntax


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
