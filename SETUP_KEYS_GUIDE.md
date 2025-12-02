# Cost Melt - Complete API Keys & Setup Guide

**Step-by-step instructions to get all keys and set up Cost Melt**

---

## Prerequisites

✅ You've already installed requirements:
```bash
cd /c/Users/DavidM/costmelt/backend
source .venv/Scripts/activate
pip install -r requirements.txt
```

Now let's get your API keys and configure everything!

---

## Step 1: Get Supabase Credentials (5 minutes)

### 1.1 Create Supabase Account

1. Go to **https://supabase.com**
2. Click **"Start your project"** or **"Sign Up"**
3. Sign up with GitHub, Google, or email (free tier works!)

### 1.2 Create a New Project

1. Click **"New Project"**
2. Fill in:
   - **Name**: `costmelt` (or any name)
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is fine
3. Click **"Create new project"**
4. Wait 2-3 minutes for project to initialize

### 1.3 Get Your Supabase Credentials

1. Once project is ready, go to **Settings** (gear icon in left sidebar)
2. Click **"API"** in the settings menu
3. You'll see two important values:

   **a) Project URL:**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```
   Copy this - this is your `SUPABASE_URL`

   **b) Service Role Key (secret):**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   ⚠️ **Important**: Use the **"service_role"** key (not the anon key)
   - It's labeled as "secret" and "service_role"
   - Copy this - this is your `SUPABASE_SERVICE_KEY`

### 1.4 Set Up Database Schema

1. In Supabase dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"New query"**
3. Open `backend/db/schema.sql` in your editor
4. Copy **ALL** the contents
5. Paste into Supabase SQL Editor
6. Click **"Run"** (or press F5)
7. You should see: "Success. No rows returned"

8. Now open `backend/db/migrations/001_api_keys.sql`
9. Copy **ALL** the contents
10. Paste into Supabase SQL Editor
11. Click **"Run"**
12. You should see: "Success. No rows returned"

✅ **Database is now set up!**

---

## Step 2: Get OpenAI API Key (2 minutes)

### 2.1 Create OpenAI Account

1. Go to **https://platform.openai.com**
2. Click **"Sign Up"** or **"Log In"**
3. Sign up/login with email or Google

### 2.2 Get API Key

1. Once logged in, click your **profile icon** (top right)
2. Click **"View API keys"**
3. Click **"Create new secret key"**
4. Give it a name: `costmelt-dev`
5. Click **"Create secret key"**
6. **⚠️ IMPORTANT**: Copy the key immediately! It looks like:
   ```
   sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   You won't be able to see it again!

7. Save it somewhere safe (password manager, notes, etc.)

✅ **OpenAI key obtained!**

---

## Step 3: Configure Environment Variables (2 minutes)

### 3.1 Create .env File

```bash
# Make sure you're in backend directory
cd /c/Users/DavidM/costmelt/backend

# Copy example file
cp .env.example .env
```

### 3.2 Edit .env File

**Option 1: Using Notepad (Easiest)**
```bash
notepad .env
```

**Option 2: Using Nano (Git Bash editor)**
```bash
nano .env
```
- Press `Ctrl+X` to exit
- Press `Y` to save
- Press `Enter` to confirm

**Option 3: Using VS Code**
```bash
code .env
```

### 3.3 Fill In Your Keys

Replace the placeholder values with your actual keys:

```env
# Supabase (from Step 1.3)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI (from Step 2.2)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Redis (default - no changes needed)
REDIS_URL=redis://localhost:6379

# Optional: Other LLM providers (skip for now)
# ANTHROPIC_API_KEY=
# GROQ_API_KEY=
# DEEPSEEK_API_KEY=

# Logging
LOG_LEVEL=info
```

**Save the file!**

---

## Step 4: Start Redis (1 minute)

### Option 1: Using Docker (Recommended)

```bash
# Start Redis container
docker run -d -p 6379:6379 --name costmelt-redis redis:7-alpine

# Verify it's running
docker ps | grep redis
```

You should see the Redis container running.

### Option 2: Verify Redis is Already Running

```bash
# Test Redis connection
redis-cli ping
```

If you see `PONG`, Redis is already running!

---

## Step 5: Verify System Setup (1 minute)

```bash
# Make sure you're in project root
cd /c/Users/DavidM/costmelt

# Go to backend and activate venv
cd backend
source .venv/Scripts/activate

# Run initialization check
python ../scripts/init_system.py
```

This will verify:
- ✅ Environment variables are set
- ✅ Dependencies installed
- ✅ Redis connection works
- ✅ Supabase connection works
- ✅ OpenAI API key is valid

If all checks pass, you're ready! 🎉

---

## Step 6: Start Backend Server

**Open a NEW Git Bash terminal** (keep this one running):

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

**✅ Backend is running! Keep this terminal open.**

---

## Step 7: Test Backend (New Terminal)

**Open another NEW Git Bash terminal:**

```bash
# Navigate to project
cd /c/Users/DavidM/costmelt

# Test health endpoint
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"healthy","service":"costmelt-backend"}
```

**Test API endpoint:**
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "user_id": "test-user"}'
```

**Expected response:**
```json
{
  "response": "Python is a high-level programming language...",
  "model_used": "gpt-4o-mini",
  "complexity": 0,
  "cache_hit": false,
  "tokens_in": 5,
  "tokens_out": 50,
  "cost": {
    "actual_cost": 0.00003,
    "baseline_cost": 0.00028,
    "absolute_savings": 0.00025,
    "savings_pct": 89.29
  },
  "latency_ms": 1200
}
```

✅ **API is working!**

---

## Step 8: Run Complete Test Suite

**In the same terminal:**

```bash
# Make sure you're in project root
cd /c/Users/DavidM/costmelt

# Make script executable
chmod +x scripts/test_everything.sh

# Run test suite
./scripts/test_everything.sh
```

This will test:
- ✅ Health endpoint
- ✅ API route endpoint
- ✅ Cache functionality
- ✅ Dashboard endpoints
- ✅ Complexity detection

**Expected output:**
```
========================================
Cost Melt - Complete Test Suite
========================================

[1/8] Checking backend health...
✓ Backend is running
[2/8] Testing health endpoint...
✓ Health check passed
[3/8] Testing /v1/route endpoint...
✓ API route test passed
...
========================================
All Tests Completed!
========================================
```

---

## Step 9: Start Dashboard (Optional)

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

**Dashboard will be at:** http://localhost:3000

Open in browser to see analytics!

---

## Quick Reference: All Your Keys

Save these somewhere safe:

### Supabase
- **URL**: `https://xxxxxxxxxxxxx.supabase.co`
- **Service Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### OpenAI
- **API Key**: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## Troubleshooting

### Supabase Connection Failed

**Problem**: Can't connect to Supabase

**Check:**
1. Is `SUPABASE_URL` correct? (should start with `https://`)
2. Is `SUPABASE_SERVICE_KEY` the **service_role** key (not anon key)?
3. Did you run the SQL schema migrations?

**Fix:**
```bash
# Check .env file
cat backend/.env | grep SUPABASE

# Re-run database setup in Supabase SQL Editor
```

### OpenAI API Key Invalid

**Problem**: OpenAI API key not working

**Check:**
1. Is the key copied correctly? (no extra spaces)
2. Does it start with `sk-`?
3. Do you have credits in your OpenAI account?

**Fix:**
```bash
# Test key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY_HERE"
```

### Redis Connection Failed

**Problem**: Can't connect to Redis

**Fix:**
```bash
# Start Redis
docker run -d -p 6379:6379 --name costmelt-redis redis:7-alpine

# Verify
docker ps | grep redis
```

### Backend Won't Start

**Problem**: Port 8000 already in use

**Fix:**
```bash
# Use different port
uvicorn main:app --reload --port 8001

# OR find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Summary Checklist

- [ ] ✅ Created Supabase account
- [ ] ✅ Created Supabase project
- [ ] ✅ Got Supabase URL and Service Key
- [ ] ✅ Ran database schema migrations
- [ ] ✅ Created OpenAI account
- [ ] ✅ Got OpenAI API key
- [ ] ✅ Created `.env` file with all keys
- [ ] ✅ Started Redis
- [ ] ✅ Verified system setup
- [ ] ✅ Started backend server
- [ ] ✅ Tested API endpoints
- [ ] ✅ Ran test suite
- [ ] ✅ Started dashboard (optional)

---

## Next Steps

Once everything is working:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **View Dashboard**: Visit http://localhost:3000
3. **Read Documentation**: Check `docs/` folder
4. **Make API Calls**: Use the Python or Node SDKs

---

**🎉 You're all set! Cost Melt is ready to use!**

