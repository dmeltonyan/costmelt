#!/bin/bash
# Cost Melt Bootstrap Script

set -e

echo "🚀 Cost Melt Bootstrap Script"
echo "================================"

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your API keys."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Dashboard setup
echo ""
echo "📦 Setting up dashboard..."
cd dashboard
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi
cd ..

# Landing setup
echo ""
echo "📦 Setting up landing page..."
cd landing
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi
cd ..

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Set up Supabase database (run backend/db/schema.sql)"
echo "3. Start services with: docker-compose up"
echo "   Or run locally:"
echo "   - Backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "   - Dashboard: cd dashboard && npm run dev"
echo "   - Landing: cd landing && npm run dev"

