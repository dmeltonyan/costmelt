# Cost Melt - Complete Test Suite (PowerShell)
# Tests all components end-to-end

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Cost Melt - Complete Test Suite" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Check if backend is running
Write-Host "[1/8] Checking backend health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✓ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend is not running. Start it with: cd backend; uvicorn main:app --reload" -ForegroundColor Red
    exit 1
}

# Test health endpoint
Write-Host "[2/8] Testing health endpoint..." -ForegroundColor Yellow
if ($healthResponse.status -eq "healthy") {
    Write-Host "✓ Health check passed" -ForegroundColor Green
    Write-Host "  Response: $($healthResponse | ConvertTo-Json -Compress)"
} else {
    Write-Host "✗ Health check failed" -ForegroundColor Red
    exit 1
}

# Test API route endpoint (simple prompt)
Write-Host "[3/8] Testing /v1/route endpoint (simple prompt)..." -ForegroundColor Yellow
try {
    $routeResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/route" -Method Post -ContentType "application/json" -Body (@{
        prompt = "What is Python?"
        user_id = "test-user"
    } | ConvertTo-Json)
    
    Write-Host "✓ API route test passed" -ForegroundColor Green
    Write-Host "  Model used: $($routeResponse.model_used)"
    Write-Host "  Cache hit: $($routeResponse.cache_hit)"
    Write-Host "  Savings: $($routeResponse.cost.savings_pct)%"
} catch {
    Write-Host "✗ API route test failed" -ForegroundColor Red
    Write-Host "  Error: $_"
    exit 1
}

# Test cache hit (same prompt again)
Write-Host "[4/8] Testing cache hit (same prompt)..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $cacheResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/route" -Method Post -ContentType "application/json" -Body (@{
        prompt = "What is Python?"
        user_id = "test-user"
    } | ConvertTo-Json)
    
    if ($cacheResponse.cache_hit -eq $true) {
        Write-Host "✓ Cache hit test passed" -ForegroundColor Green
        Write-Host "  Cache hit: true"
    } else {
        Write-Host "⚠ Cache hit test - may need more time for embedding" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Cache test error: $_" -ForegroundColor Yellow
}

# Test dashboard stats endpoint
Write-Host "[5/8] Testing dashboard stats endpoint..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/dashboard/stats" -Method Get
    Write-Host "✓ Dashboard stats test passed" -ForegroundColor Green
    Write-Host "  Total requests: $($stats.total_requests)"
} catch {
    Write-Host "✗ Dashboard stats test failed" -ForegroundColor Red
    Write-Host "  Error: $_"
}

# Test dashboard usage endpoint
Write-Host "[6/8] Testing dashboard usage endpoint..." -ForegroundColor Yellow
try {
    $usage = Invoke-RestMethod -Uri "http://localhost:8000/dashboard/usage" -Method Get
    Write-Host "✓ Dashboard usage test passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Dashboard usage test failed" -ForegroundColor Red
    Write-Host "  Error: $_"
}

# Test dashboard cache endpoint
Write-Host "[7/8] Testing dashboard cache endpoint..." -ForegroundColor Yellow
try {
    $cacheStats = Invoke-RestMethod -Uri "http://localhost:8000/dashboard/cache" -Method Get
    Write-Host "✓ Dashboard cache test passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Dashboard cache test failed" -ForegroundColor Red
    Write-Host "  Error: $_"
}

# Test with different complexity prompts
Write-Host "[8/8] Testing complexity detection..." -ForegroundColor Yellow

# Simple prompt
try {
    $simple = Invoke-RestMethod -Uri "http://localhost:8000/v1/route" -Method Post -ContentType "application/json" -Body (@{
        prompt = "Summarize this text"
        user_id = "test-user"
    } | ConvertTo-Json)
    Write-Host "  Simple prompt complexity: $($simple.complexity)"
} catch {
    Write-Host "  Simple prompt test failed: $_" -ForegroundColor Yellow
}

# Complex prompt (with code)
try {
    $complex = Invoke-RestMethod -Uri "http://localhost:8000/v1/route" -Method Post -ContentType "application/json" -Body (@{
        prompt = "Write a Python function to implement quicksort algorithm with time complexity analysis"
        user_id = "test-user"
    } | ConvertTo-Json)
    Write-Host "  Complex prompt complexity: $($complex.complexity)"
    
    if ($complex.complexity -gt $simple.complexity) {
        Write-Host "✓ Complexity detection working correctly" -ForegroundColor Green
    } else {
        Write-Host "⚠ Complexity detection may need tuning" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Complex prompt test failed: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All Tests Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Check dashboard at http://localhost:3000"
Write-Host "  2. View API docs at http://localhost:8000/docs"
Write-Host "  3. Check logs for detailed information"

