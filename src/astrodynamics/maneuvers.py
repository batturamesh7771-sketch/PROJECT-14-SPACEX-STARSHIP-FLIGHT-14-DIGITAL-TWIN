"""
Orbital Maneuvers, Delta-V Calculations & Mass Depletion
========================================================
Implements impulsive and finite burn maneuvers, frame transformations (RTN -> ECI),
propellant depletion via the Tsiolkovsky rocket equation, and deorbit burn calculations.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import numpy as np

from .constants import STANDARD_GRAVITY, MU_EARTH, R_EARTH_EQUATORIAL, ENTRY_INTERFACE_ALTITUDE_M
from .state import OrbitalState
from .frames import rtn_to_eci_matrix
from .orbit_elements import compute_keplerian_elements


@dataclass
class ManeuverResult:
    """Summary of executed orbital maneuver."""
    delta_v_mag: float
    delta_v_eci: np.ndarray
    delta_v_rtn: Optional[np.ndarray]
    initial_mass_kg: float
    final_mass_kg: float
    propellant_consumed_kg: float
    burn_duration_s: float
    initial_state: OrbitalState
    post_burn_state: OrbitalState


def apply_impulsive_delta_v(
    state: OrbitalState,
    delta_v_vec: np.ndarray,
    frame: str = "ECI",
    isp_s: float = 380.0,
    g0: float = STANDARD_GRAVITY,
    min_allowable_mass_kg: float = 138975.0  # Dry mass (99.975 t) + 26 Starlinks (39 t)
) -> ManeuverResult:
    """
    Applies an impulsive Delta-V to an orbital state and computes mass depletion.

    Parameters:
    -----------
    state : OrbitalState
        Pre-burn orbital state.
    delta_v_vec : np.ndarray (3,)
        Delta-v vector in either 'ECI' or 'RTN' frame (m/s).
    frame : str
        'ECI' or 'RTN'.
    isp_s : float
        Effective specific impulse (s) (default Raptor 3 Vacuum ~ 380 s).
    g0 : float
        Standard gravitational acceleration (9.80665 m/s^2).
    min_allowable_mass_kg : float
        Minimum allowable vehicle dry + payload mass (kg).

    Returns:
    --------
    ManeuverResult
    """
    delta_v_arr = np.asarray(delta_v_vec, dtype=np.float64)
    if delta_v_arr.shape != (3,):
        raise ValueError(f"Delta-V vector must have shape (3,), got {delta_v_arr.shape}")

    delta_v_mag = float(np.linalg.norm(delta_v_arr))
    if delta_v_mag < 0.0 or not math.isfinite(delta_v_mag):
        raise ValueError(f"Invalid Delta-V magnitude: {delta_v_mag}")

    # Transform RTN to ECI if necessary
    if frame.upper() == "RTN":
        rot_matrix = rtn_to_eci_matrix(state.r, state.v)
        delta_v_eci = rot_matrix @ delta_v_arr
        delta_v_rtn = delta_v_arr
    elif frame.upper() == "ECI":
        delta_v_eci = delta_v_arr
        rot_matrix = rtn_to_eci_matrix(state.r, state.v)
        delta_v_rtn = rot_matrix.T @ delta_v_arr
    else:
        raise ValueError(f"Unsupported maneuver frame: {frame}. Must be 'ECI' or 'RTN'.")

    # Compute propellant consumption via Tsiolkovsky rocket equation:
    # m_f = m_0 * exp(-Delta_v / (Isp * g0))
    # Delta_m = m_0 - m_f = m_0 * (1 - exp(-Delta_v / (Isp * g0)))
    effective_exhaust_vel = isp_s * g0
    mass_ratio = math.exp(-delta_v_mag / effective_exhaust_vel)
    final_mass_kg = state.mass_kg * mass_ratio
    propellant_consumed_kg = state.mass_kg - final_mass_kg

    if final_mass_kg < min_allowable_mass_kg:
        raise ValueError(
            f"Maneuver exceeds available propellant! Final mass {final_mass_kg:.1f} kg is below "
            f"dry + payload structural threshold {min_allowable_mass_kg:.1f} kg "
            f"(required propellant: {propellant_consumed_kg:.1f} kg)."
        )

    # Post-burn state has identical position (impulsive assumption) and updated velocity & mass
    post_v = state.v + delta_v_eci
    post_burn_state = OrbitalState(
        r=state.r.copy(),
        v=post_v,
        epoch=state.epoch,
        frame=state.frame,
        mass_kg=final_mass_kg,
        area_m2=state.area_m2,
        cd=state.cd
    )

    return ManeuverResult(
        delta_v_mag=delta_v_mag,
        delta_v_eci=delta_v_eci,
        delta_v_rtn=delta_v_rtn,
        initial_mass_kg=state.mass_kg,
        final_mass_kg=final_mass_kg,
        propellant_consumed_kg=propellant_consumed_kg,
        burn_duration_s=0.0,
        initial_state=state,
        post_burn_state=post_burn_state
    )


def compute_hohmann_deorbit_delta_v(
    initial_elements: Dict[str, float],
    target_perigee_altitude_km: float = 50.0,
    mu: float = MU_EARTH,
    r_eq: float = R_EARTH_EQUATORIAL
) -> Tuple[float, float]:
    """
    Computes required retrograde Delta-V at apoapsis to lower periapsis to target altitude.
    
    Returns:
    --------
    delta_v_retrograde : float (positive m/s)
    new_semi_major_axis_m : float
    """
    sma = initial_elements["semi_major_axis_m"]
    ecc = initial_elements["eccentricity"]
    
    r_apo = sma * (1.0 + ecc)
    r_peri_target = r_eq + (target_perigee_altitude_km * 1000.0)

    if r_peri_target >= r_apo:
        raise ValueError("Target periapsis radius must be smaller than initial apoapsis radius.")

    # Target transfer orbit semi-major axis
    sma_transfer = (r_apo + r_peri_target) / 2.0

    # Initial velocity at apoapsis
    v_apo_initial = math.sqrt(mu * (2.0 / r_apo - 1.0 / sma))

    # Required transfer orbit velocity at apoapsis
    v_apo_transfer = math.sqrt(mu * (2.0 / r_apo - 1.0 / sma_transfer))

    # Retrograde delta-v required
    delta_v = v_apo_initial - v_apo_transfer
    return float(delta_v), float(sma_transfer)
