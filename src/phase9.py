"""
Command-line interface (CLI) for Starship Phase 9: Aerothermal Reentry & Thermal Protection Model.

Supported commands:
  python -m src.phase9 flux
  python -m src.phase9 solve-1d --tile-thickness 28.0
  python -m src.phase9 trade
  python -m src.phase9 sensitivity
  python -m src.phase9 all
"""

import argparse
import sys
import os
import csv
import json
from typing import Dict, Any, List, Tuple

from src.thermal.material_properties import (
    RTV_BONDLINE_LIMIT_K,
    SILICA_REUSABLE_LIMIT_K,
)
from src.thermal.aerothermal_flux import (
    compute_sutton_graves_heat_flux,
    compute_detra_kemp_riddell_flux,
    compute_windward_acreage_flux,
    compute_radiative_equilibrium_temp,
)
from src.thermal.conduction_1d import (
    ThermalStackMesh,
    generate_thermal_stack_mesh,
    TransientThermalSolver1D,
    ThermalSolution1D,
)
from src.thermal.margin_analysis import (
    evaluate_bondline_margins,
    run_tile_thickness_trade_study,
    run_density_sensitivity_study,
)
from src.thermal.reporting import (
    export_thermal_history_csv,
    generate_thermal_diagnostic_plots,
)


def load_reentry_trajectory_data(csv_path: str = None) -> List[Dict[str, float]]:
    """
    Load entry trajectory states from Phase 6 output CSV or generate standard corridor.
    """
    if csv_path is None:
        csv_path = os.path.join("output", "phase6", "entry_trajectory.csv")

    rows: List[Dict[str, float]] = []

    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({
                    "time_s": float(r["time_s"]),
                    "altitude_km": float(r["altitude_m"]) / 1000.0,
                    "altitude_m": float(r["altitude_m"]),
                    "speed_relative_ms": float(r["speed_relative_ms"]),
                    "velocity_kms": float(r["speed_relative_ms"]) / 1000.0,
                    "density_kg_m3": float(r["density_kg_m3"]),
                    "temperature_k": float(r.get("temperature_k", 220.0)),
                })
    else:
        # Fallback synthetic profile if Phase 6 CSV is missing
        print(f"[!] Trajectory CSV not found at {csv_path}; generating synthetic baseline.")
        for t in range(0, 900, 2):
            alt_km = max(0.0, 120.0 - 0.133 * t)
            # Standard exponential atmospheric density
            rho = 1.225 * math.exp(-alt_km * 1000.0 / 7200.0)
            v_ms = max(100.0, 7500.0 - 8.0 * t)
            rows.append({
                "time_s": float(t),
                "altitude_km": alt_km,
                "altitude_m": alt_km * 1000.0,
                "speed_relative_ms": v_ms,
                "velocity_kms": v_ms / 1000.0,
                "density_kg_m3": rho,
                "temperature_k": 220.0,
            })

    return rows


def cmd_flux(args) -> int:
    """Evaluate aerothermal heat flux history across trajectory."""
    print("=" * 80)
    print("STARSHIP REENTRY AEROTHERMAL FLUX EVALUATION (SUTTON-GRAVES / DETRA-KEMP-RIDDELL)")
    print("=" * 80)

    traj = load_reentry_trajectory_data(args.trajectory)
    print(f"[*] Ingested {len(traj)} trajectory states from entry interface to landing.")

    times = [r["time_s"] for r in traj]
    alts = [r["altitude_km"] for r in traj]
    vels = [r["velocity_kms"] for r in traj]

    q_stag_list = []
    q_wind_list = []
    t_rad_list = []

    for r in traj:
        q_s = compute_sutton_graves_heat_flux(r["density_kg_m3"], r["speed_relative_ms"], nose_radius_m=4.5)
        q_w = compute_windward_acreage_flux(q_s, angle_of_attack_deg=40.0)
        t_rad = compute_radiative_equilibrium_temp(q_w, emissivity=0.85)

        q_stag_list.append(q_s / 1e6)  # MW/m^2
        q_wind_list.append(q_w / 1e6)  # MW/m^2
        t_rad_list.append(t_rad)

    peak_stag = max(q_stag_list)
    peak_wind = max(q_wind_list)
    peak_trad = max(t_rad_list)

    idx_peak = q_stag_list.index(peak_stag)
    t_peak = times[idx_peak]
    alt_peak = alts[idx_peak]
    vel_peak = vels[idx_peak]

    # Integrated heat load Q = integral q dt [MJ / m^2]
    tot_stag_mj = 0.0
    tot_wind_mj = 0.0
    for i in range(1, len(times)):
        dt = times[i] - times[i - 1]
        tot_stag_mj += 0.5 * (q_stag_list[i] + q_stag_list[i - 1]) * dt
        tot_wind_mj += 0.5 * (q_wind_list[i] + q_wind_list[i - 1]) * dt

    print(f"\n[+] Aerothermal Heating Results:")
    print(f"    Peak Stagnation Heat Flux:         {peak_stag:.3f} MW/m²")
    print(f"    Peak Windward Acreage Flux:        {peak_wind:.3f} MW/m²")
    print(f"    Peak Radiative Equilibrium Temp:   {peak_trad:.1f} K ({peak_trad - 273.15:.1f} °C)")
    print(f"    Epoch of Peak Heating:             T+{t_peak:.1f} s")
    print(f"    Altitude of Peak Heating:          {alt_peak:.1f} km")
    print(f"    Relative Speed at Peak:            {vel_peak:.2f} km/s (Mach ~{vel_peak*1000/300:.1f})")
    print(f"    Integrated Stagnation Heat Load:   {tot_stag_mj:.1f} MJ/m²")
    print(f"    Integrated Windward Heat Load:     {tot_wind_mj:.1f} MJ/m²")
    print("=" * 80 + "\n")
    return 0


def cmd_solve_1d(args) -> int:
    """Execute 1D transient thermal conduction through composite TPS stack."""
    print("=" * 80)
    print("STARSHIP 1D TRANSIENT TPS THERMAL CONDUCTION SOLVER (TDMA IMPLICIT)")
    print("=" * 80)

    traj = load_reentry_trajectory_data(args.trajectory)
    times = [r["time_s"] for r in traj]
    alts = [r["altitude_km"] for r in traj]
    vels = [r["velocity_kms"] for r in traj]

    q_stag_mw = []
    q_wind_w = []
    for r in traj:
        q_s = compute_sutton_graves_heat_flux(r["density_kg_m3"], r["speed_relative_ms"], nose_radius_m=4.5)
        q_w = compute_windward_acreage_flux(q_s, angle_of_attack_deg=40.0)
        q_stag_mw.append(q_s / 1e6)
        q_wind_w.append(q_w)

    tile_thk_m = args.tile_thickness / 1000.0
    mesh = generate_thermal_stack_mesh(tile_thickness_m=tile_thk_m)
    solver = TransientThermalSolver1D(mesh)
    solution = solver.solve_trajectory(times, q_wind_w)
    assessment = evaluate_bondline_margins(solution)

    print(f"\n[+] Thermal Stack Parameters:")
    print(f"    Silica Tile Thickness:             {args.tile_thickness:.1f} mm")
    print(f"    SIP/RTV Layer Thickness:           2.5 mm")
    print(f"    Stainless Steel Substrate:         4.0 mm")
    print(f"    Total Stack Depth:                 {mesh.total_thickness_m*1000.0:.1f} mm")
    print(f"    Total Discretization Nodes:        {mesh.total_nodes}")

    print(f"\n[+] Transient Thermal Response Results:")
    print(f"    Peak Outer Surface Temp:           {solution.peak_surface_temp_k:.1f} K ({solution.peak_surface_temp_k - 273.15:.1f} °C)")
    print(f"    Time of Peak Surface Temp:         T+{solution.time_of_peak_surface_s:.1f} s")
    print(f"    Peak RTV Bondline Temp:            {solution.peak_bondline_temp_k:.1f} K ({solution.peak_bondline_temp_k - 273.15:.1f} °C)")
    print(f"    Time of Peak Bondline Temp:        T+{solution.time_of_peak_bondline_s:.1f} s")
    print(f"    Heat Soak Thermal Lag:             {solution.heat_soak_lag_s:.1f} seconds")
    print(f"    Allowable RTV Bondline Limit:      {RTV_BONDLINE_LIMIT_K:.1f} K ({RTV_BONDLINE_LIMIT_K - 273.15:.1f} °C)")
    print(f"    Bondline Temperature Margin:       {assessment.temperature_margin_k:.1f} K")
    print(f"    Thermal Margin of Safety:          {assessment.margin_of_safety:+.3f}")
    status_str = "PASS (POSITIVE MARGIN)" if assessment.is_acceptable else "FAIL (BONDLINE OVERHEAT)"
    print(f"    Compliance Status:                 {status_str}")
    print("=" * 80 + "\n")

    output_dir = args.output or os.path.join("output", "phase9")
    os.makedirs(output_dir, exist_ok=True)

    # Export history CSV
    csv_path = os.path.join(output_dir, "reentry_thermal_history.csv")
    q_wind_mw = [q / 1e6 for q in q_wind_w]
    export_thermal_history_csv(times, alts, vels, q_stag_mw, q_wind_mw, solution, csv_path)
    print(f"[+] Thermal history CSV exported to: {csv_path}")

    # Export summary JSON
    json_path = os.path.join(output_dir, "tps_bondline_margin_summary.json")
    with open(json_path, "w") as f:
        json.dump(assessment.to_dict(), f, indent=2)
    print(f"[+] Margin summary JSON exported to: {json_path}")
    return 0


def cmd_trade(args) -> int:
    """Run tile thickness sizing trade study (15mm to 40mm)."""
    print("=" * 80)
    print("PHASE 9 TILE THICKNESS SIZING TRADE STUDY")
    print("=" * 80)

    traj = load_reentry_trajectory_data(args.trajectory)
    times = [r["time_s"] for r in traj]
    q_wind_w = []
    for r in traj:
        q_s = compute_sutton_graves_heat_flux(r["density_kg_m3"], r["speed_relative_ms"], nose_radius_m=4.5)
        q_w = compute_windward_acreage_flux(q_s, angle_of_attack_deg=40.0)
        q_wind_w.append(q_w)

    thicknesses = [15.0, 18.0, 22.0, 25.0, 28.0, 32.0, 36.0, 40.0]
    results = run_tile_thickness_trade_study(times, q_wind_w, thicknesses)

    print(f"{'Thickness [mm]':<16} | {'Peak Surf [°C]':<15} | {'Peak Bond [°C]':<15} | {'Margin [K]':<12} | {'MoS':<8} | {'Status':<10}")
    print("-" * 88)

    for r in results:
        status = "ACCEPT" if r["is_acceptable"] else "OVERHEAT"
        print(f"{r['tile_thickness_mm']:<16.1f} | {r['peak_surface_temp_degC']:<15.1f} | {r['peak_bondline_temp_degC']:<15.1f} | {r['temperature_margin_K']:<12.1f} | {r['margin_of_safety']:<+8.3f} | {status:<10}")

    output_dir = args.output or os.path.join("output", "phase9")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "tile_thickness_trade_study.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Trade study exported to: {csv_path}\n")
    return 0


def cmd_sensitivity(args) -> int:
    """Run atmospheric density sensitivity study (+/- 20%)."""
    print("=" * 80)
    print("PHASE 9 ATMOSPHERIC DENSITY UNCERTAINTY QUANTIFICATION (±20%)")
    print("=" * 80)

    traj = load_reentry_trajectory_data(args.trajectory)
    results = run_density_sensitivity_study(traj, [0.80, 0.90, 1.00, 1.10, 1.20])

    print(f"{'Perturbation':<14} | {'Peak Flux [MW/m²]':<18} | {'Heat Load [MJ/m²]':<18} | {'Peak Surf [K]':<14} | {'Peak Bond [K]':<14} | {'Margin [K]':<10}")
    print("-" * 98)

    for r in results:
        sign = "+" if r["density_perturbation_percent"] > 0 else ""
        label = f"{sign}{r['density_perturbation_percent']:.0f}%"
        print(f"{label:<14} | {r['peak_heat_flux_MW_m2']:<18.3f} | {r['integrated_heat_load_MJ_m2']:<18.2f} | {r['peak_surface_temp_K']:<14.1f} | {r['peak_bondline_temp_K']:<14.1f} | {r['bondline_margin_K']:<10.1f}")

    output_dir = args.output or os.path.join("output", "phase9")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "density_sensitivity_study.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Sensitivity results exported to: {csv_path}\n")
    return 0


def cmd_all(args) -> int:
    """Run full Phase 9 execution suite with diagnostic plots."""
    print("=" * 80)
    print("PHASE 9 AEROTHERMAL REENTRY & TPS MODEL — COMPLETE BATCH SUITE")
    print("=" * 80)

    traj = load_reentry_trajectory_data(args.trajectory)
    times = [r["time_s"] for r in traj]
    alts = [r["altitude_km"] for r in traj]
    vels = [r["velocity_kms"] for r in traj]

    q_stag_mw = []
    q_wind_w = []
    for r in traj:
        q_s = compute_sutton_graves_heat_flux(r["density_kg_m3"], r["speed_relative_ms"], nose_radius_m=4.5)
        q_w = compute_windward_acreage_flux(q_s, angle_of_attack_deg=40.0)
        q_stag_mw.append(q_s / 1e6)
        q_wind_w.append(q_w)
    q_wind_mw = [q / 1e6 for q in q_wind_w]

    # 1. 1D Transient Solve
    mesh = generate_thermal_stack_mesh(tile_thickness_m=0.028)
    solver = TransientThermalSolver1D(mesh)
    solution = solver.solve_trajectory(times, q_wind_w)
    assessment = evaluate_bondline_margins(solution)

    # 2. Trade study
    thickness_results = run_tile_thickness_trade_study(times, q_wind_w)

    # 3. Sensitivity study
    sensitivity_results = run_density_sensitivity_study(traj)

    output_dir = args.output or os.path.join("output", "phase9")
    os.makedirs(output_dir, exist_ok=True)

    # Export artifacts
    csv_history = os.path.join(output_dir, "reentry_thermal_history.csv")
    export_thermal_history_csv(times, alts, vels, q_stag_mw, q_wind_mw, solution, csv_history)

    summary_json = os.path.join(output_dir, "tps_bondline_margin_summary.json")
    with open(summary_json, "w") as f:
        json.dump(assessment.to_dict(), f, indent=2)

    trade_csv = os.path.join(output_dir, "tile_thickness_trade_study.csv")
    with open(trade_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(thickness_results[0].keys()))
        writer.writeheader()
        writer.writerows(thickness_results)

    sens_csv = os.path.join(output_dir, "density_sensitivity_study.csv")
    with open(sens_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sensitivity_results[0].keys()))
        writer.writeheader()
        writer.writerows(sensitivity_results)

    # Plots
    plot_png = os.path.join(output_dir, "thermal_profile_plots.png")
    generate_thermal_diagnostic_plots(times, alts, q_stag_mw, q_wind_mw, solution, thickness_results, plot_png)

    print("\n" + "=" * 80)
    print("PHASE 9 BATCH EXECUTION SUMMARY")
    print("=" * 80)
    print(f"  Peak Stagnation Heat Flux:         {max(q_stag_mw):.3f} MW/m²")
    print(f"  Peak Windward Heat Flux:           {max(q_wind_mw):.3f} MW/m²")
    print(f"  Peak Tile Surface Temp:            {solution.peak_surface_temp_k:.1f} K ({solution.peak_surface_temp_k - 273.15:.1f} °C)")
    print(f"  Peak RTV Bondline Temp:            {solution.peak_bondline_temp_k:.1f} K ({solution.peak_bondline_temp_k - 273.15:.1f} °C)")
    print(f"  RTV Bondline Temperature Margin:   {assessment.temperature_margin_k:.1f} K (Limit: {RTV_BONDLINE_LIMIT_K:.1f} K)")
    print(f"  Heat Soak Thermal Diffusion Lag:   {solution.heat_soak_lag_s:.1f} seconds")
    print(f"  Thermal History CSV:               {csv_history}")
    print(f"  Diagnostic 4-Panel Plot:           {plot_png}")
    print(f"  Margin Summary JSON:               {summary_json}")
    print("=" * 80 + "\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Starship Phase 9 Aerothermal Reentry & TPS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # flux
    p_flux = subparsers.add_parser("flux", help="Evaluate stagnation and windward heat flux")
    p_flux.add_argument("--trajectory", default=None, help="Path to entry trajectory CSV")
    p_flux.add_argument("--output", default="output/phase9", help="Output directory")

    # solve-1d
    p_sol = subparsers.add_parser("solve-1d", help="Execute 1D transient conduction solve")
    p_sol.add_argument("--trajectory", default=None, help="Path to entry trajectory CSV")
    p_sol.add_argument("--tile-thickness", type=float, default=28.0, help="Tile thickness in mm")
    p_sol.add_argument("--output", default="output/phase9", help="Output directory")

    # trade
    p_trade = subparsers.add_parser("trade", help="Run tile thickness sizing study")
    p_trade.add_argument("--trajectory", default=None, help="Path to entry trajectory CSV")
    p_trade.add_argument("--output", default="output/phase9", help="Output directory")

    # sensitivity
    p_sens = subparsers.add_parser("sensitivity", help="Run atmospheric density sensitivity study")
    p_sens.add_argument("--trajectory", default=None, help="Path to entry trajectory CSV")
    p_sens.add_argument("--output", default="output/phase9", help="Output directory")

    # all
    p_all = subparsers.add_parser("all", help="Run full Phase 9 batch suite")
    p_all.add_argument("--trajectory", default=None, help="Path to entry trajectory CSV")
    p_all.add_argument("--output", default="output/phase9", help="Output directory")

    args = parser.parse_args()

    if args.command == "flux":
        sys.exit(cmd_flux(args))
    elif args.command == "solve-1d":
        sys.exit(cmd_solve_1d(args))
    elif args.command == "trade":
        sys.exit(cmd_trade(args))
    elif args.command == "sensitivity":
        sys.exit(cmd_sensitivity(args))
    elif args.command == "all":
        sys.exit(cmd_all(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
