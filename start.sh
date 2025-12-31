#!/bin/bash
# Production startup script for ChurnModel service
# Uses Gunicorn with Uvicorn workers for optimal performance

# Configuration
WORKERS=${WORKERS:-2}         # Number of worker processes (default: 2)
THREADS=${THREADS:-4}         # Threads per worker (default: 4)
TIMEOUT=${TIMEOUT:-120}       # Worker timeout in seconds (default: 120)
PORT=${PORT:-8000}            # Service port (default: 8000)
HOST=${HOST:-0.0.0.0}         # Bind address (default: 0.0.0.0)

# Design Decisions:
# 
# 1. Workers (--workers=2):
#    - Each worker loads the model (~5GB RAM)
#    - With 16GB node RAM: 2 workers = 10GB + 2GB overhead = 12GB (safe margin)
#    - More workers = more concurrent request handling but higher memory usage
#    - Calculation: floor((Node RAM - Overhead) / Model Size) = floor((16GB - 2GB) / 5GB) = 2
#
# 2. Worker Class (--worker-class=uvicorn.workers.UvicornWorker):
#    - UvicornWorker for ASGI compatibility with FastAPI
#    - Enables async request handling for better I/O performance
#    - Each worker can handle multiple concurrent requests via async
#
# 3. Threads (--threads=4):
#    - Additional parallelism within each worker
#    - Helps with I/O-bound operations (e.g., preprocessing, logging)
#    - Does not significantly increase memory usage
#
# 4. Timeout (--timeout=120):
#    - Prevents workers from hanging on long requests
#    - 120s accommodates model loading and complex inference
#    - Can be adjusted based on p99 latency requirements
#
# 5. Keep-alive (--keep-alive=5):
#    - Maintains HTTP connections for better performance
#    - Reduces connection overhead for repeated requests from same client
#
# 6. Preload (--preload-app):
#    - NOT used here because it would load model before forking
#    - Each worker loads model independently for isolation
#    - Prevents shared memory issues with large ML models

echo "Starting Churn Model Service with Gunicorn + Uvicorn"
echo "Workers: $WORKERS"
echo "Threads per worker: $THREADS"
echo "Timeout: $TIMEOUT seconds"
echo "Port: $PORT"

exec gunicorn app:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers $WORKERS \
  --threads $THREADS \
  --bind $HOST:$PORT \
  --timeout $TIMEOUT \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --max-requests 1000 \
  --max-requests-jitter 100
