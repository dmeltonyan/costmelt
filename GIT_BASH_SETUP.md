# Cost Melt - Complete Git Bash Setup Guide

**For directory: `C:\Users\DavidM\costmelt`**

---

## ⚠️ Important: Git Bash Path Format

Git Bash uses **Unix-style paths**, not Windows paths!

- ❌ Wrong: `C:\Users\DavidM\costmelt`
- ✅ Correct: `/c/Users/DavidM/costmelt`

---

## Step 1: Navigate to Project Directory

```bash
# Navigate to your project (Git Bash uses /c/ not C:\)
cd /c/Users/DavidM/costmelt

# Verify you're in the right place
pwd
# Should show: /c/Users/DavidM/costmelt

# List files to confirm
ls
```

---

## Step 2: Set Up Backend

```bash
# Make sure you're in the project root
cd /c/Users/DavidM/costmelt

# Navigate to backend
cd backend

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment (Git Bash)
source .venv/Scripts/activate

# You should see (.venv) in your prompt now
# Example: (venv) NSG03Z8VQ8C1@DESKTOP-6642315 MINGW64 ~/costmelt/backend

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

---

## Step 3: Configure Environment Variables

```bash
# Make sure you're in backend directory
cd /c/Users/DavidM/costmelt/backend

# Copy example env file (if not exists)
cp .env.example .env

# Edit .env file with your keys
# Option 1: Use nano (Git Bash editor)
nano .env

# Option 2: Use notepad (Windows)
notepad .env

# Option 3: Use VS Code
code .env
```

**Required in `.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-key-here
REDIS_URL=redis://localhost:6379
```

---

## Step 4: Set Up Database (Supabase)

1. Go to https://supabase.com
2. Open your project (or create one)
3. Go to **SQL Editor**
4. Copy contents of `backend/db/schema.sql`
5. Paste and click **Run**
6. Copy contents of `backend/db/migrations/001_api_keys.sql`
7. Paste and click **Run**

---

## Step 5: Start Redis

**Option 1: Docker (Recommended)**
```bash
# Start Redis in Docker
docker run -d -p 6379:6379 --name costmelt-redis redis:7-alpine

# Verify it's running
docker ps | grep redis
```

**Option 2: Check if Redis is already running**
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

---

## Step 6: Verify System Setup

```bash
# Make sure you're in project root
cd /c/Users/DavidM/costmelt

# Run initialization check
cd backend
source .venv/Scripts/activate
python ../scripts/init_system.py
```

This will check:
- ✅ Environment variables
- ✅ Dependencies
- ✅ Redis connection
- ✅ Supabase connection
- ✅ OpenAI API key

---

## Step 7: Start Backend Server

**Keep this terminal open!**

```bash
# Navigate to backend
cd /c/Users/DavidM/costmelt/backend

# Activate virtual environment
source .venv/Scripts/activate

# Start the server
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal running!**

---

## Step 8: Test Backend (New Terminal)

Open a **NEW Git Bash terminal**:

```bash
# Navigate to project
cd /c/Users/DavidM/costmelt

# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy","service":"costmelt-backend"}

# Test API endpoint
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'
```

---

## Step 9: Run Complete Test Suite

**In the new terminal:**

```bash
# Navigate to project root
cd /c/Users/DavidM/costmelt

# Make script executable (if needed)
chmod +x scripts/test_everything.sh

# Run test suite
./scripts/test_everything.sh
```

---

## Step 10: Start Dashboard (Optional)

**Open another NEW Git Bash terminal:**

```bash
# Navigate to project
cd /c/Users/DavidM/costmelt

# Go to dashboard
cd dashboard

# Install dependencies (first time only)
npm install

# Create .env.local file
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local

# Start dashboard
npm run dev
```

Dashboard will be at: http://localhost:3000

---

## Complete Command Sequence (Copy-Paste Ready)

```bash
# ============================================
# TERMINAL 1: Backend Setup & Start
# ============================================

# Navigate to project
cd /c/Users/DavidM/costmelt

# Go to backend
cd backend

# Create venv (if needed)
python -m venv .venv

# Activate venv
source .venv/Scripts/activate

# Install dependencies (first time)
pip install -r requirements.txt

# Configure .env (edit with your keys)
cp .env.example .env
nano .env  # or: notepad .env

# Start backend server
uvicorn main:app --reload --port 8000

# ============================================
# TERMINAL 2: Redis (if not using Docker)
# ============================================

# Start Redis with Docker
docker run -d -p 6379:6379 --name costmelt-redis redis:7-alpine

# OR if Redis is installed locally
redis-server

# ============================================
# TERMINAL 3: Testing
# ============================================

# Navigate to project
cd /c/Users/DavidM/costmelt

# Test health
curl http://localhost:8000/health

# Test API
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'

# Run full test suite
./scripts/test_everything.sh

# ============================================
# TERMINAL 4: Dashboard (Optional)
# ============================================

# Navigate to project
cd /c/Users/DavidM/costmelt

# Go to dashboard
cd dashboard

# Install (first time)
npm install

# Create env file
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local

# Start dashboard
npm run dev
```

---

## Common Git Bash Path Issues

### Problem: `cd C:\Users\DavidM\costmelt` doesn't work

**Solution**: Use Unix-style path
```bash
cd /c/Users/DavidM/costmelt
```

### Problem: Backslash issues

**Wrong:**
```bash
cd C:\Users\DavidM\costmelt
```

**Correct:**
```bash
cd /c/Users/DavidM/costmelt
```

### Problem: Spaces in path

If your path has spaces, use quotes:
```bash
cd "/c/Users/David M/costmelt"
```

### Quick Path Conversion

- Windows: `C:\Users\DavidM\costmelt`
- Git Bash: `/c/Users/DavidM/costmelt`

**Rule**: Replace `C:\` with `/c/` and use forward slashes `/`

---

## Quick Reference Commands

```bash
# Navigate to project
cd /c/Users/DavidM/costmelt

# Activate backend venv
cd backend
source .venv/Scripts/activate

# Start backend
uvicorn main:app --reload --port 8000

# Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test", "user_id": "test"}'

# Run tests
./scripts/test_everything.sh
```

---

## Troubleshooting

### Virtual Environment Won't Activate

**Problem**: `source .venv/Scripts/activate` doesn't work

**Solution**: Check you're in the backend directory
```bash
cd /c/Users/DavidM/costmelt/backend
pwd  # Should show: /c/Users/DavidM/costmelt/backend
source .venv/Scripts/activate
```

### Python Not Found

**Problem**: `python: command not found`

**Solution**: Try `python3` instead
```bash
python3 -m venv .venv
python3 -m pip install -r requirements.txt
```

### Redis Connection Failed

**Problem**: Can't connect to Redis

**Solution**: Start Redis first
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Backend Won't Start

**Problem**: Port 8000 already in use

**Solution**: Use different port or kill process
```bash
# Use different port
uvicorn main:app --reload --port 8001

# OR find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Access Points

Once everything is running:

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **Landing Page**: http://localhost:3001

---

## Next Steps

1. ✅ Set up backend (Steps 1-7)
2. ✅ Start backend server (Step 7)
3. ✅ Test everything (Step 8-9)
4. ✅ Start dashboard (Step 10)
5. ✅ View dashboard at http://localhost:3000

---

**Ready to start? Begin with Step 1!**

