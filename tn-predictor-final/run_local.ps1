# Local Deployment Script for TN Election Predictor 2026
# This script starts the final production build using the FastAPI backend.

Write-Host "--- TN Election Predictor 2026: Local Excellence Build ---" -ForegroundColor Cyan

# 1. Check if dist exists
if (-not (Test-Path "dist")) {
    Write-Host "Frontend build not found. Running npm run build..." -ForegroundColor Yellow
    npm run build
}

# 2. Check backend dependencies without forcing network installs
Write-Host "Checking backend dependencies..." -ForegroundColor Gray
$dependencyCheck = @'
import importlib.util, sys
required = ["fastapi", "uvicorn", "pydantic", "requests"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print("MISSING:" + ",".join(missing))
    raise SystemExit(1)
print("OK")
'@

$dependencyCheck | python -
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend dependencies are missing in this environment." -ForegroundColor Red
    Write-Host "Run: python -m pip install -r backend/requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 3. Start the server
Write-Host "Starting production server on http://localhost:7860" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
$env:PYTHONPATH = ".;$env:PYTHONPATH"
python -m uvicorn backend.app_v2:app --host 0.0.0.0 --port 7860
