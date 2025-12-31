"""
Inference Service for ChurnModel

FastAPI-based REST API for serving real-time churn predictions.
Designed to run with Gunicorn + Uvicorn workers on Kubernetes.
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any

from churn_model import ChurnModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Churn Prediction Service",
    description="Real-time customer churn prediction API",
    version="1.0.0"
)

# Global model instance - loaded once per worker
model = None


class PredictionRequest(BaseModel):
    """Request schema for churn prediction"""
    comments: str = Field(
        ...,
        description="Customer comments text",
        example="I want to cancel my subscription because the service is too expensive"
    )


class PredictionResponse(BaseModel):
    """Response schema for churn prediction"""
    churn_prob: float = Field(
        ...,
        description="Probability of customer churn (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )


@app.on_event("startup")
async def startup_event():
    """
    Load model artifacts on service startup.
    
    This ensures the model is loaded once per worker process,
    reducing memory footprint and improving response times.
    """
    global model
    logger.info("Starting up Churn Prediction Service...")
    
    try:
        model = ChurnModel(artifacts_dir="./artifacts")
        model.load_artifacts()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns service status - used by Kubernetes liveness/readiness probes.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    return {"status": "healthy", "model": "loaded"}


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, str]:
    """Root endpoint with service information"""
    return {
        "service": "Churn Prediction Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Predict churn probability for a customer.
    
    This endpoint handles real-time single-request inference.
    
    Args:
        request: PredictionRequest containing customer comments
    
    Returns:
        PredictionResponse with churn probability
    
    Raises:
        HTTPException: If prediction fails
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        logger.info("Received prediction request")
        input_data = {"comments": request.comments}
        result = model.predict(input_data)
        logger.info(f"Prediction completed: churn_prob={result['churn_prob']:.3f}")
        return PredictionResponse(**result)
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )
