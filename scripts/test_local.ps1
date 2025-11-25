# Cost Melt - Quick Local Test Script (PowerShell)
# Tests all components to ensure everything is working

$ErrorActionPreference = "Stop"

Write-Host "🧪 Cost Melt Local Testing" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

$BASE_URL = if ($env:BENCHMARK_BASE_URL) { $env:BENCHMARK_BASE_URL } else { "http://localhost:8000" }

# Test 1: Health Check
Write-Host "1️⃣  Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    Write-Host "✓ Backend is healthy" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "✗ Backend is not responding" -ForegroundColor Red
    Write-Host "   Make sure backend is running: cd backend && uvicorn main:app --reload" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 2: API Route Endpoint
Write-Host "2️⃣  Testing /v1/route Endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        prompt = "What is machine learning?"
        user_id = "test-script"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/v1/route" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✓ API route endpoint working" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ API route endpoint failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 3: Dashboard Backend Endpoints
Write-Host "3️⃣  Testing Dashboard Endpoints..." -ForegroundColor Yellow

$endpoints = @("stats", "usage", "cache", "routing", "daily")

foreach ($endpoint in $endpoints) {
    try {
        $null = Invoke-RestMethod -Uri "$BASE_URL/dashboard/$endpoint" -Method Get
        Write-Host "✓ /dashboard/$endpoint" -ForegroundColor Green
    } catch {
        Write-Host "⚠ /dashboard/$endpoint (may need data first)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 4: Check Services
Write-Host "4️⃣  Checking Services..." -ForegroundColor Yellow
Write-Host "ℹ  Make sure Redis is running:" -ForegroundColor Cyan
Write-Host "   docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Gray
Write-Host "   OR: redis-server" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "==========================" -ForegroundColor Cyan
Write-Host "✅ Basic tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start dashboard: cd dashboard && npm run dev" -ForegroundColor Gray
Write-Host "  2. Open http://localhost:3000" -ForegroundColor Gray
Write-Host "  3. Make more API calls to generate data" -ForegroundColor Gray
Write-Host "  4. Check dashboard for analytics" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed testing, see: docs/LOCAL_TESTING.md" -ForegroundColor Cyan

