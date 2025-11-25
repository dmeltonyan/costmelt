# Cost Melt - Local Testing Guide

Complete step-by-step guide to test Cost Melt locally on your machine.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Setup](#manual-setup)
- [Testing the Backend](#testing-the-backend)
- [Testing the Dashboard](#testing-the-dashboard)
- [Testing the Landing Page](#testing-the-landing-page)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** installed
- **Docker & Docker Compose** (for quick start)
- **Git** installed
- **Supabase account** (free tier works)
- **API keys** for at least one LLM provider:
  - OpenAI API key (recommended for testing)
  - Or Anthropic, Groq, or DeepSeek

---

## Quick Start (Docker)

The fastest way to test everything locally:

### 1. Clone and Navigate

```bash
git clone https://github.com/dmeltonyan/costmelt.git
cd costmelt
```

### 2. Set Up Environment Variables

Create `.env` file in the root directory:

```bash
# Backend Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-key
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=info

# Dashboard Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Set Up Database

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run the SQL from `backend/db/schema.sql` to create tables
4. Run the migration from `backend/db/migrations/001_api_keys.sql` for authentication

### 4. Start All Services

```bash
docker-compose up --build
```

This will start:
- **Backend** at `http://localhost:8000`
- **Dashboard** at `http://localhost:3000`
- **Landing** at `http://localhost:3001`
- **Redis** on port `6379`

### 5. Test the API

Open a new terminal and test:

```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status": "healthy", "service": "costmelt-backend"}
```

---

## Manual Setup

For development and debugging, you can run services manually:

### Step 1: Set Up Backend

#### 1.1 Create Virtual Environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

#### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 1.3 Configure Environment

Create `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-key  # Optional
GROQ_API_KEY=gsk_your-key  # Optional
DEEPSEEK_API_KEY=sk-your-key  # Optional
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=info
```

#### 1.4 Set Up Database

1. Open Supabase dashboard → SQL Editor
2. Copy and run `backend/db/schema.sql`
3. Copy and run `backend/db/migrations/001_api_keys.sql`

#### 1.5 Start Redis (if not using Docker)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
# macOS: brew install redis && redis-server
# Linux: sudo apt-get install redis-server && redis-server
```

#### 1.6 Start Backend

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

#### 1.7 Verify Backend

Open browser: `http://localhost:8000/docs`

You should see the FastAPI interactive documentation.

### Step 2: Test Backend API

#### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "costmelt-backend"}
```

#### Test /v1/route Endpoint (Without Auth)

If authentication is not enabled, test directly:

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is machine learning?",
    "user_id": "test-user"
  }'
```

Expected response:
```json
{
  "response": "...",
  "model_used": "gpt-4o-mini",
  "complexity": 0,
  "cache_hit": false,
  "tokens_in": 15,
  "tokens_out": 120,
  "cost": {
    "actual_cost": 0.00002,
    "baseline_cost": 0.00015,
    "absolute_savings": 0.00013,
    "savings_pct": 86.7
  },
  "latency_ms": 450
}
```

#### Test with Authentication

If authentication is enabled:

1. **Create an API key** (via Supabase SQL or API):

```sql
-- Insert a test API key (you'll need to hash it with bcrypt)
-- For testing, you can temporarily disable auth middleware
```

Or use the API (if you have an admin key):

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-project",
    "role": "write"
  }'
```

2. **Use the API key**:

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain recursion",
    "user_id": "test-user"
  }'
```

### Step 3: Set Up Dashboard

#### 3.1 Install Dependencies

```bash
cd ../dashboard
npm install
```

#### 3.2 Configure Environment

Create `dashboard/.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

#### 3.3 Start Dashboard

```bash
npm run dev
```

Dashboard will be available at: `http://localhost:3000`

#### 3.4 Test Dashboard

1. Open `http://localhost:3000` in browser
2. You should see the dashboard home page
3. Navigate to different pages:
   - `/usage` - Model usage breakdown
   - `/cache` - Cache performance
   - `/routing` - Routing complexity
   - `/models` - Model comparison

### Step 4: Set Up Landing Page

#### 4.1 Install Dependencies

```bash
cd ../landing
npm install
```

#### 4.2 Start Landing Page

```bash
npm run dev
```

Landing page will be available at: `http://localhost:3001`

#### 4.3 Test Landing Page

1. Open `http://localhost:3001` in browser
2. You should see the marketing landing page
3. Test navigation and animations

---

## Testing the Backend

### Using cURL

#### Simple Request

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is Python?",
    "user_id": "test-user-123"
  }'
```

#### With Metadata

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a SQL query for top 10 customers",
    "user_id": "test-user-123",
    "metadata": {
      "source": "test",
      "priority": "high"
    },
    "max_output_tokens": 500
  }'
```

### Using Python

Create `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Test health
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# Test route endpoint
response = requests.post(
    f"{BASE_URL}/v1/route",
    json={
        "prompt": "Explain what a vector database is.",
        "user_id": "python-test-user"
    }
)

data = response.json()
print("\nResponse:")
print(f"Model: {data['model_used']}")
print(f"Complexity: {data['complexity']}")
print(f"Cache Hit: {data['cache_hit']}")
print(f"Cost: ${data['cost']['actual_cost']:.6f}")
print(f"Savings: {data['cost']['savings_pct']:.1f}%")
print(f"Latency: {data['latency_ms']}ms")
print(f"\nResponse text: {data['response'][:200]}...")
```

Run:
```bash
python test_api.py
```

### Using the SDK

#### Python SDK

```bash
cd sdk/python
pip install -e .
```

Test script:

```python
from costmelt import CostMeltClient

client = CostMeltClient(
    base_url="http://localhost:8000",
    # api_key="your-key"  # If auth enabled
)

response = client.route("What is machine learning?")
print(f"Response: {response['response']}")
print(f"Model: {response['model_used']}")
print(f"Savings: {response['cost']['savings_pct']:.1f}%")
```

#### Node.js SDK

```bash
cd sdk/node
npm install
npm run build
```

Test script:

```javascript
import { CostMeltClient } from 'costmelt';

const client = new CostMeltClient({
  baseUrl: 'http://localhost:8000',
  // apiKey: 'your-key'  // If auth enabled
});

const response = await client.route('What is machine learning?');
console.log('Response:', response.response);
console.log('Model:', response.model_used);
console.log('Savings:', response.cost.savings_pct + '%');
```

### Using Postman

1. Import the collection: `postman/CostMelt.postman_collection.json`
2. Set `base_url` variable to `http://localhost:8000`
3. Test the `/v1/route` endpoint

---

## Testing the Dashboard

### Manual Testing

1. **Start backend** (must be running)
2. **Start dashboard**: `cd dashboard && npm run dev`
3. **Open browser**: `http://localhost:3000`
4. **Test each page**:
   - Home (`/`) - Overview metrics
   - Usage (`/usage`) - Model breakdown
   - Cache (`/cache`) - Cache performance
   - Routing (`/routing`) - Complexity distribution
   - Models (`/models`) - Cost comparison
   - Daily (`/daily`) - Timeseries
   - Savings (`/savings`) - Historical savings

### Generate Test Data

To see meaningful data in the dashboard, make some API calls first:

```bash
# Make 10 test requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/route \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test request $i\", \"user_id\": \"test-user\"}"
  sleep 1
done
```

Then refresh the dashboard to see the data.

---

## Running Tests

### Backend Tests

```bash
cd backend
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_routing_engine.py

# Verbose output
pytest -v
```

### Frontend Tests

```bash
# Dashboard
cd dashboard
npm test

# Landing
cd ../landing
npm test
```

### Integration Tests

Test the full flow:

```bash
# 1. Start backend
cd backend
uvicorn main:app --port 8000 &

# 2. Make test requests
python test_api.py

# 3. Check dashboard
# Open http://localhost:3000
```

---

## Load Testing

### Using Locust

```bash
cd benchmarks
pip install -r requirements.txt

# Set environment
export BENCHMARK_BASE_URL=http://localhost:8000

# Run load test
locust -f locustfile.py --users 10 --spawn-rate 2 --host http://localhost:8000

# Open browser: http://localhost:8089
```

### Using k6

```bash
# Install k6 first (see benchmarks/README.md)

cd benchmarks
k6 run k6_basic.js
```

### Profiling

```bash
cd benchmarks
python profiling_runner.py --count 50
```

---

## Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

**Issue**: `Connection refused` to Supabase

**Solution**: Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`

**Issue**: `Connection refused` to Redis

**Solution**: 
- Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
- Or check `REDIS_URL` in `.env`

### Dashboard Shows Errors

**Issue**: "Failed to fetch" errors

**Solution**: 
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_BACKEND_URL` in `dashboard/.env.local`
- Check browser console for CORS errors

**Issue**: Blank pages

**Solution**:
- Check browser console for errors
- Ensure backend API is responding
- Try making a test API call first to generate data

### API Returns 401 Unauthorized

**Issue**: Authentication required but no key provided

**Solution**:
- Check if auth middleware is enabled in `main.py`
- Create an API key via Supabase or API
- Include `Authorization: Bearer YOUR_KEY` header

### No Data in Dashboard

**Issue**: Dashboard shows zeros or "No data"

**Solution**:
- Make some API calls first to generate data
- Check Supabase database for records
- Verify backend is logging to database

### Port Already in Use

**Issue**: `Address already in use`

**Solution**:
```bash
# Find process using port
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# Kill process or use different port
uvicorn main:app --port 8001
```

---

## Quick Test Checklist

- [ ] Backend starts without errors
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] `/v1/route` endpoint accepts requests
- [ ] Dashboard loads at `http://localhost:3000`
- [ ] Landing page loads at `http://localhost:3001`
- [ ] API returns valid responses with cost data
- [ ] Dashboard shows data after making API calls
- [ ] Redis is connected (check logs)
- [ ] Supabase connection works (check logs)

---

## Next Steps

Once local testing is working:

1. **Read the documentation**:
   - [API Documentation](API.md)
   - [Security Guide](SECURITY.md)
   - [Deployment Guide](DEPLOYMENT.md)

2. **Run benchmarks**:
   - See [BENCHMARKS.md](BENCHMARKS.md)

3. **Deploy to production**:
   - See [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Need Help?** Open an issue on GitHub or check the troubleshooting section above.

