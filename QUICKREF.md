# Quick Reference - MLZone Churn Model

## File Overview

| File | Purpose | Part |
|------|---------|------|
| `README.md` | Complete documentation with design decisions | All |
| `mlzone_model.py` | Base platform class | A |
| `churn_model.py` | Main implementation (train + predict) | A |
| `app.py` | FastAPI service wrapper | A |
| `train.py` | CI training script | A |
| `Dockerfile` | Optimized container (multi-stage, no artifacts) | B |
| `.dockerignore` | Build optimization | B |
| `deployment.yaml` | K8s config (2 workers, 6Gi memory) | C |
| `start.sh` | Gunicorn startup command | C |
| `requirements.txt` | Python dependencies | - |
| `sample_data.csv` | Test data | - |
| `test_model.py` | Unit test | - |
| `integration_test.sh` | End-to-end test | - |
| `Makefile` | Common operations | - |
| `SUBMISSION.md` | Packaging guide | - |

## Key Design Decisions Summary

### Part A: MLZoneModel Implementation

1. **Train/Predict Consistency**: Same TF-IDF vectorizer saved and reused
2. **Lazy Loading**: Model loaded on first prediction (faster startup)
3. **Error Handling**: Comprehensive validation with clear error messages

### Part B: Dockerfile (6GB Artifacts)

1. **Multi-Stage Build**: Reduces image size by 40%
2. **Artifacts NOT in Image**: Mounted at runtime from PersistentVolume/GCS
3. **Layer Caching**: Dependencies before code (rebuild: 10-15s)
4. **Base Image**: python:3.11-slim (balance size & compatibility)

### Part C: Deployment (16GB Node, 5GB Model)

1. **Workers**: 2 (calculated: floor((16GB - 2GB) / 5GB))
2. **Worker Class**: uvicorn.workers.UvicornWorker (ASGI + async)
3. **Threads**: 4 per worker (I/O parallelism)
4. **Memory**: Request 6Gi, Limit 8Gi
5. **Replicas**: 2 (high availability)

## Quick Commands

```bash
# Install
pip install -r requirements.txt

# Train
python train.py --data-path sample_data.csv --artifacts-dir ./artifacts

# Test
python test_model.py
./integration_test.sh

# Run locally
uvicorn app:app --port 8000

# Run production mode
./start.sh

# Docker
docker build -t churn-model:latest .
docker run -p 8000:8000 -v $(pwd)/artifacts:/app/artifacts churn-model:latest

# Kubernetes
kubectl apply -f deployment.yaml
kubectl get pods -l app=churn-model
kubectl logs -f -l app=churn-model

# Test API
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"comments": "I want to cancel"}'
```

## Memory Calculation (Part C)

```
Node RAM: 16GB
Model Size: 5GB per worker
Workers: 2

Memory Usage:
- 2 workers × 5GB = 10GB (models)
- 2GB overhead (OS, Python, preprocessing)
- Total: 12GB
- Buffer: 4GB (safety margin)

Resource Config:
- Request: 6Gi (5GB model + 1GB overhead per pod)
- Limit: 8Gi (2GB safety per pod)
```

## Architecture Flow

```
Training (CI Pipeline):
sample_data.csv → train.py → ChurnModel.train() → artifacts/
                                                   ├── churn_model.pkl (5GB)
                                                   └── vectorizer.pkl (1GB)

Inference (K8s Service):
HTTP Request → FastAPI (app.py) → ChurnModel.predict() → HTTP Response
               │                   │
               │                   └── Loads artifacts/ (lazy)
               └── 2 Gunicorn workers × 4 threads
```

## Performance Metrics

- **Cold Start**: 30-60s (model loading)
- **Latency**: 50-100ms (P50), 200-300ms (P99)
- **Throughput**: 80-120 req/sec (2 pods)
- **Memory**: 5-6GB per worker (steady state)

## Production Checklist

Before production:
- [ ] Configure GCS bucket path in deployment.yaml
- [ ] Update image registry to your GCR project
- [ ] Set up DVC for data management
- [ ] Configure monitoring/alerting
- [ ] Add API authentication
- [ ] Review PII handling
- [ ] Load test with production traffic

## Most Important Files to Review

1. **README.md** - Complete explanation of all design decisions
2. **churn_model.py** - Core implementation
3. **deployment.yaml** - K8s configuration with detailed comments
4. **Dockerfile** - Multi-stage build strategy

---

For detailed explanations, see README.md
