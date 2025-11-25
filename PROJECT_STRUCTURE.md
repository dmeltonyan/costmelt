# Cost Melt - Project Structure

## Complete Project Overview

This document outlines the complete structure of the Cost Melt monorepo.

## Directory Structure

```
costmelt/
├── backend/                    # FastAPI backend service
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend Docker image
│   ├── api/                    # API routers
│   │   ├── gateway.py          # Main /v1/route endpoint
│   │   ├── dashboard.py        # Dashboard analytics endpoints
│   │   ├── routing_engine.py   # Model routing logic
│   │   ├── semantic_cache.py   # Vector-based caching
│   │   ├── prompt_compressor.py # Prompt optimization
│   │   ├── overkill_detector.py # Complexity classification
│   │   └── batch_queue.py      # Redis batch queue
│   ├── services/               # LLM client implementations
│   │   ├── openai_client.py    # OpenAI (GPT-4o, GPT-4o-mini, embeddings)
│   │   ├── anthropic_client.py # Anthropic (Claude models)
│   │   ├── deepseek_client.py  # DeepSeek API
│   │   └── groq_client.py      # Groq (Llama 3)
│   ├── db/                     # Database layer
│   │   ├── supabase_client.py  # Supabase client wrapper
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── schema.sql           # PostgreSQL schema with pgvector
│   ├── workers/                # Background workers
│   │   └── batch_worker.py     # Redis batch processor
│   └── utils/                  # Utilities
│       ├── token_counter.py    # Token counting (tiktoken)
│       ├── cost_calculator.py  # Cost calculation
│       └── logger.py           # Logging configuration
│
├── dashboard/                  # Next.js dashboard application
│   ├── app/                    # Next.js app router
│   │   ├── page.tsx            # Dashboard home
│   │   ├── logs/               # Request logs page
│   │   ├── routing/            # Routing breakdown page
│   │   ├── cache/              # Cache statistics page
│   │   ├── keys/               # API key management
│   │   ├── billing/            # Billing & usage
│   │   └── api/                # API route handlers
│   ├── components/             # React components
│   │   ├── StatsCard.tsx       # Statistics card component
│   │   ├── CostChart.tsx      # Cost chart (Recharts)
│   │   └── ModelHeatmap.tsx    # Model routing visualization
│   ├── package.json            # Node.js dependencies
│   ├── Dockerfile              # Dashboard Docker image
│   └── tsconfig.json           # TypeScript configuration
│
├── landing/                    # Next.js marketing site
│   ├── app/                    # Next.js app router
│   │   ├── page.tsx            # Landing page with animations
│   │   └── layout.tsx           # Root layout
│   ├── package.json            # Node.js dependencies
│   ├── Dockerfile              # Landing page Docker image
│   └── tsconfig.json           # TypeScript configuration
│
├── scripts/                    # Bootstrap scripts
│   ├── bootstrap.sh            # Linux/Mac bootstrap
│   └── bootstrap.ps1           # Windows PowerShell bootstrap
│
├── docker-compose.yml          # Multi-service Docker setup
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Main documentation
└── PROJECT_STRUCTURE.md        # This file
```

## Key Features Implemented

### Backend Features

1. **Routing Engine** (`api/routing_engine.py`)
   - Complexity-based model selection
   - Supports 6 models: GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet, Claude Haiku, DeepSeek, Llama 3
   - Automatic cost optimization

2. **Semantic Cache** (`api/semantic_cache.py`)
   - Vector embeddings using OpenAI text-embedding-3-small
   - Cosine similarity threshold: 0.92
   - Supabase pgvector integration

3. **Prompt Compression** (`api/prompt_compressor.py`)
   - Uses GPT-4o-mini for compression
   - Only compresses if savings > 50 tokens
   - Preserves essential meaning

4. **Overkill Detector** (`api/overkill_detector.py`)
   - Classifies prompts: Simple (0), Medium (1), Complex (2)
   - Prevents overuse of expensive models

5. **Batch Queue** (`api/batch_queue.py`)
   - Redis-based queue system
   - 5-10ms batching window
   - Up to 10 requests per batch

6. **Cost Calculator** (`utils/cost_calculator.py`)
   - Real-time cost tracking
   - Savings calculation
   - Multi-model pricing support

### Dashboard Features

1. **Home Page** (`dashboard/app/page.tsx`)
   - Overall statistics cards
   - Cost & savings chart
   - Model routing heatmap

2. **Request Logs** (`dashboard/app/logs/page.tsx`)
   - Table of all requests
   - Filtering and search (TODO)

3. **Routing Breakdown** (`dashboard/app/routing/page.tsx`)
   - Model usage statistics
   - Cost per model
   - Percentage breakdown

4. **Cache Statistics** (`dashboard/app/cache/page.tsx`)
   - Cache hit rate
   - Total hits/misses
   - Savings from caching

5. **API Key Management** (`dashboard/app/keys/page.tsx`)
   - Placeholder for key management UI

6. **Billing** (`dashboard/app/billing/page.tsx`)
   - Placeholder for billing information

### Landing Page Features

1. **Hero Section** (`landing/app/page.tsx`)
   - Animated headline with Framer Motion
   - Call-to-action button
   - Feature explanation

2. **How It Works** Section
   - 4 feature cards with animations

3. **Features Grid**
   - 6 feature highlights

4. **Pricing Tiers**
   - Free, Pro, Enterprise plans

5. **FAQ Section**
   - Common questions with animations

## API Endpoints

### Main Endpoint
- `POST /v1/route` - Main optimization endpoint

### Dashboard Endpoints
- `GET /dashboard/stats` - Overall statistics
- `GET /dashboard/usage?days=7` - Usage over time
- `GET /dashboard/cache` - Cache statistics
- `GET /dashboard/routing` - Routing breakdown
- `GET /dashboard/daily?days=30` - Daily statistics

## Database Schema

Tables:
- `requests` - Request logs with metadata
- `cache` - Cached prompt-response pairs with embeddings
- `users` - User accounts (extends Supabase Auth)
- `api_keys` - API key management

See `backend/db/schema.sql` for full schema.

## Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `SUPABASE_ANON_KEY` - Supabase anon key

Optional:
- `ANTHROPIC_API_KEY` - Anthropic API key
- `DEEPSEEK_API_KEY` - DeepSeek API key
- `GROQ_API_KEY` - Groq API key
- `REDIS_URL` - Redis connection URL (default: redis://localhost:6379)

## Next Steps

1. **Setup Environment**
   - Copy `.env.example` to `.env`
   - Fill in API keys

2. **Setup Database**
   - Create Supabase project
   - Run `backend/db/schema.sql` in Supabase SQL editor

3. **Start Services**
   - Run `docker-compose up` for full stack
   - Or use bootstrap scripts for local development

4. **Test**
   - Send test request to `/v1/route`
   - Check dashboard at `http://localhost:3000`

## Development Notes

- Backend uses FastAPI with async/await
- Frontend uses Next.js 14 with App Router
- Styling with Tailwind CSS
- Charts with Recharts
- Animations with Framer Motion
- Database: Supabase (PostgreSQL + pgvector)
- Queue: Redis
- All services containerized with Docker

## TODO Items

- [ ] Implement authentication/authorization
- [ ] Complete API key management UI
- [ ] Add real-time request logs
- [ ] Implement advanced analytics
- [ ] Add webhook support
- [ ] Implement rate limiting
- [ ] Add multi-tenant support
- [ ] Create custom model configurations

