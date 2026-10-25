"""
Sensitivity study and Monte Carlo uncertainty quantification engine.
"""

from typing import Dict, Any, List, Tuple
import random
import os
import csv
import json
import copy
from src.landing.simulation import LandingSimulation


class MonteCarloSimulator:
    """Executes seeded Monte Carlo parameter ensembles for terminal landing uncertainty."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        mc_cfg = config.get("monte_carlo", {})
        self.sample_count: int = mc_cfg.get("sample_count", 50)
        self.random_seed: int = mc_cfg.get("random_seed", 42)
        self.distributions: Dict[str, Any] = mc_cfg.get("distributions", {})

    def run_ensemble(self, base_sim_config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Run the Monte Carlo ensemble.
        Returns: (sample_records, summary_stats)
        """
        # Set deterministic seed
        rng = random.Random(self.random_seed)

        sample_records: List[Dict[str, Any]] = []
        outcomes_count: Dict[str, int] = {}

        vz_list: List[float] = []
        vx_list: List[float] = []
        prop_list: List[float] = []
        g_list: List[float] = []

        vz_dist = self.distributions.get("initial_vz_mps", {})
        mass_dist = self.distributions.get("initial_mass_kg", {})
        delay_dist = self.distributions.get("ignition_delay_s", {})
        thrust_dist = self.distributions.get("thrust_scale", {})

        for i in range(self.sample_count):
            sample_cfg = copy.deepcopy(base_sim_config)
            sample_cfg["scenario_id"] = f"mc_sample_{i:03d}"
            sample_cfg["integrator"]["dt_s"] = 0.02  # slightly larger dt for faster ensemble execution

            # Perturb initial vz
            if vz_dist.get("type") == "normal":
                vz_pert = rng.gauss(vz_dist.get("mean", -95.0), vz_dist.get("std_dev", 4.0))
            else:
                vz_pert = -95.0
            sample_cfg["initial_state"]["velocity_mps"][1] = vz_pert

            # Perturb initial mass
            if mass_dist.get("type") == "normal":
                mass_pert = rng.gauss(mass_dist.get("mean", 124980.0), mass_dist.get("std_dev", 1500.0))
            else:
                mass_pert = 124980.0
            sample_cfg["initial_state"]["mass_kg"] = mass_pert

            # Perturb ignition delay
            if delay_dist.get("type") == "uniform":
                delay_pert = rng.uniform(delay_dist.get("min", 0.6), delay_dist.get("max", 1.6))
            else:
                delay_pert = 1.0
            sample_cfg["propulsion"]["ignition_delay_s"] = delay_pert

            # Perturb thrust scale
            if thrust_dist.get("type") == "uniform":
                t_scale = rng.uniform(thrust_dist.get("min", 0.95), thrust_dist.get("max", 1.05))
            else:
                t_scale = 1.0
            nom_thrust = sample_cfg["propulsion"]["thrust_per_engine_nominal_N"]
            sample_cfg["propulsion"]["thrust_per_engine_nominal_N"] = nom_thrust * t_scale

            # Run single simulation
            sim = LandingSimulation(sample_cfg)
            _, report, _ = sim.run()

            outcome = report.outcome_classification
            outcomes_count[outcome] = outcomes_count.get(outcome, 0) + 1

            vz_list.append(report.terminal_vertical_speed_mps)
            vx_list.append(report.terminal_horizontal_speed_mps)
            prop_list.append(report.propellant_consumed_kg)
            g_list.append(report.peak_apparent_g)

            sample_records.append({
                "sample_id": i,
                "initial_vz_mps": round(vz_pert, 2),
                "initial_mass_kg": round(mass_pert, 1),
                "ignition_delay_s": round(delay_pert, 3),
                "thrust_scale": round(t_scale, 3),
                "terminal_vz_mps": report.terminal_vertical_speed_mps,
                "terminal_vx_mps": report.terminal_horizontal_speed_mps,
                "propellant_consumed_kg": report.propellant_consumed_kg,
                "peak_apparent_g": report.peak_apparent_g,
                "outcome_classification": outcome
            })

        # Summary statistics
        def stats(vals):
            if not vals:
                return {}
            mean = sum(vals) / len(vals)
            variance = sum((x - mean) ** 2 for x in vals) / len(vals)
            return {
                "mean": round(mean, 3),
                "min": round(min(vals), 3),
                "max": round(max(vals), 3),
                "std_dev": round(variance ** 0.5, 3)
            }

        summary = {
            "sample_count": self.sample_count,
            "random_seed": self.random_seed,
            "outcome_counts": outcomes_count,
            "success_fraction": round(outcomes_count.get("SUCCESS_CANDIDATE", 0) / self.sample_count, 3),
            "terminal_vertical_speed_mps": stats(vz_list),
            "terminal_horizontal_speed_mps": stats(vx_list),
            "propellant_consumed_kg": stats(prop_list),
            "peak_apparent_g": stats(g_list),
            "note": "Success fraction is conditional on assumed input distributions and educational simulation models."
        }

        return sample_records, summary

    def export_results(self, output_dir: str,
                       sample_records: List[Dict[str, Any]],
                       summary: Dict[str, Any]) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)

        samples_csv = os.path.join(output_dir, "monte_carlo_samples.csv")
        with open(samples_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "sample_id", "initial_vz_mps", "initial_mass_kg", "ignition_delay_s",
                "thrust_scale", "terminal_vz_mps", "terminal_vx_mps", "propellant_consumed_kg",
                "peak_apparent_g", "outcome_classification"
            ])
            writer.writeheader()
            for r in sample_records:
                writer.writerow(r)

        summary_json = os.path.join(output_dir, "monte_carlo_summary.json")
        with open(summary_json, "w") as f:
            json.dump(summary, f, indent=2)

        return {"samples_csv": samples_csv, "summary_json": summary_json}
