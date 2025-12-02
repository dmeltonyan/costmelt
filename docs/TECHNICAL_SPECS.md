# Cost Melt - Technical Specifications

**Version 1.0.0 | Last Updated: 2025-01-XX**

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [API Specifications](#api-specifications)
3. [Database Schema](#database-schema)
4. [Algorithm Specifications](#algorithm-specifications)
5. [Performance Requirements](#performance-requirements)
6. [Security Specifications](#security-specifications)
7. [Integration Specifications](#integration-specifications)

---

## System Architecture

### Technology Stack

**Backend**:
- Language: Python 3.11+
- Framework: FastAPI 0.104+
- ASGI Server: Uvicorn
- Database: PostgreSQL (Supabase) with pgvector
- Cache/Queue: Redis 7+
- Authentication: Bcrypt

**Frontend**:
- Framework: Next.js 14 (App Router)
- Language: TypeScript 5+
- Styling: TailwindCSS 3+
- UI Components: shadcn/ui
- Charts: Recharts
- Animations: Framer Motion

**Infrastructure**:
- Containerization: Docker
- Orchestration: Docker Compose (local), Kubernetes (production)
- CI/CD: GitHub Actions
- Monitoring: CloudWatch / Datadog

### Component Specifications

#### API Gateway (`backend/api/gateway.py`)

**Class**: `LLMOrchestrator`

**Methods**:
```python
async def route(
    self,
    prompt: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    max_output_tokens: Optional[int] = 400
) -> RouteResponse
```

**Request Flow**:
1. Normalize prompt (strip, dedent)
2. Semantic cache lookup
3. If cache hit: return cached response
4. Prompt compression
5. Complexity detection
6. Model routing
7. Batch queue enqueue
8. Wait for response (max 30s timeout)
9. Token counting
10. Cost calculation
11. Supabase logging
12. Return response

**Response Format**:
```json
{
  "response": "string",
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

#### Semantic Cache (`backend/api/semantic_cache.py`)

**Class**: `SemanticCache`

**Methods**:
```python
async def lookup(self, prompt: str) -> CacheResult
async def store(self, prompt: str, response: str, model: str, tokens_in: int, tokens_out: int) -> None
```

**Algorithm**:
1. Compute embedding using `text-embedding-3-small` (1536 dimensions)
2. Query Supabase vector DB: `SELECT * FROM semantic_cache WHERE prompt_embedding <-> $1 < 0.95 ORDER BY prompt_embedding <-> $1 LIMIT 1`
3. Check Redis for TTL and LRU status
4. If match found and valid: return cached response
5. If no match: store new entry with embedding

**Eviction Policy**:
- LRU: Track access order in Redis
- TTL: Default 7 days, configurable per user
- Size Limit: Max 10,000 entries per user

**Similarity Threshold**: 0.95 cosine similarity (configurable)

#### Prompt Compressor (`backend/api/prompt_compressor.py`)

**Class**: `PromptCompressor`

**Methods**:
```python
async def compress(self, prompt: str) -> dict
```

**Compression Pipeline**:
1. **Normalization**:
   - Strip leading/trailing whitespace
   - Dedent (remove common leading spaces)
   - Normalize line breaks
   - Convert tabs to spaces

2. **Rule-Based Compression**:
   - Remove filler phrases: "Please note that", "Kindly be informed", etc.
   - Deduplicate instructions (85% token similarity)
   - Shorten boilerplate: "explain in detail" → "explain briefly"
   - Collapse enumerations (>5 items)

3. **LLM-Based Compression**:
   - Use GPT-4o-mini with temperature=0
   - System prompt: "Compress prompt while preserving meaning and instructions"
   - User prompt: Original prompt
   - Max tokens: 50% of original

4. **Safety Checks**:
   - Length must decrease
   - Must contain key instructions
   - Must preserve user intent
   - If unsafe: fallback to rule-based only

**Target Reduction**: 20-50% token reduction

#### Overkill Detector (`backend/api/overkill_detector.py`)

**Class**: `OverkillDetector`

**Methods**:
```python
async def score(self, prompt: str) -> int
```

**Complexity Signals**:
1. **Token Count**:
   - < 80 tokens → -0.5 (simple)
   - 80-250 tokens → 0 (medium)
   - > 250 tokens → +1 (complex)

2. **Keyword Detection**:
   - Simple keywords: -0.3 each
   - Medium keywords: +0.2 each
   - Complex keywords: +0.5 each

3. **Code Detection**:
   - Code blocks present → +0.5
   - Code > 150 tokens → +1

4. **Math/Reasoning**:
   - Math patterns → +1
   - "prove", "derive", "calculate" → +1

5. **Multi-Step Instructions**:
   - 2 steps → +0.5
   - 3+ steps → +1

6. **Embedding Similarity**:
   - Compare to complex examples → +0.5 if similar
   - Compare to simple examples → -0.3 if similar

**Scoring Formula**:
```
complexity_score = (
    token_weight * 0.3 +
    keyword_weight * 0.25 +
    code_weight * 0.2 +
    math_weight * 0.15 +
    multistep_weight * 0.1 +
    embedding_weight * 0.1
)
```

**Classification**:
- score < 1.0 → complexity 0 (simple)
- score < 2.0 → complexity 1 (medium)
- score >= 2.0 → complexity 2 (complex)

#### Routing Engine (`backend/api/routing_engine.py`)

**Class**: `RoutingEngine`

**Methods**:
```python
async def route(self, prompt: str, complexity: int, user_id: Optional[str] = None) -> RouteInfo
```

**Routing Matrix**:

| Complexity | Models | Selection Criteria |
|------------|--------|-------------------|
| 0 (Simple) | gpt-4o-mini, claude-3-haiku, llama3-70b-groq, deepseek-chat | Cheapest available |
| 1 (Medium) | gpt-4o-mini, claude-3-haiku, claude-3-5-sonnet | Cost + latency |
| 2 (Complex) | gpt-4o, claude-3-5-sonnet | Capability + cost |

**Provider Health**:
- Health check every 30 seconds
- Circuit breaker: 3 failures → mark unhealthy
- Recovery: 1 success → mark healthy
- Automatic failover to backup providers

#### Batch Queue (`backend/api/batch_queue.py`)

**Class**: `BatchQueue`

**Methods**:
```python
async def enqueue(self, request: dict) -> dict
```

**Configuration**:
- `BATCH_WINDOW_MS`: 10ms
- `MAX_BATCH_SIZE`: 16 requests
- `POLL_TIMEOUT`: 30 seconds

**Redis Keys**:
- Queue: `costmelt:batch:{model}` (Redis List)
- Pending: `costmelt:pending:{request_id}` (Redis String, JSON)

**Batching Logic**:
1. Group requests by model
2. Check queue length
3. If length >= MAX_BATCH_SIZE: pop MAX_BATCH_SIZE
4. Else if oldest item > BATCH_WINDOW_MS: pop all available
5. Else: wait for more requests

#### Cost Calculator (`backend/utils/cost_calculator.py`)

**Class**: `CostCalculator`

**Methods**:
```python
def compute_request_cost(model: str, input_tokens: int, output_tokens: int) -> float
def compute_baseline_cost(input_tokens: int, output_tokens: int, baseline_model: Optional[str] = None) -> float
def compute_savings(model: str, input_tokens: int, output_tokens: int, baseline_model: Optional[str] = None) -> dict
```

**Pricing Table** (per 1K tokens):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $0.005 | $0.015 |
| gpt-4o-mini | $0.00015 | $0.00060 |
| claude-3-haiku | $0.00025 | $0.00125 |
| claude-3-5-sonnet | $0.003 | $0.015 |
| llama3-70b-groq | $0.00006 | $0.00006 |
| deepseek-chat | $0.00002 | $0.00002 |

**Default Baseline**: gpt-4o

---

## API Specifications

### Authentication

**Header Format**:
```
Authorization: Bearer <api_key>
OR
X-API-Key: <api_key>
```

**API Key Format**:
```
cm_live_<32_random_chars>
```

**Rate Limits**:
- Free: 60 requests/minute
- Pro: 600 requests/minute
- Enterprise: Custom

### Endpoints

#### POST /v1/route

**Request**:
```json
{
  "prompt": "string (required)",
  "user_id": "string (optional)",
  "metadata": "object (optional)",
  "max_output_tokens": "number (optional, default 400)"
}
```

**Response**:
```json
{
  "response": "string",
  "model_used": "string",
  "complexity": 0|1|2,
  "cache_hit": boolean,
  "tokens_in": number,
  "tokens_out": number,
  "cost": {
    "actual_cost": number,
    "baseline_cost": number,
    "absolute_savings": number,
    "savings_pct": number
  },
  "latency_ms": number
}
```

**Error Responses**:
- `400`: Invalid request
- `401`: Unauthorized
- `429`: Rate limit exceeded
- `500`: Internal server error
- `504`: Batch queue timeout

#### GET /dashboard/stats

**Response**:
```json
{
  "total_requests": number,
  "total_tokens_in": number,
  "total_tokens_out": number,
  "total_actual_cost": number,
  "total_baseline_cost": number,
  "total_savings": number,
  "savings_pct": number,
  "cache_hit_rate": number
}
```

#### GET /dashboard/usage

**Response**:
```json
{
  "models": [
    {
      "model": "string",
      "count": number,
      "input_tokens": number,
      "output_tokens": number,
      "actual_cost": number
    }
  ]
}
```

---

## Database Schema

### Tables

#### `requests`

```sql
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    project_id TEXT,
    prompt TEXT NOT NULL,
    compressed_prompt TEXT,
    response TEXT NOT NULL,
    model_selected TEXT NOT NULL,
    complexity INT,
    tokens_in INT NOT NULL,
    tokens_out INT NOT NULL,
    cache_hit BOOLEAN DEFAULT FALSE,
    actual_cost DECIMAL(10, 8),
    baseline_cost DECIMAL(10, 8),
    savings DECIMAL(10, 8),
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_requests_user_id ON requests(user_id);
CREATE INDEX idx_requests_created_at ON requests(created_at);
CREATE INDEX idx_requests_model ON requests(model_selected);
CREATE INDEX idx_requests_cache_hit ON requests(cache_hit);
```

#### `api_keys`

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    prefix TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'write',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_api_keys_prefix ON api_keys(prefix);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_user_project ON api_keys(user_id, project_id);
```

#### `semantic_cache`

```sql
CREATE TABLE semantic_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    prompt_embedding vector(1536) NOT NULL,
    response TEXT NOT NULL,
    model_used TEXT NOT NULL,
    tokens_in INT NOT NULL,
    tokens_out INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    access_count INT DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_semantic_cache_user_id ON semantic_cache(user_id);
CREATE INDEX idx_semantic_cache_embedding ON semantic_cache USING ivfflat (prompt_embedding vector_cosine_ops);
```

---

## Performance Requirements

### Latency Targets

- **Cache Hit**: < 100ms (p95)
- **Cache Miss**: < 2s (p95)
- **Dashboard Load**: < 2s
- **API Response**: < 200ms (p95, cache hit), < 2s (p95, cache miss)

### Throughput Targets

- **API**: 1000+ requests/second (with horizontal scaling)
- **Batch Processing**: 100+ batches/second
- **Cache Lookups**: 5000+ lookups/second

### Scalability Targets

- **Horizontal Scaling**: Stateless design, scale to 10+ instances
- **Database**: Support 1M+ requests/day
- **Cache**: Support 100K+ cached entries
- **Concurrent Users**: 1000+ simultaneous users

---

## Security Specifications

### Authentication

- **API Keys**: Bcrypt hashed (cost factor 12)
- **Key Format**: `cm_live_<32_chars>` (prefix for fast lookup)
- **Key Rotation**: Support rotation without downtime
- **Key Revocation**: Immediate revocation

### Authorization

- **RBAC**: Three roles (admin/write/read)
- **Route Protection**: Middleware on `/v1/*` routes
- **Dashboard Protection**: API key required

### Data Security

- **Encryption**: TLS 1.3 for transit, Supabase encryption at rest
- **Secrets**: Environment variables, no hardcoded keys
- **API Keys**: Never logged, never returned in responses

### Rate Limiting

- **Algorithm**: Token bucket (Redis)
- **Limits**: Per subscription tier
- **Burst**: Allow short bursts, smooth over time

---

## Integration Specifications

### LLM Provider Integrations

#### OpenAI

**Client**: `backend/services/openai_client.py`

**Models**:
- `gpt-4o`: Chat completion
- `gpt-4o-mini`: Chat completion
- `text-embedding-3-small`: Embeddings

**API**: OpenAI Python SDK

#### Anthropic

**Client**: `backend/services/anthropic_client.py`

**Models**:
- `claude-3-haiku`: Chat completion
- `claude-3-5-sonnet`: Chat completion

**API**: Anthropic Python SDK

#### Groq

**Client**: `backend/services/groq_client.py`

**Models**:
- `llama3-70b-groq`: Chat completion

**API**: Groq Python SDK

#### DeepSeek

**Client**: `backend/services/deepseek_client.py`

**Models**:
- `deepseek-chat`: Chat completion

**API**: REST API (requests)

### SDK Integrations

#### Python SDK

**Package**: `costmelt`

**Usage**:
```python
from costmelt import CostMeltClient

client = CostMeltClient(api_key="cm_live_...")
result = client.route("Explain binary search.")
print(result["response"])
```

#### Node SDK

**Package**: `costmelt`

**Usage**:
```typescript
import { CostMeltClient } from "costmelt";

const client = new CostMeltClient({ apiKey: "cm_live_..." });
const result = await client.route("Explain binary search.");
console.log(result.response);
```

---

**Document Owner**: Engineering Team  
**Review Cycle**: Quarterly  
**Version Control**: Git

