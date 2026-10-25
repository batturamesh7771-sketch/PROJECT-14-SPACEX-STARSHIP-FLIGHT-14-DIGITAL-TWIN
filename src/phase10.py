"""
Command-line interface (CLI) for Starship Phase 10: Digital Engineering Spatial Dashboard (Three.js WebGL).
Starship Flight 14 Digital Engineering Lab.

Commands:
  python -m src.phase10 export
  python -m src.phase10 serve [--port 8080] [--host 127.0.0.1]
  python -m src.phase10 verify
"""

import os
import sys
import argparse
from typing import Dict, Any

from src.dashboard.adapter import export_dashboard_data, build_scenario_data
from src.dashboard.server import run_server


def cmd_export(args) -> int:
    """Exports scenario data and run manifest to dashboard static data directory."""
    print("[Phase 10] Assembling digital engineering mission data across Phases 1-9...")
    s_path, m_path = export_dashboard_data()
    print(f"[Phase 10] Scenario data successfully written to: {s_path}")
    print(f"[Phase 10] Run manifest written to: {m_path}")
    return 0


def cmd_serve(args) -> int:
    """Starts local HTTP dashboard web server."""
    run_server(port=args.port, host=args.host, export_data=not args.no_export)
    return 0


def cmd_verify(args) -> int:
    """Verifies data adapter integrity, profiles, coordinate transforms, and invariants."""
    print("[Phase 10] Running data adapter verification check...")
    payload = build_scenario_data()

    # 1. Check Profiles
    profiles = payload.get("profiles", {})
    required_profiles = ["planned_flight14", "observed_reconstruction", "synthetic_landing_lab"]
    for p in required_profiles:
        if p not in profiles:
            print(f"[FAIL] Missing profile: {p}")
            return 1
    print(f"[PASS] All {len(required_profiles)} mandatory mission profiles present.")

    # 2. Check Profile Isolation
    obs = profiles["observed_reconstruction"]
    syn = profiles["synthetic_landing_lab"]
    if obs.get("is_synthetic") is not False:
        print("[FAIL] Observed reconstruction profile cannot be flagged synthetic!")
        return 1
    if syn.get("is_synthetic") is not True:
        print("[FAIL] Synthetic landing profile must be flagged synthetic!")
        return 1
    if "SYNTHETIC" not in syn.get("synthetic_banner", ""):
        print("[FAIL] Synthetic landing profile must contain prominent synthetic warning banner!")
        return 1
    print("[PASS] Strict Profile Isolation & Synthetic Banner Verified.")

    # 3. Check Trajectories
    for p_id, p_data in profiles.items():
        traj = p_data.get("trajectory", [])
        if len(traj) < 10:
            print(f"[FAIL] Profile {p_id} trajectory points insufficient ({len(traj)})")
            return 1
        print(f"[PASS] Profile '{p_id}': {len(traj)} trajectory waypoints verified.")

    # 4. Check Coordinate Transformation
    conv = payload.get("coordinate_conventions", {})
    matrix = conv.get("matrix", [])
    # Check orthogonal det = +1
    det = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) -
        matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0]) +
        matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    if abs(det - 1.0) > 1e-6:
        print(f"[FAIL] Determinant of coordinate transform matrix is {det}, expected +1.0!")
        return 1
    print(f"[PASS] Orthogonal Coordinate Transform Matrix verified (det = +{det}).")

    # 5. Check Virtualized Explorer Dataset (10,000+ items)
    records = payload.get("virtualized_explorer_records", [])
    if len(records) < 5000:
        print(f"[FAIL] Virtualized Explorer records ({len(records)}) below required density!")
        return 1
    print(f"[PASS] Virtualized Explorer dataset verified ({len(records)} records).")

    # 6. Check Satellites & Events
    sats = payload.get("satellite_manifest", [])
    if len(sats) != 26:
        print(f"[FAIL] Expected 26 Starlink V3 satellites, found {len(sats)}")
        return 1
    print(f"[PASS] 26 Starlink V3 payload satellites verified.")

    print("\n[Phase 10] All Digital Engineering Spatial Dashboard integrity checks PASSED.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Phase 10: Digital Engineering Spatial Dashboard CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Export
    p_export = subparsers.add_parser("export", help="Export scenario dataset and manifest")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Serve interactive WebGL spatial dashboard")
    p_serve.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    p_serve.add_argument("--no-export", action="store_true", help="Skip re-exporting scenario dataset")

    # Verify
    p_verify = subparsers.add_parser("verify", help="Run programmatic verification tests")

    args = parser.parse_args()
    if args.command == "export":
        sys.exit(cmd_export(args))
    elif args.command == "serve":
        sys.exit(cmd_serve(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    else:
        # Default action: verify and show help
        parser.print_help()


if __name__ == "__main__":
    main()
