"""
Gravitational Field Models & Perturbation Accelerations
======================================================
Implements central point-mass gravitational acceleration and Earth J2
zonal harmonic oblateness perturbation in ECI coordinates (NASA SP-8007, GMAT Math Spec).
"""

import math
import numpy as np
from .constants import MU_EARTH, R_EARTH_EQUATORIAL, J2_EARTH

def compute_point_mass_acceleration(r_vec: np.ndarray, mu: float = MU_EARTH) -> np.ndarray:
    """
    Computes Newtonian point-mass central acceleration: a = -mu * r / |r|^3

    Parameters:
    -----------
    r_vec : np.ndarray (3,)
        Position vector in inertial frame (m)
    mu : float
        Gravitational parameter (m^3/s^2)

    Returns:
    --------
    a_vec : np.ndarray (3,)
        Gravitational acceleration vector (m/s^2)
    """
    r_sq = float(r_vec[0]**2 + r_vec[1]**2 + r_vec[2]**2)
    r_norm = math.sqrt(r_sq)

    if r_norm < 1.0:
        raise ValueError(f"Position magnitude near origin: {r_norm} m")

    return -mu * r_vec / (r_sq * r_norm)

def compute_j2_acceleration(
    r_vec: np.ndarray,
    mu: float = MU_EARTH,
    j2: float = J2_EARTH,
    r_eq: float = R_EARTH_EQUATORIAL
) -> np.ndarray:
    """
    Computes Earth J2 zonal harmonic oblateness acceleration in ECI coordinates.

    Mathematical formulation (NASA SP-8007):
    a_x = - (3/2) * J2 * (mu * R_eq^2 / r^5) * x * (1 - 5 * z^2 / r^2)
    a_y = - (3/2) * J2 * (mu * R_eq^2 / r^5) * y * (1 - 5 * z^2 / r^2)
    a_z = - (3/2) * J2 * (mu * R_eq^2 / r^5) * z * (3 - 5 * z^2 / r^2)
    """
    x, y, z = float(r_vec[0]), float(r_vec[1]), float(r_vec[2])
    r_sq = x*x + y*y + z*z
    r_norm = math.sqrt(r_sq)

    if r_norm < 1.0:
        raise ValueError(f"Position magnitude near origin: {r_norm} m")

    z_sq = z * z
    factor = 1.5 * j2 * mu * (r_eq**2) / (r_norm**5)
    z_ratio = 5.0 * z_sq / r_sq

    a_x = -factor * x * (1.0 - z_ratio)
    a_y = -factor * y * (1.0 - z_ratio)
    a_z = -factor * z * (3.0 - z_ratio)

    return np.array([a_x, a_y, a_z], dtype=np.float64)

def compute_gravitational_acceleration(
    r_vec: np.ndarray,
    mu: float = MU_EARTH,
    enable_j2: bool = False,
    j2_coeff: float = J2_EARTH,
    r_eq: float = R_EARTH_EQUATORIAL
) -> np.ndarray:
    """
    Computes total gravitational acceleration (point mass + optional J2).
    """
    a_grav = compute_point_mass_acceleration(r_vec, mu=mu)
    if enable_j2:
        a_grav += compute_j2_acceleration(r_vec, mu=mu, j2=j2_coeff, r_eq=r_eq)
    return a_grav
