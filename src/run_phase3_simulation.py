"""
Master Execution Script — Phase 3: Propulsion & 3-DOF Ascent Dynamics Core
==========================================================================
Executes the high-fidelity numerical simulation of Starship Flight 14 powered ascent:
1. Nominal 33-Raptor powered ascent to MECO (T+140s)
2. Injected single-engine anomaly scenario (Engine 17 shutdown at T+95s with throttle compensation)
3. Step-size numerical convergence study (dt=0.05s vs dt=0.01s)
4. Keplerian energy conservation limiting case audit
5. Exports telemetry CSVs and JSON summary reports to output/
"""

import os
import sys
import math
import time
import json
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dynamics.ascent_3dof import (
    simulate_ascent,
    save_telemetry_csv,
    get_initial_state_eci,
    ascent_derivatives
)
from src.propulsion.raptor3_model import BoosterCluster33
from src.environment.atmosphere_1976 import gravity_j2, GM_EARTH
from src.numerics.rk4_solver import rk4_solve

def run_phase3():
    print("=" * 80)
    print("  STARSHIP FLIGHT 14 — PHASE 3: PROPULSION & 3-DOF ASCENT DYNAMICS")
    print("=" * 80)

    out_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)

    nominal_csv_path = os.path.join(out_dir, "flight14_ascent_nominal.csv")
    anomaly_csv_path = os.path.join(out_dir, "flight14_ascent_anomaly.csv")
    summary_json_path = os.path.join(out_dir, "flight14_ascent_summary.json")

    # --------------------------------------------------------------------------
    # 1. NOMINAL ASCENT TRAJECTORY SIMULATION
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Running Nominal Ascent Trajectory Simulation (33 Engines)...")
    t0 = time.time()
    records_nominal, sum_nominal = simulate_ascent(enable_anomaly=False, dt=0.05)
    t_nominal = time.time() - t0

    save_telemetry_csv(records_nominal, nominal_csv_path)
    print(f"  --> Nominal trajectory simulated in {t_nominal:.3f} s ({len(records_nominal)} steps)")
    print(f"  --> Telemetry saved: {nominal_csv_path} ({os.path.getsize(nominal_csv_path):,} bytes)")

    # --------------------------------------------------------------------------
    # 2. INJECTED ENGINE ANOMALY ASCENT SIMULATION
    # --------------------------------------------------------------------------
    print("\n[STEP 2] Running Injected Anomaly Ascent Trajectory Simulation (Engine 17 Out at T+35s)...")
    t0 = time.time()
    records_anomaly, sum_anomaly = simulate_ascent(enable_anomaly=True, dt=0.05)
    t_anomaly = time.time() - t0

    save_telemetry_csv(records_anomaly, anomaly_csv_path)
    print(f"  --> Anomaly trajectory simulated in {t_anomaly:.3f} s ({len(records_anomaly)} steps)")
    print(f"  --> Telemetry saved: {anomaly_csv_path} ({os.path.getsize(anomaly_csv_path):,} bytes)")

    # --------------------------------------------------------------------------
    # 3. NUMERICAL STEP-SIZE CONVERGENCE STUDY (dt=0.05s vs dt=0.01s)
    # --------------------------------------------------------------------------
    print("\n[STEP 3] Running RK4 Step-Size Sensitivity & Convergence Study...")
    records_fine, _ = simulate_ascent(enable_anomaly=False, dt=0.01)

    r_nominal = np.array([records_nominal[-1]["eci_x_m"], records_nominal[-1]["eci_y_m"], records_nominal[-1]["eci_z_m"]], dtype=float)
    r_fine = np.array([records_fine[-1]["eci_x_m"], records_fine[-1]["eci_y_m"], records_fine[-1]["eci_z_m"]], dtype=float)

    delta_r = np.linalg.norm(r_nominal - r_fine)
    r_mag = np.linalg.norm(r_fine)
    convergence_error_pct = (delta_r / r_mag) * 100.0

    print(f"  MECO Position Residual (|dr|): {delta_r:.4f} m across 140s trajectory")
    print(f"  Relative Convergence Residual:  {convergence_error_pct:.6f}% (Tolerance: < 0.01%)")
    assert convergence_error_pct < 0.01, f"Convergence residual {convergence_error_pct}% exceeds 0.01% limit"
    print("  --> RK4 Numerical Convergence: PASSED")

    # --------------------------------------------------------------------------
    # 4. LIMITING CASE: KEPLERIAN ZERO-THRUST CONSERVATION AUDIT
    # --------------------------------------------------------------------------
    print("\n[STEP 4] Executing Analytical Keplerian Energy Conservation Test...")
    # Pure gravity orbital motion derivative function
    def two_body_ode(t, y):
        r_v = y[0:3]
        v_v = y[3:6]
        g_v = gravity_j2(r_v)
        return np.hstack([v_v, g_v])

    # Initial state: circular orbit at 300 km altitude
    r_circ = 6378137.0 + 300000.0
    v_circ = math.sqrt(GM_EARTH / r_circ)
    y0_orbit = np.array([r_circ, 0.0, 0.0, 0.0, v_circ, 0.0])

    t_orb, y_orb = rk4_solve(two_body_ode, (0.0, 1000.0), y0_orbit, 0.1)

    # Compute specific orbital energy E = 0.5 * v^2 - mu / r
    r_mags = np.linalg.norm(y_orb[:, 0:3], axis=1)
    v_mags = np.linalg.norm(y_orb[:, 3:6], axis=1)
    energies = 0.5 * (v_mags ** 2) - (GM_EARTH / r_mags)

    e_initial = energies[0]
    e_final = energies[-1]
    energy_drift = abs(e_final - e_initial) / abs(e_initial)

    print(f"  Initial Specific Energy: {e_initial:,.2f} J/kg")
    print(f"  Final Specific Energy:   {e_final:,.2f} J/kg (after 1,000 s propagation)")
    print(f"  Relative Energy Drift:   {energy_drift:.2e} (Tolerance: < 1.0e-5)")
    assert energy_drift < 1.0e-5, f"Keplerian energy drift {energy_drift} exceeds tolerance"
    print("  --> Analytical Limiting Conservation: PASSED")

    # --------------------------------------------------------------------------
    # 5. COMPILE AND EXPORT FLIGHT 14 ASCENT SUMMARY REPORT
    # --------------------------------------------------------------------------
    master_summary = {
        "mission": "Starship Flight 14 Digital Engineering Laboratory",
        "phase": "Phase 3: Propulsion & 3-DOF Ascent Dynamics Core",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nominal_profile": sum_nominal,
        "anomaly_profile": sum_anomaly,
        "verification_metrics": {
            "rk4_step_sensitivity_pct": round(convergence_error_pct, 6),
            "rk4_position_residual_m": round(delta_r, 4),
            "keplerian_energy_drift": round(energy_drift, 9),
            "status": "ALL_TESTS_VERIFIED"
        }
    }

    with open(summary_json_path, "w", encoding="utf-8") as jf:
        json.dump(master_summary, jf, indent=2)

    print("\n" + "=" * 80)
    print("  STARSHIP FLIGHT 14 ASCENT TRAJECTORY METRICS COMPARISON:")
    print("=" * 80)
    print(f"  Parameter                     | Nominal Baseline       | Anomaly (Eng 17 Out)")
    print("  " + "-" * 76)
    print(f"  Liftoff Mass                  | {sum_nominal['liftoff_total_mass_tonnes']:>10.2f} t          | {sum_anomaly['liftoff_total_mass_tonnes']:>10.2f} t")
    print(f"  Liftoff Thrust                | {sum_nominal['liftoff_thrust_mn']:>10.2f} MN         | {sum_anomaly['liftoff_thrust_mn']:>10.2f} MN")
    print(f"  Liftoff TWR                   | {sum_nominal['liftoff_twr']:>10.3f}            | {sum_anomaly['liftoff_twr']:>10.3f}")
    print(f"  Max Dynamic Pressure (Max-Q)  | {sum_nominal['max_q']['value_kpa']:>10.2f} kPa        | {sum_anomaly['max_q']['value_kpa']:>10.2f} kPa")
    print(f"  Max-Q Timestamp               | {sum_nominal['max_q']['time_s']:>10.2f} s          | {sum_anomaly['max_q']['time_s']:>10.2f} s")
    print(f"  Max-Q Altitude                | {sum_nominal['max_q']['altitude_km']:>10.2f} km         | {sum_anomaly['max_q']['altitude_km']:>10.2f} km")
    print(f"  Max-Q Mach Number             | {sum_nominal['max_q']['mach']:>10.2f} M          | {sum_anomaly['max_q']['mach']:>10.2f} M")
    print(f"  MECO Timestamp                | {sum_nominal['meco']['time_s']:>10.2f} s          | {sum_anomaly['meco']['time_s']:>10.2f} s")
    print(f"  MECO Altitude                 | {sum_nominal['meco']['altitude_km']:>10.2f} km         | {sum_anomaly['meco']['altitude_km']:>10.2f} km")
    print(f"  MECO Downrange                | {sum_nominal['meco']['downrange_km']:>10.2f} km         | {sum_anomaly['meco']['downrange_km']:>10.2f} km")
    print(f"  MECO Inertial Velocity        | {sum_nominal['meco']['inertial_velocity_ms']:>10.1f} m/s        | {sum_anomaly['meco']['inertial_velocity_ms']:>10.1f} m/s")
    print(f"  MECO Relative Velocity        | {sum_nominal['meco']['relative_velocity_ms']:>10.1f} m/s        | {sum_anomaly['meco']['relative_velocity_ms']:>10.1f} m/s")
    print(f"  MECO Stage Acceleration       | {sum_nominal['meco']['final_accel_g']:>10.2f} g          | {sum_anomaly['meco']['final_accel_g']:>10.2f} g")
    print(f"  Remaining Vehicle Mass        | {sum_nominal['meco']['mass_tonnes']:>10.2f} t          | {sum_anomaly['meco']['mass_tonnes']:>10.2f} t")
    print("=" * 80)
    print(f"  Summary saved: {summary_json_path}")
    print("  PHASE 3 ASCENT SIMULATION COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_phase3()
