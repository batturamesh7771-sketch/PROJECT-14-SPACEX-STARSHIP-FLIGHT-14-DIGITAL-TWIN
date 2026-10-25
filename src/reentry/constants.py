"""
Reentry & Aerothermodynamic Physical Constants
=============================================
Phase 6: Standard geophysical, gas dynamic, aerothermal, and geometric constants
for the Starship Flight 14 atmospheric entry and deceleration simulation.
"""

from src.astrodynamics.constants import (
    MU_EARTH,
    R_EARTH_EQUATORIAL,
    R_EARTH_POLAR,
    FLATTENING_EARTH,
    J2_EARTH,
    OMEGA_EARTH,
    STANDARD_GRAVITY
)

# Thermodynamics and Gas Dynamics for Dry Air (US Standard Atmosphere 1976)
SPECIFIC_GAS_CONSTANT_AIR = 287.05287  # J / (kg * K)
SPECIFIC_HEAT_RATIO_AIR = 1.40         # Dimensionless ratio of specific heats (gamma)
SEA_LEVEL_TEMPERATURE_K = 288.15      # Standard sea-level temperature (K)
SEA_LEVEL_PRESSURE_PA = 101325.0       # Standard sea-level pressure (Pa)
SEA_LEVEL_DENSITY_KG_M3 = 1.2250       # Standard sea-level density (kg / m^3)
SEA_LEVEL_SPEED_OF_SOUND_MS = 340.294  # Standard sea-level speed of sound (m / s)

# Atmospheric Interface & Boundaries
ENTRY_INTERFACE_ALTITUDE_M = 120000.0  # 120 km international standard entry interface
SEA_LEVEL_ALTITUDE_M = 0.0             # 0 m surface / ocean impact datum
MAX_ATMOSPHERE_ALTITUDE_M = 150000.0   # 150 km sensible atmosphere cut-off

# Sutton-Graves Convective Stagnation-Point Heating Correlation
# Equation: q_dot_stag = k_SG * sqrt(rho / R_n) * V_rel^3  [W / m^2]
# Reference: Sutton, K. & Graves, R.A., "A General Stagnation-Point Convective Heating
# Equation for Arbitrary Gas Mixtures", NASA TR R-376 (1971).
# Earth air coefficient: k_SG = 1.7415e-4 W*s^3 / (m^3.5 * kg^0.5)
SUTTON_GRAVES_K_EARTH = 1.7415e-4

# Default Starship-Like Vehicle Geometric & Heating Parameters
DEFAULT_NOSE_RADIUS_M = 4.50           # Stagnation region effective radius of curvature (m)
DEFAULT_VEHICLE_MASS_KG = 177272.71    # Post-deployment & post-deorbit entry mass (kg)
DEFAULT_REFERENCE_AREA_M2 = 63.617     # Cross-sectional reference area: pi * (4.5m)^2 (m^2)
DEFAULT_WINDWARD_AREA_M2 = 360.0       # Effective high-alpha windward planform area (m^2)
DEFAULT_REFERENCE_LENGTH_M = 50.0      # Total vehicle length (m)

# Default Modeled Ocean Splashdown Target (Pacific Ocean North of Hawaii)
DEFAULT_TARGET_LAT_DEG = 26.50         # Target latitude (deg N)
DEFAULT_TARGET_LON_DEG = -162.00       # Target longitude (deg W)
DEFAULT_TARGET_RADIUS_M = 50000.0      # Target circular corridor radius (50 km)
