#!/usr/bin/env bash
# Starship Flight 14 Digital Engineering Lab — Unix/macOS Launcher
echo "========================================================"
echo " STARSHIP FLIGHT 14 DIGITAL ENGINEERING LAB SERVER"
echo " Serving WebGL Replay at: http://127.0.0.1:8080/replay.html"
echo " Serving Spatial Dashboard at: http://127.0.0.1:8080/index.html"
echo "========================================================"
python3 -m src.dashboard.server --host 0.0.0.0 --port 8080 --no-export
