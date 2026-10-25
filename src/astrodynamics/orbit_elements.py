"""
Classical Orbital Elements & State Conversions
==============================================
Standard conversions between 3D Cartesian state vectors and Keplerian elements,
including rigorous singularity handling for circular and equatorial orbits (Vallado, 2013).
"""

import math
from typing import Dict, Any, Optional
import numpy as np

from .constants import MU_EARTH, R_EARTH_EQUATORIAL
from .state import OrbitalState

def compute_keplerian_elements(
    r_vec: np.ndarray,
    v_vec: np.ndarray,
    mu: float = MU_EARTH,
    tol_circ: float = 1e-7,
    tol_eq: float = 1e-7
) -> Dict[str, Any]:
    """
    Computes classical Keplerian orbital elements from Cartesian state.

    Parameters:
    -----------
    r_vec : np.ndarray (3,)
        Position in ECI frame (m)
    v_vec : np.ndarray (3,)
        Velocity in ECI frame (m/s)
    mu : float
        Gravitational parameter (m^3/s^2)
    tol_circ : float
        Eccentricity tolerance threshold for circular orbit
    tol_eq : float
        Sine of inclination threshold for equatorial orbit

    Returns:
    --------
    dict containing:
        semi_major_axis_m, semi_major_axis_km, eccentricity, inclination_rad, inclination_deg,
        raan_rad, raan_deg, arg_periapsis_rad, arg_periapsis_deg, true_anomaly_rad, true_anomaly_deg,
        orbital_period_s, orbital_period_min, perigee_radius_m, perigee_altitude_km,
        apogee_radius_m, apogee_altitude_km, specific_energy_j_kg, specific_angular_momentum_m2_s,
        is_bound, orbit_type
    """
    r_vec = np.asarray(r_vec, dtype=np.float64)
    v_vec = np.asarray(v_vec, dtype=np.float64)

    r_norm = float(np.linalg.norm(r_vec))
    v_norm = float(np.linalg.norm(v_vec))

    if r_norm < 1.0:
        raise ValueError(f"Position magnitude must be > 1.0 m, got {r_norm}")

    # Specific angular momentum vector h = r x v
    h_vec = np.cross(r_vec, v_vec)
    h_norm = float(np.linalg.norm(h_vec))

    # Line of nodes vector n = k x h = [-hy, hx, 0]
    n_vec = np.array([-h_vec[1], h_vec[0], 0.0], dtype=np.float64)
    n_norm = float(np.linalg.norm(n_vec))

    # Specific orbital energy E = v^2/2 - mu/r
    energy = (v_norm**2 / 2.0) - (mu / r_norm)

    # Eccentricity vector e = ((v^2 - mu/r)*r - (r.v)*v) / mu
    r_dot_v = float(np.dot(r_vec, v_vec))
    e_vec = (((v_norm**2 - mu / r_norm) * r_vec) - (r_dot_v * v_vec)) / mu
    ecc = float(np.linalg.norm(e_vec))

    # Semi-major axis a
    is_bound = energy < 0.0
    if abs(1.0 - ecc) < 1e-6:
        orbit_type = "parabolic"
        sma = math.inf
    elif is_bound:
        orbit_type = "elliptical" if ecc > tol_circ else "circular"
        sma = -mu / (2.0 * energy)
    else:
        orbit_type = "hyperbolic"
        sma = -mu / (2.0 * energy) # Negative for hyperbolas

    # Inclination i = acos(hz / h)
    inc = math.acos(max(-1.0, min(1.0, h_vec[2] / h_norm)))

    # Classification of geometric singularities
    is_circular = ecc < tol_circ
    is_equatorial = (n_norm / h_norm) < tol_eq or math.sin(inc) < tol_eq

    # 1. Right Ascension of Ascending Node (RAAN, Omega)
    if is_equatorial:
        raan = 0.0
    else:
        raan = math.acos(max(-1.0, min(1.0, n_vec[0] / n_norm)))
        if n_vec[1] < 0.0:
            raan = 2.0 * math.pi - raan

    # 2. Argument of Periapsis (omega)
    if is_circular:
        arg_p = 0.0
    elif is_equatorial:
        # Longitude of periapsis pi = acos(ex / e)
        arg_p = math.acos(max(-1.0, min(1.0, e_vec[0] / ecc)))
        if e_vec[1] < 0.0:
            arg_p = 2.0 * math.pi - arg_p
    else:
        arg_p = math.acos(max(-1.0, min(1.0, np.dot(n_vec, e_vec) / (n_norm * ecc))))
        if e_vec[2] < 0.0:
            arg_p = 2.0 * math.pi - arg_p

    # 3. True Anomaly (nu)
    if is_circular and is_equatorial:
        # True longitude lambda = acos(rx / r)
        nu = math.acos(max(-1.0, min(1.0, r_vec[0] / r_norm)))
        if r_vec[1] < 0.0:
            nu = 2.0 * math.pi - nu
    elif is_circular:
        # Argument of latitude u = acos((n.r) / (n*r))
        nu = math.acos(max(-1.0, min(1.0, np.dot(n_vec, r_vec) / (n_norm * r_norm))))
        if r_vec[2] < 0.0:
            nu = 2.0 * math.pi - nu
    else:
        nu = math.acos(max(-1.0, min(1.0, np.dot(e_vec, r_vec) / (ecc * r_norm))))
        if r_dot_v < 0.0:
            nu = 2.0 * math.pi - nu

    # Derived radius & altitudes
    if is_bound:
        r_p = sma * (1.0 - ecc)
        r_a = sma * (1.0 + ecc)
        period_s = 2.0 * math.pi * math.sqrt((sma**3) / mu)
        period_min = period_s / 60.0
    else:
        r_p = (h_norm**2) / (mu * (1.0 + ecc))
        r_a = math.inf
        period_s = math.inf
        period_min = math.inf

    h_p_km = (r_p - R_EARTH_EQUATORIAL) / 1000.0
    h_a_km = (r_a - R_EARTH_EQUATORIAL) / 1000.0 if math.isfinite(r_a) else math.inf

    return {
        "semi_major_axis_m": float(sma),
        "semi_major_axis_km": float(sma / 1000.0),
        "eccentricity": float(ecc),
        "inclination_rad": float(inc),
        "inclination_deg": float(math.degrees(inc)),
        "raan_rad": float(raan),
        "raan_deg": float(math.degrees(raan)),
        "arg_periapsis_rad": float(arg_p),
        "arg_periapsis_deg": float(math.degrees(arg_p)),
        "true_anomaly_rad": float(nu),
        "true_anomaly_deg": float(math.degrees(nu)),
        "orbital_period_s": float(period_s),
        "orbital_period_min": float(period_min),
        "period_s": float(period_s),
        "period_min": float(period_min),
        "periapsis_radius_m": float(r_p),
        "perigee_radius_m": float(r_p),
        "periapsis_altitude_m": float(h_p_km * 1000.0),
        "perigee_altitude_m": float(h_p_km * 1000.0),
        "perigee_altitude_km": float(h_p_km),
        "apoapsis_radius_m": float(r_a),
        "apogee_radius_m": float(r_a),
        "apoapsis_altitude_m": float(h_a_km * 1000.0) if math.isfinite(h_a_km) else math.inf,
        "apogee_altitude_m": float(h_a_km * 1000.0) if math.isfinite(h_a_km) else math.inf,
        "apogee_altitude_km": float(h_a_km),
        "specific_energy_j_kg": float(energy),
        "specific_angular_momentum_m2_s": float(h_norm),
        "is_bound": is_bound,
        "orbit_type": orbit_type,
        "is_circular": is_circular,
        "is_equatorial": is_equatorial
    }

def classical_to_cartesian(
    sma_m: float,
    ecc: float,
    inc_rad: float,
    raan_rad: float,
    arg_p_rad: float,
    nu_rad: float,
    mu: float = MU_EARTH
):
    """
    Converts classical Keplerian elements to Cartesian position and velocity in ECI.
    """
    if ecc < 1.0:
        p = sma_m * (1.0 - ecc**2)
    else:
        p = sma_m * (ecc**2 - 1.0) # For hyperbolic

    r_orbit = p / (1.0 + ecc * math.cos(nu_rad))

    # Position in perifocal frame (PQW)
    r_pqw = np.array([
        r_orbit * math.cos(nu_rad),
        r_orbit * math.sin(nu_rad),
        0.0
    ], dtype=np.float64)

    # Velocity in perifocal frame (PQW)
    v_factor = math.sqrt(mu / p)
    v_pqw = np.array([
        -v_factor * math.sin(nu_rad),
        v_factor * (ecc + math.cos(nu_rad)),
        0.0
    ], dtype=np.float64)

    # Transformation matrix from perifocal to ECI: R = Rz(-raan) Rx(-inc) Rz(-arg_p)
    cos_o = math.cos(raan_rad)
    sin_o = math.sin(raan_rad)
    cos_i = math.cos(inc_rad)
    sin_i = math.sin(inc_rad)
    cos_w = math.cos(arg_p_rad)
    sin_w = math.sin(arg_p_rad)

    P_x = cos_o * cos_w - sin_o * sin_w * cos_i
    P_y = sin_o * cos_w + cos_o * sin_w * cos_i
    P_z = sin_w * sin_i

    Q_x = -cos_o * sin_w - sin_o * cos_w * cos_i
    Q_y = -sin_o * sin_w + cos_o * cos_w * cos_i
    Q_z = cos_w * sin_i

    r_eci = np.array([
        P_x * r_pqw[0] + Q_x * r_pqw[1],
        P_y * r_pqw[0] + Q_y * r_pqw[1],
        P_z * r_pqw[0] + Q_z * r_pqw[1]
    ], dtype=np.float64)

    v_eci = np.array([
        P_x * v_pqw[0] + Q_x * v_pqw[1],
        P_y * v_pqw[0] + Q_y * v_pqw[1],
        P_z * v_pqw[0] + Q_z * v_pqw[1]
    ], dtype=np.float64)

    return r_eci, v_eci
