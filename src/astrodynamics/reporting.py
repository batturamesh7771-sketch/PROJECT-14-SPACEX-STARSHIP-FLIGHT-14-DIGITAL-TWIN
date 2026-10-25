"""
Phase 5 Output Exporters, Serialization & Metadata Logging
==========================================================
Exports trajectory time-series, orbital elements, detected events,
GMAT cross-checks, sensitivity studies, and Monte Carlo ensembles
to structured CSV and JSON files following project schemas.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List
import numpy as np

from .propagator import PropagationResult
from .uncertainty import SensitivityResult, MonteCarloSummary


def export_trajectory_csv(result: PropagationResult, filepath: str):
    """Exports Cartesian state history to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "epoch_utc",
            "x_m", "y_m", "z_m",
            "vx_m_s", "vy_m_s", "vz_m_s",
            "radius_km", "speed_km_s", "altitude_km",
            "specific_energy_mj_kg", "angular_momentum_m2_s"
        ])
        for i, t in enumerate(result.times_s):
            r = result.states_r[i]
            v = result.states_v[i]
            r_km = float(np.linalg.norm(r)) / 1000.0
            v_kms = float(np.linalg.norm(v)) / 1000.0
            epoch_str = result.epochs[i].isoformat() if i < len(result.epochs) else ""
            writer.writerow([
                f"{t:.2f}", epoch_str,
                f"{r[0]:.3f}", f"{r[1]:.3f}", f"{r[2]:.3f}",
                f"{v[0]:.4f}", f"{v[1]:.4f}", f"{v[2]:.4f}",
                f"{r_km:.3f}", f"{v_kms:.4f}", f"{result.altitudes_km[i]:.3f}",
                f"{result.energies_mj_kg[i]:.6f}", f"{result.angular_momenta[i]:.3f}"
            ])


def export_elements_csv(result: PropagationResult, filepath: str):
    """Exports Keplerian elements history to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "epoch_utc",
            "semi_major_axis_km", "eccentricity",
            "inclination_deg", "raan_deg", "arg_periapsis_deg", "true_anomaly_deg",
            "perigee_altitude_km", "apogee_altitude_km", "period_min"
        ])
        for i, t in enumerate(result.times_s):
            if i < len(result.elements_history):
                elem = result.elements_history[i]
                epoch_str = result.epochs[i].isoformat() if i < len(result.epochs) else ""
                sma_km = elem.get("semi_major_axis_m", 0.0) / 1000.0
                ecc = elem.get("eccentricity", 0.0)
                inc = elem.get("inclination_deg", 0.0)
                raan = elem.get("raan_deg", 0.0)
                argp = elem.get("arg_periapsis_deg", 0.0)
                nu = elem.get("true_anomaly_deg", 0.0)
                hp_km = elem.get("perigee_altitude_m", 0.0) / 1000.0
                ha_km = elem.get("apogee_altitude_m", 0.0) / 1000.0
                per_min = elem.get("period_s", 0.0) / 60.0

                writer.writerow([
                    f"{t:.2f}", epoch_str,
                    f"{sma_km:.3f}", f"{ecc:.6f}",
                    f"{inc:.4f}", f"{raan:.4f}", f"{argp:.4f}", f"{nu:.4f}",
                    f"{hp_km:.3f}", f"{ha_km:.3f}", f"{per_min:.2f}"
                ])


def export_events_csv(result: PropagationResult, filepath: str):
    """Exports detected events to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "epoch_utc", "event_name",
            "altitude_km", "x_m", "y_m", "z_m", "vx_m_s", "vy_m_s", "vz_m_s"
        ])
        for ev in result.events:
            writer.writerow([
                f"{ev.time_s:.2f}", ev.epoch.isoformat(), ev.event_name,
                f"{ev.altitude_spherical_km:.3f}",
                f"{ev.r[0]:.2f}", f"{ev.r[1]:.2f}", f"{ev.r[2]:.2f}",
                f"{ev.v[0]:.2f}", f"{ev.v[1]:.2f}", f"{ev.v[2]:.2f}"
            ])


def export_summary_json(summary_dict: Dict[str, Any], filepath: str):
    """Exports summary dictionary to formatted JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)


def export_sensitivity_csv(sens_results: List[SensitivityResult], filepath: str):
    """Exports deterministic sensitivity results to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "parameter", "nominal_value", "perturbation", "perturbed_value",
            "delta_sma_km", "delta_ecc", "delta_perigee_km", "delta_apogee_km",
            "d_sma_d_param", "d_ecc_d_param"
        ])
        for r in sens_results:
            writer.writerow([
                r.parameter_name, f"{r.nominal_value:.4f}", f"{r.perturbation:.4f}", f"{r.perturbed_value:.4f}",
                f"{r.delta_sma_km:.4f}", f"{r.delta_ecc:.6f}", f"{r.delta_perigee_km:.4f}", f"{r.delta_apogee_km:.4f}",
                f"{r.influence_d_sma:.6f}", f"{r.influence_d_ecc:.8f}"
            ])


def export_monte_carlo_results(mc_summary: MonteCarloSummary, samples_path: str, summary_path: str):
    """Exports Monte Carlo sample realizations and summary statistics."""
    os.makedirs(os.path.dirname(os.path.abspath(samples_path)), exist_ok=True)
    with open(samples_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id", "dr_x_m", "dr_y_m", "dr_z_m", "dv_x_ms", "dv_y_ms", "dv_z_ms",
            "mass_kg", "cd", "final_sma_km", "final_ecc", "final_perigee_km", "final_apogee_km", "period_min"
        ])
        for s in mc_summary.samples:
            writer.writerow([
                s.sample_id,
                f"{s.delta_r[0]:.2f}", f"{s.delta_r[1]:.2f}", f"{s.delta_r[2]:.2f}",
                f"{s.delta_v[0]:.4f}", f"{s.delta_v[1]:.4f}", f"{s.delta_v[2]:.4f}",
                f"{s.mass_kg:.1f}", f"{s.cd:.3f}",
                f"{s.final_sma_km:.3f}", f"{s.final_ecc:.6f}",
                f"{s.final_perigee_km:.3f}", f"{s.final_apogee_km:.3f}", f"{s.final_period_min:.2f}"
            ])

    export_summary_json({
        "sample_count": mc_summary.sample_count,
        "seed": mc_summary.seed,
        "duration_s": mc_summary.duration_s,
        "metrics": mc_summary.metrics
    }, summary_path)


def export_gmat_comparison_csv(comp_dict: Dict[str, Any], filepath: str):
    """Exports GMAT vs Python comparison metrics to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "python_value", "gmat_value", "difference", "error_percent", "status"])
        writer.writerow([
            "semi_major_axis_km",
            f"{comp_dict.get('python_sma_km', 0.0):.4f}",
            f"{comp_dict.get('gmat_sma_km', 0.0):.4f}",
            f"{comp_dict.get('sma_diff_km', 0.0):.4f}",
            f"{comp_dict.get('sma_error_percent', 0.0):.4f}%",
            comp_dict.get("status", "N/A")
        ])
        writer.writerow([
            "eccentricity",
            f"{comp_dict.get('python_ecc', 0.0):.6f}",
            f"{comp_dict.get('gmat_ecc', 0.0):.6f}",
            f"{comp_dict.get('ecc_diff', 0.0):.6f}",
            "-",
            comp_dict.get("status", "N/A")
        ])
        writer.writerow([
            "perigee_radius_km",
            f"{comp_dict.get('python_periapsis_km', 0.0):.4f}",
            f"{comp_dict.get('gmat_periapsis_km', 0.0):.4f}",
            f"{comp_dict.get('periapsis_diff_km', 0.0):.4f}",
            "-",
            comp_dict.get("status", "N/A")
        ])
        writer.writerow([
            "apogee_radius_km",
            f"{comp_dict.get('python_apoapsis_km', 0.0):.4f}",
            f"{comp_dict.get('gmat_apoapsis_km', 0.0):.4f}",
            f"{comp_dict.get('apoapsis_diff_km', 0.0):.4f}",
            "-",
            comp_dict.get("status", "N/A")
        ])
