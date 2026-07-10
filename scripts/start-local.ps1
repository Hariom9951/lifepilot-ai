# ==============================================================================
# LifePilot AI - Local Start Script
# Runs backend and frontend development servers.
# ==============================================================================

Write-Host "=========================================" -ForegroundColor Green
Write-Host "   Starting LifePilot AI Development     " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Determine working directory context
$RootPath = Resolve-Path ".."
if ($PWD -like "*scripts*") {
    $RootPath = Resolve-Path ".."
} else {
    $RootPath = Resolve-Path "."
}

# 1. Start Backend in a separate window
$VenvPath = Join-Path $RootPath "venv\Scripts\python.exe"
if (Test-Path $VenvPath) {
    Write-Host "[Backend] Launching FastAPI server (Port 8000)..." -ForegroundColor Yellow
    $BackendCmd = "cd backend; ..\venv\Scripts\poetry run uvicorn app.main:app --reload --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd
} else {
    Write-Host "[Backend] Error: Local virtualenv not found at root. Skip automatic launch." -ForegroundColor Red
}

# 2. Start Frontend in the active console
Write-Host "[Frontend] Launching Next.js server (Port 3000)..." -ForegroundColor Yellow
Set-Location (Join-Path $RootPath "frontend")
npm run dev
