"""
Staging Separation Sensitivity & Parameter Uncertainty Study
============================================================
Quantifies numerical sensitivity and parameter variations for Starship Flight 14
hot-staging separation dynamics (L1 3-DOF point-mass model).
"""

import os
import sys
import json
import math

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dynamics.staging_separation import simulate_hot_staging_separation

def run_sensitivity_study():
    m_booster_nom = 671000.0
    m_ship_nom = 1338975.0
    v0_nom = 1807.8

    results = {
        "baseline_reproduction": {},
        "time_step_sensitivity": [],
        "plume_force_sensitivity": [],
        "booster_throttle_sensitivity": [],
        "booster_mass_sensitivity": [],
        "modes_verification": {}
    }

    # 1. Baseline reproduction
    recs_base, sum_base = simulate_hot_staging_separation(
        m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, mode="hot_staging"
    )
    results["baseline_reproduction"] = {
        "center_displacement_increment_1s_m": sum_base["center_displacement_increment_1s_m"],
        "center_displacement_increment_3s_m": sum_base["center_displacement_increment_3s_m"],
        "final_relative_distance_10s_m": sum_base["final_relative_distance_m"],
        "final_relative_velocity_10s_ms": sum_base["final_relative_velocity_ms"],
        "peak_relative_accel_g": sum_base["peak_relative_accel_g"],
        "peak_plume_force_kn": sum_base["peak_plume_force_kn"]
    }

    # 2. Time-step convergence study
    dt_list = [0.05, 0.02, 0.01, 0.005, 0.001]
    ref_1s = None
    ref_3s = None
    for dt in reversed(dt_list):
        _, s = simulate_hot_staging_separation(m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=dt)
        if ref_1s is None:
            ref_1s = s["center_displacement_increment_1s_m"]
            ref_3s = s["center_displacement_increment_3s_m"]

    for dt in dt_list:
        _, s = simulate_hot_staging_separation(m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=dt)
        d1 = s["center_displacement_increment_1s_m"]
        d3 = s["center_displacement_increment_3s_m"]
        results["time_step_sensitivity"].append({
            "dt_s": dt,
            "disp_1s_m": d1,
            "disp_3s_m": d3,
            "error_1s_m": abs(d1 - ref_1s),
            "error_1s_pct": abs(d1 - ref_1s) / ref_1s * 100.0,
            "error_3s_m": abs(d3 - ref_3s),
            "error_3s_pct": abs(d3 - ref_3s) / ref_3s * 100.0
        })

    # 3. Plume force sensitivity
    plume_factors = [0.0, 0.5, 0.8, 1.0, 1.2, 1.5]
    for fac in plume_factors:
        f_p = 1.90e6 * fac
        _, s = simulate_hot_staging_separation(
            m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, f_plume_peak=f_p
        )
        results["plume_force_sensitivity"].append({
            "factor": fac,
            "f_plume_peak_kn": f_p / 1000.0,
            "disp_1s_m": s["center_displacement_increment_1s_m"],
            "disp_3s_m": s["center_displacement_increment_3s_m"],
            "delta_from_baseline_1s_m": s["center_displacement_increment_1s_m"] - sum_base["center_displacement_increment_1s_m"]
        })

    # 4. Booster throttle sensitivity
    throttles = [0.0, 0.20, 0.40, 0.60]
    for thr in throttles:
        _, s = simulate_hot_staging_separation(
            m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, booster_throttle_staging=thr
        )
        results["booster_throttle_sensitivity"].append({
            "throttle": thr,
            "disp_1s_m": s["center_displacement_increment_1s_m"],
            "disp_3s_m": s["center_displacement_increment_3s_m"]
        })

    # 5. Booster mass sensitivity
    mass_variations = [-0.10, -0.05, 0.0, 0.05, 0.10]
    for m_var in mass_variations:
        m_b = m_booster_nom * (1.0 + m_var)
        _, s = simulate_hot_staging_separation(
            m_b, m_ship_nom, v0_ms=v0_nom, dt=0.01
        )
        results["booster_mass_sensitivity"].append({
            "variation_pct": m_var * 100.0,
            "m_booster_kg": m_b,
            "disp_1s_m": s["center_displacement_increment_1s_m"],
            "disp_3s_m": s["center_displacement_increment_3s_m"]
        })

    # 6. Mode verification: Zero impulse
    _, s_zero = simulate_hot_staging_separation(
        m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, mode="zero_impulse"
    )
    # Mode verification: Prescribed impulse (J = 1.0e6 N*s)
    J_test = 1.0e6
    _, s_imp = simulate_hot_staging_separation(
        m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, mode="prescribed_impulse", impulse_ns=J_test
    )
    # Mode verification: Prescribed delta-v (dv_rel = 5.0 m/s)
    dv_test = 5.0
    _, s_dv = simulate_hot_staging_separation(
        m_booster_nom, m_ship_nom, v0_ms=v0_nom, dt=0.01, mode="prescribed_relative_delta_v", delta_v_rel_ms=dv_test
    )

    results["modes_verification"] = {
        "zero_impulse": {
            "disp_1s_m": s_zero["center_displacement_increment_1s_m"],
            "rel_velocity_ms": s_zero["final_relative_velocity_ms"]
        },
        "prescribed_impulse": {
            "impulse_ns": J_test,
            "disp_1s_m": s_imp["center_displacement_increment_1s_m"],
            "rel_velocity_ms": s_imp["final_relative_velocity_ms"],
            "expected_rel_vel_ms": J_test / m_ship_nom - (-J_test / m_booster_nom),
            "momentum_error_kg_ms": s_imp["momentum_error_kg_ms"]
        },
        "prescribed_relative_delta_v": {
            "prescribed_dv_ms": dv_test,
            "rel_velocity_ms": s_dv["final_relative_velocity_ms"],
            "momentum_error_kg_ms": s_dv["momentum_error_kg_ms"]
        }
    }

    out_file = os.path.join(PROJECT_ROOT, "output", "staging_sensitivity_study.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    res = run_sensitivity_study()
    print("Baseline Reproduction:")
    print(f"  1s Center Displacement: {res['baseline_reproduction']['center_displacement_increment_1s_m']:.4f} m (reported 5.50 m)")
    print(f"  3s Center Displacement: {res['baseline_reproduction']['center_displacement_increment_3s_m']:.4f} m (reported 48.06 m)")
    print("\nTime-step Convergence:")
    for row in res["time_step_sensitivity"]:
        print(f"  dt={row['dt_s']:6.3f}s | 1s disp={row['disp_1s_m']:7.4f}m | 1s err={row['error_1s_pct']:6.4f}% | 3s disp={row['disp_3s_m']:7.4f}m | 3s err={row['error_3s_pct']:6.4f}%")
    print("\nPlume Force Sensitivity:")
    for row in res["plume_force_sensitivity"]:
        print(f"  Plume={row['f_plume_peak_kn']:6.1f} kN ({row['factor']*100:3.0f}%) | 1s disp={row['disp_1s_m']:7.4f}m (delta={row['delta_from_baseline_1s_m']:+6.4f}m)")
    print("\nModes Verification:")
    print(f"  Zero Impulse: final rel vel = {res['modes_verification']['zero_impulse']['rel_velocity_ms']:.6f} m/s")
    print(f"  Prescribed Impulse: rel vel = {res['modes_verification']['prescribed_impulse']['rel_velocity_ms']:.6f} m/s, momentum err = {res['modes_verification']['prescribed_impulse']['momentum_error_kg_ms']:.2e} kg*m/s")
    print(f"  Prescribed Delta-V: rel vel = {res['modes_verification']['prescribed_relative_delta_v']['rel_velocity_ms']:.6f} m/s, momentum err = {res['modes_verification']['prescribed_relative_delta_v']['momentum_error_kg_ms']:.2e} kg*m/s")
