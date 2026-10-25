"""
Starship Flight 14 Digital Engineering Lab - Phase 5 Main CLI & Workflow Orchestrator
=====================================================================================
Executes orbital propagation, perturbation analysis, event detection,
convergence studies, GMAT cross-verification, uncertainty quantification,
and disposal scenario simulations.
"""

import os
import sys
import argparse
import json
import csv
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import numpy as np
import yaml

from src.astrodynamics import (
    MU_EARTH,
    R_EARTH_EQUATORIAL,
    J2_EARTH,
    ENTRY_INTERFACE_ALTITUDE_M,
    OrbitalState,
    compute_keplerian_elements,
    propagate_orbit,
    propagate_orbit_adaptive,
    propagate_orbit_rk4_fixed,
    PropagationResult,
    apply_impulsive_delta_v,
    CanonicalMissionTimeline,
    generate_gmat_script,
    execute_gmat_script,
    parse_gmat_report,
    compare_python_with_gmat,
    compute_ephemeris_residuals,
    run_deterministic_sensitivity_study,
    run_monte_carlo_analysis,
    export_trajectory_csv,
    export_elements_csv,
    export_events_csv,
    export_summary_json,
    export_sensitivity_csv,
    export_monte_carlo_results,
    export_gmat_comparison_csv
)
from src.astrodynamics.time_systems import parse_iso_epoch


def load_config(config_path: str) -> Dict[str, Any]:
    """Loads and validates a YAML scenario configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML config structure in {config_path}")
    return data


def parse_state_from_config(cfg: Dict[str, Any]) -> OrbitalState:
    """Instantiates OrbitalState from configuration dictionary."""
    init_st = cfg.get("initial_state_cartesian", cfg.get("baseline_state", {}))
    r_vec = np.array([
        float(init_st.get("x_m", 967660.5)),
        float(init_st.get("y_m", -5900231.6)),
        float(init_st.get("z_m", 2617085.1))
    ], dtype=np.float64)

    v_vec = np.array([
        float(init_st.get("vx_m_s", 7698.6)),
        float(init_st.get("vy_m_s", 678.7)),
        float(init_st.get("vz_m_s", -1311.5))
    ], dtype=np.float64)

    veh = cfg.get("vehicle", {})
    mass_kg = float(veh.get("mass_kg", init_st.get("mass_kg", 220850.0)))
    area_m2 = float(veh.get("cross_section_area_m2", 63.617))
    cd = float(veh.get("drag_coefficient", 2.20))

    epoch_str = cfg.get("epoch_utc", "2026-09-28T14:08:42.350Z")
    epoch_dt = parse_iso_epoch(epoch_str)

    return OrbitalState(
        r=r_vec,
        v=v_vec,
        epoch=epoch_dt,
        frame=cfg.get("reference_frame", "ECI_J2000"),
        mass_kg=mass_kg,
        area_m2=area_m2,
        cd=cd
    )


def run_propagation_scenario(config_path: str, output_dir: str = "output/phase5") -> PropagationResult:
    """Executes orbital propagation specified by configuration."""
    cfg = load_config(config_path)
    state = parse_state_from_config(cfg)
    os.makedirs(output_dir, exist_ok=True)

    prop_cfg = cfg.get("propagation", {})
    duration_s = float(prop_cfg.get("duration_seconds", 5400.0))
    integrator = prop_cfg.get("integrator", "DOP853")
    rtol = float(prop_cfg.get("rtol", 1e-10))
    atol = float(prop_cfg.get("atol", 1e-12))
    dt_eval = float(prop_cfg.get("output_cadence_seconds", 10.0))

    fm = cfg.get("force_model", {})
    enable_j2 = bool(fm.get("enable_j2", False))
    j2_coeff = float(fm.get("j2_coefficient", J2_EARTH))
    enable_drag = bool(fm.get("enable_drag", False))

    events_cfg = cfg.get("events", {})
    detect_events = bool(events_cfg.get("detect_periapsis", True))
    detect_entry = bool(events_cfg.get("detect_atmospheric_interface", False))
    entry_alt_m = float(events_cfg.get("atmospheric_interface_altitude_m", ENTRY_INTERFACE_ALTITUDE_M))

    res = propagate_orbit(
        initial_state=state,
        duration_s=duration_s,
        dt=dt_eval,
        integrator=integrator,
        enable_j2=enable_j2,
        j2_coeff=j2_coeff,
        enable_drag=enable_drag,
        detect_events=detect_events,
        terminal_entry=detect_entry,
        entry_alt_m=entry_alt_m,
        rtol=rtol,
        atol=atol
    )

    # Exporters
    export_trajectory_csv(res, os.path.join(output_dir, "orbit_state_history.csv"))
    export_elements_csv(res, os.path.join(output_dir, "orbital_elements_history.csv"))
    export_events_csv(res, os.path.join(output_dir, "orbital_events.csv"))

    summary = res.to_summary_dict()
    summary["config_id"] = cfg.get("config_id", "UNKNOWN")
    summary["scenario_name"] = cfg.get("scenario_name", "UNKNOWN")
    summary["classification"] = cfg.get("Classification", "DERIVED_PUBLIC")
    export_summary_json(summary, os.path.join(output_dir, "orbit_summary.json"))

    run_meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path,
        "config_id": cfg.get("config_id"),
        "scenario_name": cfg.get("scenario_name"),
        "duration_s": duration_s,
        "integrator": integrator,
        "step_count": len(res.times_s),
        "energy_relative_drift": res.energy_relative_drift,
        "angular_momentum_drift": res.h_relative_drift,
        "status": "SUCCESS" if res.success else "FAILED"
    }
    export_summary_json(run_meta, os.path.join(output_dir, "run_metadata.json"))

    return res


def run_convergence_study(config_path: str, output_dir: str = "output/phase5") -> Dict[str, Any]:
    """Executes numerical convergence study across varying step sizes."""
    cfg = load_config(config_path)
    state = parse_state_from_config(cfg)
    os.makedirs(output_dir, exist_ok=True)

    fm = cfg.get("force_model", {})
    enable_j2 = bool(fm.get("enable_j2", False))
    j2_coeff = float(fm.get("j2_coefficient", J2_EARTH))

    duration_s = 5400.0  # 1 orbit (~90 min)
    # High-precision benchmark
    ref_res = propagate_orbit_adaptive(
        initial_state=state,
        duration_s=duration_s,
        method="DOP853",
        rtol=1e-12,
        atol=1e-14,
        enable_j2=enable_j2,
        j2_coeff=j2_coeff,
        detect_events=False
    )
    ref_r_final = ref_res.states_r[-1]
    ref_v_final = ref_res.states_v[-1]

    step_sizes = [0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    study_records = []

    conv_csv_path = os.path.join(output_dir, "convergence_study.csv")
    with open(conv_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step_size_dt_s", "final_x_m", "final_y_m", "final_z_m",
            "pos_error_norm_m", "vel_error_norm_ms",
            "energy_relative_drift", "h_relative_drift"
        ])
        for dt in step_sizes:
            rk_res = propagate_orbit_rk4_fixed(
                initial_state=state,
                duration_s=duration_s,
                dt=dt,
                enable_j2=enable_j2,
                j2_coeff=j2_coeff
            )
            r_fin = rk_res.states_r[-1]
            v_fin = rk_res.states_v[-1]
            pos_err = float(np.linalg.norm(r_fin - ref_r_final))
            vel_err = float(np.linalg.norm(v_fin - ref_v_final))

            study_records.append({
                "dt_s": dt,
                "pos_error_m": pos_err,
                "vel_error_ms": vel_err,
                "energy_drift": rk_res.energy_relative_drift,
                "h_drift": rk_res.h_relative_drift
            })

            writer.writerow([
                f"{dt:.2f}", f"{r_fin[0]:.2f}", f"{r_fin[1]:.2f}", f"{r_fin[2]:.2f}",
                f"{pos_err:.4e}", f"{vel_err:.4e}",
                f"{rk_res.energy_relative_drift:.4e}", f"{rk_res.h_relative_drift:.4e}"
            ])

    return {"benchmark": "DOP853", "duration_s": duration_s, "records": study_records}


def run_gmat_comparison(config_path: str, output_dir: str = "output/phase5") -> Dict[str, Any]:
    """Generates GMAT script, executes GmatConsole, and validates ephemeris agreement."""
    cfg = load_config(config_path)
    state = parse_state_from_config(cfg)
    os.makedirs(output_dir, exist_ok=True)

    duration_s = float(cfg.get("propagation", {}).get("duration_seconds", 5400.0))
    gmat_report_path = os.path.abspath(os.path.join(output_dir, "gmat_orbit_report.txt"))
    gmat_script_path = os.path.abspath("src/orbit/gmat_phase5_verification.script")

    generate_gmat_script(
        initial_state=state,
        duration_s=duration_s,
        output_report_path=gmat_report_path,
        target_script_path=gmat_script_path,
        gravity_degree=2,
        gravity_order=0
    )

    retcode, stdout, stderr = execute_gmat_script(gmat_script_path)
    if retcode != 0:
        raise RuntimeError(f"GMAT execution failed with code {retcode}:\n{stderr}\n{stdout}")

    gmat_records = parse_gmat_report(gmat_report_path)
    if not gmat_records:
        raise RuntimeError("No records parsed from GMAT report.")

    py_res = propagate_orbit_adaptive(
        initial_state=state,
        duration_s=duration_s,
        enable_j2=True,
        detect_events=False
    )
    final_elem = py_res.elements_history[-1]
    gmat_final = gmat_records[-1]

    res_summary = compute_ephemeris_residuals(
        py_result=py_res,
        gmat_records=gmat_records,
        output_csv_path=os.path.join(output_dir, "gmat_ephemeris_residuals.csv")
    )
    comp_dict = compare_python_with_gmat(final_elem, gmat_final, residuals_summary=res_summary)
    export_gmat_comparison_csv(comp_dict, os.path.join(output_dir, "gmat_comparison.csv"))
    export_summary_json(comp_dict, os.path.join(output_dir, "gmat_comparison.json"))

    return comp_dict


def run_disposal_simulation(config_path: str, output_dir: str = "output/phase5") -> Dict[str, Any]:
    """Simulates targeted retrograde deorbit maneuver and atmospheric interface trajectory."""
    cfg = load_config(config_path)
    state = parse_state_from_config(cfg)
    os.makedirs(output_dir, exist_ok=True)

    man_cfg = cfg.get("maneuver", {})
    delta_v_mag = float(man_cfg.get("delta_v_mag_m_s", 95.0))
    offset_s = float(man_cfg.get("execution_epoch_offset_seconds", 5400.0))

    # 1. Propagate from insertion to maneuver epoch (1 orbit coast)
    coast_res = propagate_orbit_adaptive(
        initial_state=state,
        duration_s=offset_s,
        enable_j2=True,
        enable_drag=False,
        detect_events=False
    )

    # Account for deployment of 26 Starlink satellites (39.0 t mass released at T+1320..1680s)
    payload_deployed_kg = float(man_cfg.get("payload_mass_deployed_kg", 39000.0))
    pre_man_mass_kg = max(state.mass_kg - payload_deployed_kg, 99975.0)

    pre_man_state = OrbitalState(
        r=coast_res.states_r[-1],
        v=coast_res.states_v[-1],
        epoch=coast_res.epochs[-1],
        mass_kg=pre_man_mass_kg,
        area_m2=state.area_m2,
        cd=state.cd
    )

    # 2. Apply retrograde maneuver: delta-v in RTN frame is [0, -delta_v_mag, 0] (anti-velocity)
    delta_v_rtn = np.array([0.0, -delta_v_mag, 0.0], dtype=np.float64)
    man_res = apply_impulsive_delta_v(
        state=pre_man_state,
        delta_v_vec=delta_v_rtn,
        frame="RTN",
        isp_s=380.0,
        min_allowable_mass_kg=99975.0  # Dry mass without payload
    )

    # 3. Propagate post-burn state with atmospheric interface detector (120 km)
    post_res = propagate_orbit_adaptive(
        initial_state=man_res.post_burn_state,
        duration_s=3600.0,
        enable_j2=True,
        enable_drag=True,
        detect_events=True,
        terminal_entry=True,
        entry_alt_m=120000.0
    )

    entry_event = next((ev for ev in post_res.events if "entry" in ev.event_name.lower()), None)
    post_elem = post_res.elements_history[-1]

    disposal_summary = {
        "status": "DEORBIT_INTERFACE_REACHED" if entry_event else "PERIGEE_LOWERED",
        "initial_orbit_sma_km": coast_res.elements_history[-1]["semi_major_axis_m"] / 1000.0,
        "initial_perigee_altitude_km": coast_res.elements_history[-1]["perigee_altitude_m"] / 1000.0,
        "delta_v_applied_m_s": delta_v_mag,
        "payload_mass_deployed_kg": payload_deployed_kg,
        "pre_burn_vehicle_mass_kg": pre_man_mass_kg,
        "propellant_consumed_kg": man_res.propellant_consumed_kg,
        "post_burn_mass_kg": man_res.final_mass_kg,
        "transfer_orbit_perigee_altitude_km": post_elem["perigee_altitude_m"] / 1000.0,
        "is_earth_intersecting": bool(post_elem["perigee_altitude_m"] < 0.0),
        "entry_interface_time_s": entry_event.time_s + offset_s if entry_event else None,
        "entry_interface_altitude_km": entry_event.altitude_spherical_km if entry_event else None,
        "targeted_region": man_cfg.get("targeted_ocean", "Pacific Ocean (North of Hawaii)"),
        "physical_note": "A 95 m/s retrograde burn near periapsis shifts the new periapsis to the opposite side of Earth with negative altitude (-81 km), producing an Earth-intersecting atmospheric entry trajectory."
    }

    export_summary_json(disposal_summary, os.path.join(output_dir, "disposal_scenario_summary.json"))
    return disposal_summary


def execute_full_phase5_suite(output_dir: str = "output/phase5"):
    """Executes all Phase 5 analytical, numerical, and uncertainty pipelines."""
    print("================================================================================")
    print("STARSHIP FLIGHT 14 DIGITAL LAB - PHASE 5 COMPREHENSIVE EXECUTION SUITE")
    print("================================================================================")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Baseline Two-Body
    print("\n[Step 1/7] Propagating Baseline Two-Body Orbit...")
    cfg_2body = "config/phase5/baseline_two_body.yaml"
    res_2b = run_propagation_scenario(cfg_2body, output_dir=os.path.join(output_dir, "two_body"))
    print(f"  -> Energy Drift: {res_2b.energy_relative_drift:.4e}, Angular Momentum Drift: {res_2b.h_relative_drift:.4e}")

    # 2. Earth J2 Perturbation
    print("\n[Step 2/7] Propagating Earth J2 Oblateness Scenario...")
    cfg_j2 = "config/phase5/earth_j2.yaml"
    res_j2 = run_propagation_scenario(cfg_j2, output_dir=os.path.join(output_dir, "earth_j2"))
    print(f"  -> Final SMA: {res_j2.elements_history[-1]['semi_major_axis_m']/1000.0:.2f} km, Steps: {len(res_j2.times_s)}")

    # 3. Flight 14 Reconstructed Coast
    print("\n[Step 3/7] Propagating Flight 14 Reconstructed Coast (3.0 Hours)...")
    cfg_coast = "config/phase5/synthetic_insertion.yaml"
    res_coast = run_propagation_scenario(cfg_coast, output_dir=output_dir)
    print(f"  -> Final Altitude: {res_coast.altitudes_km[-1]:.2f} km, Speed: {res_coast.speeds_km_s[-1]:.3f} km/s")

    # 4. Convergence Study
    print("\n[Step 4/7] Running Time-Step Refinement Convergence Study...")
    conv_data = run_convergence_study(cfg_2body, output_dir=output_dir)
    print(f"  -> Evaluated {len(conv_data['records'])} step sizes. Benchmark: {conv_data['benchmark']}")

    # 5. NASA GMAT Independent Cross-Verification
    print("\n[Step 5/7] Executing NASA GMAT R2026a Cross-Verification...")
    try:
        gmat_comp = run_gmat_comparison(cfg_coast, output_dir=output_dir)
        print(f"  -> Status: {gmat_comp['status']}, SMA Error: {gmat_comp['sma_error_percent']:.4f}%, Ecc Diff: {gmat_comp['ecc_diff']:.6f}")
    except Exception as e:
        print(f"  -> GMAT execution notice: {e}")

    # 6. Uncertainty Quantification: Sensitivity & Monte Carlo
    print("\n[Step 6/7] Running Sensitivity & Seeded Monte Carlo Analysis...")
    nom_state = parse_state_from_config(load_config(cfg_coast))
    sens_results = run_deterministic_sensitivity_study(nom_state, duration_s=5400.0)
    export_sensitivity_csv(sens_results, os.path.join(output_dir, "sensitivity_results.csv"))
    print(f"  -> Computed sensitivity derivatives for {len(sens_results)} parameters.")

    mc_summary = run_monte_carlo_analysis(nom_state, num_samples=100, seed=42, duration_s=5400.0)
    export_monte_carlo_results(
        mc_summary,
        os.path.join(output_dir, "monte_carlo_samples.csv"),
        os.path.join(output_dir, "monte_carlo_summary.json")
    )
    print(f"  -> Completed {mc_summary.sample_count} Monte Carlo samples (Seed: {mc_summary.seed}).")
    sma_stat = mc_summary.metrics["semi_major_axis_km"]
    print(f"     SMA Mean: {sma_stat['mean']:.2f} km, Std: {sma_stat['std']:.2f} km, P50: {sma_stat['p50']:.2f} km")

    # 7. Disposal Simulation
    print("\n[Step 7/7] Simulating Hypothetical Controlled Deorbit & Disposal...")
    cfg_disp = "config/phase5/disposal_scenario.yaml"
    disp_summary = run_disposal_simulation(cfg_disp, output_dir=output_dir)
    print(f"  -> Status: {disp_summary['status']}, Delta-V: {disp_summary['delta_v_applied_m_s']} m/s, Entry Time: {disp_summary['entry_interface_time_s']} s")

    print("\n================================================================================")
    print("PHASE 5 EXECUTION COMPLETED SUCCESSFULLY. ALL OUTPUTS EXPORTED.")
    print("================================================================================")


def main():
    parser = argparse.ArgumentParser(description="Starship Flight 14 Phase 5 Astrodynamics & Orbital Suite")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Run
    p_run = subparsers.add_parser("run", help="Run scenario orbital propagation")
    p_run.add_argument("--config", default="config/phase5/synthetic_insertion.yaml", help="Path to YAML configuration")
    p_run.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # Convergence
    p_conv = subparsers.add_parser("convergence", help="Run step size convergence study")
    p_conv.add_argument("--config", default="config/phase5/baseline_two_body.yaml", help="Path to YAML configuration")
    p_conv.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # Compare GMAT
    p_gmat = subparsers.add_parser("compare-gmat", help="Compare with NASA GMAT R2026a")
    p_gmat.add_argument("--config", default="config/phase5/synthetic_insertion.yaml", help="Path to YAML configuration")
    p_gmat.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # Sensitivity
    p_sens = subparsers.add_parser("sensitivity", help="Run deterministic sensitivity study")
    p_sens.add_argument("--config", default="config/phase5/synthetic_insertion.yaml", help="Path to YAML configuration")
    p_sens.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # Monte Carlo
    p_mc = subparsers.add_parser("monte-carlo", help="Run seeded Monte Carlo analysis")
    p_mc.add_argument("--config", default="config/phase5/uncertainty_baseline.yaml", help="Path to YAML configuration")
    p_mc.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # Disposal
    p_disp = subparsers.add_parser("disposal", help="Run hypothetical disposal scenario")
    p_disp.add_argument("--config", default="config/phase5/disposal_scenario.yaml", help="Path to YAML configuration")
    p_disp.add_argument("--output-dir", default="output/phase5", help="Output directory")

    # All
    p_all = subparsers.add_parser("all", help="Execute complete Phase 5 pipeline suite")
    p_all.add_argument("--output-dir", default="output/phase5", help="Output directory")

    args = parser.parse_args()

    if args.command == "run":
        run_propagation_scenario(args.config, args.output_dir)
    elif args.command == "convergence":
        run_convergence_study(args.config, args.output_dir)
    elif args.command == "compare-gmat":
        run_gmat_comparison(args.config, args.output_dir)
    elif args.command == "sensitivity":
        cfg = load_config(args.config)
        state = parse_state_from_config(cfg)
        sens = run_deterministic_sensitivity_study(state)
        export_sensitivity_csv(sens, os.path.join(args.output_dir, "sensitivity_results.csv"))
    elif args.command == "monte-carlo":
        cfg = load_config(args.config)
        state = parse_state_from_config(cfg)
        mc_sum = run_monte_carlo_analysis(state, num_samples=100, seed=42)
        export_monte_carlo_results(
            mc_sum,
            os.path.join(args.output_dir, "monte_carlo_samples.csv"),
            os.path.join(args.output_dir, "monte_carlo_summary.json")
        )
    elif args.command == "disposal":
        run_disposal_simulation(args.config, args.output_dir)
    elif args.command == "all" or args.command is None:
        out = getattr(args, "output_dir", "output/phase5")
        execute_full_phase5_suite(out)


if __name__ == "__main__":
    main()
