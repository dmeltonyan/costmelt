#!/bin/bash

# Cost Melt - Migration Script
# Runs database migrations for Supabase

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running Cost Melt Database Migrations...${NC}"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}Error: backend/.env not found.${NC}"
    echo -e "${YELLOW}Please create backend/.env with your Supabase credentials${NC}"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' backend/.env | xargs)

# Check if SUPABASE_URL is set
if [ -z "$SUPABASE_URL" ]; then
    echo -e "${RED}Error: SUPABASE_URL not set in backend/.env${NC}"
    exit 1
fi

# Method 1: Using Supabase CLI (if available)
if command -v supabase &> /dev/null; then
    echo -e "${GREEN}Using Supabase CLI...${NC}"
    cd backend
    supabase db push
    cd ..
    echo -e "${GREEN}Migrations completed!${NC}"
    exit 0
fi

# Method 2: Using psql (if available)
if command -v psql &> /dev/null; then
    echo -e "${GREEN}Using psql...${NC}"
    
    # Extract connection details from SUPABASE_URL
    # Format: postgresql://postgres:[password]@[host]:[port]/postgres
    if [[ $SUPABASE_URL == postgresql://* ]]; then
        echo -e "${YELLOW}Running schema.sql...${NC}"
        psql "$SUPABASE_URL" < backend/db/schema.sql
        echo -e "${GREEN}Migrations completed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}SUPABASE_URL format not recognized for psql.${NC}"
    fi
fi

# Method 3: Using Python script (if available)
if [ -f "backend/db/migrate.py" ]; then
    echo -e "${GREEN}Using Python migration script...${NC}"
    cd backend
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install -q -r requirements.txt
    python db/migrate.py
    cd ..
    echo -e "${GREEN}Migrations completed!${NC}"
    exit 0
fi

# Method 4: Manual instructions
echo -e "${YELLOW}No migration tool found. Please use one of the following methods:${NC}"
echo -e "\n${GREEN}Method 1: Supabase Dashboard${NC}"
echo -e "1. Open your Supabase project dashboard"
echo -e "2. Navigate to SQL Editor"
echo -e "3. Copy contents of backend/db/schema.sql"
echo -e "4. Paste and execute in SQL Editor"
echo -e "\n${GREEN}Method 2: Install Supabase CLI${NC}"
echo -e "npm install -g supabase"
echo -e "supabase link --project-ref your-project-ref"
echo -e "supabase db push"
echo -e "\n${GREEN}Method 3: Install psql${NC}"
echo -e "psql \$SUPABASE_URL < backend/db/schema.sql"

exit 1

