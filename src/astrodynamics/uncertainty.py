"""
Uncertainty Quantification: Deterministic Sensitivity & Monte Carlo Analysis
============================================================================
Quantifies orbital trajectory and element dispersion arising from:
- Insertion state vector uncertainties (delta-r, delta-v)
- Spacecraft parameter variations (mass, Cd, cross-sectional area)
- Upper atmospheric density perturbations
Provides deterministic 1-at-a-time sensitivity gradients and seeded Monte Carlo ensembles.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .constants import MU_EARTH, R_EARTH_EQUATORIAL
from .state import OrbitalState
from .propagator import propagate_orbit_adaptive, propagate_orbit_rk4_fixed
from .orbit_elements import compute_keplerian_elements


@dataclass
class SensitivityResult:
    """Result for single parameter perturbation in sensitivity study."""
    parameter_name: str
    nominal_value: float
    perturbation: float
    perturbed_value: float
    delta_sma_km: float
    delta_ecc: float
    delta_perigee_km: float
    delta_apogee_km: float
    influence_d_sma: float  # d(SMA) / d(Param)
    influence_d_ecc: float  # d(Ecc) / d(Param)


@dataclass
class MonteCarloSample:
    """Single sample result from Monte Carlo ensemble."""
    sample_id: int
    delta_r: np.ndarray
    delta_v: np.ndarray
    mass_kg: float
    cd: float
    final_sma_km: float
    final_ecc: float
    final_perigee_km: float
    final_apogee_km: float
    final_period_min: float


@dataclass
class MonteCarloSummary:
    """Statistical summary across Monte Carlo ensemble."""
    sample_count: int
    seed: int
    duration_s: float
    metrics: Dict[str, Dict[str, float]]  # {metric_name: {'mean', 'std', 'min', 'max', 'p10', 'p50', 'p90'}}
    samples: List[MonteCarloSample]


def run_deterministic_sensitivity_study(
    nominal_state: OrbitalState,
    duration_s: float = 5400.0,
    enable_j2: bool = True,
    enable_drag: bool = False
) -> List[SensitivityResult]:
    """
    Executes one-at-a-time (OAT) deterministic sensitivity study.
    Perturbs position, velocity, vehicle mass, and drag coefficient by 1-sigma standard increments.
    """
    # 1. Nominal propagation run
    nom_res = propagate_orbit_adaptive(
        initial_state=nominal_state,
        duration_s=duration_s,
        enable_j2=enable_j2,
        enable_drag=enable_drag,
        detect_events=False
    )
    nom_elem = nom_res.elements_history[-1]
    nom_sma_km = nom_elem["semi_major_axis_m"] / 1000.0
    nom_ecc = nom_elem["eccentricity"]
    nom_hp_km = nom_elem["perigee_altitude_m"] / 1000.0
    nom_ha_km = nom_elem["apogee_altitude_m"] / 1000.0

    perturbations = [
        ("r_x_m", 0, 100.0, "position"),
        ("r_y_m", 1, 100.0, "position"),
        ("r_z_m", 2, 100.0, "position"),
        ("v_x_ms", 0, 1.0, "velocity"),
        ("v_y_ms", 1, 1.0, "velocity"),
        ("v_z_ms", 2, 1.0, "velocity"),
        ("mass_kg", None, 1000.0, "mass"),
        ("cd", None, 0.20, "cd")
    ]

    results: List[SensitivityResult] = []

    for name, idx, delta_val, ptype in perturbations:
        pert_r = nominal_state.r.copy()
        pert_v = nominal_state.v.copy()
        pert_mass = nominal_state.mass_kg
        pert_cd = nominal_state.cd

        if ptype == "position":
            pert_r[idx] += delta_val
            nom_val = nominal_state.r[idx]
        elif ptype == "velocity":
            pert_v[idx] += delta_val
            nom_val = nominal_state.v[idx]
        elif ptype == "mass":
            pert_mass += delta_val
            nom_val = nominal_state.mass_kg
        elif ptype == "cd":
            pert_cd += delta_val
            nom_val = nominal_state.cd
        else:
            continue

        p_state = OrbitalState(
            r=pert_r,
            v=pert_v,
            epoch=nominal_state.epoch,
            frame=nominal_state.frame,
            mass_kg=pert_mass,
            area_m2=nominal_state.area_m2,
            cd=pert_cd
        )

        p_res = propagate_orbit_adaptive(
            initial_state=p_state,
            duration_s=duration_s,
            enable_j2=enable_j2,
            enable_drag=enable_drag,
            detect_events=False
        )
        p_elem = p_res.elements_history[-1]

        p_sma_km = p_elem["semi_major_axis_m"] / 1000.0
        p_ecc = p_elem["eccentricity"]
        p_hp_km = p_elem["perigee_altitude_m"] / 1000.0
        p_ha_km = p_elem["apogee_altitude_m"] / 1000.0

        d_sma = p_sma_km - nom_sma_km
        d_ecc = p_ecc - nom_ecc
        d_hp = p_hp_km - nom_hp_km
        d_ha = p_ha_km - nom_ha_km

        infl_sma = d_sma / delta_val
        infl_ecc = d_ecc / delta_val

        results.append(SensitivityResult(
            parameter_name=name,
            nominal_value=float(nom_val),
            perturbation=float(delta_val),
            perturbed_value=float(nom_val + delta_val),
            delta_sma_km=d_sma,
            delta_ecc=d_ecc,
            delta_perigee_km=d_hp,
            delta_apogee_km=d_ha,
            influence_d_sma=infl_sma,
            influence_d_ecc=infl_ecc
        ))

    return results


def run_monte_carlo_analysis(
    nominal_state: OrbitalState,
    num_samples: int = 100,
    seed: int = 42,
    duration_s: float = 5400.0,
    sigma_r_m: float = 100.0,
    sigma_v_ms: float = 1.0,
    sigma_mass_kg: float = 1000.0,
    sigma_cd: float = 0.15,
    enable_j2: bool = True,
    enable_drag: bool = False
) -> MonteCarloSummary:
    """
    Executes a seeded Monte Carlo dispersion analysis over specified sample count.
    Generates repeatable pseudo-random Gaussian perturbations.
    """
    rng = np.random.default_rng(seed)

    samples: List[MonteCarloSample] = []
    sma_vals = []
    ecc_vals = []
    hp_vals = []
    ha_vals = []
    period_vals = []

    for i in range(num_samples):
        # Draw perturbations
        dr = rng.normal(0.0, sigma_r_m, size=3)
        dv = rng.normal(0.0, sigma_v_ms, size=3)
        dm = rng.normal(0.0, sigma_mass_kg)
        dcd = rng.normal(0.0, sigma_cd)

        pert_mass = max(nominal_state.mass_kg + dm, 138975.0)
        pert_cd = max(nominal_state.cd + dcd, 0.5)

        sample_state = OrbitalState(
            r=nominal_state.r + dr,
            v=nominal_state.v + dv,
            epoch=nominal_state.epoch,
            frame=nominal_state.frame,
            mass_kg=pert_mass,
            area_m2=nominal_state.area_m2,
            cd=pert_cd
        )

        res = propagate_orbit_rk4_fixed(
            initial_state=sample_state,
            duration_s=duration_s,
            dt=5.0,  # Fast high-precision fixed step for MC ensemble
            enable_j2=enable_j2,
            enable_drag=enable_drag
        )

        final_elem = res.elements_history[-1]
        sma_km = final_elem["semi_major_axis_m"] / 1000.0
        ecc = final_elem["eccentricity"]
        hp_km = final_elem["perigee_altitude_m"] / 1000.0
        ha_km = final_elem["apogee_altitude_m"] / 1000.0
        period_min = final_elem["period_s"] / 60.0

        sma_vals.append(sma_km)
        ecc_vals.append(ecc)
        hp_vals.append(hp_km)
        ha_vals.append(ha_km)
        period_vals.append(period_min)

        samples.append(MonteCarloSample(
            sample_id=i + 1,
            delta_r=dr,
            delta_v=dv,
            mass_kg=pert_mass,
            cd=pert_cd,
            final_sma_km=sma_km,
            final_ecc=ecc,
            final_perigee_km=hp_km,
            final_apogee_km=ha_km,
            final_period_min=period_min
        ))

    def _calc_stats(arr: List[float]) -> Dict[str, float]:
        np_arr = np.array(arr)
        return {
            "mean": float(np.mean(np_arr)),
            "std": float(np.std(np_arr)),
            "min": float(np.min(np_arr)),
            "max": float(np.max(np_arr)),
            "p10": float(np.percentile(np_arr, 10)),
            "p50": float(np.percentile(np_arr, 50)),
            "p90": float(np.percentile(np_arr, 90))
        }

    metrics = {
        "semi_major_axis_km": _calc_stats(sma_vals),
        "eccentricity": _calc_stats(ecc_vals),
        "perigee_altitude_km": _calc_stats(hp_vals),
        "apogee_altitude_km": _calc_stats(ha_vals),
        "period_minutes": _calc_stats(period_vals)
    }

    return MonteCarloSummary(
        sample_count=num_samples,
        seed=seed,
        duration_s=duration_s,
        metrics=metrics,
        samples=samples
    )
