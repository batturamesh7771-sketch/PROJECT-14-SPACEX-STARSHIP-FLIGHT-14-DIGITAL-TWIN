# ====================================================================
# Starship Flight 14 Digital Engineering Lab — PowerShell Dashboard Launcher
# ====================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[Launcher] Starship Flight 14 Digital Engineering Lab" -ForegroundColor Cyan
Write-Host "[Launcher] Exporting scenario dataset..." -ForegroundColor Gray
python -m src.phase10 export

Write-Host "[Launcher] Launching default browser at http://127.0.0.1:8080/ ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8080/"

Write-Host "[Launcher] Starting local HTTP server on port 8080 (Ctrl+C to stop)..." -ForegroundColor Yellow
python -m src.dashboard.server --port 8080
