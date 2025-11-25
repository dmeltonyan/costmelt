# 🚀 Cost Melt

**Production-ready LLM cost optimization platform that reduces AI token costs by 40–70% through intelligent routing, semantic caching, prompt compression, and micro-batching.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](https://github.com/dmeltonyan/costmelt)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Dashboard Setup](#dashboard-setup)
  - [Landing Setup](#landing-setup)
- [Docker](#docker)
- [Configuration](#configuration)
- [API Usage](#api-usage)
- [Dashboard Overview](#dashboard-overview)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Cost Melt is an intelligent LLM proxy that sits between your application and LLM providers, automatically optimizing every request to minimize token costs without requiring code changes. It acts as a drop-in replacement for direct API calls, handling model routing, semantic caching, prompt compression, and micro-batching behind the scenes.

The system intelligently routes requests to the most cost-effective model capable of handling the task complexity, caches semantically similar prompts to avoid redundant API calls, compresses prompts to reduce token usage, and batches compatible requests for maximum efficiency. All of this happens transparently—you simply point your application to Cost Melt's endpoint instead of the provider's API.

Cost Melt is built for AI startups, infrastructure teams, and indie developers who want to reduce their LLM bills without sacrificing functionality. It's model-agnostic, supporting OpenAI, Anthropic, Groq, DeepSeek, and other providers through a unified interface.

The project consists of two major components: a **Backend** built with FastAPI, Redis, and Supabase that handles all optimization logic, and a **Dashboard + Landing** built with Next.js, Tailwind CSS, and shadcn/ui that provides analytics and marketing pages.

---

## Key Features

- **Smart Model Routing** – Automatically chooses the cheapest capable LLM per request using a complexity classifier that analyzes prompt characteristics (token count, code patterns, reasoning requirements, etc.) to route simple tasks to cost-effective models and complex tasks to premium models.

- **Semantic Caching** – Uses vector embeddings to identify and reuse answers for semantically similar prompts, dramatically reducing costs for repeated or similar queries. Cache hits return instantly with near-zero cost.

- **Prompt Compression** – Reduces token count by 20–50% by intelligently compressing prompts while preserving meaning and required context. Uses a hybrid approach combining rule-based compression with LLM-based summarization.

- **Micro-Batching** – Groups compatible requests together and sends them as a single batch to LLM providers, reducing per-request overhead and improving throughput while maintaining low latency.

- **Cost Analytics Dashboard** – Comprehensive dashboard that visualizes requests, tokens, savings, routing choices, and cache performance. Track your spending, identify optimization opportunities, and monitor ROI in real-time.

- **Provider-Agnostic** – Supports multiple LLM providers (OpenAI, Anthropic, Groq, DeepSeek) through a unified interface. Add new providers without changing your application code.

- **Drop-In Proxy** – Change one URL in your app to start saving money. No code refactoring required—just replace your LLM API endpoint with Cost Melt's proxy.

---

## Architecture

Cost Melt's architecture is designed for scalability, reliability, and ease of integration. The system consists of several interconnected components that work together to optimize every request.

### Components

- **API Gateway** (`/backend/api/gateway.py`) – Main entry point that orchestrates all subsystems and handles request/response lifecycle.

- **Routing Engine** – Analyzes prompt complexity and selects the optimal model based on cost, capability, and provider health.

- **Overkill Detector** – Classifies prompt complexity (0=simple, 1=medium, 2=complex) using multiple signals including token count, code patterns, math/reasoning indicators, and semantic similarity.

- **Semantic Cache** – Stores and retrieves responses using vector embeddings. Queries Supabase vector database for similarity matches and uses Redis for LRU eviction and TTL management.

- **Prompt Compressor** – Reduces token count through rule-based compression and LLM-based summarization while preserving meaning and instructions.

- **Batch Queue** – Collects compatible requests and groups them into micro-batches for efficient processing. Uses Redis for queue management and async workers for batch execution.

- **Cost Calculator** – Tracks token costs per model, computes actual vs. baseline costs, and calculates savings for analytics and billing.

- **Supabase Logging** – Stores all requests, responses, costs, and metadata in Supabase for analytics, debugging, and compliance.

- **Dashboard Frontend** – Next.js application that provides real-time analytics, charts, and insights into usage patterns and cost savings.

### Request Flow

```
Your App
  |
  v
[ Cost Melt Proxy (/v1/route) ]
  |   |   |   |
  |   |   |   +--> Overkill Detector (complexity)
  |   |   +------> Prompt Compressor
  |   +----------> Semantic Cache (Supabase + embeddings)
  +--------------> Routing Engine (model selection)
                      |
                      v
                Batch Queue → LLM Providers (OpenAI, Anthropic, Groq, DeepSeek)
                      |
                      v
                Response + Cost Logging (Supabase)
                      |
                      v
               Cost Melt Dashboard (Next.js)
```

### How It Works

1. **Request arrives** at the API Gateway (`/v1/route` endpoint).

2. **Semantic cache is checked first** – If a similar prompt was processed recently, the cached response is returned immediately with minimal cost.

3. **Prompt is compressed** – The system analyzes the prompt and applies compression techniques to reduce token count while preserving meaning.

4. **Complexity is classified** – The Overkill Detector analyzes the prompt to determine complexity level (0, 1, or 2).

5. **Model is selected** – The Routing Engine chooses the optimal model based on complexity, cost, and provider availability.

6. **Request is batched** – Compatible requests are grouped together and sent as a batch to reduce costs and improve throughput.

7. **Response is processed** – The LLM response is received, token counts are calculated, and costs are computed.

8. **Data is logged** – Request details, costs, and metrics are stored in Supabase for analytics.

9. **Response is returned** – The optimized response is returned to your application with full cost and performance metadata.

10. **Dashboard updates** – Analytics are available in real-time through the Cost Melt dashboard.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Backend** | Python 3.11+, FastAPI |
| **Database** | Supabase Postgres + Vector Extensions |
| **Cache/Queue** | Redis |
| **Frontend** | Next.js 14 (App Router), TypeScript |
| **UI** | TailwindCSS, shadcn/ui, Recharts, Framer Motion |
| **Infrastructure** | Docker, docker-compose |
| **LLM Providers** | OpenAI, Anthropic, Groq, DeepSeek |

---

## Quickstart

### Prerequisites

- **Python 3.11+** – For backend development
- **Node.js 18+** – For frontend development
- **Docker & docker-compose** – For containerized deployment
- **Supabase project** – With URL and service key
- **API keys** – For at least one LLM provider (OpenAI, Anthropic, Groq, or DeepSeek)

### Clone the Repository

```bash
git clone https://github.com/your-username/costmelt.git
cd costmelt
```

### Backend Setup

1. **Navigate to backend directory:**

```bash
cd backend
```

2. **Create virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Create a `.env` file in the `backend` directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk_your-groq-key
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Optional: Backend Configuration
BACKEND_PORT=8000
LOG_LEVEL=INFO
```

5. **Set up database:**

- Open your Supabase project dashboard
- Navigate to SQL Editor
- Run the SQL schema from `backend/db/schema.sql` to create required tables

6. **Start the backend:**

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### Dashboard Setup

1. **Navigate to dashboard directory:**

```bash
cd ../dashboard
```

2. **Install dependencies:**

```bash
npm install
```

3. **Configure environment variables:**

Create a `.env.local` file:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

4. **Start the dashboard:**

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Landing Setup

1. **Navigate to landing directory:**

```bash
cd ../landing
```

2. **Install dependencies:**

```bash
npm install
```

3. **Start the landing page:**

```bash
npm run dev
```

The landing page will be available at `http://localhost:3001`.

---

## Docker

For a one-command development setup, use Docker Compose:

```bash
docker-compose up --build
```

This command will:

- Build and start the **backend** service on `http://localhost:8000`
- Build and start the **dashboard** service on `http://localhost:3000`
- Build and start the **landing** service on `http://localhost:3001`
- Start **Redis** as a service for caching and batching
- Optionally start a local **Supabase** instance (if configured)

Ensure your `.env` files are properly configured before running docker-compose. The `docker-compose.yml` file includes service definitions for all components and handles networking between services automatically.

To stop all services:

```bash
docker-compose down
```

---

## Configuration

All configuration is done through environment variables. Here's a comprehensive reference:

| Variable | Description | Required | Default |
|----------|-------------|-----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key | Optional* | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional* | - |
| `GROQ_API_KEY` | Groq API key | Optional* | - |
| `DEEPSEEK_API_KEY` | DeepSeek API key | Optional* | - |
| `REDIS_URL` | Redis connection URL | Yes | `redis://localhost:6379` |
| `BACKEND_PORT` | Backend server port | No | `8000` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | `INFO` |
| `NEXT_PUBLIC_BACKEND_URL` | Backend URL for dashboard/landing | Yes | `http://localhost:8000` |

\* At least one LLM provider API key is required for the system to function.

### Additional Configuration

- **Batch Queue Settings** – Configured in `backend/api/batch_queue.py`:
  - `BATCH_WINDOW_MS`: Maximum wait time before flushing a batch (default: 10ms)
  - `MAX_BATCH_SIZE`: Maximum requests per batch (default: 16)

- **Cache Settings** – Configured in `backend/api/semantic_cache.py`:
  - `SIMILARITY_THRESHOLD`: Minimum similarity for cache hits (default: 0.92)
  - `TTL_SECONDS`: Cache entry time-to-live (default: 604800 = 7 days)

- **Routing Settings** – Configured in `backend/api/routing_engine.py`:
  - Model cost tables and routing rules can be customized per deployment

---

## API Usage

### Main Endpoint

**POST** `/v1/route`

The primary endpoint for routing LLM requests through Cost Melt's optimization pipeline.

### Request Example

**cURL:**

```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Big O notation with examples.",
    "user_id": "demo-user-123",
    "max_output_tokens": 400
  }'
```

**Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/route",
    json={
        "prompt": "Write a SQL query to find users who haven't logged in for 30 days.",
        "user_id": "demo-user-123",
        "max_output_tokens": 400
    }
)

data = response.json()
print(f"Response: {data['response']}")
print(f"Model used: {data['model_used']}")
print(f"Cost saved: ${data['cost']['absolute_savings']:.6f}")
print(f"Savings: {data['cost']['savings_pct']:.1f}%")
```

**Node.js:**

```javascript
const response = await fetch('http://localhost:8000/v1/route', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Explain the difference between REST and GraphQL.',
    user_id: 'demo-user-123',
    max_output_tokens: 400
  })
});

const data = await response.json();
console.log(`Response: ${data.response}`);
console.log(`Model: ${data.model_used}`);
console.log(`Savings: ${data.cost.savings_pct}%`);
```

### Response Format

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

### Response Fields

- **`response`** – The LLM-generated response text
- **`model_used`** – The model selected by the routing engine (e.g., `gpt-4o-mini`, `claude-3-haiku`, `cache`)
- **`complexity`** – Complexity classification (0=simple, 1=medium, 2=complex)
- **`cache_hit`** – Boolean indicating if the response came from semantic cache
- **`tokens_in`** – Number of input tokens (after compression)
- **`tokens_out`** – Number of output tokens
- **`cost`** – Cost breakdown object:
  - `actual_cost` – Actual cost for this request
  - `baseline_cost` – Estimated cost if using GPT-4o baseline
  - `absolute_savings` – Dollar amount saved
  - `savings_pct` – Percentage saved vs. baseline
- **`latency_ms`** – End-to-end request latency in milliseconds

### Request Parameters

- **`prompt`** (required) – The user prompt to process
- **`user_id`** (optional) – User identifier for analytics and logging
- **`metadata`** (optional) – Additional metadata dictionary
- **`max_output_tokens`** (optional) – Maximum output tokens (default: 400)

### How Routing Works

The routing engine automatically selects the optimal model based on:

1. **Prompt complexity** – Analyzed by the Overkill Detector
2. **Model capabilities** – Each model's strengths and limitations
3. **Cost efficiency** – Token costs per model
4. **Provider health** – Real-time availability checks

Simple prompts (Q&A, summaries) are routed to cost-effective models like `gpt-4o-mini` or `llama3-70b-groq`. Complex prompts (code generation, reasoning) are routed to premium models like `gpt-4o` or `claude-3-5-sonnet`.

---

## Dashboard Overview

The Cost Melt Dashboard provides comprehensive analytics and insights into your LLM usage, costs, and optimization performance.

### Access

Once the dashboard is running, access it at:

```
http://localhost:3000
```

### Features

The dashboard includes several pages:

#### Home Dashboard (`/`)

- **Top Metrics Cards** – Total requests, tokens, cost saved, cache hit rate
- **Savings Over Time Chart** – Line chart showing daily savings
- **Model Distribution** – Pie chart of model usage
- **Routing Complexity** – Bar chart of complexity distribution
- **Daily Usage Preview** – Timeseries of requests and costs

#### Usage Page (`/usage`)

- **Model Usage Table** – Detailed breakdown by model with request counts, tokens, and costs
- **Requests per Model Chart** – Bar chart visualization
- **Cost Comparison** – Pie chart showing cost distribution

#### Cache Page (`/cache`)

- **Cache Performance Metrics** – Hits, misses, hit rate
- **Hits vs Misses Chart** – Bar chart comparison
- **Recent Cache Hits Table** – List of recent cached responses

#### Routing Page (`/routing`)

- **Complexity Distribution Table** – Breakdown by complexity level
- **Complexity Bar Chart** – Visual distribution
- **Model Distribution** – Pie chart of routing choices

#### Models Page (`/models`)

- **Model Cost Comparison Table** – Side-by-side cost analysis
- **Summary Cards** – Total models, requests, and costs

#### Daily Page (`/daily`)

- **Full-Width Timeseries Chart** – Requests, tokens, costs, and savings over time
- **Date Range Selector** – Filter by 7, 30, or 90 days
- **Summary Statistics** – Aggregated totals

#### Savings Page (`/savings`)

- **Historical Savings Chart** – Area chart of savings over time
- **Summary Totals** – Total savings, average daily, days tracked
- **Daily Savings Breakdown Table** – Detailed savings by date

### Screenshots

![Cost Melt Dashboard Overview](docs/screenshots/dashboard-overview.png)

*Note: Screenshots will be added to the repository. For now, run the dashboard locally to see the interface.*

---

## Roadmap

Cost Melt is actively developed with the following features planned:

- [ ] **Multi-tenant Organization Support** – Add support for organizations, projects, and team collaboration with role-based access control

- [ ] **Per-User Budgets and Rate Limits** – Implement budget tracking and rate limiting per user or organization to prevent overages

- [ ] **Additional LLM Providers** – Add support for Google Gemini, local models (via Ollama), and other emerging providers

- [ ] **Pluggable Routing Policies** – Allow users to define custom routing rules and policies for model selection

- [ ] **Fine-Tuned Overkill Detector** – Train the complexity classifier on real usage data to improve accuracy

- [ ] **Hosted Version** – Launch a managed, hosted version of Cost Melt with automatic scaling and high availability

- [ ] **SDKs** – Publish official SDKs for Python, Node.js, and Go to simplify integration

- [ ] **Webhook Support** – Add webhook notifications for budget alerts, rate limit warnings, and system events

- [ ] **Advanced Analytics** – Add predictive analytics, cost forecasting, and optimization recommendations

- [ ] **A/B Testing Framework** – Allow users to test different routing strategies and compare performance

---

## Contributing

We welcome contributions from the community! Here's how you can help:

### Opening Issues

If you find a bug or have a feature request, please open an issue on GitHub with:

- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- Environment details (OS, Python/Node versions, etc.)

### Submitting Pull Requests

1. **Fork the repository** and clone your fork
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding style guidelines
4. **Write or update tests** to cover your changes
5. **Run tests** to ensure everything passes:
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend tests
   cd ../dashboard
   npm test
   ```
6. **Commit your changes** with clear, descriptive commit messages
7. **Push to your fork** and open a pull request

### Coding Style

- **Python**: Follow PEP 8, use type hints, and include docstrings
- **TypeScript/React**: Follow Next.js conventions, use TypeScript strictly, and format with Prettier
- **Commits**: Use conventional commit messages (e.g., `feat: add new routing rule`, `fix: resolve cache eviction bug`)

### Testing

All contributions should include tests:

- **Backend**: Use `pytest` for Python tests
- **Frontend**: Use Jest/Vitest for React component tests
- **Integration**: Test API endpoints and component interactions

### Major Features

If you're planning to add a major feature, please open an issue first to discuss the design and implementation approach. This helps ensure the feature aligns with the project's goals and architecture.

---

## License

Cost Melt is open-sourced under the [MIT License](./LICENSE).

---

---

## 👨‍💻 Author

**David Melton** - Senior AI Infrastructure Engineer

- GitHub: [@dmeltonyan](https://github.com/dmeltonyan)
- Project: [Cost Melt](https://github.com/dmeltonyan/costmelt)

**Built with ❤️ for the AI developer community**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
