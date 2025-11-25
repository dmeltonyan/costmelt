#!/bin/bash

# Cost Melt - Start Script
# Starts all services using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Cost Melt with Docker Compose...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: docker-compose is not installed.${NC}"
        exit 1
    else
        COMPOSE_CMD="docker compose"
    fi
else
    COMPOSE_CMD="docker-compose"
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found. Copying from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}Please edit backend/.env with your API keys and Supabase credentials${NC}"
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
    read
fi

if [ ! -f "dashboard/.env.local" ]; then
    echo -e "${YELLOW}Warning: dashboard/.env.local not found. Copying from .env.local.example...${NC}"
    cp dashboard/.env.local.example dashboard/.env.local
fi

if [ ! -f "landing/.env.local" ]; then
    echo -e "${YELLOW}Warning: landing/.env.local not found. Copying from .env.local.example...${NC}"
    cp landing/.env.local.example landing/.env.local
fi

# Build and start services
echo -e "${GREEN}Building and starting services...${NC}"
$COMPOSE_CMD up --build -d

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 5

# Check service status
echo -e "\n${GREEN}Service Status:${NC}"
$COMPOSE_CMD ps

echo -e "\n${GREEN}Cost Melt is running!${NC}"
echo -e "${GREEN}Backend:    http://localhost:8000${NC}"
echo -e "${GREEN}Dashboard:  http://localhost:3000${NC}"
echo -e "${GREEN}Landing:    http://localhost:3001${NC}"
echo -e "${GREEN}API Docs:   http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}View logs: docker-compose logs -f${NC}"
echo -e "${YELLOW}Stop:       ./scripts/stop.sh${NC}\n"

