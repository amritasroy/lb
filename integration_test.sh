#!/bin/bash
# Integration test script for ChurnModel service
# Tests the complete workflow: train -> serve -> predict

set -e  # Exit on any error

echo "================================"
echo "ChurnModel Integration Test"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    if [ ! -z "$SERVICE_PID" ]; then
        echo "Stopping service (PID: $SERVICE_PID)..."
        kill $SERVICE_PID 2>/dev/null || true
    fi
    rm -rf ./test_integration_artifacts
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "Step 1: Training model..."
python train.py --data-path sample_data.csv --artifacts-dir ./test_integration_artifacts
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Training completed${NC}"
else
    echo -e "${RED}✗ Training failed${NC}"
    exit 1
fi
echo ""

echo "Step 2: Verifying artifacts..."
if [ -f "./test_integration_artifacts/churn_model.pkl" ] && [ -f "./test_integration_artifacts/vectorizer.pkl" ]; then
    echo -e "${GREEN}✓ Artifacts found${NC}"
else
    echo -e "${RED}✗ Artifacts missing${NC}"
    exit 1
fi
echo ""

echo "Step 3: Starting service..."
# Copy artifacts to expected location
mkdir -p ./artifacts
cp -r ./test_integration_artifacts/* ./artifacts/

# Start service in background
python -m uvicorn app:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
SERVICE_PID=$!

# Wait for service to be ready
echo "Waiting for service to start..."
for i in {1..15}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service started (PID: $SERVICE_PID)${NC}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "${RED}✗ Service failed to start${NC}"
        exit 1
    fi
    sleep 1
done
echo ""

echo "Step 4: Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "  Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

echo "Step 5: Testing prediction endpoint (negative comment)..."
PRED1=$(curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"comments": "I want to cancel my subscription because it is too expensive"}')

if echo "$PRED1" | grep -q "churn_prob"; then
    PROB1=$(echo "$PRED1" | python -c "import sys, json; print(json.load(sys.stdin)['churn_prob'])")
    echo -e "${GREEN}✓ Prediction 1 successful${NC}"
    echo "  Comment: 'I want to cancel...' → Churn probability: $PROB1"
else
    echo -e "${RED}✗ Prediction 1 failed${NC}"
    echo "  Response: $PRED1"
    exit 1
fi
echo ""

echo "Step 6: Testing prediction endpoint (positive comment)..."
PRED2=$(curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"comments": "This service is amazing and I love using it every day!"}')

if echo "$PRED2" | grep -q "churn_prob"; then
    PROB2=$(echo "$PRED2" | python -c "import sys, json; print(json.load(sys.stdin)['churn_prob'])")
    echo -e "${GREEN}✓ Prediction 2 successful${NC}"
    echo "  Comment: 'This service is amazing...' → Churn probability: $PROB2"
else
    echo -e "${RED}✗ Prediction 2 failed${NC}"
    echo "  Response: $PRED2"
    exit 1
fi
echo ""

echo "Step 7: Testing error handling (missing field)..."
ERROR_RESPONSE=$(curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"wrong_field": "test"}')

if echo "$ERROR_RESPONSE" | grep -q "detail"; then
    echo -e "${GREEN}✓ Error handling works${NC}"
    echo "  Properly returns error for invalid input"
else
    echo -e "${RED}✗ Error handling failed${NC}"
    exit 1
fi
echo ""

echo "================================"
echo -e "${GREEN}All tests passed!${NC}"
echo "================================"
echo ""
echo "Summary:"
echo "  - Model training: ✓"
echo "  - Artifact persistence: ✓"
echo "  - Service startup: ✓"
echo "  - Health checks: ✓"
echo "  - Predictions: ✓"
echo "  - Error handling: ✓"
echo ""
