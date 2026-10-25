"""
Reentry Machine-Readable Serialization & Reporting Module
=========================================================
Phase 6: Exporters for trajectory CSVs, aerothermal history, event logs,
control commands, terminal splashdown assessments, and uncertainty summaries.
"""

import os
import csv
import json
from typing import Dict, Any, List
import numpy as np

from .dynamics import ReentrySimulationResult, ReentryTrajectoryStep
from .events import ReentryEventRecord
from .splashdown import TerminalSplashdownAssessment
from .uncertainty import SensitivityResult, MonteCarloSummary


def export_trajectory_csv(steps: List[ReentryTrajectoryStep], file_path: str):
    """Exports primary 3-DOF trajectory time series to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "epoch_utc",
            "x_eci_m", "y_eci_m", "z_eci_m",
            "vx_eci_ms", "vy_eci_ms", "vz_eci_ms",
            "vx_rel_ms", "vy_rel_ms", "vz_rel_ms",
            "altitude_m", "geodetic_lat_deg", "geodetic_lon_deg",
            "speed_inertial_ms", "speed_relative_ms", "mach",
            "flight_path_angle_deg", "dynamic_pressure_pa",
            "density_kg_m3", "temperature_k", "pressure_pa",
            "drag_force_n", "lift_force_n", "drag_accel_ms2", "lift_accel_ms2",
            "total_accel_ms2", "apparent_g_load",
            "stagnation_heat_flux_mw_m2", "windward_heat_flux_mw_m2",
            "cumulative_heat_load_mj_m2", "radiative_eq_temp_deg_c",
            "bank_angle_cmd_deg", "crossrange_error_km", "downrange_error_km"
        ])
        for s in steps:
            writer.writerow([
                f"{s.time_s:.3f}", s.epoch_utc,
                f"{s.r_eci[0]:.2f}", f"{s.r_eci[1]:.2f}", f"{s.r_eci[2]:.2f}",
                f"{s.v_eci[0]:.4f}", f"{s.v_eci[1]:.4f}", f"{s.v_eci[2]:.4f}",
                f"{s.v_rel_eci[0]:.4f}", f"{s.v_rel_eci[1]:.4f}", f"{s.v_rel_eci[2]:.4f}",
                f"{s.altitude_m:.2f}", f"{s.geodetic_lat_deg:.5f}", f"{s.geodetic_lon_deg:.5f}",
                f"{s.speed_inertial_ms:.2f}", f"{s.speed_relative_ms:.2f}", f"{s.mach:.2f}",
                f"{s.flight_path_angle_deg:.3f}", f"{s.dynamic_pressure_pa:.1f}",
                f"{s.density_kg_m3:.6e}", f"{s.temperature_k:.2f}", f"{s.pressure_pa:.2f}",
                f"{s.drag_force_n:.1f}", f"{s.lift_force_n:.1f}",
                f"{s.drag_accel_ms2:.4f}", f"{s.lift_accel_ms2:.4f}",
                f"{s.total_accel_ms2:.4f}", f"{s.apparent_g_load:.3f}",
                f"{s.stagnation_heat_flux_mw_m2:.4f}", f"{s.windward_heat_flux_mw_m2:.4f}",
                f"{s.cumulative_heat_load_mj_m2:.3f}", f"{s.radiative_equilibrium_temp_deg_c:.1f}",
                f"{s.bank_angle_cmd_deg:.2f}", f"{s.crossrange_error_km:.2f}", f"{s.downrange_error_km:.2f}"
            ])


def export_aerothermal_history_csv(steps: List[ReentryTrajectoryStep], file_path: str):
    """Exports dedicated aerothermal heating time series to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "altitude_km", "speed_rel_ms", "mach",
            "density_kg_m3", "dynamic_pressure_kpa",
            "stagnation_heat_flux_mw_m2", "stagnation_heat_flux_w_cm2",
            "windward_heat_flux_mw_m2", "cumulative_heat_load_mj_m2",
            "radiative_eq_temp_k", "radiative_eq_temp_deg_c"
        ])
        for s in steps:
            writer.writerow([
                f"{s.time_s:.2f}", f"{s.altitude_m / 1000.0:.3f}", f"{s.speed_relative_ms:.2f}",
                f"{s.mach:.2f}", f"{s.density_kg_m3:.5e}", f"{s.dynamic_pressure_pa / 1000.0:.3f}",
                f"{s.stagnation_heat_flux_mw_m2:.4f}", f"{s.stagnation_heat_flux_mw_m2 * 100.0:.2f}",
                f"{s.windward_heat_flux_mw_m2:.4f}", f"{s.cumulative_heat_load_mj_m2:.3f}",
                f"{s.radiative_equilibrium_temp_deg_c + 273.15:.2f}", f"{s.radiative_equilibrium_temp_deg_c:.1f}"
            ])


def export_event_log_csv(events: List[ReentryEventRecord], file_path: str):
    """Exports discrete mission event log to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "event_name", "altitude_km",
            "geodetic_lat_deg", "geodetic_lon_deg",
            "speed_rel_ms", "mach", "dynamic_pressure_kpa",
            "apparent_g_load", "stagnation_heat_flux_mw_m2",
            "cumulative_heat_load_mj_m2"
        ])
        for ev in events:
            writer.writerow([
                f"{ev.time_s:.2f}", ev.event_name, f"{ev.altitude_m / 1000.0:.3f}",
                f"{ev.geodetic_lat_deg:.4f}", f"{ev.geodetic_lon_deg:.4f}",
                f"{ev.speed_rel_ms:.2f}", f"{ev.mach:.2f}", f"{ev.dynamic_pressure_pa / 1000.0:.2f}",
                f"{ev.apparent_g_load:.2f}", f"{ev.stagnation_heat_flux_mw_m2:.4f}",
                f"{ev.cumulative_heat_load_mj_m2:.3f}"
            ])


def export_control_history_csv(steps: List[ReentryTrajectoryStep], file_path: str):
    """Exports guidance control commands and error signals to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s", "altitude_km", "dynamic_pressure_kpa",
            "bank_angle_cmd_deg", "angle_of_attack_deg",
            "crossrange_error_km", "downrange_error_km", "guidance_active"
        ])
        for s in steps:
            writer.writerow([
                f"{s.time_s:.2f}", f"{s.altitude_m / 1000.0:.2f}", f"{s.dynamic_pressure_pa / 1000.0:.2f}",
                f"{s.bank_angle_cmd_deg:.2f}", f"{s.angle_of_attack_deg:.2f}",
                f"{s.crossrange_error_km:.2f}", f"{s.downrange_error_km:.2f}",
                s.guidance_active
            ])


def export_sensitivity_csv(sensitivities: List[SensitivityResult], file_path: str):
    """Exports OAT sensitivity derivatives to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "parameter", "units", "baseline_value", "perturbation", "perturbed_value",
            "delta_peak_q_kpa", "delta_peak_g", "delta_peak_heat_mw_m2",
            "delta_total_heat_mj_m2", "delta_impact_time_s", "delta_miss_dist_km"
        ])
        for s in sensitivities:
            writer.writerow([
                s.parameter, s.units, f"{s.baseline_value:.4f}", f"{s.perturbation:.4f}", f"{s.perturbed_value:.4f}",
                f"{s.delta_peak_q_kpa:.3f}", f"{s.delta_peak_g:.3f}", f"{s.delta_peak_heat_mw_m2:.4f}",
                f"{s.delta_total_heat_mj_m2:.3f}", f"{s.delta_impact_time_s:.2f}", f"{s.delta_miss_dist_km:.2f}"
            ])


def export_monte_carlo_csv(samples: List[Dict[str, Any]], file_path: str):
    """Exports raw Monte Carlo realization samples to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    if not samples:
        return
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        keys = list(samples[0].keys())
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(samples)


def export_json_summary(data: Dict[str, Any], file_path: str):
    """Exports structured summary dictionary to indented JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
