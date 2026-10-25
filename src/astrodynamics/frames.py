"""
Coordinate Frames & Transformations
===================================
Rigorous transforms between:
- Earth-Centered Inertial J2000 (ECI)
- Earth-Centered Earth-Fixed (ECEF)
- WGS-84 Geodetic Coordinates (Latitude, Longitude, Altitude via Bowring's method)
- Radial-Transverse-Normal (RTN / RSW / Hill frame) for spacecraft-relative vectors
"""

import math
import numpy as np
from .constants import R_EARTH_EQUATORIAL, R_EARTH_POLAR, FLATTENING_EARTH, OMEGA_EARTH

def eci_to_ecef(r_eci: np.ndarray, v_eci: np.ndarray, theta_gst_rad: float):
    """
    Transforms state vector from ECI to ECEF accounting for frame rotation.

    Parameters:
    -----------
    r_eci : np.ndarray (3,)
        Position in ECI (m)
    v_eci : np.ndarray (3,)
        Velocity in ECI (m/s)
    theta_gst_rad : float
        Greenwich Sidereal Time / rotation angle (rad)

    Returns:
    --------
    r_ecef, v_ecef : np.ndarray (3,)
    """
    cos_t = math.cos(theta_gst_rad)
    sin_t = math.sin(theta_gst_rad)

    R_z = np.array([
        [ cos_t, sin_t, 0.0],
        [-sin_t, cos_t, 0.0],
        [   0.0,   0.0, 1.0]
    ], dtype=np.float64)

    r_ecef = R_z @ r_eci

    # v_ecef = R_z @ v_eci - omega x r_ecef
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    v_ecef = (R_z @ v_eci) - np.cross(omega_vec, r_ecef)

    return r_ecef, v_ecef

def ecef_to_eci(r_ecef: np.ndarray, v_ecef: np.ndarray, theta_gst_rad: float):
    """
    Transforms state vector from ECEF to ECI accounting for frame rotation.
    """
    cos_t = math.cos(theta_gst_rad)
    sin_t = math.sin(theta_gst_rad)

    R_z_inv = np.array([
        [cos_t, -sin_t, 0.0],
        [sin_t,  cos_t, 0.0],
        [  0.0,    0.0, 1.0]
    ], dtype=np.float64)

    r_eci = R_z_inv @ r_ecef
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    v_eci = R_z_inv @ (v_ecef + np.cross(omega_vec, r_ecef))

    return r_eci, v_eci

def ecef_to_geodetic(r_ecef: np.ndarray):
    """
    Computes geodetic latitude, longitude, and height above WGS-84 ellipsoid
    using Bowring's closed-form algorithm (exact to sub-millimeter level).

    Parameters:
    -----------
    r_ecef : np.ndarray (3,)
        Position in ECEF (m)

    Returns:
    --------
    lat_deg, lon_deg, alt_m : float
    """
    x, y, z = float(r_ecef[0]), float(r_ecef[1]), float(r_ecef[2])
    a = R_EARTH_EQUATORIAL
    b = R_EARTH_POLAR
    e2 = 2.0 * FLATTENING_EARTH - FLATTENING_EARTH**2
    e_prime2 = (a**2 - b**2) / (b**2)

    p = math.hypot(x, y)
    lon_rad = math.atan2(y, x)

    if p < 1e-6:
        # Near pole
        lat_rad = math.copysign(math.pi / 2.0, z)
        alt_m = abs(z) - b
        return math.degrees(lat_rad), math.degrees(lon_rad), alt_m

    theta = math.atan2(z * a, p * b)
    lat_rad = math.atan2(
        z + e_prime2 * b * (math.sin(theta)**3),
        p - e2 * a * (math.cos(theta)**3)
    )

    n_val = a / math.sqrt(1.0 - e2 * (math.sin(lat_rad)**2))
    alt_m = (p / math.cos(lat_rad)) - n_val

    return math.degrees(lat_rad), math.degrees(lon_rad), alt_m

def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    """
    Computes ECEF position from geodetic latitude, longitude, and height.
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    a = R_EARTH_EQUATORIAL
    e2 = 2.0 * FLATTENING_EARTH - FLATTENING_EARTH**2

    n_val = a / math.sqrt(1.0 - e2 * (math.sin(lat_rad)**2))
    x = (n_val + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (n_val + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (n_val * (1.0 - e2) + alt_m) * math.sin(lat_rad)

    return np.array([x, y, z], dtype=np.float64)

def eci_to_rtn_matrix(r_eci: np.ndarray, v_eci: np.ndarray) -> np.ndarray:
    """
    Constructs the rotation matrix from ECI to Radial-Transverse-Normal (RTN / RSW).
    - R (Radial): Unit vector along position r
    - N (Normal / Cross-track): Unit vector along orbital angular momentum h = r x v
    - T (Transverse / In-track): Completes right-handed system (N x R)
    """
    r_norm = np.linalg.norm(r_eci)
    if r_norm < 1e-6:
        raise ValueError("Position vector near zero; cannot define RTN frame")

    u_r = r_eci / r_norm
    h_vec = np.cross(r_eci, v_eci)
    h_norm = np.linalg.norm(h_vec)
    if h_norm < 1e-6:
        raise ValueError("Angular momentum near zero; rectilinear trajectory cannot define RTN")

    u_n = h_vec / h_norm
    u_t = np.cross(u_n, u_r)

    # Matrix transforms ECI vector to RTN: v_rtn = R_eci_to_rtn @ v_eci
    return np.vstack([u_r, u_t, u_n])

def rtn_to_eci_matrix(r_eci: np.ndarray, v_eci: np.ndarray) -> np.ndarray:
    """
    Constructs the rotation matrix from RTN to ECI (transpose of ECI to RTN).
    v_eci = R_rtn_to_eci @ v_rtn
    """
    return eci_to_rtn_matrix(r_eci, v_eci).T

