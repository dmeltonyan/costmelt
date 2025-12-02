# Cost Melt - Complete Testing Guide

**End-to-end testing guide for all components**

---

## Quick Start Testing

### 1. Initialize System

```bash
# Check all components are set up correctly
cd backend
python ../scripts/init_system.py
```

This will verify:
- ✅ Environment variables are set
- ✅ Python dependencies installed
- ✅ Redis is accessible
- ✅ Supabase is connected
- ✅ OpenAI API key is valid

### 2. Start Services

**Terminal 1: Backend**
```bash
cd backend
source .venv/Scripts/activate  # Git Bash
# OR
.venv\Scripts\activate  # PowerShell
uvicorn main:app --reload --port 8000
```

**Terminal 2: Redis** (if not using Docker)
```bash
redis-server
```

**Terminal 3: Dashboard** (optional)
```bash
cd dashboard
npm run dev
```

### 3. Run Complete Test Suite

**Git Bash:**
```bash
./scripts/test_everything.sh
```

**PowerShell:**
```powershell
.\scripts\test_everything.ps1
```

**Manual Testing:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API route
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'
```

---

## Component Testing

### Backend API Testing

#### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "costmelt-backend"}
```

#### Main Route Endpoint

**Simple Prompt:**
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is Python?",
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
  "tokens_in": 5,
  "tokens_out": 50,
  "cost": {
    "actual_cost": 0.00003,
    "baseline_cost": 0.00028,
    "absolute_savings": 0.00025,
    "savings_pct": 89.29
  },
  "latency_ms": 1200
}
```

**Cache Hit Test:**
```bash
# Run same prompt twice
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'

# Second call should return cache_hit: true
```

**Complex Prompt:**
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to implement quicksort with time complexity analysis",
    "user_id": "test-user"
  }'
```

Expected: `complexity: 2`, routed to `gpt-4o` or `claude-3-5-sonnet`

### Dashboard API Testing

#### Stats Endpoint
```bash
curl http://localhost:8000/dashboard/stats
```

#### Usage Endpoint
```bash
curl http://localhost:8000/dashboard/usage
```

#### Cache Endpoint
```bash
curl http://localhost:8000/dashboard/cache
```

#### Routing Endpoint
```bash
curl http://localhost:8000/dashboard/routing
```

#### Daily Endpoint
```bash
curl http://localhost:8000/dashboard/daily
```

#### Models Endpoint
```bash
curl http://localhost:8000/dashboard/models
```

#### Savings Endpoint
```bash
curl http://localhost:8000/dashboard/savings
```

---

## Integration Testing

### Test Scenarios

#### Scenario 1: First Request (Cache Miss)
1. Send request with new prompt
2. Verify: `cache_hit: false`
3. Verify: Response contains LLM output
4. Verify: Cost calculated correctly
5. Verify: Request logged to Supabase

#### Scenario 2: Cache Hit
1. Send same prompt again (within 7 days)
2. Verify: `cache_hit: true`
3. Verify: Response returned quickly (< 100ms)
4. Verify: Cost is minimal (~$0.0001)

#### Scenario 3: Prompt Compression
1. Send long prompt (> 100 tokens)
2. Verify: `tokens_in` reduced by 20-50%
3. Verify: Response quality maintained
4. Verify: Compression logged

#### Scenario 4: Complexity Routing
1. Send simple prompt → Verify routed to `gpt-4o-mini`
2. Send medium prompt → Verify routed to `claude-3-haiku` or `gpt-4o-mini`
3. Send complex prompt → Verify routed to `gpt-4o` or `claude-3-5-sonnet`

#### Scenario 5: Batch Processing
1. Send multiple requests simultaneously
2. Verify: Requests batched together
3. Verify: Responses returned correctly
4. Verify: Latency improved

---

## Load Testing

### Using Locust

```bash
cd benchmarks
pip install -r requirements.txt
locust -f locustfile.py --users 50 --spawn-rate 10 --host http://localhost:8000
```

Open browser: http://localhost:8089

### Using k6

```bash
cd benchmarks
k6 run k6_basic.js
```

### Using curl (Simple)

```bash
# Send 10 requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/route \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test request $i\", \"user_id\": \"test-user\"}" &
done
wait
```

---

## Performance Testing

### Latency Targets

- **Cache Hit**: < 100ms (p95)
- **Cache Miss**: < 2s (p95)
- **Dashboard Load**: < 2s

### Throughput Targets

- **API**: 100+ requests/second
- **Cache Lookups**: 1000+ lookups/second

### Test Commands

```bash
# Measure latency
time curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "user_id": "test"}'

# Measure throughput
ab -n 100 -c 10 -p request.json -T application/json http://localhost:8000/v1/route
```

---

## Error Testing

### Invalid Request
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected: `400 Bad Request`

### Empty Prompt
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": ""}'
```

Expected: `400 Bad Request`

### Missing API Key (when auth enabled)
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test"}'
```

Expected: `401 Unauthorized`

---

## Database Testing

### Verify Tables Exist

```sql
-- In Supabase SQL Editor
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

Should show:
- `requests`
- `cache`
- `users`
- `api_keys`

### Verify Data Insertion

```sql
-- Check requests table
SELECT COUNT(*) FROM requests;

-- Check cache table
SELECT COUNT(*) FROM cache;

-- Check recent requests
SELECT * FROM requests ORDER BY created_at DESC LIMIT 10;
```

---

## Frontend Testing

### Dashboard

1. Open http://localhost:3000
2. Verify all pages load:
   - `/` - Home dashboard
   - `/usage` - Usage breakdown
   - `/cache` - Cache metrics
   - `/routing` - Routing breakdown
   - `/models` - Model comparison
   - `/daily` - Daily timeseries
   - `/savings` - Savings chart

3. Verify charts render
4. Verify data updates after API calls

### Landing Page

1. Open http://localhost:3001
2. Verify pages load:
   - `/` - Landing page
   - `/pricing` - Pricing page
   - `/privacy` - Privacy policy
   - `/terms` - Terms of service

---

## Automated Testing

### Backend Unit Tests

```bash
cd backend
pytest tests/
```

### Backend Integration Tests

```bash
cd backend
pytest tests/integration/
```

### Frontend Tests

```bash
cd dashboard
npm test
```

---

## Troubleshooting

### Backend Not Starting

**Error**: `ModuleNotFoundError`
**Solution**: Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Error**: `Redis connection failed`
**Solution**: Start Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Error**: `Supabase connection failed`
**Solution**: Check `.env` file has correct credentials

### API Returns Errors

**Error**: `500 Internal Server Error`
**Solution**: Check backend logs for details

**Error**: `504 Gateway Timeout`
**Solution**: Check batch worker is running

**Error**: `401 Unauthorized`
**Solution**: Check API key is valid (when auth enabled)

### Dashboard Not Loading

**Error**: `Cannot connect to backend`
**Solution**: Check `NEXT_PUBLIC_BACKEND_URL` in `dashboard/.env.local`

**Error**: `CORS error`
**Solution**: Check backend CORS settings in `main.py`

---

## Test Checklist

Before considering the system "ready":

- [ ] Health endpoint responds
- [ ] API route endpoint works
- [ ] Cache hit works (same prompt twice)
- [ ] Prompt compression reduces tokens
- [ ] Complexity detection works
- [ ] Routing selects correct model
- [ ] Cost calculation is accurate
- [ ] Requests logged to Supabase
- [ ] Dashboard endpoints return data
- [ ] Dashboard frontend loads
- [ ] Landing page loads
- [ ] Error handling works
- [ ] Rate limiting works (when enabled)

---

**Ready to test? Run: `./scripts/test_everything.sh`**

