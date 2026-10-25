"""
Command-line interface (CLI) for Starship Phase 7 Terminal Landing Dynamics.

Supported commands:
  python -m src.phase7 validate --config config/phase7/synthetic_landing_baseline.yaml
  python -m src.phase7 run --config config/phase7/synthetic_landing_baseline.yaml
  python -m src.phase7 compare --baseline config/phase7/synthetic_landing_baseline.yaml --variant config/phase7/synthetic_landing_low_thrust.yaml
  python -m src.phase7 all
"""

import argparse
import sys
import os
import yaml
import json
from typing import Dict, Any

from src.landing.simulation import LandingSimulation
from src.landing.uncertainty import MonteCarloSimulator
from src.landing.reporting import generate_plots


def load_yaml_config(path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def cmd_validate(args) -> int:
    """Validate scenario configuration schema and physical bounds."""
    print(f"[*] Validating configuration: {args.config}")
    try:
        cfg = load_yaml_config(args.config)
        # Check required fields
        required = ["scenario_id", "initial_state", "vehicle", "propulsion", "guidance"]
        for r in required:
            if r not in cfg:
                print(f"[ERROR] Missing required section: {r}")
                return 1

        init = cfg["initial_state"]
        if init.get("position_m") is None or init.get("velocity_mps") is None:
            print("[ERROR] Position or velocity cannot be null")
            return 1

        print(f"[+] Configuration '{cfg['scenario_id']}' is structurally VALID.")
        return 0
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}")
        return 1


def cmd_run(args) -> int:
    """Execute single simulation scenario and export artifacts."""
    print(f"[*] Running scenario from: {args.config}")
    try:
        cfg = load_yaml_config(args.config)
        output_dir = args.output or os.path.join("output", "phase7")

        sim = LandingSimulation(cfg)
        history, report, event_log = sim.run()

        exported = sim.export_results(output_dir, history, report, event_log)
        print(f"[+] Simulation completed: {report.outcome_classification}")
        print(f"    Touchdown Time:     {report.touchdown_time_s:.2f} s")
        print(f"    Terminal Vz:        {report.terminal_vertical_speed_mps:.2f} m/s")
        print(f"    Terminal Vx:        {report.terminal_horizontal_speed_mps:.2f} m/s")
        print(f"    Terminal Pitch:     {report.terminal_pitch_deg:.2f} deg")
        print(f"    Pad Miss Distance:  {report.miss_distance_m:.2f} m")
        print(f"    Propellant Used:    {report.propellant_consumed_kg:.1f} kg")
        print(f"    Burn Duration:      {report.burn_duration_s:.2f} s")
        print(f"    Peak Deceleration:  {report.peak_apparent_g:.2f} g")

        # Generate plots if requested
        plot_path = os.path.join(output_dir, f"{sim.scenario_id}_plots.png")
        generate_plots(history, report, plot_path, title_prefix=sim.scenario_id)
        print(f"[+] Artifacts written to: {output_dir}")
        return 0
    except Exception as e:
        print(f"[ERROR] Run failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_compare(args) -> int:
    """Compare nominal baseline against variant failure or anomaly scenario."""
    print(f"[*] Comparing Baseline: {args.baseline} against Variant: {args.variant}")
    try:
        cfg_base = load_yaml_config(args.baseline)
        cfg_var = load_yaml_config(args.variant)
        output_dir = args.output or os.path.join("output", "phase7")

        sim_base = LandingSimulation(cfg_base)
        _, rep_base, _ = sim_base.run()

        sim_var = LandingSimulation(cfg_var)
        _, rep_var, _ = sim_var.run()

        print("\n" + "=" * 70)
        print("SCENARIO COMPARISON MATRIX")
        print("=" * 70)
        print(f"{'Metric':<32} | {'Baseline':<16} | {'Variant':<16}")
        print("-" * 70)
        print(f"{'Scenario ID':<32} | {sim_base.scenario_id:<16} | {sim_var.scenario_id:<16}")
        print(f"{'Outcome Classification':<32} | {rep_base.outcome_classification:<16} | {rep_var.outcome_classification:<16}")
        print(f"{'Terminal Vz [m/s]':<32} | {rep_base.terminal_vertical_speed_mps:<16.2f} | {rep_var.terminal_vertical_speed_mps:<16.2f}")
        print(f"{'Terminal Vx [m/s]':<32} | {rep_base.terminal_horizontal_speed_mps:<16.2f} | {rep_var.terminal_horizontal_speed_mps:<16.2f}")
        print(f"{'Miss Distance [m]':<32} | {rep_base.miss_distance_m:<16.2f} | {rep_var.miss_distance_m:<16.2f}")
        print(f"{'Propellant Used [kg]':<32} | {rep_base.propellant_consumed_kg:<16.1f} | {rep_var.propellant_consumed_kg:<16.1f}")
        print(f"{'Peak Apparent Load [g]':<32} | {rep_base.peak_apparent_g:<16.2f} | {rep_var.peak_apparent_g:<16.2f}")
        print("=" * 70 + "\n")

        # Export comparison summary
        comp_summary = {
            "baseline": rep_base.to_dict(),
            "variant": rep_var.to_dict(),
        }
        comp_path = os.path.join(output_dir, f"comparison_{sim_base.scenario_id}_vs_{sim_var.scenario_id}.json")
        os.makedirs(output_dir, exist_ok=True)
        with open(comp_path, "w") as f:
            json.dump(comp_summary, f, indent=2)
        print(f"[+] Comparison JSON exported to: {comp_path}")
        return 0
    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")
        return 1


def cmd_all(args) -> int:
    """Execute all nominal, anomaly, and Monte Carlo scenarios."""
    print("=" * 80)
    print("PHASE 7 TERMINAL LANDING DYNAMICS — COMPLETE BATCH SUITE")
    print("=" * 80)

    configs = [
        "config/phase7/synthetic_landing_baseline.yaml",
        "config/phase7/synthetic_landing_low_thrust.yaml",
        "config/phase7/synthetic_landing_ignition_delay.yaml",
        "config/phase7/synthetic_landing_controlled_flip.yaml",
    ]

    output_dir = args.output or os.path.join("output", "phase7")

    for c in configs:
        print(f"\n---> Executing: {c}")
        args_run = argparse.Namespace(config=c, output=output_dir)
        ret = cmd_run(args_run)
        if ret != 0:
            print(f"[ERROR] Execution failed for {c}")
            return ret

    # Run Monte Carlo ensemble
    mc_cfg_path = "config/phase7/synthetic_landing_uncertainty.yaml"
    if os.path.exists(mc_cfg_path):
        print(f"\n---> Executing Monte Carlo Ensemble: {mc_cfg_path}")
        mc_cfg = load_yaml_config(mc_cfg_path)
        base_cfg = load_yaml_config(mc_cfg.get("base_config", configs[0]))
        mc_sim = MonteCarloSimulator(mc_cfg)
        samples, summary = mc_sim.run_ensemble(base_cfg)
        mc_sim.export_results(output_dir, samples, summary)
        print(f"[+] Monte Carlo complete: {summary['sample_count']} samples, Success Fraction: {summary['success_fraction']}")

    print("\n" + "=" * 80)
    print("ALL PHASE 7 SCENARIOS AND ENSEMBLES COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Starship Phase 7 Terminal Landing Dynamics CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate scenario configuration")
    p_val.add_argument("--config", required=True, help="Path to scenario YAML config")

    # run
    p_run = subparsers.add_parser("run", help="Run scenario simulation")
    p_run.add_argument("--config", required=True, help="Path to scenario YAML config")
    p_run.add_argument("--output", default="output/phase7", help="Output directory")

    # compare
    p_comp = subparsers.add_parser("compare", help="Compare two scenarios")
    p_comp.add_argument("--baseline", required=True, help="Path to baseline YAML")
    p_comp.add_argument("--variant", required=True, help="Path to variant YAML")
    p_comp.add_argument("--output", default="output/phase7", help="Output directory")

    # all
    p_all = subparsers.add_parser("all", help="Run all standard scenarios and Monte Carlo")
    p_all.add_argument("--output", default="output/phase7", help="Output directory")

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(cmd_validate(args))
    elif args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "compare":
        sys.exit(cmd_compare(args))
    elif args.command == "all":
        sys.exit(cmd_all(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
