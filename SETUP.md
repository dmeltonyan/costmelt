# Cost Melt - Local Development Setup Guide

Complete guide for setting up Cost Melt on your local machine for development.

---

## Table of Contents

- [Requirements](#requirements)
- [Directory Guide](#directory-guide)
- [Local Dev Setup Options](#local-dev-setup-options)
  - [Option 1: Docker Compose (Recommended)](#option-1-docker-compose-recommended)
  - [Option 2: Manual Setup](#option-2-manual-setup)
- [Environment Variables](#environment-variables)
- [Running Migrations](#running-migrations)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

---

## Requirements

Before you begin, ensure you have the following installed:

- **Python 3.11+** – For backend development
  - Check version: `python --version` or `python3 --version`
- **Node.js 18+** – For frontend development
  - Check version: `node --version`
- **Docker & Docker Compose** – For containerized development
  - Check Docker: `docker --version`
  - Check Compose: `docker-compose --version`
- **Supabase Project** – Cloud instance or local Supabase CLI
  - Sign up at [supabase.com](https://supabase.com) or install Supabase CLI
- **LLM Provider API Keys** – At least one required:
  - OpenAI: [platform.openai.com](https://platform.openai.com)
  - Anthropic: [console.anthropic.com](https://console.anthropic.com)
  - Groq: [console.groq.com](https://console.groq.com)
  - DeepSeek: [platform.deepseek.com](https://platform.deepseek.com)

---

## Directory Guide

Cost Melt is organized into several directories:

### `/backend`

FastAPI backend service containing:
- **API Gateway** (`api/gateway.py`) – Main orchestration endpoint
- **Routing Engine** – Model selection logic
- **Semantic Cache** – Vector-based caching
- **Prompt Compressor** – Token reduction
- **Batch Queue** – Micro-batching system
- **Workers** (`workers/`) – Background batch processing workers
- **Database Models** (`db/`) – Supabase integration
- **Utilities** (`utils/`) – Cost calculator, token counter, logging

### `/dashboard`

Next.js analytics dashboard providing:
- Real-time cost analytics
- Usage metrics and charts
- Cache performance monitoring
- Routing breakdowns
- Model comparison tables
- Daily timeseries visualizations

### `/landing`

Next.js marketing site with:
- Hero section and features
- Pricing tiers
- Testimonials
- FAQ and legal pages

### `/scripts`

Helper scripts for development:
- `dev.sh` – Run all services in development mode
- `start.sh` – Start Docker Compose stack
- `stop.sh` – Stop Docker Compose stack
- `migrate.sh` – Run database migrations

---

## Local Dev Setup Options

### Option 1: Docker Compose (Recommended)

The easiest way to get everything running is with Docker Compose.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/costmelt.git
cd costmelt
```

#### Step 2: Configure Environment Variables

Copy the example environment files and fill in your values:

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys and Supabase credentials

# Dashboard
cp dashboard/.env.local.example dashboard/.env.local
# Edit dashboard/.env.local if needed

# Landing (optional)
cp landing/.env.local.example landing/.env.local
```

#### Step 3: Run Database Migrations

See [Running Migrations](#running-migrations) section below.

#### Step 4: Start All Services

```bash
# Using helper script
./scripts/start.sh

# Or directly with docker-compose
docker-compose up --build
```

This will start:
- **Backend** on `http://localhost:8000`
- **Dashboard** on `http://localhost:3000`
- **Landing** on `http://localhost:3001`
- **Redis** on `localhost:6379`
- **Batch Worker** (background process)

#### Step 5: Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3000

# Check landing
curl http://localhost:3001
```

### Option 2: Manual Setup

For development without Docker, you can run services manually.

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations (see Running Migrations section)

# Start backend
uvicorn main:app --reload --port 8000
```

#### Dashboard Setup

```bash
cd dashboard

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local if needed

# Start dashboard
npm run dev
```

#### Landing Setup

```bash
cd landing

# Install dependencies
npm install

# Start landing page
npm run dev
```

#### Redis Setup

```bash
# Using Docker (easiest)
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt-get install redis-server && sudo systemctl start redis
```

#### Batch Worker Setup

In a separate terminal:

```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m workers
```

---

## Environment Variables

### Backend Environment Variables

Create `backend/.env`:

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
REDIS_URL=redis://localhost:6379/0

# Backend Configuration
LOG_LEVEL=info
BACKEND_PORT=8000
```

### Dashboard Environment Variables

Create `dashboard/.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Landing Environment Variables

Create `landing/.env.local` (optional, no required variables):

```env
# No required environment variables for landing page
# Add here if email subscription or other features are added
```

---

## Running Migrations

### Method 1: Using Supabase Dashboard

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `backend/db/schema.sql`
4. Paste and execute in the SQL Editor

### Method 2: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref your-project-ref

# Push schema
supabase db push
```

### Method 3: Using Migration Script

```bash
# Run migration script
./scripts/migrate.sh

# Or manually with psql
psql $SUPABASE_URL < backend/db/schema.sql
```

### Method 4: Using Python Script

```bash
cd backend
python db/migrate.py
```

---

## Common Commands

### Development Scripts

```bash
# Run all services in development mode (manual setup)
./scripts/dev.sh

# Start Docker Compose stack
./scripts/start.sh

# Stop Docker Compose stack
./scripts/stop.sh

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f dashboard
```

### Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Start with rebuild
docker-compose up --build -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart a specific service
docker-compose restart backend

# View service status
docker-compose ps

# Execute command in container
docker-compose exec backend python -m pytest
```

### Backend Commands

```bash
# Run tests
cd backend
pytest

# Run specific test file
pytest tests/test_gateway.py

# Run with coverage
pytest --cov=api --cov=utils

# Format code
black .
isort .

# Type checking
mypy .
```

### Frontend Commands

```bash
# Dashboard
cd dashboard
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
npm test             # Run tests
npm run lint         # Lint code

# Landing
cd landing
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
```

---

## Troubleshooting

### Port Conflicts

**Problem:** Services fail to start because ports are already in use.

**Solution:**
```bash
# Check what's using the port
# macOS/Linux
lsof -i :8000
lsof -i :3000
lsof -i :3001
lsof -i :6379

# Windows
netstat -ano | findstr :8000

# Kill the process or change ports in docker-compose.yml
```

### Missing .env Files

**Problem:** Services fail with "environment variable not set" errors.

**Solution:**
```bash
# Ensure all .env files exist
ls -la backend/.env
ls -la dashboard/.env.local
ls -la landing/.env.local

# Copy from examples if missing
cp backend/.env.example backend/.env
cp dashboard/.env.local.example dashboard/.env.local
cp landing/.env.local.example landing/.env.local

# Fill in required values
```

### Redis Connection Errors

**Problem:** Backend cannot connect to Redis.

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check REDIS_URL in backend/.env
# Should be: redis://redis:6379/0 (Docker) or redis://localhost:6379/0 (manual)

# Restart Redis
docker-compose restart redis
```

### Supabase Authentication Errors

**Problem:** "Invalid API key" or "Authentication failed" errors.

**Solution:**
```bash
# Verify SUPABASE_URL format
# Should be: https://xxxxx.supabase.co (no trailing slash)

# Verify SUPABASE_SERVICE_KEY
# Should be the service_role key, not anon key
# Get it from: Supabase Dashboard > Settings > API > service_role key

# Test connection
curl -H "apikey: $SUPABASE_SERVICE_KEY" $SUPABASE_URL/rest/v1/
```

### Node Version Mismatch

**Problem:** `npm install` fails or Next.js errors about Node version.

**Solution:**
```bash
# Check Node version
node --version
# Should be 18.x or higher

# Use nvm to switch versions (recommended)
nvm install 18
nvm use 18

# Or update Node.js from nodejs.org
```

### CORS Issues

**Problem:** Dashboard cannot connect to backend API.

**Solution:**
```bash
# Check NEXT_PUBLIC_BACKEND_URL in dashboard/.env.local
# Should match backend URL: http://localhost:8000

# Check backend CORS settings in backend/main.py
# Should allow localhost:3000

# Clear browser cache and hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
```

### Backend Cannot Find Workers

**Problem:** Batch queue doesn't process requests.

**Solution:**
```bash
# Check batch-worker service is running
docker-compose ps batch-worker

# Check worker logs
docker-compose logs batch-worker

# Verify Redis connection from worker
docker-compose exec batch-worker python -c "import redis; r=redis.from_url('redis://redis:6379'); print(r.ping())"

# Restart worker
docker-compose restart batch-worker
```

### Database Connection Errors

**Problem:** Backend cannot connect to Supabase.

**Solution:**
```bash
# Verify Supabase URL and key
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Test connection
curl -H "apikey: $SUPABASE_SERVICE_KEY" \
     -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
     "$SUPABASE_URL/rest/v1/"

# Check if tables exist
# Run migrations (see Running Migrations section)

# Verify network connectivity
ping your-project.supabase.co
```

### Docker Build Failures

**Problem:** `docker-compose build` fails.

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test ./backend

# Verify Docker has enough resources
# Docker Desktop > Settings > Resources
```

### Module Import Errors

**Problem:** Python imports fail in backend.

**Solution:**
```bash
# Ensure you're in the backend directory
cd backend

# Verify virtual environment is activated
which python  # Should show .venv path

# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Next Steps

Once everything is running:

1. **Test the API:**
   ```bash
   curl -X POST http://localhost:8000/v1/route \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, world!"}'
   ```

2. **Access the Dashboard:**
   Open `http://localhost:3000` in your browser

3. **View the Landing Page:**
   Open `http://localhost:3001` in your browser

4. **Read the API Docs:**
   Visit `http://localhost:8000/docs` for interactive API documentation

5. **Check Logs:**
   ```bash
   docker-compose logs -f
   ```

---

## Getting Help

If you encounter issues not covered here:

1. Check the [README.md](./README.md) for general information
2. Review service logs: `docker-compose logs -f [service-name]`
3. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, versions)
   - Relevant log output

---

**Happy coding! 🚀**

