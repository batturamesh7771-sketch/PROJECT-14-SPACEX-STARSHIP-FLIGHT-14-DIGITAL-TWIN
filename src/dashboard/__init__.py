"""
Phase 10: Digital Engineering Spatial Dashboard (Three.js WebGL)
Starship Flight 14 Digital Engineering Lab.

Provides data adaptation from Phases 1-9 simulation solvers,
local HTTP serving, and interactive WebGL telemetry inspection.
"""

from src.dashboard.adapter import build_scenario_data, export_dashboard_data


def run_server(*args, **kwargs):
    from src.dashboard.server import run_server as _rs
    return _rs(*args, **kwargs)


__all__ = ["build_scenario_data", "export_dashboard_data", "run_server"]
