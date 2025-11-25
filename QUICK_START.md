# Cost Melt - Complete Git Bash Setup Guide

**Step-by-step commands to run in Git Bash. Copy and paste each section.**

---

## Step 1: Navigate to Your Project

```bash
# If you haven't cloned yet, clone the repo
cd ~
git clone https://github.com/dmeltonyan/costmelt.git
cd costmelt

# If you already have it, just navigate
cd ~/costmelt
# OR if it's in a different location
cd /c/Users/DavidM/costmelt
```

---

## Step 2: Set Up Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Git Bash)
source .venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (you'll need to edit this with your keys)
cp .env.example .env

# Edit .env file with your actual keys
# Use: nano .env  OR  notepad .env
# Add your SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, etc.

# Start Redis (in a new terminal or background)
# Option 1: Docker
docker run -d -p 6379:6379 redis:7-alpine

# Option 2: If you have Redis installed
redis-server &

# Start the backend server
uvicorn main:app --reload --port 8000
```

**Keep this terminal open!** The backend is now running.

---

## Step 3: Set Up Database (In Supabase)

1. Go to https://supabase.com and sign in
2. Open your project (or create one)
3. Go to **SQL Editor**
4. Copy and paste the contents of `backend/db/schema.sql`
5. Click **Run**
6. Copy and paste the contents of `backend/db/migrations/001_api_keys.sql`
7. Click **Run**

---

## Step 4: Test Backend (New Git Bash Terminal)

Open a **NEW Git Bash terminal** (keep backend running in the first one):

```bash
# Navigate to project root
cd ~/costmelt
# OR
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

## Step 5: Set Up Dashboard

Open a **NEW Git Bash terminal**:

```bash
# Navigate to project root
cd ~/costmelt
# OR
cd /c/Users/DavidM/costmelt

# Navigate to dashboard
cd dashboard

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# Edit .env.local (should already have correct URL)
# Use: nano .env.local  OR  notepad .env.local
# Should contain: NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Start dashboard
npm run dev
```

**Keep this terminal open!** Dashboard is now running at http://localhost:3000

---

## Step 6: Set Up Landing Page (Optional)

Open a **NEW Git Bash terminal**:

```bash
# Navigate to project root
cd ~/costmelt
# OR
cd /c/Users/DavidM/costmelt

# Navigate to landing
cd landing

# Install dependencies
npm install

# Start landing page
npm run dev
```

Landing page is now running at http://localhost:3001

---

## Step 7: Test Everything

### Test Backend API

```bash
# In a new Git Bash terminal
cd ~/costmelt

# Health check
curl http://localhost:8000/health

# Make a test API call
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain what machine learning is in simple terms",
    "user_id": "test-user-123"
  }'
```

### Test Dashboard

1. Open browser: http://localhost:3000
2. You should see the dashboard
3. Make a few API calls first to generate data, then refresh dashboard

### Test Landing Page

1. Open browser: http://localhost:3001
2. You should see the marketing landing page

---

## Quick Reference: All Commands in Order

```bash
# ============================================
# TERMINAL 1: Backend
# ============================================
cd ~/costmelt
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys (nano .env or notepad .env)
uvicorn main:app --reload --port 8000

# ============================================
# TERMINAL 2: Redis (if not using Docker)
# ============================================
docker run -d -p 6379:6379 redis:7-alpine
# OR if Redis is installed:
redis-server

# ============================================
# TERMINAL 3: Dashboard
# ============================================
cd ~/costmelt
cd dashboard
npm install
cp .env.local.example .env.local
npm run dev

# ============================================
# TERMINAL 4: Landing (Optional)
# ============================================
cd ~/costmelt
cd landing
npm install
npm run dev

# ============================================
# TERMINAL 5: Testing
# ============================================
cd ~/costmelt

# Test health
curl http://localhost:8000/health

# Test API
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "user_id": "test"}'
```

---

## What You Need Before Starting

1. **Supabase Account** (free)
   - Sign up at https://supabase.com
   - Create a new project
   - Get your URL and service key from Settings → API

2. **OpenAI API Key** (or other LLM provider)
   - Sign up at https://platform.openai.com
   - Get API key from API Keys section

3. **Docker** (for Redis)
   - Download from https://www.docker.com/products/docker-desktop
   - OR install Redis directly

---

## Environment Variables to Set

### backend/.env

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
OPENAI_API_KEY=sk-your-openai-key-here
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=info
```

### dashboard/.env.local

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Troubleshooting

### "python: command not found"
```bash
# Try python3 instead
python3 -m venv .venv
python3 -m pip install -r requirements.txt
```

### "npm: command not found"
- Install Node.js from https://nodejs.org
- Restart Git Bash after installation

### "uvicorn: command not found"
```bash
# Make sure virtual environment is activated
source .venv/Scripts/activate
pip install -r requirements.txt
```

### "Connection refused" errors
- Make sure backend is running (Terminal 1)
- Make sure Redis is running
- Check that ports 8000, 3000, 3001 are not in use

### "Module not found" errors
```bash
# Make sure you're in the right directory
cd backend
source .venv/Scripts/activate
pip install -r requirements.txt
```

---

## Stopping Services

Press `Ctrl+C` in each terminal to stop:
- Backend (Terminal 1)
- Dashboard (Terminal 3)
- Landing (Terminal 4)

To stop Redis:
```bash
docker stop $(docker ps -q --filter ancestor=redis:7-alpine)
```

---

## Next Steps

Once everything is running:

1. **Make API calls** to generate data
2. **Check dashboard** at http://localhost:3000
3. **Read documentation**:
   - `docs/LOCAL_TESTING.md` - Detailed testing guide
   - `docs/API.md` - API documentation
   - `docs/SECURITY.md` - Security features

---

**That's it! You should now have everything running locally.**

