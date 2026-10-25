"""
Phase 6 Command-Line Interface & Master Execution Orchestrator
=============================================================
Phase 6: Atmospheric Reentry, Hypersonic Aerodynamics, Deceleration,
Aerothermal Heating, Guidance, and Ocean Splashdown Simulation.
"""

import os
import sys
import csv
import argparse
import json
import yaml
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

from src.astrodynamics.state import OrbitalState
from src.reentry import (
    ReentryVehicleConfig,
    USStandardAtmosphere1976,
    CrossrangeBankGuidanceController,
    propagate_reentry,
    run_reentry_sensitivity_study,
    run_reentry_monte_carlo,
    export_trajectory_csv,
    export_aerothermal_history_csv,
    export_event_log_csv,
    export_control_history_csv,
    export_sensitivity_csv,
    export_monte_carlo_csv,
    export_json_summary
)


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Loads and validates a YAML scenario configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML config structure in {config_path}")
    return data


def parse_reentry_setup_from_config(cfg: Dict[str, Any]) -> Tuple[OrbitalState, ReentryVehicleConfig, USStandardAtmosphere1976, Optional[CrossrangeBankGuidanceController], Dict[str, Any]]:
    """Instantiates physical state, vehicle, atmosphere, and guidance from configuration dictionary."""
    # 1. Initial State
    st_cfg = cfg.get("initial_state_cartesian", {})
    r_vec = np.array([
        float(st_cfg.get("x_m", 5528938.10)),
        float(st_cfg.get("y_m", -3319172.12)),
        float(st_cfg.get("z_m", 798881.33))
    ], dtype=np.float64)

    v_vec = np.array([
        float(st_cfg.get("vx_m_s", 3895.7417)),
        float(st_cfg.get("vy_m_s", 5894.2764)),
        float(st_cfg.get("vz_m_s", -3257.6110))
    ], dtype=np.float64)

    veh_cfg = cfg.get("vehicle", {})
    mass_kg = float(veh_cfg.get("mass_kg", 177272.71))
    elapsed_s = float(st_cfg.get("elapsed_mission_seconds", 6527.315))

    initial_state = OrbitalState(
        r=r_vec,
        v=v_vec,
        epoch=elapsed_s,
        mass_kg=mass_kg
    )

    # 2. Vehicle Configuration
    vehicle = ReentryVehicleConfig(
        vehicle_id=veh_cfg.get("vehicle_id", "Starship_Flight14_UpperStage"),
        scenario_id=cfg.get("scenario_name", "SYNTHETIC_REENTRY"),
        mass_kg=mass_kg,
        reference_area_m2=float(veh_cfg.get("reference_area_m2", 63.617)),
        reference_length_m=float(veh_cfg.get("reference_length_m", 50.0)),
        nose_radius_m=float(veh_cfg.get("nose_radius_m", 4.50)),
        nominal_angle_of_attack_deg=float(veh_cfg.get("nominal_angle_of_attack_deg", 70.0)),
        cd_hypersonic_70deg=float(veh_cfg.get("cd_hypersonic", 1.50)),
        cl_hypersonic_70deg=float(veh_cfg.get("cl_hypersonic", 0.40)),
        max_bank_angle_deg=float(veh_cfg.get("max_bank_angle_deg", 45.0)),
        max_bank_rate_deg_s=float(veh_cfg.get("max_bank_rate_deg_s", 10.0))
    )

    # 3. Atmosphere
    atm_cfg = cfg.get("atmosphere", {})
    atmosphere = USStandardAtmosphere1976(
        density_scale=float(atm_cfg.get("density_scale_factor", 1.0)),
        temp_offset_k=float(atm_cfg.get("temperature_offset_k", 0.0))
    )

    # 4. Target definition
    tgt_cfg = cfg.get("target", {})
    target_info = {
        "name": tgt_cfg.get("target_name", "Recovery Corridor"),
        "lat_deg": float(tgt_cfg.get("latitude_deg", -14.04)),
        "lon_deg": float(tgt_cfg.get("longitude_deg", -15.49)),
        "radius_m": float(tgt_cfg.get("corridor_radius_m", 100000.0))
    }

    # 5. Guidance Controller
    guide_cfg = cfg.get("guidance", {})
    if guide_cfg.get("enabled", False):
        guidance = CrossrangeBankGuidanceController(
            target_lat_deg=target_info["lat_deg"],
            target_lon_deg=target_info["lon_deg"],
            entry_lat_deg=7.1084,
            entry_lon_deg=-58.3341,
            nominal_aoa_deg=vehicle.nominal_angle_of_attack_deg,
            max_bank_angle_deg=vehicle.max_bank_angle_deg,
            max_bank_rate_deg_s=vehicle.max_bank_rate_deg_s,
            min_control_dynamic_pressure_pa=float(guide_cfg.get("min_control_dynamic_pressure_pa", 50.0)),
            activation_altitude_m=float(guide_cfg.get("activation_altitude_m", 100000.0)),
            termination_altitude_m=float(guide_cfg.get("termination_altitude_m", 15000.0)),
            kp_bank_deg_per_km=float(guide_cfg.get("kp_bank_deg_per_km", 0.60)),
            kd_bank_s_per_km=float(guide_cfg.get("kd_bank_s_per_km", 0.08)),
            enabled=True
        )
    else:
        guidance = None

    return initial_state, vehicle, atmosphere, guidance, target_info


def run_reentry_scenario(config_path: str, output_dir: str = "output/phase6") -> Dict[str, Any]:
    """Executes a single reentry simulation scenario from YAML configuration."""
    cfg = load_yaml_config(config_path)
    os.makedirs(output_dir, exist_ok=True)
    scenario_id = cfg.get("scenario_name", "synthetic_entry")

    initial_state, vehicle, atmosphere, guidance, target_info = parse_reentry_setup_from_config(cfg)
    prop_cfg = cfg.get("propagation", {})
    max_duration_s = float(prop_cfg.get("max_duration_seconds", 1500.0))
    eval_step_s = float(prop_cfg.get("eval_step_seconds", 1.0))
    integrator = str(prop_cfg.get("integrator", "DOP853"))
    rtol = float(prop_cfg.get("rtol", 1e-8))
    atol = float(prop_cfg.get("atol", 1e-10))

    res = propagate_reentry(
        initial_state=initial_state,
        vehicle_config=vehicle,
        atmosphere=atmosphere,
        guidance=guidance,
        enable_j2=prop_cfg.get("enable_j2", True),
        max_duration_s=max_duration_s,
        eval_step_s=eval_step_s,
        integrator=integrator,
        rtol=rtol,
        atol=atol,
        target_lat_deg=target_info["lat_deg"],
        target_lon_deg=target_info["lon_deg"],
        target_radius_m=target_info["radius_m"],
        scenario_id=scenario_id
    )

    # Export machine-readable deliverables
    prefix = f"{scenario_id}_" if scenario_id != "synthetic_entry_baseline" else ""
    export_trajectory_csv(res.steps, os.path.join(output_dir, f"{prefix}entry_trajectory.csv"))
    export_aerothermal_history_csv(res.steps, os.path.join(output_dir, f"{prefix}heating_history.csv"))
    export_event_log_csv(res.events, os.path.join(output_dir, f"{prefix}event_log.csv"))
    export_control_history_csv(res.steps, os.path.join(output_dir, f"{prefix}control_history.csv"))

    terminal_dict = res.terminal_assessment.to_dict()
    export_json_summary(terminal_dict, os.path.join(output_dir, f"{prefix}terminal_state.json"))

    summary_dict = {
        "scenario_id": scenario_id,
        "classification": cfg.get("Classification", "SYNTHETIC_SCENARIO"),
        "initial_entry_altitude_km": res.steps[0].altitude_m / 1000.0,
        "initial_relative_speed_ms": res.steps[0].speed_relative_ms,
        "initial_mach": res.steps[0].mach,
        "entry_flight_path_angle_deg": res.steps[0].flight_path_angle_deg,
        "peak_dynamic_pressure_kpa": res.peak_dynamic_pressure_pa / 1000.0,
        "peak_apparent_g_load": res.peak_apparent_g_load,
        "peak_stagnation_heat_flux_mw_m2": res.peak_stagnation_heat_flux_mw_m2,
        "cumulative_heat_load_mj_m2": res.total_heat_load_mj_m2,
        "reentry_flight_duration_s": res.impact_time_s,
        "terminal_impact_lat_deg": res.terminal_assessment.geodetic_lat_deg,
        "terminal_impact_lon_deg": res.terminal_assessment.geodetic_lon_deg,
        "terminal_relative_speed_ms": res.terminal_relative_speed_ms,
        "target_miss_distance_km": res.miss_distance_km,
        "outcome_classification": res.terminal_assessment.outcome_classification,
        "target_within_corridor": res.terminal_assessment.target_within_corridor
    }
    export_json_summary(summary_dict, os.path.join(output_dir, f"{prefix}entry_summary.json"))

    print(f"\nScenario '{scenario_id}' Simulation Results:")
    print(f"  Entry Interface:        {summary_dict['initial_entry_altitude_km']:.2f} km @ {summary_dict['initial_relative_speed_ms']:.1f} m/s (Mach {summary_dict['initial_mach']:.1f})")
    print(f"  Flight Path Angle:      {summary_dict['entry_flight_path_angle_deg']:.3f} deg")
    print(f"  Peak Dynamic Pressure:  {summary_dict['peak_dynamic_pressure_kpa']:.2f} kPa")
    print(f"  Peak Deceleration:      {summary_dict['peak_apparent_g_load']:.2f} g")
    print(f"  Peak Stagnation Heat:   {summary_dict['peak_stagnation_heat_flux_mw_m2']:.3f} MW/m^2 ({summary_dict['peak_stagnation_heat_flux_mw_m2']*100:.1f} W/cm^2)")
    print(f"  Total Heat Load:        {summary_dict['cumulative_heat_load_mj_m2']:.2f} MJ/m^2")
    print(f"  Duration to Surface:    {summary_dict['reentry_flight_duration_s']:.2f} s (~{summary_dict['reentry_flight_duration_s']/60:.1f} min)")
    print(f"  Terminal Lat / Lon:     {summary_dict['terminal_impact_lat_deg']:.4f} deg, {summary_dict['terminal_impact_lon_deg']:.4f} deg")
    print(f"  Terminal Speed:         {summary_dict['terminal_relative_speed_ms']:.1f} m/s")
    print(f"  Target Miss Distance:   {summary_dict['target_miss_distance_km']:.2f} km")
    print(f"  Outcome Classification: {summary_dict['outcome_classification']}")

    return summary_dict


def run_controlled_comparison(baseline_cfg_path: str, guided_cfg_path: str, output_dir: str = "output/phase6") -> Dict[str, Any]:
    """Runs and directly compares uncontrolled vs guided reentry trajectories."""
    print("--------------------------------------------------------------------------------")
    print("RUNNING REENTRY TRAJECTORY GUIDANCE COMPARISON (UNCONTROLLED vs GUIDED)")
    print("--------------------------------------------------------------------------------")
    uncontrolled = run_reentry_scenario(baseline_cfg_path, output_dir=output_dir)
    guided = run_reentry_scenario(guided_cfg_path, output_dir=output_dir)

    d_miss_diff_km = uncontrolled["target_miss_distance_km"] - guided["target_miss_distance_km"]
    pct_miss_improvement = (d_miss_diff_km / max(uncontrolled["target_miss_distance_km"], 1e-6)) * 100.0

    comp = {
        "comparison_title": "Starship Flight 14 Reentry Guidance Assessment",
        "uncontrolled_miss_km": uncontrolled["target_miss_distance_km"],
        "guided_miss_km": guided["target_miss_distance_km"],
        "miss_reduction_km": d_miss_diff_km,
        "miss_improvement_percent": pct_miss_improvement,
        "uncontrolled_peak_g": uncontrolled["peak_apparent_g_load"],
        "guided_peak_g": guided["peak_apparent_g_load"],
        "uncontrolled_peak_heat_mw_m2": uncontrolled["peak_stagnation_heat_flux_mw_m2"],
        "guided_peak_heat_mw_m2": guided["peak_stagnation_heat_flux_mw_m2"],
        "uncontrolled_total_heat_load_mj_m2": uncontrolled["cumulative_heat_load_mj_m2"],
        "guided_total_heat_load_mj_m2": guided["cumulative_heat_load_mj_m2"],
        "guided_target_status": guided["outcome_classification"]
    }

    export_json_summary(comp, os.path.join(output_dir, "guidance_comparison_summary.json"))

    print("\n================================================================================")
    print("GUIDANCE ASSESSMENT SUMMARY:")
    print(f"  Uncontrolled Miss Distance: {comp['uncontrolled_miss_km']:.2f} km")
    print(f"  Guided Miss Distance:       {comp['guided_miss_km']:.2f} km")
    print(f"  Miss Distance Reduction:    {comp['miss_reduction_km']:.2f} km ({comp['miss_improvement_percent']:.1f}% Improvement)")
    print(f"  Peak Deceleration Tradeoff: {comp['uncontrolled_peak_g']:.2f} g -> {comp['guided_peak_g']:.2f} g")
    print(f"  Peak Heating Tradeoff:      {comp['uncontrolled_peak_heat_mw_m2']:.3f} MW/m^2 -> {comp['guided_peak_heat_mw_m2']:.3f} MW/m^2")
    print(f"  Guided Corridor Status:     {comp['guided_target_status']}")
    print("================================================================================")
    return comp


def run_numerical_convergence_study(config_path: str, output_dir: str = "output/phase6") -> List[Dict[str, Any]]:
    """Runs integration step-size refinement study comparing RK4 against DOP853 benchmark."""
    print("--------------------------------------------------------------------------------")
    print("RUNNING TIME-STEP REFINEMENT CONVERGENCE STUDY (RK4 vs DOP853)")
    print("--------------------------------------------------------------------------------")
    cfg = load_yaml_config(config_path)
    initial_state, vehicle, atmosphere, guidance, target_info = parse_reentry_setup_from_config(cfg)

    # High-precision adaptive benchmark
    benchmark = propagate_reentry(
        initial_state=initial_state,
        vehicle_config=vehicle,
        atmosphere=atmosphere,
        guidance=guidance,
        integrator="DOP853",
        rtol=1e-10,
        atol=1e-12,
        eval_step_s=0.5,
        target_lat_deg=target_info["lat_deg"],
        target_lon_deg=target_info["lon_deg"]
    )

    bench_t_impact = benchmark.impact_time_s
    bench_r_final = benchmark.steps[-1].r_eci
    bench_v_final = benchmark.steps[-1].v_eci
    bench_peak_q = benchmark.peak_dynamic_pressure_pa
    bench_peak_g = benchmark.peak_apparent_g_load
    bench_peak_heat = benchmark.peak_stagnation_heat_flux_mw_m2
    bench_tot_heat = benchmark.total_heat_load_mj_m2

    step_sizes = [0.25, 0.50, 1.0, 2.0, 5.0]
    study_rows = []

    for dt in step_sizes:
        res = propagate_reentry(
            initial_state=initial_state,
            vehicle_config=vehicle,
            atmosphere=atmosphere,
            guidance=guidance,
            integrator="RK4_FIXED",
            eval_step_s=dt,
            target_lat_deg=target_info["lat_deg"],
            target_lon_deg=target_info["lon_deg"]
        )

        pos_err = float(np.linalg.norm(res.steps[-1].r_eci - bench_r_final))
        vel_err = float(np.linalg.norm(res.steps[-1].v_eci - bench_v_final))
        dt_err = abs(res.impact_time_s - bench_t_impact)
        dq_err = abs(res.peak_dynamic_pressure_pa - bench_peak_q)
        dg_err = abs(res.peak_apparent_g_load - bench_peak_g)
        dheat_err = abs(res.peak_stagnation_heat_flux_mw_m2 - bench_peak_heat)
        dtot_err = abs(res.total_heat_load_mj_m2 - bench_tot_heat)

        row = {
            "time_step_s": dt,
            "steps_count": len(res.steps),
            "pos_error_norm_m": pos_err,
            "vel_error_norm_ms": vel_err,
            "impact_time_diff_s": dt_err,
            "peak_q_error_pa": dq_err,
            "peak_g_error": dg_err,
            "peak_heat_error_mw_m2": dheat_err,
            "total_heat_error_mj_m2": dtot_err
        }
        study_rows.append(row)
        print(f"  dt={dt:4.2f}s | Steps={len(res.steps):4d} | Pos Err={pos_err:8.2f}m | Vel Err={vel_err:6.3f}m/s | dt Err={dt_err:5.2f}s | dQ Err={dtot_err:5.2f}MJ/m^2")

    # Export convergence CSV
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "convergence_study.csv")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(study_rows[0].keys()))
        writer.writeheader()
        writer.writerows(study_rows)

    return study_rows


def run_full_uncertainty_suite(config_path: str, output_dir: str = "output/phase6") -> Dict[str, Any]:
    """Executes OAT sensitivity study and seeded Monte Carlo ensemble."""
    print("--------------------------------------------------------------------------------")
    print("RUNNING REENTRY SENSITIVITY & MONTE CARLO UNCERTAINTY ANALYSIS")
    print("--------------------------------------------------------------------------------")
    cfg = load_yaml_config(config_path)
    initial_state, vehicle, atmosphere, guidance, target_info = parse_reentry_setup_from_config(cfg)
    unc_cfg = cfg.get("uncertainty", {})
    sample_count = int(unc_cfg.get("monte_carlo_samples", 50))
    seed = int(unc_cfg.get("random_seed", 42))

    # 1. Sensitivity Study
    sens = run_reentry_sensitivity_study(
        baseline_state=initial_state,
        vehicle_config=vehicle,
        atmosphere=atmosphere,
        guidance=guidance,
        target_lat_deg=target_info["lat_deg"],
        target_lon_deg=target_info["lon_deg"],
        target_radius_m=target_info["radius_m"]
    )
    export_sensitivity_csv(sens, os.path.join(output_dir, "sensitivity_results.csv"))
    print(f"  Computed sensitivity derivatives across {len(sens)} physical parameters.")

    # 2. Monte Carlo Ensemble
    mc = run_reentry_monte_carlo(
        baseline_state=initial_state,
        vehicle_config=vehicle,
        atmosphere=atmosphere,
        guidance=guidance,
        sample_count=sample_count,
        seed=seed,
        target_lat_deg=target_info["lat_deg"],
        target_lon_deg=target_info["lon_deg"],
        target_radius_m=target_info["radius_m"]
    )
    export_monte_carlo_csv(mc.samples, os.path.join(output_dir, "monte_carlo_samples.csv"))
    export_json_summary(mc.to_dict(), os.path.join(output_dir, "monte_carlo_summary.json"))

    print(f"  Completed {mc.completed_count}/{mc.sample_count} Monte Carlo samples (Seed: {mc.seed}).")
    q_stat = mc.metrics["peak_dynamic_pressure_kpa"]
    g_stat = mc.metrics["peak_apparent_g_load"]
    h_stat = mc.metrics["peak_stagnation_heat_flux_mw_m2"]
    q_tot = mc.metrics["total_heat_load_mj_m2"]
    print(f"    Peak Dynamic Pressure: Mean={q_stat['mean']:.2f} kPa, Std={q_stat['std']:.2f} kPa")
    print(f"    Peak Apparent Decel:   Mean={g_stat['mean']:.2f} g, Std={g_stat['std']:.2f} g")
    print(f"    Peak Stagnation Heat:  Mean={h_stat['mean']:.3f} MW/m^2, Std={h_stat['std']:.3f} MW/m^2")
    print(f"    Total Heat Load:       Mean={q_tot['mean']:.2f} MJ/m^2, Std={q_tot['std']:.2f} MJ/m^2")
    print(f"    Corridor Hit Fraction: {mc.target_hit_fraction * 100:.1f}%")

    return {
        "sensitivity_count": len(sens),
        "monte_carlo_samples": sample_count,
        "monte_carlo_metrics": mc.metrics
    }


def execute_full_phase6_suite(output_dir: str = "output/phase6"):
    """Executes the complete Phase 6 scientific pipeline, generating all deliverables and figures."""
    print("================================================================================")
    print("STARSHIP FLIGHT 14 DIGITAL LAB - PHASE 6 MASTER REENTRY EXECUTION SUITE")
    print("================================================================================")
    t_start = datetime.now(timezone.utc)

    # 1. Baseline Run
    print("\n[Step 1/5] Executing Baseline Synthetic Reentry Simulation...")
    base_summary = run_reentry_scenario("config/phase6/synthetic_entry_baseline.yaml", output_dir=output_dir)

    # 2. Controlled vs Uncontrolled Comparison
    print("\n[Step 2/5] Executing Guidance-to-Dynamics Comparison...")
    comp_summary = run_controlled_comparison(
        baseline_cfg_path="config/phase6/synthetic_entry_uncontrolled.yaml",
        guided_cfg_path="config/phase6/synthetic_entry_guided.yaml",
        output_dir=output_dir
    )

    # 3. Numerical Convergence Study
    print("\n[Step 3/5] Executing Integration Step-Size Convergence Study...")
    conv_rows = run_numerical_convergence_study("config/phase6/synthetic_entry_baseline.yaml", output_dir=output_dir)

    # 4. Sensitivity & Monte Carlo Analysis
    print("\n[Step 4/5] Executing Uncertainty Quantification Suite...")
    unc_summary = run_full_uncertainty_suite("config/phase6/synthetic_entry_uncertainty.yaml", output_dir=output_dir)

    # 5. Metadata Export
    t_end = datetime.now(timezone.utc)
    wall_time_s = (t_end - t_start).total_seconds()

    meta = {
        "phase": 6,
        "phase_title": "Atmospheric Reentry, Hypersonic Aerodynamics, Aerothermal Heating, and Splashdown",
        "execution_epoch_utc": t_start.isoformat(),
        "wall_time_seconds": wall_time_s,
        "git_branch": "master",
        "upstream_handoff": {
            "source_phase": 5,
            "interface_altitude_km": 120.0,
            "vehicle_mass_entry_kg": 177272.71,
            "starlinks_deployed_count": 26,
            "starlink_payload_mass_kg": 39000.0
        },
        "baseline_metrics": base_summary,
        "guidance_metrics": comp_summary,
        "convergence_steps_evaluated": len(conv_rows),
        "monte_carlo_samples_executed": unc_summary["monte_carlo_samples"]
    }
    export_json_summary(meta, os.path.join(output_dir, "run_metadata.json"))
    export_json_summary(base_summary, os.path.join(output_dir, "phase6_summary.json"))

    print("\n[Step 5/5] All simulation runs completed. Run metadata exported.")
    print("================================================================================")
    print(f"PHASE 6 EXECUTION SUITE FINISHED IN {wall_time_s:.2f} s. ALL OUTPUTS SAVED TO {output_dir}")
    print("================================================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Starship Flight 14 Phase 6 Master CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_p = subparsers.add_parser("run", help="Run a single reentry simulation scenario")
    run_p.add_argument("--config", type=str, default="config/phase6/synthetic_entry_baseline.yaml", help="Path to scenario YAML config")
    run_p.add_argument("--output", type=str, default="output/phase6", help="Output directory")

    comp_p = subparsers.add_parser("compare", help="Compare uncontrolled vs guided reentry scenarios")
    comp_p.add_argument("--baseline", type=str, default="config/phase6/synthetic_entry_uncontrolled.yaml")
    comp_p.add_argument("--controlled", type=str, default="config/phase6/synthetic_entry_guided.yaml")
    comp_p.add_argument("--output", type=str, default="output/phase6")

    conv_p = subparsers.add_parser("convergence", help="Run numerical step-size convergence study")
    conv_p.add_argument("--config", type=str, default="config/phase6/synthetic_entry_baseline.yaml")
    conv_p.add_argument("--output", type=str, default="output/phase6")

    sens_p = subparsers.add_parser("sensitivity", help="Run OAT sensitivity and Monte Carlo analysis")
    sens_p.add_argument("--config", type=str, default="config/phase6/synthetic_entry_uncertainty.yaml")
    sens_p.add_argument("--output", type=str, default="output/phase6")

    all_p = subparsers.add_parser("all", help="Execute complete Phase 6 suite")
    all_p.add_argument("--output", type=str, default="output/phase6")

    args = parser.parse_args()

    if args.command == "run":
        run_reentry_scenario(args.config, output_dir=args.output)
    elif args.command == "compare":
        run_controlled_comparison(args.baseline, args.controlled, output_dir=args.output)
    elif args.command == "convergence":
        run_numerical_convergence_study(args.config, output_dir=args.output)
    elif args.command == "sensitivity":
        run_full_uncertainty_suite(args.config, output_dir=args.output)
    elif args.command == "all" or args.command is None:
        execute_full_phase6_suite(output_dir=getattr(args, "output", "output/phase6"))


if __name__ == "__main__":
    main()
