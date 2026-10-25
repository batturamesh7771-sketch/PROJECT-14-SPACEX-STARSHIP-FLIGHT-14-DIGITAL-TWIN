"""
Aerothermal heat flux correlations and radiative equilibrium models for hypersonic reentry.
Implements:
  - Sutton-Graves stagnation point convective heat flux.
  - Detra-Kemp-Riddell hypersonic stagnation correlation.
  - Oblique windward acreage heating with angle-of-attack scaling.
  - Surface radiative equilibrium temperature with Stefan-Boltzmann balance.
References:
  - Sutton, K. and Graves, R.A., "A General Stagnation-Point Convective-Heating Equation for Arbitrary Gas Mixtures", NASA TR R-376, 1971.
  - Detra, R.W., Kemp, N.H., Riddell, F.R., "Addendum to Heat Transfer to Blunt Bodies in Hypersonic Flight", Jet Propulsion, 1957.
"""

import math
from typing import Dict, Any, Tuple
from src.thermal.material_properties import STEFAN_BOLTZMANN


# Sutton-Graves constant for Earth air atmosphere [W * s^3 / (m^3 * sqrt(kg/m^3))]
C_SUTTON_GRAVES_EARTH = 1.74153e-4

# Reference sea-level density and orbital circular speed for Detra-Kemp-Riddell
RHO_0_SEA_LEVEL = 1.225         # [kg / m^3]
V_CIRCULAR_REF = 7925.0         # [m / s]


def compute_sutton_graves_heat_flux(density_kg_m3: float,
                                    velocity_ms: float,
                                    nose_radius_m: float = 4.5,
                                    c_constant: float = C_SUTTON_GRAVES_EARTH) -> float:
    """
    Compute convective stagnation-point heat flux via the Sutton-Graves correlation:
      q_stag = C * sqrt(rho / R_n) * v^3  [W / m^2]
    """
    if density_kg_m3 <= 0.0 or velocity_ms <= 0.0 or nose_radius_m <= 0.0:
        return 0.0
    return c_constant * math.sqrt(density_kg_m3 / nose_radius_m) * (velocity_ms ** 3)


def compute_detra_kemp_riddell_flux(density_kg_m3: float,
                                    velocity_ms: float,
                                    nose_radius_m: float = 4.5) -> float:
    """
    Compute stagnation heat flux via Detra-Kemp-Riddell (DKR) correlation:
      q_stag = (11030 / sqrt(R_n)) * (rho / rho_0)^0.5 * (v / v_c)^3.15  [Btu / (ft^2 * s)]
    Converted to SI units [W / m^2]:
      1 Btu / (ft^2 * s) = 1.13565267e7 W / m^2
      1 ft = 0.3048 m
    """
    if density_kg_m3 <= 0.0 or velocity_ms <= 0.0 or nose_radius_m <= 0.0:
        return 0.0
    r_ft = nose_radius_m / 0.3048
    ratio_rho = math.sqrt(density_kg_m3 / RHO_0_SEA_LEVEL)
    ratio_v = (velocity_ms / V_CIRCULAR_REF) ** 3.15

    q_btu_ft2_s = (11030.0 / math.sqrt(r_ft)) * ratio_rho * ratio_v
    btu_to_w_m2 = 11356.5267  # 1 Btu/(ft^2*s) = 1055.056 J / (0.09290304 m^2 * s) = 11356.5267 W/m^2
    return q_btu_ft2_s * btu_to_w_m2




def compute_windward_acreage_flux(stagnation_flux_w_m2: float,
                                  angle_of_attack_deg: float = 40.0,
                                  body_position_factor: float = 0.40) -> float:
    """
    Compute windward belly acreage heat flux scaling from stagnation value:
      q_windward = q_stag * (sin(alpha))^1.6 * f_body  [W / m^2]
    """
    if stagnation_flux_w_m2 <= 0.0:
        return 0.0
    alpha_rad = math.radians(max(0.0, min(angle_of_attack_deg, 90.0)))
    sin_alpha = math.sin(alpha_rad)
    pitch_factor = (sin_alpha ** 1.6) if sin_alpha > 0.0 else 0.0
    return stagnation_flux_w_m2 * pitch_factor * body_position_factor


def compute_radiative_equilibrium_temp(heat_flux_w_m2: float,
                                      emissivity: float = 0.85,
                                      ambient_temp_k: float = 220.0) -> float:
    """
    Compute surface radiative equilibrium temperature:
      q_in = eps * sigma * (T_surf^4 - T_amb^4)
      T_surf = [ (q_in / (eps * sigma)) + T_amb^4 ]^(1/4)  [K]
    """
    if heat_flux_w_m2 <= 0.0:
        return ambient_temp_k
    rad_denom = max(emissivity * STEFAN_BOLTZMANN, 1e-12)
    t4 = (heat_flux_w_m2 / rad_denom) + (ambient_temp_k ** 4)
    return t4 ** 0.25
