# Cost Melt - Benchmarking & Load Testing Guide

Complete guide for benchmarking and load testing the Cost Melt API to measure performance, identify bottlenecks, and validate cost savings.

---

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Running Locust](#running-locust)
- [Running k6 Basic Test](#running-k6-basic-test)
- [Running k6 Cache vs No Cache](#running-k6-cache-vs-no-cache)
- [Profiling Runner](#profiling-runner)
- [Suggested Scenarios](#suggested-scenarios)
- [CI/CD Integration](#cicd-integration)
- [Interpreting Results](#interpreting-results)

---

## Overview

### Why Benchmarks Matter

Cost Melt's value proposition depends on:

1. **Proving Cost Savings** - Demonstrate that routing, caching, and compression actually reduce token costs
2. **Ensuring Scalability** - Verify that routing engine, semantic cache, and batch queue can handle production load
3. **Performance Validation** - Confirm that optimizations don't introduce unacceptable latency
4. **Regression Detection** - Catch performance regressions before they reach production

### Tools Overview

The benchmarking suite includes three complementary tools:

| Tool | Purpose | Best For |
|------|---------|----------|
| **Locust** | Scenario-based load testing with web UI | Interactive testing, complex user behaviors |
| **k6** | Scriptable load testing with metrics | CI/CD integration, automated testing |
| **profiling_runner** | CPU profiling and hotspot analysis | Debugging slow code paths |

### What We Measure

- **Requests per second (RPS)** - Throughput capacity
- **Latency percentiles** - p50, p90, p95, p99 response times
- **Error rates** - Success vs failure rates
- **Cache hit rates** - Effectiveness of semantic caching
- **Cost per request** - Token usage and cost optimization
- **CPU hotspots** - Functions consuming most CPU time

---

## Setup

### Prerequisites

1. **Python 3.9+** - For Locust and profiling runner
2. **k6** - For k6 load tests (see installation below)
3. **Running Cost Melt backend** - API must be accessible
4. **Optional: API key** - If authentication is enabled

### Install Python Dependencies

```bash
cd benchmarks
pip install -r requirements.txt
```

This installs:
- `locust` - Load testing framework
- `requests` - HTTP client for profiling

### Install k6

k6 is a standalone binary, not a Python package.

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
# Download and install from k6 releases
# See: https://k6.io/docs/getting-started/installation/
```

**Windows:**
```bash
# Download installer from k6 releases
# See: https://k6.io/docs/getting-started/installation/
```

**Verify installation:**
```bash
k6 version
```

### Environment Variables

Set these environment variables before running benchmarks:

```bash
# Base URL for Cost Melt API
export BENCHMARK_BASE_URL=http://localhost:8000

# API key (optional, omit for local dev without auth)
export BENCHMARK_API_KEY=cm_live_your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:BENCHMARK_BASE_URL="http://localhost:8000"
$env:BENCHMARK_API_KEY="cm_live_your_api_key_here"
```

---

## Running Locust

Locust provides an interactive web UI for load testing with real-time metrics.

### Basic Usage

```bash
locust -f benchmarks/locustfile.py --users 50 --spawn-rate 10 --host http://localhost:8000
```

**Parameters:**
- `--users` - Total number of concurrent users
- `--spawn-rate` - Users spawned per second
- `--host` - Base URL (can also use `BENCHMARK_BASE_URL` env var)

### Web UI

After starting Locust, open your browser to:
```
http://localhost:8089
```

**Features:**
- Start/stop tests interactively
- Real-time metrics dashboard
- Charts showing RPS, response times, failures
- Download CSV reports

### Headless Mode

For CI/CD or automated testing:

```bash
locust -f benchmarks/locustfile.py \
  --users 100 \
  --spawn-rate 20 \
  --host http://localhost:8000 \
  --headless \
  --run-time 5m \
  --html report.html
```

### What Locust Tests

The `locustfile.py` simulates realistic user behavior:

- **30% simple prompts** - Basic questions
- **50% medium prompts** - Code/SQL queries
- **20% complex prompts** - Multi-step reasoning
- **Random wait times** - 0.5-2 seconds between requests

### Interpreting Results

**Key Metrics:**
- **RPS (Requests per second)** - Throughput
- **Response time (ms)** - p50, p95, p99 percentiles
- **Failures** - Error rate and types

**Good Performance:**
- p95 latency < 1 second
- p99 latency < 2 seconds
- Error rate < 1%

**Red Flags:**
- p99 latency > 5 seconds
- Error rate > 5%
- RPS dropping over time (indicates degradation)

---

## Running k6 Basic Test

k6 is ideal for scriptable, CI/CD-friendly load testing.

### Basic Usage

```bash
cd benchmarks
k6 run k6_basic.js
```

### With Custom Parameters

```bash
k6 run --vus 100 --duration 2m k6_basic.js
```

**Parameters:**
- `--vus` - Virtual users (concurrent)
- `--duration` - Test duration (e.g., `2m`, `30s`)

### Test Configuration

The `k6_basic.js` script uses a **staged ramp-up**:

1. **0-30s:** Ramp to 10 users
2. **30s-1m30s:** Ramp to 50 users
3. **1m30s-2m30s:** Hold at 50 users
4. **2m30s-3m:** Ramp down to 0 users

### Thresholds

The test enforces these thresholds:

```javascript
thresholds: {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],  // 95% < 1s, 99% < 2s
  http_req_failed: ['rate<0.01'],                    // Error rate < 1%
}
```

If thresholds are exceeded, k6 exits with a non-zero code (useful for CI/CD).

### Output

k6 prints real-time metrics to console:

```
✓ status is 200
✓ response has body
✓ response time < 2s

checks.........................: 100% ✓ 1500  ✗ 0
data_received..................: 2.5 MB  42 kB/s
data_sent......................: 450 kB  7.5 kB/s
http_req_duration..............: avg=450ms min=120ms med=380ms max=2100ms p(90)=850ms p(95)=1100ms
http_req_failed................: 0.00%  ✓ 0    ✗ 1500
http_reqs.......................: 1500   25.0/s
vus............................: 50     min=10 max=50
vus_max........................: 50     min=10 max=50
```

### Interpreting Results

**http_req_duration:**
- `avg` - Average latency
- `p(95)` - 95th percentile (critical for SLA)
- `p(99)` - 99th percentile (worst-case users)

**http_req_failed:**
- Should be < 1% for production readiness

---

## Running k6 Cache vs No Cache

This test compares performance with semantic cache hits vs cache misses.

### Usage

```bash
cd benchmarks
k6 run k6_cache_vs_no_cache.js
```

### What It Tests

The script runs **two scenarios in parallel**:

1. **Cached Scenario:**
   - Sends the **same prompt** repeatedly
   - Should result in **high cache hit rate** after first request
   - Measures latency with cache hits

2. **Uncached Scenario:**
   - Sends **random prompts** with unique suffixes
   - Should result in **low cache hit rate**
   - Measures latency with cache misses

### Metrics

k6 tracks separate metrics for each scenario:

- `cached_latency` - Response times for cached requests
- `uncached_latency` - Response times for uncached requests
- `cache_hits` - Cache hit rate

### Expected Results

**Cached requests should be:**
- **Faster** - p95 < 500ms (cache lookup is fast)
- **Cheaper** - No LLM API calls
- **More reliable** - No external API dependencies

**Uncached requests should be:**
- **Slower** - p95 < 2000ms (includes LLM API call)
- **More expensive** - Full LLM API cost
- **Variable** - Depends on model and prompt complexity

### Interpreting Results

Compare the metrics:

```bash
# Cached scenario
cached_latency: p(95)=320ms, p(99)=580ms

# Uncached scenario
uncached_latency: p(95)=1850ms, p(99)=4200ms
```

**Cache Benefit:**
- **Latency reduction:** ~80% faster (320ms vs 1850ms)
- **Cost reduction:** 100% (no LLM API calls)
- **Reliability:** Higher (no external dependencies)

### Cache Hit Rate

Monitor the `cache_hits` metric:

- **Cached scenario:** Should approach 100% after warm-up
- **Uncached scenario:** Should be near 0%

If cache hit rate is low in cached scenario, investigate:
- Semantic cache configuration
- Similarity threshold settings
- Cache TTL/eviction policies

---

## Profiling Runner

The profiling runner identifies CPU hotspots in the backend code.

### Usage

```bash
cd benchmarks
python profiling_runner.py
```

### With Custom Count

```bash
python profiling_runner.py --count 100
```

### Save Profile Stats

```bash
python profiling_runner.py --count 200 --output profile.stats
```

View saved stats:
```bash
python -m pstats profile.stats
```

### What It Does

1. Makes N sequential requests to `/v1/route`
2. Measures latency for each request
3. Uses `cProfile` to track CPU usage
4. Prints statistics and top 20 CPU-consuming functions

### Output

**Request Statistics:**
```
Request Statistics:
  Total requests:     50
  Successful:         50
  Failed:             0
  Success rate:       100.0%

Latency Statistics (ms):
  Average:            450.23
  Minimum:            120.50
  Maximum:            2100.00
  p50 (median):       380.00
  p90:                850.00
  p95:                1100.00
  p99:                1950.00

Cache Performance:
  Cache hit rate:     45.0%

Model Distribution:
  gpt-4o-mini:        30 (60.0%)
  claude-3-haiku:     15 (30.0%)
  gpt-4o:             5 (10.0%)
```

**CPU Profiling:**
```
CPU PROFILING - TOP 20 FUNCTIONS BY TOTAL TIME
============================================================
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     50    2.500    0.050    15.200   0.304   gateway.py:45(route_llm)
     50    1.200    0.024    8.500    0.170   semantic_cache.py:120(lookup)
     50    0.800    0.016    5.200    0.104   routing_engine.py:89(route)
     ...
```

### Using Results

**Identify Hotspots:**
- Functions with high `tottime` - CPU-intensive
- Functions with high `cumtime` - Including subcalls

**Optimization Targets:**
- `semantic_cache.lookup` - Cache lookup performance
- `routing_engine.route` - Routing decision logic
- `prompt_compressor.compress` - Compression overhead
- `batch_queue.enqueue` - Queue operations

**Example Optimization:**
If `semantic_cache.lookup` shows high `tottime`:
- Optimize database queries
- Add Redis caching layer
- Improve embedding similarity search

---

## Suggested Scenarios

### 1. Concurrent User Scaling

Test how the system handles increasing load:

```bash
# 10 concurrent users
locust -f benchmarks/locustfile.py --users 10 --spawn-rate 5

# 100 concurrent users
locust -f benchmarks/locustfile.py --users 100 --spawn-rate 20

# 500 concurrent users
locust -f benchmarks/locustfile.py --users 500 --spawn-rate 50
```

**What to measure:**
- Does latency degrade with more users?
- Does error rate increase?
- Does RPS plateau (indicating bottleneck)?

### 2. Prompt Complexity Mix

Test with different prompt complexity distributions:

**Current mix (in locustfile.py):**
- 30% simple, 50% medium, 20% complex

**Custom mix (modify locustfile.py):**
- 50% simple, 30% medium, 20% complex (lighter load)
- 10% simple, 30% medium, 60% complex (heavier load)

**What to measure:**
- Cost per request (complex prompts cost more)
- Latency distribution (complex prompts take longer)
- Model routing accuracy (correct model selection)

### 3. Cache Effectiveness

Test cache performance under different conditions:

```bash
# Warm cache first (send same prompts)
# Then test with cache hits
k6 run k6_cache_vs_no_cache.js
```

**Variations:**
- Test with cache disabled (if toggle exists)
- Test with different similarity thresholds
- Test cache eviction under memory pressure

### 4. Model Mix Experiments

Test routing with different model availability:

**Scenarios:**
- All models available (normal)
- OpenAI down (fallback to Anthropic/Groq)
- Only cheap models available (Groq, DeepSeek)
- Only expensive models available (GPT-4o, Claude Sonnet)

**What to measure:**
- Cost impact of model selection
- Latency impact of fallbacks
- Routing accuracy

### 5. Batch Queue Performance

Test batch queue under high concurrency:

```bash
# High spawn rate to trigger batching
locust -f benchmarks/locustfile.py --users 200 --spawn-rate 100
```

**What to measure:**
- Batch size distribution
- Batch latency vs individual latency
- Queue depth and wait times

### 6. Compression Impact

If compression can be toggled, compare:

**With compression:**
- Token reduction percentage
- Compression overhead (CPU time)
- Overall latency impact

**Without compression:**
- Baseline token usage
- Baseline latency

**Expected:**
- Compression adds ~50-100ms overhead
- Saves 20-50% tokens
- Net benefit for longer prompts

---

## CI/CD Integration

### Automated Testing

Run k6 tests on every deployment to catch regressions:

**.github/workflows/benchmark.yml:**
```yaml
name: Performance Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D9
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Run benchmarks
        env:
          BENCHMARK_BASE_URL: ${{ secrets.BENCHMARK_BASE_URL }}
          BENCHMARK_API_KEY: ${{ secrets.BENCHMARK_API_KEY }}
        run: |
          cd benchmarks
          k6 run k6_basic.js
```

### Thresholds for CI/CD

Set strict thresholds to fail builds on regressions:

```javascript
thresholds: {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed: ['rate<0.01'],
}
```

**If thresholds fail:**
- Build fails (prevents deployment)
- Review performance regression
- Fix or adjust thresholds

### Tracking Over Time

Store benchmark results for trend analysis:

```bash
# Save results to file
k6 run --out json=results.json k6_basic.js

# Upload to monitoring service
# (e.g., Datadog, Grafana, custom dashboard)
```

**Metrics to track:**
- p95 latency trend
- Error rate trend
- RPS capacity
- Cache hit rate

---

## Interpreting Results

### Good Performance Indicators

✅ **Latency:**
- p50 < 500ms
- p95 < 1000ms
- p99 < 2000ms

✅ **Throughput:**
- Sustained RPS matches target
- No degradation over time

✅ **Reliability:**
- Error rate < 1%
- No 5xx errors
- Rate limiting works correctly

✅ **Cost Optimization:**
- Cache hit rate > 40% (for repeated prompts)
- Average cost per request < baseline
- Routing selects appropriate models

### Red Flags

🚨 **Latency Issues:**
- p99 > 5000ms - Backend is overloaded or has bottlenecks
- Increasing latency over time - Memory leak or resource exhaustion
- High variance - Inconsistent performance

🚨 **Reliability Issues:**
- Error rate > 5% - Backend instability
- 5xx errors - Server-side problems
- Timeouts - Backend can't handle load

🚨 **Cost Issues:**
- Cache hit rate < 20% - Cache not working effectively
- High cost per request - Routing not optimizing
- Expensive models used unnecessarily - Overkill detector failing

### Debugging Performance Issues

**High Latency:**
1. Check CPU profiling results
2. Review database query performance
3. Check Redis connection and latency
4. Review LLM API response times
5. Check batch queue depth

**High Error Rate:**
1. Check backend logs
2. Review rate limiting configuration
3. Check API key authentication
4. Verify LLM API keys are valid
5. Check database connectivity

**Low Cache Hit Rate:**
1. Review similarity threshold settings
2. Check cache TTL configuration
3. Verify embeddings are being generated
4. Check cache eviction policies
5. Review prompt normalization

---

## Best Practices

1. **Warm Up Before Testing** - Make a few requests to warm caches
2. **Test Realistic Scenarios** - Use prompts similar to production
3. **Monitor During Tests** - Watch backend logs and metrics
4. **Run Multiple Times** - Average results for consistency
5. **Test Under Load** - Don't just test with 1 user
6. **Compare Baselines** - Track performance over time
7. **Test Failure Scenarios** - What happens when Redis/DB is down?

---

## Support

For benchmarking questions:

- **Documentation:** [https://docs.costmelt.com/benchmarks](https://docs.costmelt.com/benchmarks)
- **Issues:** [https://github.com/your-username/costmelt/issues](https://github.com/your-username/costmelt/issues)
- **Email:** support@costmelt.com

---

**Last Updated:** January 2025

