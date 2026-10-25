"""
Orbital Event Functions & Crossing Detectors
===========================================
Defines root-finding event functions for orbital integration using SciPy solve_ivp
and custom step-wise detectors:
- Periapsis passage (r . v = 0, rising)
- Apoapsis passage (r . v = 0, falling)
- Ascending node crossing (z = 0, rising)
- Descending node crossing (z = 0, falling)
- Atmospheric entry interface (altitude = 120 km, falling, terminal)
- Ground surface impact (altitude = 0 km, falling, terminal)
"""

import math
from typing import Callable, Dict, Any, List
import numpy as np

from .constants import R_EARTH_EQUATORIAL, R_EARTH_ENTRY_INTERFACE, ENTRY_INTERFACE_ALTITUDE_M


def make_periapsis_event() -> Callable[[float, np.ndarray], float]:
    """
    Detects periapsis passage: r . v = 0, changing from negative to positive.
    """
    def periapsis_event(t: float, y: np.ndarray) -> float:
        r = y[0:3]
        v = y[3:6]
        return float(np.dot(r, v))
    
    periapsis_event.direction = 1.0  # Crossing from negative to positive
    periapsis_event.terminal = False
    periapsis_event.name = "periapsis"
    return periapsis_event


def make_apoapsis_event() -> Callable[[float, np.ndarray], float]:
    """
    Detects apoapsis passage: r . v = 0, changing from positive to negative.
    """
    def apoapsis_event(t: float, y: np.ndarray) -> float:
        r = y[0:3]
        v = y[3:6]
        return float(np.dot(r, v))
    
    apoapsis_event.direction = -1.0  # Crossing from positive to negative
    apoapsis_event.terminal = False
    apoapsis_event.name = "apoapsis"
    return apoapsis_event


def make_ascending_node_event() -> Callable[[float, np.ndarray], float]:
    """
    Detects equatorial ascending node crossing: z = 0, vz > 0.
    """
    def ascending_node_event(t: float, y: np.ndarray) -> float:
        return float(y[2])
    
    ascending_node_event.direction = 1.0  # Crossing z=0 upward
    ascending_node_event.terminal = False
    ascending_node_event.name = "ascending_node"
    return ascending_node_event


def make_descending_node_event() -> Callable[[float, np.ndarray], float]:
    """
    Detects equatorial descending node crossing: z = 0, vz < 0.
    """
    def descending_node_event(t: float, y: np.ndarray) -> float:
        return float(y[2])
    
    descending_node_event.direction = -1.0  # Crossing z=0 downward
    descending_node_event.terminal = False
    descending_node_event.name = "descending_node"
    return descending_node_event


def make_entry_interface_event(
    altitude_threshold_m: float = ENTRY_INTERFACE_ALTITUDE_M,
    r_eq: float = R_EARTH_EQUATORIAL,
    terminal: bool = True
) -> Callable[[float, np.ndarray], float]:
    """
    Detects atmospheric entry interface crossing (default 120 km spherical altitude).
    Triggers when altitude crosses altitude_threshold_m downward.
    """
    target_radius = r_eq + altitude_threshold_m

    def entry_interface_event(t: float, y: np.ndarray) -> float:
        r = y[0:3]
        r_mag = math.sqrt(float(r[0]*r[0] + r[1]*r[1] + r[2]*r[2]))
        return r_mag - target_radius

    entry_interface_event.direction = -1.0  # Inward/downward crossing
    entry_interface_event.terminal = terminal
    entry_interface_event.name = "atmospheric_entry_interface"
    return entry_interface_event


def make_surface_impact_event(
    r_eq: float = R_EARTH_EQUATORIAL,
    terminal: bool = True
) -> Callable[[float, np.ndarray], float]:
    """
    Detects surface collision / impact: r - R_earth = 0, downward.
    """
    def surface_impact_event(t: float, y: np.ndarray) -> float:
        r = y[0:3]
        r_mag = math.sqrt(float(r[0]*r[0] + r[1]*r[1] + r[2]*r[2]))
        return r_mag - r_eq

    surface_impact_event.direction = -1.0
    surface_impact_event.terminal = terminal
    surface_impact_event.name = "surface_impact"
    return surface_impact_event


def get_standard_orbital_events(
    terminal_entry: bool = False,
    entry_alt_m: float = ENTRY_INTERFACE_ALTITUDE_M
) -> List[Callable]:
    """
    Returns standard list of orbital events for numerical propagation:
    - Periapsis passage
    - Apoapsis passage
    - Ascending node
    - Descending node
    - Atmospheric entry interface (120 km)
    - Surface impact (0 km)
    """
    return [
        make_periapsis_event(),
        make_apoapsis_event(),
        make_ascending_node_event(),
        make_descending_node_event(),
        make_entry_interface_event(altitude_threshold_m=entry_alt_m, terminal=terminal_entry),
        make_surface_impact_event(terminal=True)
    ]
