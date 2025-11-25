#!/bin/bash

# Cost Melt - Stop Script
# Stops all services using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stopping Cost Melt services...${NC}"

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

# Stop services
$COMPOSE_CMD down

echo -e "${GREEN}All services stopped.${NC}"

# Optional: Remove volumes (uncomment if you want to clear data)
# echo -e "${YELLOW}Removing volumes...${NC}"
# $COMPOSE_CMD down -v

