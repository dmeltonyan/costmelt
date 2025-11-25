# Cost Melt Bootstrap Script (PowerShell)

Write-Host "🚀 Cost Melt Bootstrap Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check for .env file
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "✅ Created .env file. Please edit it with your API keys." -ForegroundColor Green
    } else {
        Write-Host "❌ .env.example not found. Please create .env manually." -ForegroundColor Red
        exit 1
    }
}

# Backend setup
Write-Host ""
Write-Host "📦 Setting up backend..." -ForegroundColor Cyan
Set-Location backend
if (-not (Test-Path venv)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

Write-Host "Installing Python dependencies..."
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..

# Dashboard setup
Write-Host ""
Write-Host "📦 Setting up dashboard..." -ForegroundColor Cyan
Set-Location dashboard
if (-not (Test-Path node_modules)) {
    Write-Host "Installing Node.js dependencies..."
    npm install
}
Set-Location ..

# Landing setup
Write-Host ""
Write-Host "📦 Setting up landing page..." -ForegroundColor Cyan
Set-Location landing
if (-not (Test-Path node_modules)) {
    Write-Host "Installing Node.js dependencies..."
    npm install
}
Set-Location ..

Write-Host ""
Write-Host "✅ Bootstrap complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit .env file with your API keys"
Write-Host "2. Set up Supabase database (run backend/db/schema.sql)"
Write-Host "3. Start services with: docker-compose up"
Write-Host "   Or run locally:"
Write-Host "   - Backend: cd backend && .\venv\Scripts\Activate.ps1 && uvicorn main:app --reload"
Write-Host "   - Dashboard: cd dashboard && npm run dev"
Write-Host "   - Landing: cd landing && npm run dev"

