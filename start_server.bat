@echo off
title Starship Flight 14 Digital Lab Server
cd /d "%~dp0"
echo ========================================================
echo  STARSHIP FLIGHT 14 DIGITAL ENGINEERING LAB SERVER
echo  Serving WebGL Replay at: http://127.0.0.1:8080/replay.html
echo  Serving Spatial Dashboard at: http://127.0.0.1:8080/index.html
echo ========================================================
python -m src.dashboard.server --host 0.0.0.0 --port 8080 --no-export
pause
