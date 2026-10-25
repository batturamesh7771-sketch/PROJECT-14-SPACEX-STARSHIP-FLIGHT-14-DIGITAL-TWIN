"""
Thermal Protection System (TPS) margin analysis, tile thickness sizing trade study,
and atmospheric density uncertainty quantification.
"""

import math
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from src.thermal.material_properties import RTV_BONDLINE_LIMIT_K
from src.thermal.conduction_1d import (
    ThermalStackMesh,
    generate_thermal_stack_mesh,
    TransientThermalSolver1D,
    ThermalSolution1D,
)
from src.thermal.aerothermal_flux import (
    compute_sutton_graves_heat_flux,
    compute_windward_acreage_flux,
)


@dataclass
class BondlineMarginAssessment:
    """Detailed structural thermal bondline margin assessment."""
    tile_thickness_mm: float
    peak_surface_temp_k: float
    peak_bondline_temp_k: float
    allowable_bondline_temp_k: float
    temperature_margin_k: float
    margin_of_safety: float
    heat_soak_lag_s: float
    is_acceptable: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tile_thickness_mm": round(self.tile_thickness_mm, 1),
            "peak_surface_temp_K": round(self.peak_surface_temp_k, 2),
            "peak_surface_temp_degC": round(self.peak_surface_temp_k - 273.15, 2),
            "peak_bondline_temp_K": round(self.peak_bondline_temp_k, 2),
            "peak_bondline_temp_degC": round(self.peak_bondline_temp_k - 273.15, 2),
            "allowable_bondline_temp_K": round(self.allowable_bondline_temp_k, 2),
            "allowable_bondline_temp_degC": round(self.allowable_bondline_temp_k - 273.15, 2),
            "temperature_margin_K": round(self.temperature_margin_k, 2),
            "margin_of_safety": round(self.margin_of_safety, 3),
            "heat_soak_lag_seconds": round(self.heat_soak_lag_s, 1),
            "is_acceptable": self.is_acceptable,
        }


def evaluate_bondline_margins(solution: ThermalSolution1D,
                              initial_temp_k: float = 293.15) -> BondlineMarginAssessment:
    """Evaluate RTV silicone bondline margin against 533.15 K limit."""
    peak_bond = solution.peak_bondline_temp_k
    margin_k = RTV_BONDLINE_LIMIT_K - peak_bond

    # Margin of Safety based on allowable temperature rise
    delta_t_allow = RTV_BONDLINE_LIMIT_K - initial_temp_k
    delta_t_actual = peak_bond - initial_temp_k
    mos = (delta_t_allow / max(delta_t_actual, 1.0)) - 1.0

    tile_thk_mm = solution.mesh.layers[0].thickness_m * 1000.0

    return BondlineMarginAssessment(
        tile_thickness_mm=tile_thk_mm,
        peak_surface_temp_k=solution.peak_surface_temp_k,
        peak_bondline_temp_k=peak_bond,
        allowable_bondline_temp_k=RTV_BONDLINE_LIMIT_K,
        temperature_margin_k=margin_k,
        margin_of_safety=mos,
        heat_soak_lag_s=solution.heat_soak_lag_s,
        is_acceptable=(margin_k > 0.0)
    )


def run_tile_thickness_trade_study(times_s: List[float],
                                   heat_flux_w_m2: List[float],
                                   thicknesses_mm: List[float] = None) -> List[Dict[str, Any]]:
    """
    Perform tile thickness sizing study (e.g. 15mm to 40mm) to assess thermal protection margins.
    """
    if thicknesses_mm is None:
        thicknesses_mm = [15.0, 20.0, 25.0, 28.0, 32.0, 36.0, 40.0]

    results: List[Dict[str, Any]] = []

    for thk in thicknesses_mm:
        thk_m = thk / 1000.0
        mesh = generate_thermal_stack_mesh(tile_thickness_m=thk_m)
        solver = TransientThermalSolver1D(mesh)
        sol = solver.solve_trajectory(times_s, heat_flux_w_m2)
        assessment = evaluate_bondline_margins(sol)
        rec = assessment.to_dict()
        results.append(rec)

    return results


def run_density_sensitivity_study(trajectory_rows: List[Dict[str, float]],
                                  density_multipliers: List[float] = None) -> List[Dict[str, Any]]:
    """
    Quantify sensitivity of aerothermal heating and bondline temperature to
    atmospheric density fluctuations (+/- 10%, +/- 20%).
    """
    if density_multipliers is None:
        density_multipliers = [0.80, 0.90, 1.00, 1.10, 1.20]

    records: List[Dict[str, Any]] = []

    times = [r["time_s"] for r in trajectory_rows]

    for mult in density_multipliers:
        fluxes = []
        for r in trajectory_rows:
            rho = r["density_kg_m3"] * mult
            v = r["speed_relative_ms"]
            q_stag = compute_sutton_graves_heat_flux(rho, v, nose_radius_m=4.5)
            q_wind = compute_windward_acreage_flux(q_stag, angle_of_attack_deg=40.0)
            fluxes.append(q_wind)

        # Integrated heat load Q = integral q dt [MJ / m^2]
        tot_heat_load_mj_m2 = 0.0
        for i in range(1, len(times)):
            dt = times[i] - times[i - 1]
            tot_heat_load_mj_m2 += 0.5 * (fluxes[i] + fluxes[i - 1]) * dt / 1e6

        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.028)
        solver = TransientThermalSolver1D(mesh)
        sol = solver.solve_trajectory(times, fluxes)
        assessment = evaluate_bondline_margins(sol)

        peak_flux_mw_m2 = max(fluxes) / 1e6

        records.append({
            "density_multiplier": mult,
            "density_perturbation_percent": round((mult - 1.0) * 100.0, 1),
            "peak_heat_flux_MW_m2": round(peak_flux_mw_m2, 3),
            "integrated_heat_load_MJ_m2": round(tot_heat_load_mj_m2, 2),
            "peak_surface_temp_K": round(sol.peak_surface_temp_k, 2),
            "peak_bondline_temp_K": round(sol.peak_bondline_temp_k, 2),
            "bondline_margin_K": round(assessment.temperature_margin_k, 2),
            "is_acceptable": assessment.is_acceptable,
        })

    return records
