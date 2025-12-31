# MLZone Platform Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MLZone Platform                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline (Training)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  DVC-Managed Data (50GB)                                            │
│  churn_data.csv                                                      │
│         │                                                             │
│         ▼                                                             │
│  ┌─────────────────┐                                                │
│  │   train.py      │                                                │
│  │  (CI Script)    │                                                │
│  └────────┬────────┘                                                │
│           │                                                           │
│           ▼                                                           │
│  ┌─────────────────────┐                                            │
│  │  ChurnModel.train() │                                            │
│  │  - Load data        │                                            │
│  │  - TF-IDF vectorize │                                            │
│  │  - Train RF         │                                            │
│  │  - Save artifacts   │                                            │
│  └────────┬────────────┘                                            │
│           │                                                           │
│           ▼                                                           │
│  ┌──────────────────────┐                                           │
│  │  Model Artifacts     │                                           │
│  │  ├─ churn_model.pkl  │  (~5GB)                                  │
│  │  └─ vectorizer.pkl   │  (~1GB)                                  │
│  └────────┬─────────────┘                                           │
│           │                                                           │
│           ▼                                                           │
│  Upload to GCS Bucket                                                │
│  gs://mlzone-models/churn-model/v1/                                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    Production Deployment (GKE)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Kubernetes Cluster                          │ │
│  │                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────┐  │ │
│  │  │              Service (Load Balancer)                     │  │ │
│  │  │              churn-model-service:80                      │  │ │
│  │  └──────────────────────┬──────────────────────────────────┘  │ │
│  │                         │                                       │ │
│  │           ┌─────────────┴─────────────┐                        │ │
│  │           │                           │                        │ │
│  │           ▼                           ▼                        │ │
│  │  ┌────────────────┐          ┌────────────────┐               │ │
│  │  │   Pod 1        │          │   Pod 2        │               │ │
│  │  │   (16GB Node)  │          │   (16GB Node)  │               │ │
│  │  ├────────────────┤          ├────────────────┤               │ │
│  │  │ Init Container │          │ Init Container │               │ │
│  │  │ Download Model │          │ Download Model │               │ │
│  │  │ from GCS       │          │ from GCS       │               │ │
│  │  └────────┬───────┘          └────────┬───────┘               │ │
│  │           │                           │                        │ │
│  │           ▼                           ▼                        │ │
│  │  ┌────────────────┐          ┌────────────────┐               │ │
│  │  │   Gunicorn     │          │   Gunicorn     │               │ │
│  │  │   Master       │          │   Master       │               │ │
│  │  ├────────────────┤          ├────────────────┤               │ │
│  │  │  Worker 1      │          │  Worker 1      │               │ │
│  │  │  (5GB RAM)     │          │  (5GB RAM)     │               │ │
│  │  │  ┌──────────┐  │          │  ┌──────────┐  │               │ │
│  │  │  │ Uvicorn  │  │          │  │ Uvicorn  │  │               │ │
│  │  │  │ 4 threads│  │          │  │ 4 threads│  │               │ │
│  │  │  │ FastAPI  │  │          │  │ FastAPI  │  │               │ │
│  │  │  │ + Model  │  │          │  │ + Model  │  │               │ │
│  │  │  └──────────┘  │          │  └──────────┘  │               │ │
│  │  │                │          │                │               │ │
│  │  │  Worker 2      │          │  Worker 2      │               │ │
│  │  │  (5GB RAM)     │          │  (5GB RAM)     │               │ │
│  │  │  ┌──────────┐  │          │  ┌──────────┐  │               │ │
│  │  │  │ Uvicorn  │  │          │  │ Uvicorn  │  │               │ │
│  │  │  │ 4 threads│  │          │  │ 4 threads│  │               │ │
│  │  │  │ FastAPI  │  │          │  │ FastAPI  │  │               │ │
│  │  │  │ + Model  │  │          │  │ + Model  │  │               │ │
│  │  │  └──────────┘  │          │  └──────────┘  │               │ │
│  │  └────────────────┘          └────────────────┘               │ │
│  │                                                                 │ │
│  │  Memory per Pod: 10GB (2 workers × 5GB) + 2GB overhead        │ │
│  │  Total Capacity: 2 pods × 2 workers × 4 threads = 16 threads  │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Request Flow                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Client Request                                                       │
│       │                                                               │
│       ▼                                                               │
│  POST /predict                                                        │
│  {                                                                    │
│    "comments": "I want to cancel my subscription..."                │
│  }                                                                    │
│       │                                                               │
│       ▼                                                               │
│  K8s Service (Load Balancer)                                         │
│       │                                                               │
│       ▼                                                               │
│  FastAPI Endpoint (app.py)                                           │
│       │                                                               │
│       ├─ Validate input                                              │
│       ├─ Extract "comments"                                          │
│       │                                                               │
│       ▼                                                               │
│  ChurnModel.predict()                                                │
│       │                                                               │
│       ├─ Load artifacts (lazy, first request only)                   │
│       ├─ TF-IDF transform: "comments" → vector (1000 features)      │
│       ├─ Random Forest predict_proba()                               │
│       ├─ Extract churn probability                                   │
│       │                                                               │
│       ▼                                                               │
│  Response                                                             │
│  {                                                                    │
│    "churn_prob": 0.75                                                │
│  }                                                                    │
│       │                                                               │
│       ▼                                                               │
│  Client receives prediction                                          │
│                                                                       │
│  Latency: 50-100ms (P50), 200-300ms (P99)                           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Resource Calculation

```
┌────────────────────────────────────────────────┐
│ Kubernetes Node: 16GB RAM                      │
├────────────────────────────────────────────────┤
│                                                 │
│  Pod 1 (6Gi requested, 8Gi limit)              │
│  ├─ Worker 1: 5GB (model) + 0.5GB = 5.5GB     │
│  ├─ Worker 2: 5GB (model) + 0.5GB = 5.5GB     │
│  └─ Total: ~11GB                                │
│                                                 │
│  System Overhead: ~2GB                          │
│  ├─ OS and kernel                               │
│  ├─ Kubelet                                     │
│  └─ System services                             │
│                                                 │
│  Total Used: 11GB + 2GB = 13GB                 │
│  Available: 16GB - 13GB = 3GB buffer           │
│                                                 │
│  Safety Margin: 3GB (18.75%)                   │
│                                                 │
└────────────────────────────────────────────────┘

Decision: 2 workers per pod is safe and optimal
```

## Deployment Strategy

```
┌──────────────────────────────────────────────────────────────┐
│                    Deployment Timeline                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  T=0s    Pod starts                                          │
│  │                                                            │
│  ├─ T=0-30s    Init container downloads 6GB artifacts        │
│  │              from GCS to /app/artifacts                    │
│  │                                                            │
│  ├─ T=30s      Main container starts                         │
│  │              Gunicorn spawns 2 workers                     │
│  │                                                            │
│  ├─ T=30-40s   Readiness probe starts checking               │
│  │              GET /health                                   │
│  │                                                            │
│  ├─ T=40s      First request arrives                         │
│  │              Model lazy-loads artifacts (5-10s)           │
│  │                                                            │
│  ├─ T=50s      Model loaded, ready to serve                  │
│  │              Readiness probe passes                        │
│  │                                                            │
│  └─ T=60s+     Pod receives production traffic               │
│                 Liveness probe monitors health                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Scaling Behavior

```
┌──────────────────────────────────────────────────────────────┐
│             Horizontal Pod Autoscaler (HPA)                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Min Replicas: 2                                             │
│  Max Replicas: 10                                            │
│                                                               │
│  Scale Up Trigger:                                           │
│  - CPU > 70% for 30 seconds                                  │
│  - Memory > 80% for 30 seconds                               │
│                                                               │
│  Scale Down Trigger:                                         │
│  - CPU < 70% for 5 minutes                                   │
│  - Memory < 80% for 5 minutes                                │
│                                                               │
│  ┌────────────────────────────────────────────┐             │
│  │  Traffic Pattern vs Replicas               │             │
│  │                                             │             │
│  │  10 replicas ├────────────────┐            │             │
│  │              │                 │            │             │
│  │   5 replicas ├────────┐        │            │             │
│  │              │        │        │            │             │
│  │   2 replicas ├────────┴────────┴────────    │             │
│  │              │                              │             │
│  │              └──────────────────────────    │             │
│  │              Normal  Peak    Normal         │             │
│  │              Traffic Traffic Traffic        │             │
│  └────────────────────────────────────────────┘             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

This architecture provides:
- High availability (2+ replicas)
- Horizontal scalability (HPA)
- Resource efficiency (calculated workers)
- Fast deployment (artifacts not in image)
- Production reliability (health checks, timeouts)
