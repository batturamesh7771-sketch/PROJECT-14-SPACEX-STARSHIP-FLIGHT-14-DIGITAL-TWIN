"""
Reentry Uncertainty Quantification & Monte Carlo Dispersion Engine
===================================================================
Phase 6: Deterministic One-At-a-Time (OAT) parameter sensitivity analysis
and seeded pseudo-random Monte Carlo trajectory dispersion ensemble.
"""

import math
import copy
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from .constants import (
    DEFAULT_VEHICLE_MASS_KG,
    DEFAULT_REFERENCE_AREA_M2,
    DEFAULT_NOSE_RADIUS_M
)
from .vehicle import ReentryVehicleConfig
from .atmosphere import USStandardAtmosphere1976
from .dynamics import propagate_reentry, ReentrySimulationResult
from .guidance import CrossrangeBankGuidanceController
from src.astrodynamics.state import OrbitalState


@dataclass
class SensitivityResult:
    """Derivative metrics for a single perturbed parameter."""
    parameter: str
    units: str
    baseline_value: float
    perturbation: float
    perturbed_value: float
    delta_peak_q_kpa: float
    delta_peak_g: float
    delta_peak_heat_mw_m2: float
    delta_total_heat_mj_m2: float
    delta_impact_time_s: float
    delta_miss_dist_km: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "units": self.units,
            "baseline_value": self.baseline_value,
            "perturbation": self.perturbation,
            "perturbed_value": self.perturbed_value,
            "delta_peak_q_kpa": self.delta_peak_q_kpa,
            "delta_peak_g": self.delta_peak_g,
            "delta_peak_heat_mw_m2": self.delta_peak_heat_mw_m2,
            "delta_total_heat_mj_m2": self.delta_total_heat_mj_m2,
            "delta_impact_time_s": self.delta_impact_time_s,
            "delta_miss_dist_km": self.delta_miss_dist_km
        }


@dataclass
class MonteCarloSummary:
    """Ensemble statistics across N stochastic reentry realizations."""
    sample_count: int
    completed_count: int
    failed_count: int
    seed: int
    target_hit_fraction: float
    metrics: Dict[str, Dict[str, float]]
    samples: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_count": self.sample_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "seed": self.seed,
            "target_hit_fraction": self.target_hit_fraction,
            "metrics": self.metrics
        }


def run_reentry_sensitivity_study(
    baseline_state: OrbitalState,
    vehicle_config: ReentryVehicleConfig,
    atmosphere: USStandardAtmosphere1976,
    guidance: Optional[CrossrangeBankGuidanceController] = None,
    target_lat_deg: float = -14.0,
    target_lon_deg: float = -15.5,
    target_radius_m: float = 100000.0
) -> List[SensitivityResult]:
    """
    Executes One-At-a-Time (OAT) parameter sensitivity analysis for 8 physical parameters.
    """
    # 1. Nominal baseline run
    base_res = propagate_reentry(
        initial_state=baseline_state,
        vehicle_config=vehicle_config,
        atmosphere=atmosphere,
        guidance=guidance,
        target_lat_deg=target_lat_deg,
        target_lon_deg=target_lon_deg,
        target_radius_m=target_radius_m,
        eval_step_s=2.0
    )

    base_q_kpa = base_res.peak_dynamic_pressure_pa / 1000.0
    base_g = base_res.peak_apparent_g_load
    base_heat = base_res.peak_stagnation_heat_flux_mw_m2
    base_tot_heat = base_res.total_heat_load_mj_m2
    base_time = base_res.impact_time_s
    base_miss = base_res.miss_distance_km

    sensitivities: List[SensitivityResult] = []

    # Parameter perturbations list: (param_name, units, base_val, delta, pert_state, pert_veh, pert_atm)
    # 1. Mass +5000 kg
    veh_m = copy.deepcopy(vehicle_config)
    veh_m.mass_kg += 5000.0
    res_m = propagate_reentry(baseline_state, veh_m, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="vehicle_mass",
        units="kg",
        baseline_value=vehicle_config.mass_kg,
        perturbation=+5000.0,
        perturbed_value=veh_m.mass_kg,
        delta_peak_q_kpa=(res_m.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_m.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_m.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_m.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_m.impact_time_s - base_time,
        delta_miss_dist_km=res_m.miss_distance_km - base_miss
    ))

    # 2. Reference area +5 m^2
    veh_a = copy.deepcopy(vehicle_config)
    veh_a.reference_area_m2 += 5.0
    res_a = propagate_reentry(baseline_state, veh_a, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="reference_area",
        units="m^2",
        baseline_value=vehicle_config.reference_area_m2,
        perturbation=+5.0,
        perturbed_value=veh_a.reference_area_m2,
        delta_peak_q_kpa=(res_a.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_a.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_a.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_a.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_a.impact_time_s - base_time,
        delta_miss_dist_km=res_a.miss_distance_km - base_miss
    ))

    # 3. Drag coefficient +0.10
    veh_cd = copy.deepcopy(vehicle_config)
    veh_cd.cd_hypersonic_70deg += 0.10
    res_cd = propagate_reentry(baseline_state, veh_cd, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="cd_hypersonic",
        units="dimensionless",
        baseline_value=vehicle_config.cd_hypersonic_70deg,
        perturbation=+0.10,
        perturbed_value=veh_cd.cd_hypersonic_70deg,
        delta_peak_q_kpa=(res_cd.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_cd.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_cd.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_cd.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_cd.impact_time_s - base_time,
        delta_miss_dist_km=res_cd.miss_distance_km - base_miss
    ))

    # 4. Lift coefficient +0.05
    veh_cl = copy.deepcopy(vehicle_config)
    veh_cl.cl_hypersonic_70deg += 0.05
    res_cl = propagate_reentry(baseline_state, veh_cl, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="cl_hypersonic",
        units="dimensionless",
        baseline_value=vehicle_config.cl_hypersonic_70deg,
        perturbation=+0.05,
        perturbed_value=veh_cl.cl_hypersonic_70deg,
        delta_peak_q_kpa=(res_cl.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_cl.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_cl.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_cl.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_cl.impact_time_s - base_time,
        delta_miss_dist_km=res_cl.miss_distance_km - base_miss
    ))

    # 5. Density factor +10%
    atm_rho = USStandardAtmosphere1976(density_scale=1.10)
    res_rho = propagate_reentry(baseline_state, vehicle_config, atm_rho, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="atmospheric_density_factor",
        units="scale",
        baseline_value=1.0,
        perturbation=+0.10,
        perturbed_value=1.10,
        delta_peak_q_kpa=(res_rho.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_rho.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_rho.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_rho.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_rho.impact_time_s - base_time,
        delta_miss_dist_km=res_rho.miss_distance_km - base_miss
    ))

    # 6. Nose radius +0.5 m
    veh_rn = copy.deepcopy(vehicle_config)
    veh_rn.nose_radius_m += 0.50
    res_rn = propagate_reentry(baseline_state, veh_rn, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="nose_radius",
        units="m",
        baseline_value=vehicle_config.nose_radius_m,
        perturbation=+0.50,
        perturbed_value=veh_rn.nose_radius_m,
        delta_peak_q_kpa=(res_rn.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_rn.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_rn.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_rn.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_rn.impact_time_s - base_time,
        delta_miss_dist_km=res_rn.miss_distance_km - base_miss
    ))

    # 7. Entry speed +25 m/s
    v_unit = baseline_state.v / np.linalg.norm(baseline_state.v)
    v_pert = baseline_state.v + 25.0 * v_unit
    st_v = OrbitalState(r=baseline_state.r, v=v_pert, epoch=baseline_state.epoch, mass_kg=baseline_state.mass_kg)
    res_v = propagate_reentry(st_v, vehicle_config, atmosphere, guidance, target_lat_deg=target_lat_deg, target_lon_deg=target_lon_deg, eval_step_s=2.0)
    sensitivities.append(SensitivityResult(
        parameter="entry_speed",
        units="m/s",
        baseline_value=float(np.linalg.norm(baseline_state.v)),
        perturbation=+25.0,
        perturbed_value=float(np.linalg.norm(v_pert)),
        delta_peak_q_kpa=(res_v.peak_dynamic_pressure_pa / 1000.0) - base_q_kpa,
        delta_peak_g=res_v.peak_apparent_g_load - base_g,
        delta_peak_heat_mw_m2=res_v.peak_stagnation_heat_flux_mw_m2 - base_heat,
        delta_total_heat_mj_m2=res_v.total_heat_load_mj_m2 - base_tot_heat,
        delta_impact_time_s=res_v.impact_time_s - base_time,
        delta_miss_dist_km=res_v.miss_distance_km - base_miss
    ))

    return sensitivities


def run_reentry_monte_carlo(
    baseline_state: OrbitalState,
    vehicle_config: ReentryVehicleConfig,
    atmosphere: USStandardAtmosphere1976,
    guidance: Optional[CrossrangeBankGuidanceController] = None,
    sample_count: int = 50,
    seed: int = 42,
    target_lat_deg: float = -14.0,
    target_lon_deg: float = -15.5,
    target_radius_m: float = 100000.0
) -> MonteCarloSummary:
    """
    Executes seeded pseudo-random Monte Carlo trajectory dispersion ensemble.
    Perturbs mass, area, aerodynamics, density, and entry velocity vector.
    """
    rng = np.random.default_rng(seed)
    samples: List[Dict[str, Any]] = []
    completed = 0
    failed = 0
    hits = 0

    q_peaks = []
    g_peaks = []
    heat_peaks = []
    tot_heats = []
    times = []
    speeds = []
    misses = []

    for idx in range(sample_count):
        # 1-sigma relative variations
        dm_rel = rng.normal(0.0, 0.02)      # +/- 2% mass
        da_rel = rng.normal(0.0, 0.03)      # +/- 3% reference area
        dcd_rel = rng.normal(0.0, 0.04)     # +/- 4% drag coeff
        dcl_rel = rng.normal(0.0, 0.05)     # +/- 5% lift coeff
        drho_rel = rng.normal(0.0, 0.05)    # +/- 5% density
        dv_mag = rng.normal(0.0, 10.0)      # +/- 10 m/s velocity norm

        # Configure perturbed vehicle & environment
        pert_veh = copy.deepcopy(vehicle_config)
        pert_veh.mass_kg *= (1.0 + dm_rel)
        pert_veh.reference_area_m2 *= (1.0 + da_rel)
        pert_veh.cd_hypersonic_70deg *= (1.0 + dcd_rel)
        pert_veh.cl_hypersonic_70deg *= (1.0 + dcl_rel)

        pert_atm = USStandardAtmosphere1976(density_scale=max(1.0 + drho_rel, 0.5))

        v_norm = np.linalg.norm(baseline_state.v)
        v_pert = baseline_state.v * ((v_norm + dv_mag) / v_norm)
        pert_st = OrbitalState(
            r=baseline_state.r,
            v=v_pert,
            epoch=baseline_state.epoch,
            mass_kg=pert_veh.mass_kg
        )

        try:
            res = propagate_reentry(
                initial_state=pert_st,
                vehicle_config=pert_veh,
                atmosphere=pert_atm,
                guidance=guidance,
                target_lat_deg=target_lat_deg,
                target_lon_deg=target_lon_deg,
                target_radius_m=target_radius_m,
                eval_step_s=2.5,
                scenario_id=f"MC_SAMPLE_{idx+1}"
            )
            completed += 1
            if res.terminal_assessment.target_within_corridor:
                hits += 1

            qp = res.peak_dynamic_pressure_pa / 1000.0
            gp = res.peak_apparent_g_load
            hp = res.peak_stagnation_heat_flux_mw_m2
            th = res.total_heat_load_mj_m2
            ti = res.impact_time_s
            vi = res.terminal_relative_speed_ms
            mi = res.miss_distance_km

            q_peaks.append(qp)
            g_peaks.append(gp)
            heat_peaks.append(hp)
            tot_heats.append(th)
            times.append(ti)
            speeds.append(vi)
            misses.append(mi)

            samples.append({
                "sample_id": idx + 1,
                "status": "COMPLETED",
                "mass_kg": pert_veh.mass_kg,
                "cd": pert_veh.cd_hypersonic_70deg,
                "cl": pert_veh.cl_hypersonic_70deg,
                "density_factor": pert_atm.density_scale,
                "peak_q_kpa": qp,
                "peak_g": gp,
                "peak_heat_mw_m2": hp,
                "total_heat_load_mj_m2": th,
                "impact_time_s": ti,
                "terminal_speed_ms": vi,
                "miss_distance_km": mi,
                "hit_corridor": res.terminal_assessment.target_within_corridor
            })
        except Exception as e:
            failed += 1
            samples.append({
                "sample_id": idx + 1,
                "status": f"FAILED: {str(e)}",
                "mass_kg": pert_veh.mass_kg,
                "hit_corridor": False
            })

    # Summary statistics
    def _calc_stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"mean": 0.0, "std": 0.0, "median": 0.0, "p10": 0.0, "p90": 0.0}
        a = np.array(arr)
        return {
            "mean": float(np.mean(a)),
            "std": float(np.std(a)),
            "median": float(np.median(a)),
            "p10": float(np.percentile(a, 10)),
            "p90": float(np.percentile(a, 90))
        }

    metrics = {
        "peak_dynamic_pressure_kpa": _calc_stats(q_peaks),
        "peak_apparent_g_load": _calc_stats(g_peaks),
        "peak_stagnation_heat_flux_mw_m2": _calc_stats(heat_peaks),
        "total_heat_load_mj_m2": _calc_stats(tot_heats),
        "impact_time_s": _calc_stats(times),
        "terminal_speed_ms": _calc_stats(speeds),
        "miss_distance_km": _calc_stats(misses)
    }

    hit_fraction = (hits / completed) if completed > 0 else 0.0

    return MonteCarloSummary(
        sample_count=sample_count,
        completed_count=completed,
        failed_count=failed,
        seed=seed,
        target_hit_fraction=hit_fraction,
        metrics=metrics,
        samples=samples
    )
