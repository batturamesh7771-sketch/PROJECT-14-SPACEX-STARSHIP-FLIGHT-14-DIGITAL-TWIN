"""
Starship Flight 14 Digital Engineering Lab - Reentry & Aerothermodynamics
========================================================================
Phase 6: Atmospheric entry, hypersonic aerodynamics, aerodynamic deceleration,
Sutton-Graves aerothermal heating, trajectory guidance, and ocean splashdown assessment.
"""

from .constants import (
    ENTRY_INTERFACE_ALTITUDE_M,
    SEA_LEVEL_ALTITUDE_M,
    MAX_ATMOSPHERE_ALTITUDE_M,
    SPECIFIC_GAS_CONSTANT_AIR,
    SPECIFIC_HEAT_RATIO_AIR,
    SUTTON_GRAVES_K_EARTH,
    DEFAULT_NOSE_RADIUS_M,
    DEFAULT_VEHICLE_MASS_KG,
    DEFAULT_REFERENCE_AREA_M2,
    DEFAULT_WINDWARD_AREA_M2,
    DEFAULT_REFERENCE_LENGTH_M,
    DEFAULT_TARGET_LAT_DEG,
    DEFAULT_TARGET_LON_DEG,
    DEFAULT_TARGET_RADIUS_M
)

from .atmosphere import (
    USStandardAtmosphere1976,
    AtmosphericState,
    get_atmospheric_state,
    compute_density,
    compute_speed_of_sound
)

from .vehicle import (
    ReentryVehicleConfig
)

from .aerodynamics import (
    AerodynamicForces,
    compute_aerodynamic_coefficients,
    compute_aerodynamic_forces
)

from .heating import (
    HeatingState,
    compute_stagnation_heat_flux,
    compute_radiative_equilibrium_temperature,
    evaluate_heating_state
)

from .guidance import (
    GuidanceCommand,
    CrossrangeBankGuidanceController
)

from .splashdown import (
    TerminalSplashdownAssessment,
    great_circle_distance_m,
    compute_crossrange_and_downrange_error,
    assess_terminal_splashdown
)

from .events import (
    ReentryEventRecord,
    make_surface_intersection_event,
    make_altitude_crossing_event
)

from .dynamics import (
    ReentryTrajectoryStep,
    ReentrySimulationResult,
    propagate_reentry
)

from .uncertainty import (
    SensitivityResult,
    MonteCarloSummary,
    run_reentry_sensitivity_study,
    run_reentry_monte_carlo
)

from .reporting import (
    export_trajectory_csv,
    export_aerothermal_history_csv,
    export_event_log_csv,
    export_control_history_csv,
    export_sensitivity_csv,
    export_monte_carlo_csv,
    export_json_summary
)

__all__ = [
    "ENTRY_INTERFACE_ALTITUDE_M",
    "SEA_LEVEL_ALTITUDE_M",
    "MAX_ATMOSPHERE_ALTITUDE_M",
    "SPECIFIC_GAS_CONSTANT_AIR",
    "SPECIFIC_HEAT_RATIO_AIR",
    "SUTTON_GRAVES_K_EARTH",
    "DEFAULT_NOSE_RADIUS_M",
    "DEFAULT_VEHICLE_MASS_KG",
    "DEFAULT_REFERENCE_AREA_M2",
    "DEFAULT_WINDWARD_AREA_M2",
    "DEFAULT_REFERENCE_LENGTH_M",
    "DEFAULT_TARGET_LAT_DEG",
    "DEFAULT_TARGET_LON_DEG",
    "DEFAULT_TARGET_RADIUS_M",
    "USStandardAtmosphere1976",
    "AtmosphericState",
    "get_atmospheric_state",
    "compute_density",
    "compute_speed_of_sound",
    "ReentryVehicleConfig",
    "AerodynamicForces",
    "compute_aerodynamic_coefficients",
    "compute_aerodynamic_forces",
    "HeatingState",
    "compute_stagnation_heat_flux",
    "compute_radiative_equilibrium_temperature",
    "evaluate_heating_state",
    "GuidanceCommand",
    "CrossrangeBankGuidanceController",
    "TerminalSplashdownAssessment",
    "great_circle_distance_m",
    "compute_crossrange_and_downrange_error",
    "assess_terminal_splashdown",
    "ReentryEventRecord",
    "make_surface_intersection_event",
    "make_altitude_crossing_event",
    "ReentryTrajectoryStep",
    "ReentrySimulationResult",
    "propagate_reentry",
    "SensitivityResult",
    "MonteCarloSummary",
    "run_reentry_sensitivity_study",
    "run_reentry_monte_carlo",
    "export_trajectory_csv",
    "export_aerothermal_history_csv",
    "export_event_log_csv",
    "export_control_history_csv",
    "export_sensitivity_csv",
    "export_monte_carlo_csv",
    "export_json_summary"
]
