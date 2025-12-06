"""
Main FastAPI application for Personal Finance ML Backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ml

# Create FastAPI app
app = FastAPI(
    title="Personal Finance ML Backend",
    description="AI-powered predictive analytics backend for personal finance management",
    version="1.0.0"
)

# Configure CORS
# WARNING: In production, update allow_origins to restrict access to specific domains
# Current setting (*) allows all origins and should be changed for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Update this in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ml.router)


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Personal Finance ML Backend",
        "version": "1.0.0",
        "endpoints": {
            "train": "POST /ml/train - Train a linear regression model for monthly savings",
            "predict": "POST /ml/predict - Predict monthly savings for future months"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
