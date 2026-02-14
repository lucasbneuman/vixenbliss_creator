# Smart test runner for avatar creation (System 1) and content generation (System 2) tests (Windows)

param(
    [string]$System = "all"  # all, system1, system2, mock, smoke
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[TEST] VixenBliss System 1 & 2 Testing Suite" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $backendDir

switch ($System) {
    "system1" {
        Write-Host "[SYSTEM 1] Avatar Creation Tests" -ForegroundColor Yellow
        Write-Host "[MOCK] Running MOCK tests (fast, no real APIs)..." -ForegroundColor Yellow
        python -m pytest tests/test_avatar_creation_mock.py tests/test_avatar_creation_smoke.py -v --tb=short
        exit $LASTEXITCODE
    }
    
    "system2" {
        Write-Host "[SYSTEM 2] Content Generation Tests" -ForegroundColor Yellow
        Write-Host "[MOCK] Running MOCK tests (fast, no real APIs)..." -ForegroundColor Yellow
        python -m pytest tests/test_content_generation_mock.py -v --tb=short
        Write-Host "[OK] System 2 mock tests passed" -ForegroundColor Green
        Write-Host ""
        
        if ($env:RUN_PRODUCTION_TESTS -eq "true") {
            Write-Host "[SMOKE] Running SMOKE tests (real APIs)..." -ForegroundColor Yellow
            python -m pytest tests/test_content_generation_smoke.py -m smoke -v --tb=short
            Write-Host "[OK] System 2 smoke tests passed" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Skipping System 2 smoke tests. Run with: `$env:RUN_PRODUCTION_TESTS='true'; .\run-tests.ps1 system2" -ForegroundColor Yellow
        }
        exit 0
    }
    
    "mock" {
        Write-Host "[MOCK] Running ALL MOCK tests (fast, no real APIs)..." -ForegroundColor Yellow
        python -m pytest tests/test_avatar_creation_mock.py tests/test_content_generation_mock.py -v --tb=short
        Write-Host "[OK] All mock tests passed" -ForegroundColor Green
        exit $LASTEXITCODE
    }
    
    "smoke" {
        Write-Host "[SMOKE] Running ALL SMOKE tests (real APIs)..." -ForegroundColor Yellow
        if ($env:RUN_PRODUCTION_TESTS -ne "true") {
            Write-Host "[INFO] Set RUN_PRODUCTION_TESTS=true to enable" -ForegroundColor Yellow
            $env:RUN_PRODUCTION_TESTS = "true"
        }
        python -m pytest tests/test_avatar_creation_smoke.py tests/test_content_generation_smoke.py -m smoke -v --tb=short
        Write-Host "[OK] All smoke tests passed" -ForegroundColor Green
        exit $LASTEXITCODE
    }
    
    "all" {
        Write-Host "[ALL] Running COMPLETE test suite (System 1 + System 2)..." -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "[STEP1] System 1 & 2 Mock tests (fast)..." -ForegroundColor Yellow
        python -m pytest tests/test_avatar_creation_mock.py tests/test_content_generation_mock.py -v --tb=short
        if ($LASTEXITCODE -ne 0) { exit 1 }
        Write-Host "[OK] Step 1 passed" -ForegroundColor Green
        Write-Host ""
        
        if ($env:RUN_PRODUCTION_TESTS -eq "true") {
            Write-Host "[STEP2] System 1 & 2 Smoke tests (real APIs)..." -ForegroundColor Yellow
            python -m pytest tests/test_avatar_creation_smoke.py tests/test_content_generation_smoke.py -m smoke -v --tb=short
            if ($LASTEXITCODE -ne 0) { exit 1 }
            Write-Host "[OK] Step 2 passed" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Skipping smoke tests. Run with: `$env:RUN_PRODUCTION_TESTS='true'; .\run-tests.ps1 all" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "[STEP3] Contract compliance..." -ForegroundColor Yellow
        python -m pytest tests/test_api_contracts.py -v --tb=short
        if ($LASTEXITCODE -ne 0) { exit 1 }
        Write-Host "[OK] Step 3 passed" -ForegroundColor Green
    }
    
    "contracts" {
        Write-Host "[CONTRACTS] Running contract compliance tests..." -ForegroundColor Yellow
        python -m pytest tests/test_api_contracts.py -v --tb=short
        exit $LASTEXITCODE
    }
    
    default {
        Write-Host "[ERROR] Unknown test type: $System" -ForegroundColor Red
        Write-Host "Usage: .\run-tests.ps1 [all|system1|system2|mock|smoke|contracts]" -ForegroundColor Red
        Write-Host ""
        Write-Host "  all       - Run complete test suite (mock + smoke + contracts)" -ForegroundColor Gray
        Write-Host "  system1   - Avatar creation tests (System 1)" -ForegroundColor Gray
        Write-Host "  system2   - Content generation tests (System 2)" -ForegroundColor Gray
        Write-Host "  mock      - All mock tests (fast, no APIs)" -ForegroundColor Gray
        Write-Host "  smoke     - All smoke tests (real APIs, requires RUN_PRODUCTION_TESTS=true)" -ForegroundColor Gray
        Write-Host "  contracts - API contract compliance tests only" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Gray
        Write-Host "  .\run-tests.ps1 system2              # Test Content Generation" -ForegroundColor Gray
        Write-Host "  `$env:RUN_PRODUCTION_TESTS='true'; .\run-tests.ps1 all  # Full suite" -ForegroundColor Gray
        exit 1
    }
}
