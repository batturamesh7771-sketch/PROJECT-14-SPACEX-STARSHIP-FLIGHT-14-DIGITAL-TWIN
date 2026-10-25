@echo off
REM ====================================================================
REM Starship Flight 14 Digital Engineering Lab — Local Dashboard Launcher
REM Starts local Python HTTP server and launches browser at http://127.0.0.1:8080/
REM ====================================================================

title Starship Flight 14 Digital Engineering Dashboard
cd /d "%~dp0"

echo [Launcher] Starship Flight 14 Digital Engineering Lab
echo [Launcher] Refreshing scenario datasets from simulation outputs...
python -m src.phase10 export

echo [Launcher] Starting local server on http://127.0.0.1:8080/ ...
start "" "http://127.0.0.1:8080/"
python -m src.dashboard.server --port 8080
pause
