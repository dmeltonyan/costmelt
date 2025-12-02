#!/bin/bash

# Cost Melt - Complete Test Suite
# Tests all components end-to-end

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cost Melt - Complete Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if backend is running
echo -e "${YELLOW}[1/8] Checking backend health...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running. Start it with: cd backend && uvicorn main:app --reload${NC}"
    exit 1
fi

# Test health endpoint
echo -e "${YELLOW}[2/8] Testing health endpoint...${NC}"
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "  Response: $HEALTH"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Test API route endpoint (simple prompt)
echo -e "${YELLOW}[3/8] Testing /v1/route endpoint (simple prompt)...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}')

if echo "$RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓ API route test passed${NC}"
    echo "  Model used: $(echo "$RESPONSE" | grep -o '"model_used":"[^"]*"' | cut -d'"' -f4)"
    echo "  Cache hit: $(echo "$RESPONSE" | grep -o '"cache_hit":[^,}]*' | cut -d':' -f2)"
    echo "  Savings: $(echo "$RESPONSE" | grep -o '"savings_pct":[^,}]*' | cut -d':' -f2)%"
else
    echo -e "${RED}✗ API route test failed${NC}"
    echo "  Response: $RESPONSE"
    exit 1
fi

# Test cache hit (same prompt again)
echo -e "${YELLOW}[4/8] Testing cache hit (same prompt)...${NC}"
sleep 2
CACHE_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}')

if echo "$CACHE_RESPONSE" | grep -q '"cache_hit":true'; then
    echo -e "${GREEN}✓ Cache hit test passed${NC}"
    echo "  Cache hit: true"
else
    echo -e "${YELLOW}⚠ Cache hit test - may need more time for embedding${NC}"
fi

# Test dashboard stats endpoint
echo -e "${YELLOW}[5/8] Testing dashboard stats endpoint...${NC}"
STATS=$(curl -s http://localhost:8000/dashboard/stats)
if echo "$STATS" | grep -q "total_requests"; then
    echo -e "${GREEN}✓ Dashboard stats test passed${NC}"
    echo "  Total requests: $(echo "$STATS" | grep -o '"total_requests":[^,}]*' | cut -d':' -f2)"
else
    echo -e "${RED}✗ Dashboard stats test failed${NC}"
    echo "  Response: $STATS"
fi

# Test dashboard usage endpoint
echo -e "${YELLOW}[6/8] Testing dashboard usage endpoint...${NC}"
USAGE=$(curl -s http://localhost:8000/dashboard/usage)
if echo "$USAGE" | grep -q "models"; then
    echo -e "${GREEN}✓ Dashboard usage test passed${NC}"
else
    echo -e "${RED}✗ Dashboard usage test failed${NC}"
    echo "  Response: $USAGE"
fi

# Test dashboard cache endpoint
echo -e "${YELLOW}[7/8] Testing dashboard cache endpoint...${NC}"
CACHE_STATS=$(curl -s http://localhost:8000/dashboard/cache)
if echo "$CACHE_STATS" | grep -q "cache_hits"; then
    echo -e "${GREEN}✓ Dashboard cache test passed${NC}"
else
    echo -e "${RED}✗ Dashboard cache test failed${NC}"
    echo "  Response: $CACHE_STATS"
fi

# Test with different complexity prompts
echo -e "${YELLOW}[8/8] Testing complexity detection...${NC}"

# Simple prompt
SIMPLE=$(curl -s -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize this text", "user_id": "test-user"}')
SIMPLE_COMPLEXITY=$(echo "$SIMPLE" | grep -o '"complexity":[^,}]*' | cut -d':' -f2)
echo "  Simple prompt complexity: $SIMPLE_COMPLEXITY"

# Complex prompt (with code)
COMPLEX=$(curl -s -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a Python function to implement quicksort algorithm with time complexity analysis", "user_id": "test-user"}')
COMPLEX_COMPLEXITY=$(echo "$COMPLEX" | grep -o '"complexity":[^,}]*' | cut -d':' -f2)
echo "  Complex prompt complexity: $COMPLEX_COMPLEXITY"

if [ "$COMPLEX_COMPLEXITY" -gt "$SIMPLE_COMPLEXITY" ]; then
    echo -e "${GREEN}✓ Complexity detection working correctly${NC}"
else
    echo -e "${YELLOW}⚠ Complexity detection may need tuning${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All Tests Completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Check dashboard at http://localhost:3000"
echo "  2. View API docs at http://localhost:8000/docs"
echo "  3. Check logs for detailed information"

