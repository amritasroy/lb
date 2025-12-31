# MLZone Platform: Submission Package

This document provides guidance on packaging and submitting this solution.

## Files Included

### Core Implementation (Part A)
- `mlzone_model.py` - Base platform wrapper class
- `churn_model.py` - ChurnModel implementation with train() and predict()
- `app.py` - FastAPI inference service
- `train.py` - Training script for CI pipeline

### Packaging (Part B)
- `Dockerfile` - Multi-stage optimized container image
- `.dockerignore` - Excludes unnecessary files from image

### Deployment (Part C)
- `deployment.yaml` - Complete Kubernetes configuration
- `start.sh` - Production startup script with Gunicorn+Uvicorn

### Additional Files
- `README.md` - Comprehensive documentation with design decisions
- `requirements.txt` - Python dependencies
- `sample_data.csv` - Sample training data for testing
- `test_model.py` - Simple test script
- `.gitignore` - Git ignore patterns

## How to Create Submission Package

### Option 1: Create ZIP without Git history

```bash
# From the repository root
zip -r mlzone-churn-model.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "artifacts/*"
```

### Option 2: Export from Git

```bash
# Create a clean export
git archive --format=zip --output=mlzone-churn-model.zip HEAD
```

### Option 3: Manual Selection

Create a new folder and copy these files:
```
mlzone-churn-model/
├── README.md              # Start here - explains everything
├── mlzone_model.py        # Part A: Base class
├── churn_model.py         # Part A: Implementation
├── app.py                 # Part A: Service wrapper
├── train.py               # Part A: Training script
├── Dockerfile             # Part B: Container image
├── .dockerignore          # Part B: Build optimization
├── deployment.yaml        # Part C: Kubernetes config
├── start.sh               # Part C: Startup command
├── requirements.txt       # Dependencies
├── sample_data.csv        # Test data
└── test_model.py          # Simple test
```

## Quick Start for Reviewers

### 1. Review the Architecture
Start with `README.md` which explains all design decisions.

### 2. Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Train with sample data
python train.py --data-path sample_data.csv --artifacts-dir ./artifacts

# Run service
uvicorn app:app --host 0.0.0.0 --port 8000

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"comments": "I want to cancel my subscription"}'
```

### 3. Review the Code

**Part A - MLZoneModel Implementation:**
- `mlzone_model.py` - Interface definition
- `churn_model.py` - Actual implementation (main file)
- `app.py` - How it's served

**Part B - Dockerfile:**
- Multi-stage build
- No artifacts in image (design decision explained in README)
- Optimized for build speed and deployment latency

**Part C - Deployment:**
- `deployment.yaml` - Full K8s configuration
- `start.sh` - Gunicorn command with detailed comments
- Memory calculation: 2 workers × 5GB = 10GB (fits in 16GB node)

## Key Design Decisions

All design decisions are documented in the README.md, including:

1. **Consistent Preprocessing**: Vectorizer saved with model
2. **Artifacts NOT in Docker Image**: Mounted at runtime
3. **Worker Count**: 2 workers (calculated from memory constraints)
4. **Lazy vs Eager Loading**: Lazy for faster startup
5. **Health Checks**: Tuned for model loading time
6. **Resource Limits**: Based on actual memory footprint

## Production Checklist

Before production deployment:
- [ ] Replace sample data with actual DVC-managed data
- [ ] Configure GCS bucket for model artifacts
- [ ] Update deployment.yaml with actual image registry
- [ ] Set up monitoring and alerting
- [ ] Configure authentication for API
- [ ] Review PII handling requirements
- [ ] Load test with production traffic patterns

## Contact

For questions about this implementation, see README.md for detailed explanations.
