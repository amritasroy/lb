# Multi-stage Dockerfile for ChurnModel Service
# Optimized for 6GB model artifacts with focus on build speed and deployment latency

# Stage 1: Base image with Python dependencies
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application code
COPY mlzone_model.py .
COPY churn_model.py .
COPY app.py .

# Create artifacts directory
# Note: In production, artifacts should be mounted from persistent storage
# or downloaded from artifact registry (GCS, S3, etc.) at startup
RUN mkdir -p /app/artifacts

# Design Decision: Model Artifacts (6GB)
# We DO NOT copy artifacts into the image because:
# 1. Build Time: 6GB artifacts significantly increase image build time
# 2. Image Size: Docker layers have size limits and large images are slow to pull
# 3. Flexibility: Models can be updated without rebuilding the image
# 4. Best Practice: Separate code from data/models
#
# Recommended approaches:
# - Mount artifacts from Kubernetes PersistentVolume or ConfigMap
# - Download from GCS/S3 bucket at container startup using init container
# - Use a sidecar container to manage model artifacts
# - For this demo, artifacts can be mounted at /app/artifacts

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the service
# Note: This CMD is overridden by Kubernetes deployment configuration
# The actual production command is specified in deployment.yaml
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
