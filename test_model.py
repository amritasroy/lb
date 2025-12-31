"""
Simple test script to verify the ChurnModel implementation
"""
import os
import tempfile
import shutil

from churn_model import ChurnModel


def test_train_and_predict():
    """Test training and prediction workflow"""
    print("Testing ChurnModel training and prediction...")
    
    # Create temporary directory for artifacts
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize model
        model = ChurnModel(artifacts_dir=temp_dir)
        
        # Train with sample data
        print("Training model...")
        model.train(data_path="sample_data.csv")
        
        # Verify artifacts were created
        assert os.path.exists(os.path.join(temp_dir, "churn_model.pkl"))
        assert os.path.exists(os.path.join(temp_dir, "vectorizer.pkl"))
        print("✓ Artifacts created successfully")
        
        # Test prediction
        print("Testing prediction...")
        result = model.predict({
            "comments": "I want to cancel my subscription because it's too expensive"
        })
        
        assert "churn_prob" in result
        assert 0 <= result["churn_prob"] <= 1
        print(f"✓ Prediction successful: churn_prob={result['churn_prob']:.3f}")
        
        # Test another prediction
        result2 = model.predict({
            "comments": "I love this service and will continue using it!"
        })
        print(f"✓ Second prediction successful: churn_prob={result2['churn_prob']:.3f}")
        
        print("\n✓ All tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_train_and_predict()
