#!/bin/bash

# Cost Melt - Development Script
# Runs backend, dashboard, and landing in development mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Cost Melt Development Environment...${NC}"

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found. Copying from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}Please edit backend/.env with your API keys and Supabase credentials${NC}"
fi

if [ ! -f "dashboard/.env.local" ]; then
    echo -e "${YELLOW}Warning: dashboard/.env.local not found. Copying from .env.local.example...${NC}"
    cp dashboard/.env.local.example dashboard/.env.local
fi

if [ ! -f "landing/.env.local" ]; then
    echo -e "${YELLOW}Warning: landing/.env.local not found. Copying from .env.local.example...${NC}"
    cp landing/.env.local.example landing/.env.local
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    kill $BACKEND_PID $DASHBOARD_PID $LANDING_PID $WORKER_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Redis (if not running)
if ! docker ps | grep -q costmelt_redis; then
    echo -e "${GREEN}Starting Redis...${NC}"
    docker run -d --name costmelt_redis -p 6379:6379 redis:7-alpine || true
    sleep 2
fi

# Start Backend
echo -e "${GREEN}Starting Backend (port 8000)...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start Batch Worker
echo -e "${GREEN}Starting Batch Worker...${NC}"
cd backend
source .venv/bin/activate
python -m workers > ../logs/worker.log 2>&1 &
WORKER_PID=$!
cd ..

# Start Dashboard
echo -e "${GREEN}Starting Dashboard (port 3000)...${NC}"
cd dashboard
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dashboard dependencies...${NC}"
    npm install
fi
npm run dev > ../logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..

# Start Landing
echo -e "${GREEN}Starting Landing Page (port 3001)...${NC}"
cd landing
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing landing dependencies...${NC}"
    npm install
fi
PORT=3001 npm run dev > ../logs/landing.log 2>&1 &
LANDING_PID=$!
cd ..

# Create logs directory if it doesn't exist
mkdir -p logs

echo -e "\n${GREEN}All services started!${NC}"
echo -e "${GREEN}Backend:    http://localhost:8000${NC}"
echo -e "${GREEN}Dashboard:  http://localhost:3000${NC}"
echo -e "${GREEN}Landing:    http://localhost:3001${NC}"
echo -e "\n${YELLOW}Logs are in the logs/ directory${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for all processes
wait

