"""
Astrodynamics & Orbital Propagation Core Module
================================================
Phase 5: Orbital mechanics, perturbation modeling, trajectory propagation,
event detection, and uncertainty quantification for the Starship Flight 14 Digital Lab.
"""

from .constants import (
    MU_EARTH,
    R_EARTH_EQUATORIAL,
    R_EARTH_POLAR,
    FLATTENING_EARTH,
    J2_EARTH,
    OMEGA_EARTH,
    STANDARD_GRAVITY,
    ENTRY_INTERFACE_ALTITUDE_M
)
from .state import OrbitalState
from .orbit_elements import compute_keplerian_elements, classical_to_cartesian
from .gravity import compute_gravitational_acceleration, compute_point_mass_acceleration, compute_j2_acceleration
from .drag import compute_aerodynamic_drag, compute_exponential_density
from .propagator import propagate_orbit, propagate_orbit_adaptive, propagate_orbit_rk4_fixed, PropagationResult
from .events import get_standard_orbital_events
from .maneuvers import apply_impulsive_delta_v, compute_hohmann_deorbit_delta_v, ManeuverResult
from .mission_timeline import CanonicalMissionTimeline, MissionEvent
from .gmat_adapter import generate_gmat_script, execute_gmat_script, parse_gmat_report, compare_python_with_gmat
from .uncertainty import run_deterministic_sensitivity_study, run_monte_carlo_analysis, SensitivityResult, MonteCarloSummary
from .reporting import (
    export_trajectory_csv,
    export_elements_csv,
    export_events_csv,
    export_summary_json,
    export_sensitivity_csv,
    export_monte_carlo_results,
    export_gmat_comparison_csv
)

__all__ = [
    "MU_EARTH",
    "R_EARTH_EQUATORIAL",
    "R_EARTH_POLAR",
    "FLATTENING_EARTH",
    "J2_EARTH",
    "OMEGA_EARTH",
    "STANDARD_GRAVITY",
    "ENTRY_INTERFACE_ALTITUDE_M",
    "OrbitalState",
    "compute_keplerian_elements",
    "classical_to_cartesian",
    "compute_gravitational_acceleration",
    "compute_point_mass_acceleration",
    "compute_j2_acceleration",
    "compute_aerodynamic_drag",
    "compute_exponential_density",
    "propagate_orbit",
    "propagate_orbit_adaptive",
    "propagate_orbit_rk4_fixed",
    "PropagationResult",
    "get_standard_orbital_events",
    "apply_impulsive_delta_v",
    "compute_hohmann_deorbit_delta_v",
    "ManeuverResult",
    "CanonicalMissionTimeline",
    "MissionEvent",
    "generate_gmat_script",
    "execute_gmat_script",
    "parse_gmat_report",
    "compare_python_with_gmat",
    "run_deterministic_sensitivity_study",
    "run_monte_carlo_analysis",
    "SensitivityResult",
    "MonteCarloSummary",
    "export_trajectory_csv",
    "export_elements_csv",
    "export_events_csv",
    "export_summary_json",
    "export_sensitivity_csv",
    "export_monte_carlo_results",
    "export_gmat_comparison_csv"
]
