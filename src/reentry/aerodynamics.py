"""
Reentry Aerodynamics & Force Model
==================================
Phase 6: Hypersonic, supersonic, and subsonic aerodynamic force calculations,
dynamic pressure, Mach number, drag and lift vectors, bank angle rotation,
and structural g-load evaluation for Starship reentry.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import numpy as np

from .constants import STANDARD_GRAVITY
from .vehicle import ReentryVehicleConfig


@dataclass
class AerodynamicForces:
    """Complete aerodynamic state snapshot at a given trajectory epoch."""
    mach: float
    dynamic_pressure_pa: float
    speed_relative_ms: float
    cd: float
    cl: float
    f_drag_vec_n: np.ndarray
    f_lift_vec_n: np.ndarray
    f_total_vec_n: np.ndarray
    a_aero_vec_ms2: np.ndarray
    apparent_g_load: float
    lift_unit_vec: np.ndarray


def compute_aerodynamic_coefficients(
    mach: float,
    angle_of_attack_deg: float,
    config: ReentryVehicleConfig
) -> Tuple[float, float]:
    """
    Computes Mach- and angle-of-attack-dependent drag (Cd) and lift (Cl) coefficients
    for a blunt-body vehicle.

    Uses modified Newtonian cross-flow theory at hypersonic Mach (M >= 5),
    smoothly blending to supersonic and subsonic regimes.
    """
    aoa_rad = math.radians(min(max(angle_of_attack_deg, 0.0), 90.0))
    sin_a = math.sin(aoa_rad)
    cos_a = math.cos(aoa_rad)

    # Hypersonic regime (M >= 5)
    # Peak blunt-body drag at alpha=70-90 deg: Cd ~ 1.5 - 1.8
    # Lift peaks around alpha = 45-55 deg: Cl = Cl_max * sin^2(alpha) * cos(alpha)
    cd_hypersonic = 0.15 + (config.cd_hypersonic_70deg - 0.15) * (sin_a ** 3)
    cl_hypersonic = 2.0 * config.cl_hypersonic_70deg * (sin_a ** 2) * cos_a

    if mach >= 5.0:
        return cd_hypersonic, cl_hypersonic

    # Subsonic regime (M <= 0.8)
    cd_sub = 0.10 + (config.cd_subsonic - 0.10) * (sin_a ** 2)
    cl_sub = 1.2 * (sin_a ** 2) * cos_a

    if mach <= 0.8:
        return cd_sub, cl_sub

    # Transonic / Supersonic blend (0.8 < M < 5.0)
    fraction = (mach - 0.8) / (5.0 - 0.8)
    # Smooth cubic hermite blend
    s = fraction * fraction * (3.0 - 2.0 * fraction)
    cd = (1.0 - s) * cd_sub + s * cd_hypersonic
    cl = (1.0 - s) * cl_sub + s * cl_hypersonic

    return cd, cl


def compute_aerodynamic_forces(
    r_vec: np.ndarray,
    v_rel_vec: np.ndarray,
    density_kg_m3: float,
    speed_of_sound_ms: float,
    config: ReentryVehicleConfig,
    bank_angle_deg: float = 0.0,
    angle_of_attack_deg: Optional[float] = None
) -> AerodynamicForces:
    """
    Computes full 3D aerodynamic forces, acceleration, dynamic pressure, and g-load
    in ECI / ECEF coordinates based on relative velocity and vehicle state.
    """
    v_rel_mag = float(np.linalg.norm(v_rel_vec))
    aoa_deg = angle_of_attack_deg if angle_of_attack_deg is not None else config.nominal_angle_of_attack_deg

    # Zero velocity / pure vacuum guard
    if v_rel_mag < 1e-6 or density_kg_m3 <= 1e-15:
        zero_vec = np.zeros(3, dtype=np.float64)
        return AerodynamicForces(
            mach=0.0,
            dynamic_pressure_pa=0.0,
            speed_relative_ms=v_rel_mag,
            cd=0.0,
            cl=0.0,
            f_drag_vec_n=zero_vec.copy(),
            f_lift_vec_n=zero_vec.copy(),
            f_total_vec_n=zero_vec.copy(),
            a_aero_vec_ms2=zero_vec.copy(),
            apparent_g_load=0.0,
            lift_unit_vec=np.array([0.0, 0.0, 1.0], dtype=np.float64)
        )

    # 1. Kinematic quantities
    mach = v_rel_mag / max(speed_of_sound_ms, 1e-3)
    q_dyn = 0.5 * density_kg_m3 * (v_rel_mag**2)

    # 2. Coefficients
    cd, cl = compute_aerodynamic_coefficients(mach, aoa_deg, config)
    a_ref = config.reference_area_m2
    mass = config.mass_kg

    # 3. Relative velocity unit vector
    v_hat = v_rel_vec / v_rel_mag

    # 4. Drag force opposes relative velocity
    f_drag_mag = q_dyn * cd * a_ref
    f_drag_vec = -f_drag_mag * v_hat

    # 5. Lift direction vector construction
    r_mag = float(np.linalg.norm(r_vec))
    r_hat = r_vec / max(r_mag, 1.0)

    # Horizontal cross-track normal vector w = r_hat x v_hat
    w_vec = np.cross(r_hat, v_hat)
    w_mag = float(np.linalg.norm(w_vec))

    if w_mag < 1e-6:
        # Near vertical descent: construct arbitrary orthogonal vector
        fallback = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        if abs(np.dot(fallback, v_hat)) > 0.9:
            fallback = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        w_hat = np.cross(v_hat, fallback)
        w_hat = w_hat / np.linalg.norm(w_hat)
    else:
        w_hat = w_vec / w_mag

    # In-plane upward lift unit vector (opposing downward gravity): u_up = v_hat x w_hat
    u_up = np.cross(v_hat, w_hat)
    u_up_norm = float(np.linalg.norm(u_up))
    if u_up_norm > 1e-12:
        u_up = u_up / u_up_norm

    # Rotate lift vector about v_hat by bank angle sigma
    sigma_rad = math.radians(bank_angle_deg)
    l_hat = (math.cos(sigma_rad) * u_up) + (math.sin(sigma_rad) * w_hat)
    l_hat_norm = float(np.linalg.norm(l_hat))
    if l_hat_norm > 1e-12:
        l_hat = l_hat / l_hat_norm

    # Lift force vector
    f_lift_mag = q_dyn * cl * a_ref
    f_lift_vec = f_lift_mag * l_hat

    # 6. Total aerodynamic force and acceleration
    f_total_vec = f_drag_vec + f_lift_vec
    a_aero_vec = f_total_vec / mass
    a_aero_mag = float(np.linalg.norm(a_aero_vec))
    g_load = a_aero_mag / STANDARD_GRAVITY

    return AerodynamicForces(
        mach=mach,
        dynamic_pressure_pa=q_dyn,
        speed_relative_ms=v_rel_mag,
        cd=cd,
        cl=cl,
        f_drag_vec_n=f_drag_vec,
        f_lift_vec_n=f_lift_vec,
        f_total_vec_n=f_total_vec,
        a_aero_vec_ms2=a_aero_vec,
        apparent_g_load=g_load,
        lift_unit_vec=l_hat
    )
