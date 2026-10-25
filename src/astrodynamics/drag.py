"""
Atmospheric Density & Aerodynamic Drag Model
============================================
Computes upper atmospheric aerodynamic drag acceleration in low-Earth orbit
using an exponential density model fitted to US Standard Atmosphere 1976 (80 km to 500 km).
"""

import math
import numpy as np
from .constants import R_EARTH_EQUATORIAL, OMEGA_EARTH

def compute_exponential_density(
    altitude_m: float,
    rho0: float = 1.225,
    h0_scale: float = 7200.0
) -> float:
    """
    Computes atmospheric density using exponential scale height approximation.
    For LEO (> 100 km), standard upper atmospheric scale height is ~7.2 km.
    """
    if altitude_m < 0.0:
        return rho0
    if altitude_m > 600000.0: # Negligible above 600 km
        return 0.0

    # Piecewise exponential fit approximating US Standard Atmosphere 1976 thermosphere:
    if altitude_m >= 150000.0:
        # Thermosphere at 150 km: rho ~ 2.0e-9 kg/m^3, scale height ~ 25 km
        return 2.076e-9 * math.exp(-(altitude_m - 150000.0) / 26000.0)
    elif altitude_m >= 120000.0:
        # Entry interface at 120 km: rho ~ 2.4e-8 kg/m^3, scale height ~ 10 km
        return 2.438e-8 * math.exp(-(altitude_m - 120000.0) / 10500.0)
    elif altitude_m >= 80000.0:
        # Mesosphere / lower thermosphere at 80 km: rho ~ 1.8e-5 kg/m^3, scale height ~ 6.5 km
        return 1.846e-5 * math.exp(-(altitude_m - 80000.0) / 6700.0)
    else:
        return rho0 * math.exp(-altitude_m / h0_scale)

def compute_aerodynamic_drag(
    r_eci: np.ndarray,
    v_eci: np.ndarray,
    mass_kg: float,
    area_m2: float = 63.617,
    cd: float = 2.20
) -> np.ndarray:
    """
    Computes aerodynamic drag acceleration in ECI coordinates:
    a_drag = - 0.5 * rho * (Cd * A / m) * |v_rel| * v_rel

    Parameters:
    -----------
    r_eci : np.ndarray (3,)
        Position in ECI (m)
    v_eci : np.ndarray (3,)
        Velocity in ECI (m/s)
    mass_kg : float
        Spacecraft mass (kg)
    area_m2 : float
        Aerodynamic cross-sectional reference area (m^2)
    cd : float
        Hypersonic drag coefficient (dimensionless)

    Returns:
    --------
    a_drag : np.ndarray (3,)
        Drag acceleration vector in ECI (m/s^2)
    """
    if mass_kg <= 0.0:
        raise ValueError(f"Mass must be strictly positive: {mass_kg} kg")
    if area_m2 <= 0.0 or cd <= 0.0:
        return np.zeros(3, dtype=np.float64)

    r_norm = float(np.linalg.norm(r_eci))
    altitude_m = r_norm - R_EARTH_EQUATORIAL

    if altitude_m > 600000.0:
        return np.zeros(3, dtype=np.float64)

    rho = compute_exponential_density(altitude_m)
    if rho <= 0.0:
        return np.zeros(3, dtype=np.float64)

    # Co-rotating atmospheric relative velocity v_rel = v_eci - omega x r_eci
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    v_rel = v_eci - np.cross(omega_vec, r_eci)
    v_rel_norm = float(np.linalg.norm(v_rel))

    if v_rel_norm < 1e-6:
        return np.zeros(3, dtype=np.float64)

    drag_mag = 0.5 * rho * (cd * area_m2 / mass_kg) * (v_rel_norm**2)
    return -drag_mag * (v_rel / v_rel_norm)
