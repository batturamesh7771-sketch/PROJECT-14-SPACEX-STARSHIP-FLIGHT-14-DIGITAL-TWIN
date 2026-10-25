"""
Reentry Event Detection & Root-Finding Mechanics
================================================
Phase 6: Continuous event zero-crossing detectors for atmospheric interface,
terminal ocean surface intersection, peak dynamic pressure, peak deceleration,
and peak heat flux during atmospheric entry.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional
import numpy as np

from src.astrodynamics.frames import eci_to_ecef, ecef_to_geodetic
from .constants import OMEGA_EARTH, SEA_LEVEL_ALTITUDE_M


@dataclass
class ReentryEventRecord:
    """Record of a discrete mission event triggered during reentry propagation."""
    time_s: float
    event_name: str
    altitude_m: float
    geodetic_lat_deg: float
    geodetic_lon_deg: float
    speed_rel_ms: float
    mach: float
    dynamic_pressure_pa: float
    apparent_g_load: float
    stagnation_heat_flux_mw_m2: float
    cumulative_heat_load_mj_m2: float
    r_eci: np.ndarray
    v_eci: np.ndarray


def make_surface_intersection_event(
    h_surface_m: float = SEA_LEVEL_ALTITUDE_M,
    theta_gst_0_rad: float = 0.0
) -> Callable[[float, np.ndarray], float]:
    """
    Creates a terminal root-finding event function detecting Earth surface intersection:
    f(t, y) = h_geodetic(t, r) - h_surface = 0.
    """
    def surface_event(t: float, y: np.ndarray) -> float:
        r_eci = y[0:3]
        theta_gst = theta_gst_0_rad + OMEGA_EARTH * t
        cos_t = np.cos(theta_gst)
        sin_t = np.sin(theta_gst)
        r_ecef = np.array([
            cos_t * r_eci[0] + sin_t * r_eci[1],
            -sin_t * r_eci[0] + cos_t * r_eci[1],
            r_eci[2]
        ], dtype=np.float64)
        _, _, alt_m = ecef_to_geodetic(r_ecef)
        return float(alt_m - h_surface_m)

    surface_event.terminal = True
    surface_event.direction = -1  # Crossing from above to below
    surface_event.name = "ocean_surface_intersection"
    return surface_event


def make_altitude_crossing_event(
    target_alt_m: float,
    theta_gst_0_rad: float = 0.0,
    terminal: bool = False,
    direction: int = -1
) -> Callable[[float, np.ndarray], float]:
    """Creates an event function detecting a specific altitude boundary crossing."""
    def alt_event(t: float, y: np.ndarray) -> float:
        r_eci = y[0:3]
        theta_gst = theta_gst_0_rad + OMEGA_EARTH * t
        cos_t = np.cos(theta_gst)
        sin_t = np.sin(theta_gst)
        r_ecef = np.array([
            cos_t * r_eci[0] + sin_t * r_eci[1],
            -sin_t * r_eci[0] + cos_t * r_eci[1],
            r_eci[2]
        ], dtype=np.float64)
        _, _, alt_m = ecef_to_geodetic(r_ecef)
        return float(alt_m - target_alt_m)

    alt_event.terminal = terminal
    alt_event.direction = direction
    alt_event.name = f"altitude_{target_alt_m/1000.0:.0f}km_crossing"
    return alt_event
