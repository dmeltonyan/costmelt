# 🚀 Cost Melt - Start Here

**Quick start guide to get everything running and tested**

---

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.11+ installed
- ✅ Node.js 18+ installed
- ✅ Docker installed (for Redis)
- ✅ Supabase account (free tier works)
- ✅ OpenAI API key

---

## Step 1: Clone & Setup (5 minutes)

```bash
# Clone the repository (if not already done)
git clone https://github.com/dmeltonyan/costmelt.git
cd costmelt

# Set up backend
cd backend
python -m venv .venv

# Activate virtual environment
# Git Bash:
source .venv/Scripts/activate
# PowerShell:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your keys (see Step 2)
```

---

## Step 2: Configure Environment Variables

Edit `backend/.env` with your credentials:

```env
# Supabase (get from https://supabase.com/dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# OpenAI (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here

# Redis (default works for local)
REDIS_URL=redis://localhost:6379

# Optional: Other LLM providers
ANTHROPIC_API_KEY=your-key
GROQ_API_KEY=your-key
DEEPSEEK_API_KEY=your-key
```

---

## Step 3: Set Up Database

1. Go to https://supabase.com
2. Create a new project (or use existing)
3. Go to **SQL Editor**
4. Copy contents of `backend/db/schema.sql`
5. Paste and click **Run**
6. Copy contents of `backend/db/migrations/001_api_keys.sql`
7. Paste and click **Run**

---

## Step 4: Start Services

### Terminal 1: Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Terminal 2: Backend
```bash
cd backend
source .venv/Scripts/activate  # Git Bash
# OR
.venv\Scripts\activate  # PowerShell

uvicorn main:app --reload --port 8000
```

### Terminal 3: Dashboard (Optional)
```bash
cd dashboard
npm install
npm run dev
```

---

## Step 5: Verify Setup

Run the initialization check:

```bash
cd backend
python ../scripts/init_system.py
```

This will verify:
- ✅ Environment variables
- ✅ Dependencies
- ✅ Redis connection
- ✅ Supabase connection
- ✅ OpenAI API key

---

## Step 6: Run Tests

### Quick Test (Git Bash)
```bash
./scripts/test_everything.sh
```

### Quick Test (PowerShell)
```powershell
.\scripts\test_everything.ps1
```

### Manual Test
```bash
# Health check
curl http://localhost:8000/health

# Test API
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'
```

---

## Step 7: Access Services

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **Landing Page**: http://localhost:3001

---

## What to Test

### ✅ Core Features

1. **API Route Endpoint**
   - Send a prompt → Get optimized response
   - Check `cache_hit`, `model_used`, `cost`, `savings_pct`

2. **Semantic Caching**
   - Send same prompt twice
   - Second call should have `cache_hit: true`
   - Latency should be < 100ms

3. **Prompt Compression**
   - Send long prompt (> 100 tokens)
   - Check `tokens_in` is reduced by 20-50%

4. **Complexity Routing**
   - Simple prompt → Routes to `gpt-4o-mini`
   - Complex prompt → Routes to `gpt-4o` or `claude-3-5-sonnet`

5. **Dashboard**
   - View analytics at http://localhost:3000
   - Check all pages load
   - Verify charts render

---

## Troubleshooting

### Backend Won't Start

**Problem**: `ModuleNotFoundError`
**Solution**: 
```bash
cd backend
pip install -r requirements.txt
```

**Problem**: `Redis connection failed`
**Solution**: 
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Problem**: `Supabase connection failed`
**Solution**: Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### API Returns Errors

**Problem**: `500 Internal Server Error`
**Solution**: Check backend terminal for error logs

**Problem**: `401 Unauthorized`
**Solution**: API key authentication not enabled by default. Check middleware if enabled.

### Dashboard Not Loading

**Problem**: `Cannot connect to backend`
**Solution**: Check `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in `dashboard/.env.local`

---

## Next Steps

Once everything is working:

1. **Read Documentation**
   - `docs/ARCHITECTURE.md` - System architecture
   - `docs/PRD.md` - Product requirements
   - `docs/ROADMAP.md` - Implementation roadmap
   - `TESTING_GUIDE.md` - Complete testing guide

2. **Explore Features**
   - Try different prompt types
   - Check dashboard analytics
   - Test cache hit rates
   - Monitor cost savings

3. **Integrate**
   - Use Python SDK: `pip install costmelt`
   - Use Node SDK: `npm install costmelt`
   - Or use REST API directly

---

## Quick Reference

```bash
# Start everything
docker run -d -p 6379:6379 redis:7-alpine
cd backend && uvicorn main:app --reload
cd dashboard && npm run dev

# Test everything
./scripts/test_everything.sh

# Check system
cd backend && python ../scripts/init_system.py

# View logs
# Backend logs appear in terminal
# Dashboard logs: Check browser console
```

---

**Ready? Start with Step 1!**

For detailed testing, see `TESTING_GUIDE.md`

