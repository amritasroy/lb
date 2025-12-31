"""
MLZone Platform Base Model Class

This is the base class that all models deployed on the MLZone platform must inherit from.
It provides a standardized interface for training and inference.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class MLZoneModel(ABC):
    """
    Base class for all MLZone models.
    
    Models inheriting from this class must implement:
    - train(): for CI pipeline training
    - predict(): for real-time inference service
    """
    
    @abstractmethod
    def train(self, data_path: str) -> None:
        """
        Train the model and save artifacts.
        
        This method is called by the CI pipeline to train the model
        and persist all necessary artifacts (model, preprocessors, etc.)
        
        Args:
            data_path: Path to the training data
        """
        pass
    
    @abstractmethod
    def predict(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions on input data.
        
        This method is called by the Inference Service for real-time predictions.
        
        Args:
            input_json: Dictionary containing input data
            
        Returns:
            Dictionary containing prediction results
        """
        pass
