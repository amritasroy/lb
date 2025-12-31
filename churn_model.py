"""
Customer Churn Model Implementation

This module implements the ChurnModel class for predicting customer churn
based on customer comments using TF-IDF vectorization and Random Forest classification.
"""
import os
import pickle
import logging
from typing import Dict, Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

from mlzone_model import MLZoneModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChurnModel(MLZoneModel):
    """
    Customer Churn Prediction Model.
    
    This model predicts the probability of customer churn based on
    customer comments using TF-IDF features and Random Forest classifier.
    """
    
    def __init__(self, artifacts_dir: str = "./artifacts"):
        """
        Initialize the ChurnModel.
        
        Args:
            artifacts_dir: Directory to save/load model artifacts
        """
        self.artifacts_dir = artifacts_dir
        self.model_path = os.path.join(artifacts_dir, "churn_model.pkl")
        self.vectorizer_path = os.path.join(artifacts_dir, "vectorizer.pkl")
        
        self.clf = None
        self.vectorizer = None
        
        # Create artifacts directory if it doesn't exist
        os.makedirs(artifacts_dir, exist_ok=True)
    
    def train(self, data_path: str) -> None:
        """
        Train the churn prediction model.
        
        This method:
        1. Loads the training data from the specified path
        2. Preprocesses customer comments using TF-IDF vectorization
        3. Trains a Random Forest classifier
        4. Saves both the model and vectorizer artifacts
        
        Args:
            data_path: Path to the training data CSV file
                      Expected columns: 'customer_comments', 'churned'
        
        Note:
            In production, large datasets (50GB+) are managed via DVC.
            The data_path should point to DVC-managed data location.
        """
        logger.info(f"Starting training with data from: {data_path}")
        
        # Load data
        # Note: For production 50GB datasets, consider chunking or Dask
        # For this implementation, we assume data fits in memory or is sampled
        logger.info("Loading training data...")
        df = pd.read_csv(data_path)
        
        logger.info(f"Loaded {len(df)} records")
        
        # Validate required columns
        if 'customer_comments' not in df.columns or 'churned' not in df.columns:
            raise ValueError("Data must contain 'customer_comments' and 'churned' columns")
        
        # Preprocessing: TF-IDF Vectorization
        # Note: customer_comments may contain PII - ensure proper data handling
        logger.info("Fitting TF-IDF vectorizer...")
        self.vectorizer = TfidfVectorizer(max_features=1000)
        X = self.vectorizer.fit_transform(df['customer_comments'])
        y = df['churned']
        
        # Training: Random Forest Classifier
        logger.info("Training Random Forest classifier...")
        self.clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        self.clf.fit(X, y)
        
        # Save artifacts
        logger.info(f"Saving model artifacts to {self.artifacts_dir}")
        with open(self.model_path, "wb") as f:
            pickle.dump(self.clf, f)
        
        with open(self.vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        
        logger.info("Training completed successfully")
    
    def load_artifacts(self) -> None:
        """
        Load pre-trained model artifacts.
        
        This method loads the trained classifier and vectorizer from disk.
        Called during service initialization before serving predictions.
        
        Raises:
            FileNotFoundError: If artifacts are not found
        """
        logger.info("Loading model artifacts...")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model artifact not found at {self.model_path}")
        
        if not os.path.exists(self.vectorizer_path):
            raise FileNotFoundError(f"Vectorizer artifact not found at {self.vectorizer_path}")
        
        with open(self.model_path, "rb") as f:
            self.clf = pickle.load(f)
        
        with open(self.vectorizer_path, "rb") as f:
            self.vectorizer = pickle.load(f)
        
        logger.info("Artifacts loaded successfully")
    
    def predict(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict churn probability for a single customer.
        
        This method is optimized for real-time single-request inference.
        
        Args:
            input_json: Dictionary with format:
                       {'comments': 'I want to cancel my subscription...'}
        
        Returns:
            Dictionary with format:
            {'churn_prob': 0.75}
        
        Raises:
            ValueError: If input format is invalid
            RuntimeError: If model is not loaded
        """
        # Lazy load artifacts on first prediction
        if self.clf is None or self.vectorizer is None:
            self.load_artifacts()
        
        # Validate input
        if 'comments' not in input_json:
            raise ValueError("Input must contain 'comments' field")
        
        comments = input_json['comments']
        
        # Ensure comments is a string
        if not isinstance(comments, str):
            raise ValueError("'comments' field must be a string")
        
        # Preprocess input using the same vectorizer
        X = self.vectorizer.transform([comments])
        
        # Get prediction probability
        # predict_proba returns [prob_no_churn, prob_churn]
        proba = self.clf.predict_proba(X)[0]
        churn_probability = float(proba[1])
        
        return {'churn_prob': churn_probability}
