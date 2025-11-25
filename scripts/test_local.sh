#!/bin/bash

# Cost Melt - Quick Local Test Script
# Tests all components to ensure everything is working

set -e

echo "🧪 Cost Melt Local Testing"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="${BENCHMARK_BASE_URL:-http://localhost:8000}"

# Test 1: Health Check
echo "1️⃣  Testing Health Endpoint..."
if curl -s -f "$BASE_URL/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
    curl -s "$BASE_URL/health" | python3 -m json.tool
else
    echo -e "${RED}✗${NC} Backend is not responding"
    echo "   Make sure backend is running: cd backend && uvicorn main:app --reload"
    exit 1
fi
echo ""

# Test 2: API Route Endpoint
echo "2️⃣  Testing /v1/route Endpoint..."
RESPONSE=$(curl -s -X POST "$BASE_URL/v1/route" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What is machine learning?",
        "user_id": "test-script"
    }')

if echo "$RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓${NC} API route endpoint working"
    echo "$RESPONSE" | python3 -m json.tool | head -20
else
    echo -e "${RED}✗${NC} API route endpoint failed"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 3: Dashboard Backend Endpoints
echo "3️⃣  Testing Dashboard Endpoints..."

ENDPOINTS=("stats" "usage" "cache" "routing" "daily")

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -f "$BASE_URL/dashboard/$endpoint" > /dev/null; then
        echo -e "${GREEN}✓${NC} /dashboard/$endpoint"
    else
        echo -e "${YELLOW}⚠${NC} /dashboard/$endpoint (may need data first)"
    fi
done
echo ""

# Test 4: Check Redis Connection (if backend logs available)
echo "4️⃣  Checking Services..."
echo -e "${YELLOW}ℹ${NC}  Make sure Redis is running:"
echo "   docker run -d -p 6379:6379 redis:7-alpine"
echo "   OR: redis-server"
echo ""

# Summary
echo "=========================="
echo -e "${GREEN}✅ Basic tests completed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start dashboard: cd dashboard && npm run dev"
echo "  2. Open http://localhost:3000"
echo "  3. Make more API calls to generate data"
echo "  4. Check dashboard for analytics"
echo ""
echo "For detailed testing, see: docs/LOCAL_TESTING.md"

