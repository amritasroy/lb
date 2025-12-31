"""
Training Script for ChurnModel

This script is used by the CI pipeline to train the model with DVC-managed data.
"""
import argparse
import logging
from churn_model import ChurnModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main training function.
    
    Usage:
        python train.py --data-path /path/to/churn_data.csv --artifacts-dir ./artifacts
    """
    parser = argparse.ArgumentParser(description="Train ChurnModel")
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="Path to training data CSV file"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        default="./artifacts",
        help="Directory to save model artifacts"
    )
    
    args = parser.parse_args()
    
    logger.info("Initializing ChurnModel training...")
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Artifacts directory: {args.artifacts_dir}")
    
    # Initialize model
    model = ChurnModel(artifacts_dir=args.artifacts_dir)
    
    # Train model
    model.train(data_path=args.data_path)
    
    logger.info("Training completed successfully!")
    logger.info(f"Artifacts saved to: {args.artifacts_dir}")


if __name__ == "__main__":
    main()
