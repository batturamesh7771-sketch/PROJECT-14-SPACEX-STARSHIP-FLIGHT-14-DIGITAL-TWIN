"""
Astrodynamics Constants & Geodetic Reference Parameters
========================================================
Authoritative geophysical and orbital constants derived from WGS-84 (NIMA TR8350.2)
and standard space vehicle design parameters (NASA SP-8007).
"""

# Earth Gravitational Parameter (GM) - WGS-84 (m^3 / s^2)
MU_EARTH = 3.986004418e14

# Earth Equatorial Semi-Major Axis (m)
R_EARTH_EQUATORIAL = 6378137.0

# Earth Polar Semi-Minor Axis (m)
R_EARTH_POLAR = 6356752.3142

# Earth Ellipsoid Flattening (f)
FLATTENING_EARTH = 1.0 / 298.257223563

# Earth Second Zonal Harmonic (J2) - Oblateness Coefficient (dimensionless)
J2_EARTH = 1.08262668e-3

# Earth Mean Angular Rotation Rate (rad/s)
OMEGA_EARTH = 7.292115e-5

# Standard Gravitational Acceleration at Sea Level (m/s^2)
STANDARD_GRAVITY = 9.80665

# Standard Atmospheric Boundary Thresholds (m)
ATMOSPHERE_ENTRY_ALTITUDE = 120000.0 # 120 km Entry Interface (EI)
ENTRY_INTERFACE_ALTITUDE_M = ATMOSPHERE_ENTRY_ALTITUDE
R_EARTH_ENTRY_INTERFACE = R_EARTH_EQUATORIAL + ENTRY_INTERFACE_ALTITUDE_M
KARMAN_LINE_ALTITUDE = 100000.0      # 100 km Legal / Astronautical boundary

# Astronomical Constants
SPEED_OF_LIGHT = 299792458.0 # m/s
SOLAR_RAD_PRESSURE_1AU = 4.56e-6 # N/m^2 (nominal solar radiation pressure at 1 AU)

