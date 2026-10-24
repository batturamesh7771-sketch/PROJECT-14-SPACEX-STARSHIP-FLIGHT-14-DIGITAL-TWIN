"""
Master Execution Script — Phase 4: Staging Dynamics & Dual-Vehicle Trajectory
=============================================================================
Orchestrates and integrates the dual-vehicle flight dynamics following booster MECO:
1. Dual-Vehicle Hot-Staging Separation Dynamics (T+140s to T+150s)
2. Super Heavy Booster Return, Boostback Burn & Gulf of Mexico Splashdown (T+142s to T+420s)
3. Starship Stage 2 Powered Ascent to SECO & Orbital Insertion (T+142s to T+525s)
4. Keplerian orbital elements calculation and cross-verification
5. Exports telemetry CSVs and comprehensive JSON reports to output/
"""

import os
import sys
import math
import time
import json
import csv
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dynamics.ascent_3dof import simulate_ascent, save_telemetry_csv
from src.dynamics.staging_separation import simulate_hot_staging_separation
from src.dynamics.booster_recovery import simulate_booster_return
from src.dynamics.starship_ascent_to_orbit import simulate_starship_ascent

def run_phase4():
    print("=" * 80)
    print("  STARSHIP FLIGHT 14 — PHASE 4: STAGING DYNAMICS & DUAL-VEHICLE TRAJECTORY")
    print("=" * 80)

    out_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)

    staging_csv = os.path.join(out_dir, "flight14_staging_relative_motion.csv")
    booster_csv = os.path.join(out_dir, "flight14_booster_return.csv")
    ship_csv = os.path.join(out_dir, "flight14_starship_upper_ascent.csv")
    summary_json = os.path.join(out_dir, "flight14_phase4_summary.json")

    # Step 1: Obtain State at T=142s from Ascent simulation
    print("\n[STEP 1] Initializing Ascent State at Hot-Staging Trigger (T+142s)...")
    # Read the nominal ascent CSV or simulate quickly
    nom_csv_path = os.path.join(out_dir, "flight14_ascent_nominal.csv")
    if os.path.exists(nom_csv_path):
        with open(nom_csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            row_140 = rows[-1]
            state_t142 = np.array([
                float(row_140["eci_x_m"]),
                float(row_140["eci_y_m"]),
                float(row_140["eci_z_m"]),
                float(row_140["eci_vx_ms"]),
                float(row_140["eci_vy_ms"]),
                float(row_140["eci_vz_ms"]),
                float(row_140["mass_tonnes"]) * 1000.0
            ], dtype=np.float64)
            v0_sep = float(row_140["v_rel_ms"])
    else:
        recs, _ = simulate_ascent(enable_anomaly=False, dt=0.05)
        row_140 = recs[-1]
        state_t142 = np.array([
            row_140["eci_x_m"], row_140["eci_y_m"], row_140["eci_z_m"],
            row_140["eci_vx_ms"], row_140["eci_vy_ms"], row_140["eci_vz_ms"],
            row_140["mass_tonnes"] * 1000.0
        ], dtype=np.float64)
        v0_sep = row_140["v_rel_ms"]

    print(f"  Staging State: Alt = {row_140['altitude_km']} km, Downrange = {row_140['downrange_km']} km, Rel Velocity = {v0_sep} m/s")

    # Step 2: High-Frequency Hot-Staging Separation Dynamics
    print("\n[STEP 2] Simulating Dual-Vehicle Hot-Staging Separation (T+140s to T+150s)...")
    m_booster_staging = 671000.0 # kg (hardware + boostback/landing propellant reserve)
    m_ship_staging = 1338975.0   # kg (hardware + payload + full upper stage propellant)

    t0 = time.time()
    records_sep, sum_sep = simulate_hot_staging_separation(
        m_booster_staging, m_ship_staging, v0_ms=v0_sep, dt=0.01, t_span=(140.0, 150.0)
    )
    t_sep_dur = time.time() - t0
    save_telemetry_csv(records_sep, staging_csv)
    print(f"  --> Separation simulated in {t_sep_dur:.3f} s ({len(records_sep)} steps)")
    print(f"  --> Clearance at 1s: {sum_sep['separation_clearance_1s_m']:.2f} m | Clearance at 3s: {sum_sep['separation_clearance_3s_m']:.2f} m")
    print(f"  --> Final 10s Separation Distance: {sum_sep['final_relative_distance_m']:.2f} m")
    print(f"  --> Peak Plume Impingement Force: {sum_sep['peak_plume_force_kn']:.1f} kN")
    print(f"  --> Telemetry saved: {staging_csv} ({os.path.getsize(staging_csv):,} bytes)")

    # Step 3: Super Heavy Booster Recovery & Splashdown Trajectory
    print("\n[STEP 3] Simulating Super Heavy Booster Return, Boostback & Splashdown (T+142s to T+420s)...")
    t0 = time.time()
    records_booster, sum_booster = simulate_booster_return(state_t142, dt=0.05)
    t_booster_dur = time.time() - t0
    save_telemetry_csv(records_booster, booster_csv)
    print(f"  --> Booster trajectory simulated in {t_booster_dur:.3f} s ({len(records_booster)} steps)")
    print(f"  --> Booster Apogee: {sum_booster['apogee']['altitude_km']:.2f} km at T+{sum_booster['apogee']['time_s']} s")
    print(f"  --> Boostback Consumed: {sum_booster['boostback_shutdown']['propellant_consumed_tonnes']:.2f} tonnes")
    print(f"  --> Splashdown at T+{sum_booster['splashdown']['time_s']} s | Touchdown Velocity: {sum_booster['splashdown']['touchdown_relative_velocity_ms']:.1f} m/s")
    print(f"  --> Telemetry saved: {booster_csv} ({os.path.getsize(booster_csv):,} bytes)")

    # Step 4: Starship Stage 2 Powered Ascent to SECO
    print("\n[STEP 4] Simulating Starship Stage 2 Ascent to Orbit (T+142s to T+525s)...")
    t0 = time.time()
    records_ship, sum_ship = simulate_starship_ascent(state_t142, actual_profile=True, dt=0.05)
    t_ship_dur = time.time() - t0
    save_telemetry_csv(records_ship, ship_csv)
    print(f"  --> Starship upper stage simulated in {t_ship_dur:.3f} s ({len(records_ship)} steps)")
    print(f"  --> SECO Timestamp: T+{sum_ship['seco_timestamp_s']} s")
    print(f"  --> SECO Altitude: {sum_ship['seco_altitude_km']:.2f} km | Downrange: {sum_ship['seco_downrange_km']:.2f} km")
    print(f"  --> SECO Inertial Velocity: {sum_ship['seco_inertial_velocity_ms']:.1f} m/s (Rel: {sum_ship['seco_relative_velocity_ms']:.1f} m/s)")
    print(f"  --> Reserve Propellant for Deorbit/Landing: {sum_ship['reserve_propellant_tonnes']:.2f} tonnes")
    print(f"  --> Orbit: {sum_ship['orbital_elements']['perigee_altitude_km']:.1f} km x {sum_ship['orbital_elements']['apogee_altitude_km']:.1f} km @ {sum_ship['orbital_elements']['inclination_deg']:.2f} deg")
    print(f"  --> Telemetry saved: {ship_csv} ({os.path.getsize(ship_csv):,} bytes)")

    # Step 5: Verification & Consistency Check
    assert sum_sep["separation_clearance_1s_m"] > 3.0, "Separation clearance at 1s failed safety margin"
    assert sum_booster["splashdown"]["touchdown_relative_velocity_ms"] < 25.0, "Booster touchdown velocity exceeds terminal limit"
    assert sum_ship["orbital_elements"]["perigee_altitude_km"] > 100.0, "Starship perigee below atmospheric interface"

    master_summary = {
        "mission": "Starship Flight 14 Digital Engineering Laboratory",
        "phase": "Phase 4: Staging Dynamics & Dual-Vehicle Trajectory",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "staging_separation": sum_sep,
        "booster_recovery": sum_booster,
        "starship_orbital_insertion": sum_ship,
        "status": "ALL_PHASE4_MODELS_VERIFIED"
    }

    with open(summary_json, "w", encoding="utf-8") as jf:
        json.dump(master_summary, jf, indent=2)

    print("\n" + "=" * 80)
    print("  PHASE 4 STAGING & DUAL-VEHICLE SIMULATION COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_phase4()
