# Cost Melt - Complete System Architecture

**End-to-End Architecture Document for Production SaaS Platform**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Deep Dive](#component-deep-dive)
4. [Data Flow](#data-flow)
5. [Infrastructure](#infrastructure)
6. [Security Architecture](#security-architecture)
7. [Scalability & Performance](#scalability--performance)
8. [Monitoring & Observability](#monitoring--observability)
9. [Deployment Architecture](#deployment-architecture)

---

## System Overview

Cost Melt is a production-ready SaaS platform that optimizes LLM costs through intelligent routing, caching, compression, and batching. The system is designed to be:

- **Drop-in Proxy**: Replace LLM API endpoints with Cost Melt
- **Multi-Provider**: Supports OpenAI, Anthropic, Groq, DeepSeek
- **Cost-Optimized**: Reduces token costs by 40-70%
- **Production-Ready**: Built for scale, reliability, and solo-founder operation

### Core Value Proposition

1. **Automatic Cost Reduction**: No code changes required
2. **Transparent Analytics**: Real-time dashboard with cost breakdowns
3. **Smart Routing**: Routes to cheapest capable model
4. **Semantic Caching**: Instant responses for similar prompts
5. **Prompt Compression**: 20-50% token reduction
6. **Micro-Batching**: Improved throughput and efficiency

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Web Apps │  Mobile Apps │  CLI Tools │  SDKs (Python/Node)    │
└───────────┴──────────────┴────────────┴────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Gateway │  Auth Middleware │  Rate Limiting │  CORS    │
└──────────────────┴──────────────────┴──────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Request Normalization │  Cache Lookup │  Compression │        │
│  Complexity Detection │  Routing Decision │  Batch Queue │       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CACHING    │    │   ROUTING    │    │   BATCHING   │
│   LAYER      │    │   ENGINE     │    │   SYSTEM     │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ Semantic     │    │ Overkill     │    │ Redis Queue  │
│ Cache        │    │ Detector     │    │ Batch Worker │
│ (Supabase)   │    │ Model Router │    │ LLM Clients  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM PROVIDER LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  OpenAI │  Anthropic │  Groq │  DeepSeek │  (Extensible)       │
└─────────┴────────────┴───────┴───────────┴──────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA & ANALYTICS LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  Supabase (Postgres + Vector) │  Redis │  Cost Calculator │     │
│  Request Logging │  Analytics │  Billing │  Metrics        │     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard (Next.js) │  Landing Page │  Admin Panel │  Docs    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. API Gateway Layer

**Location**: `backend/api/gateway.py`

**Responsibilities**:
- Request validation and normalization
- Authentication & authorization
- Rate limiting enforcement
- Error handling and response formatting
- Request/response logging

**Key Components**:
- `LLMOrchestrator`: Main orchestration class
- `RouteRequest`: Pydantic request model
- `RouteResponse`: Pydantic response model
- Middleware stack: Auth → Rate Limit → CORS

**Request Flow**:
```
POST /v1/route
  → Auth Middleware (API key validation)
  → Rate Limit Middleware (token bucket)
  → Request Normalization
  → Semantic Cache Lookup
  → Prompt Compression
  → Complexity Detection
  → Routing Decision
  → Batch Queue Enqueue
  → Cost Calculation
  → Supabase Logging
  → Response Formatting
```

### 2. Semantic Caching Layer

**Location**: `backend/api/semantic_cache.py`

**Architecture**:
- **Vector Store**: Supabase Postgres with `pgvector` extension
- **Cache Metadata**: Redis for LRU eviction and TTL
- **Embedding Model**: OpenAI `text-embedding-3-small`

**Data Structures**:
```sql
-- Supabase Table: semantic_cache
CREATE TABLE semantic_cache (
    id UUID PRIMARY KEY,
    prompt_hash TEXT,
    prompt_embedding vector(1536),
    response TEXT,
    model_used TEXT,
    tokens_in INT,
    tokens_out INT,
    created_at TIMESTAMPTZ,
    last_accessed TIMESTAMPTZ,
    access_count INT
);
```

**Cache Strategy**:
1. Compute embedding for incoming prompt
2. Vector similarity search (cosine distance < 0.95)
3. Check Redis TTL and LRU status
4. Return cached response if match found
5. Store new responses with embeddings

**Eviction Policy**:
- LRU: Redis tracks access order
- TTL: Default 7 days, configurable per user
- Size Limit: Max 10,000 entries per user

### 3. Routing Engine

**Location**: `backend/api/routing_engine.py`

**Components**:
- **Overkill Detector**: Complexity classification (0/1/2)
- **Model Router**: Selects optimal model based on complexity
- **Provider Health**: Monitors provider availability
- **Cost Matrix**: Model pricing and capability mapping

**Routing Logic**:
```
Complexity 0 (Simple):
  → gpt-4o-mini, claude-3-haiku, llama3-70b-groq, deepseek-chat
  → Select cheapest available

Complexity 1 (Medium):
  → gpt-4o-mini, claude-3-haiku, claude-3-5-sonnet
  → Select based on cost + latency

Complexity 2 (Complex):
  → gpt-4o, claude-3-5-sonnet
  → Select based on capability + cost
```

**Provider Health Monitoring**:
- Health checks every 30 seconds
- Circuit breaker pattern
- Automatic failover to backup providers
- Latency tracking and optimization

### 4. Prompt Compression Engine

**Location**: `backend/api/prompt_compressor.py`

**Compression Pipeline**:
1. **Normalization**: Whitespace, dedent, line breaks
2. **Rule-Based Compression**:
   - Remove filler phrases
   - Deduplicate instructions
   - Shorten boilerplate
   - Collapse enumerations
3. **LLM-Based Compression**:
   - Use GPT-4o-mini for summarization
   - Temperature=0 for determinism
   - Preserve instructions and intent
4. **Safety Checks**:
   - Ensure length reduction
   - Verify instruction preservation
   - Fallback to rule-based if unsafe

**Target Reduction**: 20-50% token reduction

### 5. Batch Queue System

**Location**: `backend/api/batch_queue.py`, `backend/workers/batch_worker.py`

**Architecture**:
- **Queue**: Redis Lists per model (`costmelt:batch:{model}`)
- **Pending Results**: Redis Keys (`costmelt:pending:{request_id}`)
- **Worker**: Async Python worker processes batches

**Batching Strategy**:
- Group by model and complexity
- Max batch size: 16 requests
- Batch window: 10ms (configurable)
- Flush on: size limit OR time window

**Worker Flow**:
```
1. Poll Redis queues for each model
2. Group requests into batches (max 16)
3. Call LLM provider batch API
4. Map responses back to request IDs
5. Write results to pending keys
6. Repeat
```

### 6. Cost Calculator

**Location**: `backend/utils/cost_calculator.py`

**Responsibilities**:
- Track token costs per model
- Compute baseline costs (naive routing)
- Calculate absolute and percentage savings
- Aggregate costs for analytics

**Pricing Model**:
```python
MODEL_PRICING = {
    "gpt-4o": {"input_per_1k": 0.005, "output_per_1k": 0.015},
    "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.00060},
    "claude-3-haiku": {"input_per_1k": 0.00025, "output_per_1k": 0.00125},
    # ... more models
}
```

**Savings Calculation**:
```
baseline_cost = compute_baseline_cost(tokens, baseline_model="gpt-4o")
actual_cost = compute_request_cost(model, tokens_in, tokens_out)
absolute_savings = baseline_cost - actual_cost
savings_pct = (absolute_savings / baseline_cost) * 100
```

### 7. Authentication & Security

**Location**: `backend/security/`, `backend/middleware/`

**Components**:
- **API Key Manager**: Generation, hashing (bcrypt), verification
- **RBAC**: Role-based access control (admin/write/read)
- **Rate Limiting**: Redis token bucket algorithm
- **Auth Middleware**: API key validation on all `/v1/*` routes

**API Key Format**:
```
cm_live_<32_random_chars>
Prefix: cm_live_ (for lookup)
Hash: bcrypt hash stored in DB
```

**Rate Limits**:
- Free: 60 requests/min
- Pro: 600 requests/min
- Enterprise: Custom (stored in DB)

### 8. Database Schema

**Location**: `backend/db/schema.sql`

**Core Tables**:
- `requests`: All API requests and responses
- `api_keys`: API key management
- `semantic_cache`: Vector cache storage
- `users`: User accounts (future)
- `subscriptions`: Billing subscriptions (future)
- `billing_events`: Usage-based billing events (future)

**Indexes**:
- `requests`: `(user_id, created_at)`, `(model_selected)`, `(cache_hit)`
- `api_keys`: `(prefix)`, `(user_id, project_id)`
- `semantic_cache`: Vector index on `prompt_embedding`

### 9. Frontend Dashboard

**Location**: `dashboard/`

**Tech Stack**:
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- shadcn/ui components
- Recharts for visualizations
- SWR for data fetching

**Pages**:
- `/`: Home dashboard with key metrics
- `/usage`: Model usage breakdown
- `/cache`: Cache performance metrics
- `/routing`: Routing complexity distribution
- `/models`: Model comparison table
- `/daily`: Daily timeseries charts
- `/savings`: Historical savings visualization
- `/logs`: Request logs (future)
- `/keys`: API key management (future)
- `/billing`: Subscription and billing (future)

### 10. Landing Page

**Location**: `landing/`

**Pages**:
- `/`: Hero, features, pricing, testimonials
- `/pricing`: Detailed pricing plans
- `/privacy`: Privacy policy
- `/terms`: Terms of service

**Features**:
- Framer Motion animations
- Responsive design
- SEO optimized
- Conversion-focused CTAs

---

## Data Flow

### Request Flow (Cache Miss)

```
1. Client → POST /v1/route {prompt, user_id}
2. Auth Middleware → Validate API key
3. Rate Limit → Check token bucket
4. Gateway → Normalize prompt
5. Semantic Cache → Lookup (miss)
6. Prompt Compressor → Compress prompt (20-50% reduction)
7. Overkill Detector → Classify complexity (0/1/2)
8. Routing Engine → Select model (e.g., gpt-4o-mini)
9. Batch Queue → Enqueue request
10. Batch Worker → Process batch → LLM Provider
11. LLM Provider → Response
12. Cost Calculator → Compute costs and savings
13. Supabase → Log request/response
14. Gateway → Format response
15. Client ← Response {response, model_used, cost, savings}
```

### Request Flow (Cache Hit)

```
1. Client → POST /v1/route {prompt, user_id}
2. Auth Middleware → Validate API key
3. Rate Limit → Check token bucket
4. Gateway → Normalize prompt
5. Semantic Cache → Lookup (HIT!)
6. Gateway → Return cached response (near-instant)
7. Supabase → Log cache hit
8. Client ← Response {response, cache_hit: true, cost: $0}
```

---

## Infrastructure

### Backend Infrastructure

**Runtime**: Python 3.11+ with FastAPI
**Server**: Uvicorn ASGI server
**Process Management**: Gunicorn + Uvicorn workers (production)

**Dependencies**:
- FastAPI: Web framework
- Redis: Caching, queueing, rate limiting
- Supabase: Postgres + Vector DB
- OpenAI/Anthropic/Groq/DeepSeek: LLM providers
- Tiktoken: Token counting
- Bcrypt: Password hashing

### Frontend Infrastructure

**Runtime**: Node.js 18+
**Framework**: Next.js 14 (App Router)
**Build**: Static generation + Server-side rendering
**Deployment**: Vercel, Netlify, or self-hosted

### Data Infrastructure

**Primary Database**: Supabase Postgres
- Vector extension (`pgvector`) for embeddings
- Row-level security (RLS) for multi-tenancy
- Automatic backups and point-in-time recovery

**Cache Layer**: Redis
- LRU eviction
- TTL management
- Pub/Sub for worker coordination

**Object Storage**: Supabase Storage (future)
- Log archives
- Export files

---

## Security Architecture

### Authentication

- **API Keys**: Bcrypt hashed, prefix lookup
- **Key Rotation**: Support for key rotation
- **Key Revocation**: Immediate revocation support

### Authorization

- **RBAC**: Three roles (admin/write/read)
- **Route Protection**: Middleware enforces on `/v1/*`
- **Dashboard Protection**: API key required for dashboard API

### Data Security

- **Encryption at Rest**: Supabase handles encryption
- **Encryption in Transit**: HTTPS/TLS required
- **Secrets Management**: Environment variables, no hardcoded keys
- **API Key Storage**: Hashed in database, never logged

### Rate Limiting

- **Token Bucket**: Redis-based algorithm
- **Per-User Limits**: Based on subscription tier
- **Burst Protection**: Prevents abuse

### Threat Protection

- **CORS**: Configurable origins
- **Input Validation**: Pydantic models
- **SQL Injection**: Parameterized queries only
- **XSS**: Next.js auto-escaping
- **DDoS**: Rate limiting + Cloudflare (production)

---

## Scalability & Performance

### Horizontal Scaling

**Backend**:
- Stateless API servers (scale horizontally)
- Redis for shared state
- Supabase for shared database
- Load balancer distributes traffic

**Workers**:
- Multiple batch worker instances
- Redis queues coordinate workers
- No shared state between workers

**Frontend**:
- Static generation for landing page
- Server-side rendering for dashboard
- CDN for static assets

### Performance Optimizations

**Caching**:
- Semantic cache reduces LLM calls by 30-50%
- Redis caching for frequently accessed data
- Next.js static generation for marketing pages

**Batching**:
- Micro-batching reduces per-request overhead
- 10ms window balances latency vs. efficiency

**Compression**:
- Prompt compression reduces tokens by 20-50%
- Gzip compression for API responses

**Database**:
- Indexed queries for fast lookups
- Vector indexes for similarity search
- Connection pooling

### Performance Targets

- **API Latency**: < 200ms (cache hit), < 2s (cache miss)
- **Throughput**: 1000+ requests/second (with horizontal scaling)
- **Cache Hit Rate**: 30-50% (typical usage)
- **Uptime**: 99.9% SLA target

---

## Monitoring & Observability

### Logging

**Structured Logging**:
- JSON format for parsing
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request IDs for tracing

**Log Aggregation**:
- CloudWatch (AWS)
- Datadog (alternative)
- Supabase logs (built-in)

### Metrics

**Key Metrics**:
- Request rate (RPS)
- Latency (p50, p95, p99)
- Error rate
- Cache hit rate
- Cost savings
- Token usage per model

**Monitoring Tools**:
- Prometheus + Grafana (self-hosted)
- Datadog (SaaS)
- CloudWatch (AWS)

### Alerting

**Critical Alerts**:
- API error rate > 1%
- Latency p95 > 2s
- Provider downtime
- Database connection failures
- Redis connection failures

---

## Deployment Architecture

### Production Deployment (Recommended)

**Backend**: Railway, Render, or AWS ECS
**Frontend**: Vercel, Netlify, or self-hosted
**Database**: Supabase (managed)
**Cache**: Redis Cloud or AWS ElastiCache
**CDN**: Cloudflare or Vercel Edge

### Multi-Region (Future)

- Backend replicas in multiple regions
- Database replication (Supabase)
- Redis replication
- CDN edge locations

### CI/CD Pipeline

**GitHub Actions**:
1. Run tests
2. Build Docker images
3. Push to registry
4. Deploy to staging
5. Run integration tests
6. Deploy to production

---

## Future Enhancements

### Phase 2: Billing & Subscriptions

- Stripe integration
- Usage-based billing
- Subscription management
- Invoice generation
- Payment webhooks

### Phase 3: Advanced Features

- Custom routing rules
- A/B testing framework
- Cost budgets and alerts
- Multi-project support
- Team collaboration

### Phase 4: Enterprise

- VPC deployment
- SOC2 compliance
- Dedicated support
- Custom SLAs
- On-premise deployment

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-01-XX  
**Maintained By**: Cost Melt Team

