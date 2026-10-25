"""
Aerothermal Heating & Heat Load Integration Model
=================================================
Phase 6: Sutton-Graves convective stagnation-point heat flux calculation,
windward acreage scaling, cumulative heat load integration, and radiative
equilibrium wall temperature estimation for Starship atmospheric reentry.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .constants import SUTTON_GRAVES_K_EARTH, DEFAULT_NOSE_RADIUS_M

# Stefan-Boltzmann constant for radiative equilibrium calculation
STEFAN_BOLTZMANN_CONSTANT = 5.670374419e-8  # W / (m^2 * K^4)
DEFAULT_SURFACE_EMISSIVITY = 0.85          # High-emissivity ceramic / oxidized stainless steel
WINDWARD_TO_STAGNATION_RATIO = 0.25        # Characteristic windward acreage heating fraction


@dataclass
class HeatingState:
    """Aerothermal heating metrics at a discrete trajectory step."""
    stagnation_heat_flux_w_m2: float
    stagnation_heat_flux_mw_m2: float
    stagnation_heat_flux_w_cm2: float
    windward_heat_flux_w_m2: float
    windward_heat_flux_mw_m2: float
    cumulative_heat_load_j_m2: float
    cumulative_heat_load_mj_m2: float
    radiative_equilibrium_temp_k: float
    radiative_equilibrium_temp_deg_c: float


def compute_stagnation_heat_flux(
    density_kg_m3: float,
    speed_relative_ms: float,
    nose_radius_m: float = DEFAULT_NOSE_RADIUS_M,
    k_sg: float = SUTTON_GRAVES_K_EARTH
) -> float:
    """
    Computes stagnation-point convective heat flux via the Sutton-Graves correlation:
    q_dot_stag = k_SG * sqrt(rho / R_n) * V_rel^3  [W / m^2]

    Parameters:
    -----------
    density_kg_m3 : float
        Atmospheric density (kg / m^3)
    speed_relative_ms : float
        Atmospheric-relative speed (m / s)
    nose_radius_m : float
        Effective stagnation curvature radius (m)
    k_sg : float
        Sutton-Graves constant for Earth air (W * s^3 / (m^3 * kg^0.5))

    Returns:
    --------
    float: Heat flux in Watts per square meter (W / m^2).
    """
    if density_kg_m3 <= 1e-15 or speed_relative_ms <= 1.0 or nose_radius_m <= 0.0:
        return 0.0

    return float(k_sg * math.sqrt(density_kg_m3 / nose_radius_m) * (speed_relative_ms ** 3))


def compute_radiative_equilibrium_temperature(
    heat_flux_w_m2: float,
    emissivity: float = DEFAULT_SURFACE_EMISSIVITY
) -> float:
    """
    Estimates radiative equilibrium outer mold line (OML) wall temperature:
    q_dot = epsilon * sigma * T_wall^4  =>  T_wall = (q_dot / (epsilon * sigma))^0.25

    Parameters:
    -----------
    heat_flux_w_m2 : float
        Incident heat flux (W / m^2)
    emissivity : float
        Surface total hemispherical emissivity (0 < epsilon <= 1.0)

    Returns:
    --------
    float: Wall temperature in Kelvin (K).
    """
    if heat_flux_w_m2 <= 1.0 or emissivity <= 0.0:
        return 288.15  # Return ambient reference temperature

    eps = min(max(emissivity, 0.1), 1.0)
    t_k = (heat_flux_w_m2 / (eps * STEFAN_BOLTZMANN_CONSTANT)) ** 0.25
    return float(t_k)


def evaluate_heating_state(
    density_kg_m3: float,
    speed_relative_ms: float,
    cumulative_heat_load_j_m2: float,
    nose_radius_m: float = DEFAULT_NOSE_RADIUS_M,
    emissivity: float = DEFAULT_SURFACE_EMISSIVITY
) -> HeatingState:
    """Evaluates comprehensive aerothermal heating state."""
    q_stag_w = compute_stagnation_heat_flux(
        density_kg_m3=density_kg_m3,
        speed_relative_ms=speed_relative_ms,
        nose_radius_m=nose_radius_m
    )
    q_wind_w = q_stag_w * WINDWARD_TO_STAGNATION_RATIO
    t_wall_k = compute_radiative_equilibrium_temperature(q_stag_w, emissivity=emissivity)

    return HeatingState(
        stagnation_heat_flux_w_m2=q_stag_w,
        stagnation_heat_flux_mw_m2=q_stag_w / 1e6,
        stagnation_heat_flux_w_cm2=q_stag_w / 1e4,
        windward_heat_flux_w_m2=q_wind_w,
        windward_heat_flux_mw_m2=q_wind_w / 1e6,
        cumulative_heat_load_j_m2=cumulative_heat_load_j_m2,
        cumulative_heat_load_mj_m2=cumulative_heat_load_j_m2 / 1e6,
        radiative_equilibrium_temp_k=t_wall_k,
        radiative_equilibrium_temp_deg_c=t_wall_k - 273.15
    )
