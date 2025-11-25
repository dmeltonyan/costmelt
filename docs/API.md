# Cost Melt API Reference

**Cost Melt is an LLM routing, caching, batching, and cost-optimization proxy that reduces AI token spend automatically.**

Cost Melt acts as an intelligent proxy between your application and LLM providers (OpenAI, Anthropic, Groq, DeepSeek), automatically optimizing every request through smart routing, semantic caching, prompt compression, and micro-batching.

---

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Main Endpoint: /v1/route](#main-endpoint-v1route)
- [Dashboard Endpoints](#dashboard-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Model Routing Catalog](#model-routing-catalog)
- [Semantic Cache API](#semantic-cache-api)
- [Batch Queue API](#batch-queue-api)
- [Webhooks](#webhooks)
- [Changelog](#changelog)

---

## Base URL

### Development
```
http://localhost:8000
```

### Production
```
https://api.costmelt.com
```

### Supported Providers

Cost Melt supports the following LLM providers:

- **OpenAI** – GPT-4o, GPT-4o-mini
- **Anthropic** – Claude 3 Haiku, Claude 3.5 Sonnet
- **Groq** – Llama 3 70B
- **DeepSeek** – DeepSeek Chat

---

## Authentication

### Current Status

**No API key required in local development mode.**

For production deployments, API keys will be generated per-user and required for all requests.

### Future Authentication Format

When API key authentication is enabled, include the API key in the `Authorization` header:

```bash
-H "Authorization: Bearer <YOUR_API_KEY>"
```

**Example:**

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_abc123..." \
  -d '{"prompt": "Hello, world!"}'
```

### Getting an API Key

1. Sign up for a Cost Melt account
2. Navigate to Dashboard → API Keys
3. Generate a new API key
4. Store it securely (keys are only shown once)

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/route` | POST | Optimized LLM request with automatic routing, caching, and compression |
| `/dashboard/stats` | GET | Global statistics (requests, tokens, costs, savings) |
| `/dashboard/usage` | GET | Usage breakdown by model |
| `/dashboard/cache` | GET | Cache performance metrics |
| `/dashboard/routing` | GET | Routing complexity and model distribution |
| `/dashboard/daily` | GET | Daily timeseries metrics |
| `/dashboard/models` | GET | Model cost comparison table |
| `/dashboard/savings` | GET | Historical savings over time |
| `/health` | GET | Health check endpoint |

---

## Main Endpoint: /v1/route

The primary endpoint for routing LLM requests through Cost Melt's optimization pipeline.

### Description

Send an LLM prompt to Cost Melt. The system will:

1. **Compress the prompt** – Reduces token count by 20–50% while preserving meaning
2. **Check semantic cache** – Returns cached response if a similar prompt was processed recently
3. **Determine prompt complexity** – Classifies complexity (0=simple, 1=medium, 2=complex)
4. **Route to cheapest capable model** – Selects optimal model based on complexity and cost
5. **Batch requests if possible** – Groups compatible requests for efficiency
6. **Execute LLM completion** – Sends request to selected provider
7. **Calculate cost + savings** – Computes actual cost vs. baseline and savings percentage
8. **Log the request** – Stores metrics in Supabase for analytics
9. **Return optimized result** – Returns response with full metadata

### Request

**Endpoint:** `POST /v1/route`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <YOUR_API_KEY>  # Optional in dev mode
```

**Request Body Schema:**

```json
{
  "prompt": "string (required)",
  "user_id": "string (optional)",
  "metadata": "object (optional)",
  "max_output_tokens": "number (optional, default: 400)"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | The user prompt to process |
| `user_id` | string | No | User identifier for analytics and logging |
| `metadata` | object | No | Additional metadata dictionary |
| `max_output_tokens` | number | No | Maximum output tokens (default: 400) |

### Request Examples

**cURL:**

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Big O notation with examples.",
    "user_id": "user-123",
    "max_output_tokens": 500
  }'
```

**Node.js:**

```javascript
const res = await fetch("http://localhost:8000/v1/route", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "Design a FastAPI rate limiter.",
    user_id: "user-123",
    max_output_tokens: 400
  })
});

const data = await res.json();
console.log(data.response);
console.log(`Cost: $${data.cost.actual_cost}`);
console.log(`Savings: ${data.cost.savings_pct}%`);
```

**Python:**

```python
import requests

resp = requests.post(
    "http://localhost:8000/v1/route",
    json={
        "prompt": "Write a SQL query for top 10 active customers.",
        "user_id": "user-123",
        "max_output_tokens": 400
    }
)

data = resp.json()
print(f"Response: {data['response']}")
print(f"Model: {data['model_used']}")
print(f"Cost: ${data['cost']['actual_cost']:.6f}")
print(f"Savings: {data['cost']['savings_pct']:.1f}%")
```

**Go:**

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

func main() {
    payload := map[string]interface{}{
        "prompt": "Explain the difference between REST and GraphQL.",
        "user_id": "user-123",
    }
    
    jsonData, _ := json.Marshal(payload)
    
    resp, _ := http.Post(
        "http://localhost:8000/v1/route",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    // Use result
}
```

### Response Schema

**Success Response (200 OK):**

```json
{
  "response": "Big O notation is a way to describe the time or space complexity of an algorithm...",
  "model_used": "gpt-4o-mini",
  "complexity": 1,
  "cache_hit": false,
  "tokens_in": 82,
  "tokens_out": 146,
  "cost": {
    "actual_cost": 0.00027,
    "baseline_cost": 0.00180,
    "absolute_savings": 0.00153,
    "savings_pct": 85.0
  },
  "latency_ms": 120
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | The LLM-generated response text |
| `model_used` | string | Model selected by routing engine (e.g., `gpt-4o-mini`, `claude-3-haiku`, `cache`) |
| `complexity` | integer | Complexity classification: `0` = simple, `1` = medium, `2` = complex |
| `cache_hit` | boolean | `true` if response came from semantic cache, `false` otherwise |
| `tokens_in` | integer | Number of input tokens (after compression) |
| `tokens_out` | integer | Number of output tokens |
| `cost` | object | Cost breakdown object (see below) |
| `latency_ms` | number | End-to-end request latency in milliseconds |

**Cost Object:**

| Field | Type | Description |
|-------|------|-------------|
| `actual_cost` | number | Actual cost for this request in USD |
| `baseline_cost` | number | Estimated cost if using GPT-4o baseline in USD |
| `absolute_savings` | number | Dollar amount saved vs. baseline |
| `savings_pct` | number | Percentage saved vs. baseline (0–100) |

### Response Examples

**Cache Hit Response:**

```json
{
  "response": "Cached response from previous similar request...",
  "model_used": "cache",
  "complexity": 0,
  "cache_hit": true,
  "tokens_in": 82,
  "tokens_out": 146,
  "cost": {
    "actual_cost": 0.0001,
    "baseline_cost": 0.00180,
    "absolute_savings": 0.00170,
    "savings_pct": 94.4
  },
  "latency_ms": 15
}
```

**Normal Response (No Cache):**

```json
{
  "response": "Big O notation describes algorithm complexity...",
  "model_used": "gpt-4o-mini",
  "complexity": 1,
  "cache_hit": false,
  "tokens_in": 82,
  "tokens_out": 146,
  "cost": {
    "actual_cost": 0.00027,
    "baseline_cost": 0.00180,
    "absolute_savings": 0.00153,
    "savings_pct": 85.0
  },
  "latency_ms": 120
}
```

---

## Dashboard Endpoints

All dashboard endpoints return analytics data for monitoring usage, costs, and optimization performance.

### GET /dashboard/stats

Get top-level summary statistics.

**Response:**

```json
{
  "total_requests": 15234,
  "total_tokens_in": 1920033,
  "total_tokens_out": 891224,
  "total_actual_cost": 13.92,
  "total_baseline_cost": 43.55,
  "total_savings": 29.63,
  "savings_pct": 68.0,
  "cache_hit_rate": 41.2
}
```

### GET /dashboard/usage

Get usage breakdown by model.

**Response:**

```json
{
  "models": [
    {
      "model": "gpt-4o-mini",
      "count": 5230,
      "input_tokens": 321030,
      "output_tokens": 120002,
      "actual_cost": 1.24
    },
    {
      "model": "llama3-70b-groq",
      "count": 1120,
      "input_tokens": 42011,
      "output_tokens": 11892,
      "actual_cost": 0.09
    }
  ]
}
```

### GET /dashboard/cache

Get cache performance metrics.

**Response:**

```json
{
  "cache_hits": 4100,
  "cache_misses": 5900,
  "hit_rate": 41.0,
  "recent_hits": [
    {
      "prompt": "Explain quantum computing...",
      "response_length": 120
    }
  ]
}
```

### GET /dashboard/routing

Get routing complexity and model distribution.

**Response:**

```json
{
  "complexity_distribution": {
    "0": 4020,
    "1": 8800,
    "2": 2414
  },
  "model_distribution": {
    "gpt-4o-mini": 5100,
    "claude-3-haiku": 3200,
    "llama3-70b-groq": 2100
  }
}
```

### GET /dashboard/daily

Get daily timeseries metrics.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | integer | Number of days to look back (default: 30) |

**Response:**

```json
{
  "days": [
    {
      "date": "2025-01-01",
      "requests": 440,
      "tokens_in": 55120,
      "tokens_out": 22041,
      "actual_cost": 0.27,
      "baseline_cost": 0.92,
      "savings": 0.65
    }
  ]
}
```

### GET /dashboard/models

Get model usage and cost comparison.

**Response:**

```json
{
  "entries": [
    {
      "model": "gpt-4o",
      "requests": 210,
      "actual_cost": 2.81,
      "baseline_cost": 2.81,
      "savings_pct": 0.0
    },
    {
      "model": "gpt-4o-mini",
      "requests": 5120,
      "actual_cost": 1.22,
      "baseline_cost": 16.82,
      "savings_pct": 92.8
    }
  ]
}
```

### GET /dashboard/savings

Get historical savings over time.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | integer | Number of days to look back (default: 30) |

**Response:**

```json
{
  "savings_over_time": [
    {
      "date": "2025-01-01",
      "saved": 0.38
    },
    {
      "date": "2025-01-02",
      "saved": 0.52
    }
  ]
}
```

---

## Error Handling

Cost Melt returns structured error responses with consistent formatting.

### Error Response Format

```json
{
  "error": "Error message",
  "code": 400,
  "message": "Detailed error description"
}
```

### HTTP Status Codes

| Status Code | Description | Example |
|-------------|-------------|---------|
| `200` | Success | Request processed successfully |
| `400` | Bad Request | Invalid prompt or request format |
| `401` | Unauthorized | Missing or invalid API key |
| `403` | Forbidden | API key lacks required permissions |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | No healthy LLM providers available |
| `504` | Gateway Timeout | Batch queue timeout |

### Error Examples

**400 - Invalid Prompt:**

```json
{
  "error": "Invalid request",
  "code": 400,
  "message": "Prompt cannot be empty after normalization"
}
```

**500 - Internal Server Error:**

```json
{
  "error": "Internal server error",
  "code": 500,
  "message": "An unexpected error occurred during request processing"
}
```

**504 - Batch Queue Timeout:**

```json
{
  "error": "Batch queue timeout",
  "code": 504,
  "message": "Request timed out waiting for batch processing"
}
```

**503 - Provider Unavailable:**

```json
{
  "error": "Service unavailable",
  "code": 503,
  "message": "No healthy providers available"
}
```

### Error Handling Best Practices

1. **Always check response status** before parsing JSON
2. **Handle timeouts gracefully** with retry logic
3. **Log error codes and messages** for debugging
4. **Implement exponential backoff** for retries
5. **Display user-friendly messages** based on error codes

**Example Error Handling (Node.js):**

```javascript
try {
  const res = await fetch("http://localhost:8000/v1/route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: "Hello" })
  });
  
  if (!res.ok) {
    const error = await res.json();
    if (error.code === 504) {
      // Handle timeout - retry with exponential backoff
      console.error("Request timed out, retrying...");
    } else {
      throw new Error(error.message);
    }
  }
  
  const data = await res.json();
  return data;
} catch (error) {
  console.error("Request failed:", error);
  throw error;
}
```

---

## Rate Limiting

Rate limiting is implemented per API key to prevent abuse and ensure fair usage.

### Current Limits

| Plan | Rate Limit |
|------|------------|
| **Free** | 60 requests/minute |
| **Pro** | 1,000 requests/minute |
| **Enterprise** | Unlimited |

### Rate Limit Headers

Responses include rate limit information in headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded

When rate limit is exceeded, API returns:

**Status Code:** `429 Too Many Requests`

**Response:**

```json
{
  "error": "Rate limit exceeded",
  "code": 429,
  "message": "You have exceeded the rate limit of 60 requests per minute",
  "retry_after": 15
}
```

### Best Practices

1. **Monitor rate limit headers** to avoid hitting limits
2. **Implement request queuing** for high-volume applications
3. **Use exponential backoff** when rate limited
4. **Consider upgrading** to Pro or Enterprise for higher limits

---

## Model Routing Catalog

Cost Melt automatically routes requests to the most cost-effective model capable of handling the task.

| Model | Provider | Strength | Cost Level | Complexity | Notes |
|-------|----------|----------|------------|------------|-------|
| `gpt-4o` | OpenAI | Reasoning, Code | $$$ | 2 (Complex) | Best for complex reasoning, code generation, architecture design |
| `gpt-4o-mini` | OpenAI | General Purpose | $ | 0–1 (Simple–Medium) | Default choice for most tasks, excellent cost/performance |
| `claude-3-haiku` | Anthropic | Fast, Balanced | $ | 1 (Medium) | Great for multi-step reasoning, data analysis, moderate complexity |
| `claude-3-5-sonnet` | Anthropic | High Accuracy | $$$ | 2 (Complex) | Premium model for high-quality outputs, complex reasoning |
| `llama3-70b-groq` | Groq | Very Fast | $ | 0 (Simple) | Ultra-fast for simple Q&A, summaries, basic tasks |
| `deepseek-chat` | DeepSeek | Ultra-Cheap | $ | 0 (Simple) | Lowest cost option for simple prompts, basic tasks |

### Routing Logic

The routing engine considers:

1. **Prompt Complexity** – Analyzed by Overkill Detector (0, 1, or 2)
2. **Model Capabilities** – Each model's strengths and limitations
3. **Cost Efficiency** – Token costs per model
4. **Provider Health** – Real-time availability checks
5. **User Preferences** – Custom routing rules (future feature)

**Complexity → Model Mapping:**

- **Complexity 0 (Simple):** `llama3-70b-groq`, `deepseek-chat`, `gpt-4o-mini`
- **Complexity 1 (Medium):** `claude-3-haiku`, `gpt-4o-mini`, `deepseek-chat`
- **Complexity 2 (Complex):** `gpt-4o`, `claude-3-5-sonnet`

---

## Semantic Cache API

Cost Melt uses semantic caching to identify and reuse responses for similar prompts, dramatically reducing costs.

### How It Works

1. **Embedding Generation** – Prompt is embedded using OpenAI's `text-embedding-3-small`
2. **Similarity Search** – Vector similarity search in Supabase (cosine similarity)
3. **Threshold Check** – If similarity > 0.92, return cached response
4. **Cache Storage** – New responses are stored with embeddings for future matches

### Cache Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Similarity Threshold | 0.92 | Minimum cosine similarity for cache hit |
| TTL | 7 days | Time-to-live for cache entries |
| Max Cache Size | 50,000 | Maximum cached entries (LRU eviction) |

### Cache Storage (Supabase)

Cache entries are stored in the `cache` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Unique cache entry ID |
| `prompt` | text | Original prompt text |
| `response` | text | Cached LLM response |
| `embedding_vector` | vector(1536) | Vector embedding for similarity search |
| `created_at` | timestamp | Cache entry creation time |

### Cache Performance

Typical cache performance:

- **Hit Rate:** 30–50% for production workloads
- **Latency:** < 20ms for cache hits (vs. 100–500ms for LLM calls)
- **Cost Savings:** 94%+ on cached requests (minimal embedding cost)

---

## Batch Queue API

Cost Melt uses micro-batching to group compatible requests and reduce per-request overhead.

### How It Works

1. **Request Enqueue** – Requests are pushed into Redis queues per model
2. **Batch Collection** – Worker collects requests for 5–10ms window
3. **Batch Execution** – Up to 16 requests sent as single batch to LLM provider
4. **Response Distribution** – Responses are mapped back to original requests
5. **Result Retrieval** – Clients poll for results using correlation IDs

### Batch Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Batch Window | 10ms | Maximum wait time before flushing batch |
| Max Batch Size | 16 | Maximum requests per batch |
| Timeout | 5s | Maximum wait time for batch processing |

### Queue Structure (Redis)

**Queue Keys:**
- `costmelt:batch:<model>` – List of pending requests per model
- `costmelt:pending:<request_id>` – Result storage for each request

**Request Format:**

```json
{
  "id": "uuid",
  "prompt": "string",
  "model": "gpt-4o-mini",
  "complexity": 1,
  "user_id": "string",
  "metadata": {}
}
```

**Response Format:**

```json
{
  "request_id": "uuid",
  "status": "ok",
  "response": "string",
  "from_cache": false,
  "batched": true
}
```

### Batch Worker

The batch worker (`backend/workers/batch_worker.py`) continuously:

1. Checks all model queues
2. Pops requests and groups into batches
3. Sends batches to LLM providers
4. Writes results back to pending keys
5. Handles errors and retries

---

## Webhooks

Webhooks allow you to receive notifications when requests complete (future feature).

### Webhook Endpoint (Future)

**POST** `/webhooks/completion`

### Webhook Payload

```json
{
  "user_id": "user-123",
  "request_id": "req-abc-123",
  "model_used": "gpt-4o-mini",
  "complexity": 1,
  "tokens_in": 82,
  "tokens_out": 146,
  "cost": {
    "actual_cost": 0.00027,
    "baseline_cost": 0.00180,
    "absolute_savings": 0.00153,
    "savings_pct": 85.0
  },
  "cache_hit": false,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Webhook Configuration

Configure webhooks in the Dashboard → Settings → Webhooks section:

1. Add webhook URL
2. Select events (completion, error, rate_limit)
3. Set retry policy
4. Test webhook delivery

---

## Changelog

### v0.1.0 (Initial Release)

**Released:** January 2025

**Features:**
- ✅ Main `/v1/route` endpoint with full optimization pipeline
- ✅ Semantic caching with vector similarity search
- ✅ Prompt compression (20–50% token reduction)
- ✅ Smart model routing based on complexity
- ✅ Micro-batching for cost efficiency
- ✅ Cost calculation and savings tracking
- ✅ Dashboard analytics endpoints
- ✅ Support for OpenAI, Anthropic, Groq, DeepSeek

**Improvements:**
- Comprehensive error handling
- Health check endpoint
- Structured logging
- Production-ready Docker setup

**Known Limitations:**
- API key authentication not yet implemented (dev mode only)
- Webhooks not yet available
- Custom routing rules not yet supported

---

## Support

For API support:

- **Documentation:** [https://docs.costmelt.com](https://docs.costmelt.com)
- **GitHub Issues:** [https://github.com/your-username/costmelt/issues](https://github.com/your-username/costmelt/issues)
- **Email:** support@costmelt.com

---

**Last Updated:** January 2025

