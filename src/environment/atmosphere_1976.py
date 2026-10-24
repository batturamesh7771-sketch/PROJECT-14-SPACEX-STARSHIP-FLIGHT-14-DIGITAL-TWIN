"""
Environment Module — 1976 US Standard Atmosphere & WGS-84 Gravity Model
========================================================================
Implements the 1976 US Standard Atmosphere (NOAA/NASA/USAF) from sea level
to exosphere, and the WGS-84 Earth gravitational potential including J2 oblateness.
"""

import math
import numpy as np

# Physical Constants (CODATA / WGS-84)
R_EARTH_EQUATORIAL = 6378137.0         # Equatorial radius (m)
R_EARTH_POLAR = 6356752.3142           # Polar radius (m)
R_EARTH_GEOPOTENTIAL = 6356766.0       # Geopotential Earth radius (m)
GM_EARTH = 3.986004418e14              # Earth gravitational parameter (m^3/s^2)
J2_EARTH = 1.08262668e-3               # Second zonal harmonic coefficient
OMEGA_EARTH = 7.292115e-5              # Earth rotation angular velocity (rad/s)
G0 = 9.80665                           # Standard sea-level acceleration of gravity (m/s^2)
R_AIR = 287.05287                      # Specific gas constant for dry air (J/(kg*K))
GAMMA_AIR = 1.40                       # Ratio of specific heats for dry air

def geodetic_to_ecef(lat_deg, lon_deg, alt_m=0.0):
    """
    Converts WGS-84 geodetic coordinates to Cartesian ECEF/ECI vector (m).
    """
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    a = R_EARTH_EQUATORIAL
    b = R_EARTH_POLAR
    e2 = (a**2 - b**2) / (a**2)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    N = a / math.sqrt(1.0 - e2 * (sin_lat ** 2))
    p = (N + alt_m) * cos_lat
    z = (N * (1.0 - e2) + alt_m) * sin_lat
    x = p * math.cos(lon)
    y = p * math.sin(lon)
    return np.array([x, y, z], dtype=np.float64)

def ecef_to_geodetic_height(r_vec):
    """
    Computes geodetic altitude (height above WGS-84 reference ellipsoid) in meters
    using Bowring's closed-form algorithm.
    """
    x, y, z = float(r_vec[0]), float(r_vec[1]), float(r_vec[2])
    p = math.hypot(x, y)
    if p < 1e-6:
        return abs(z) - R_EARTH_POLAR
    a = R_EARTH_EQUATORIAL
    b = R_EARTH_POLAR
    e2 = (a**2 - b**2) / (a**2)
    ep2 = (a**2 - b**2) / (b**2)
    theta = math.atan2(z * a, p * b)
    phi = math.atan2(z + ep2 * b * (math.sin(theta)**3), p - e2 * a * (math.cos(theta)**3))
    N = a / math.sqrt(1.0 - e2 * (math.sin(phi)**2))
    h = p / math.cos(phi) - N
    return h

# 1976 US Standard Atmosphere Layer Tables (0 to 86 km geopotential)
# (H_base [m], T_base [K], L [K/m], P_base [Pa])
ATMOS_LAYERS = [
    (0.0,       288.15, -0.0065, 101325.0),
    (11000.0,   216.65,  0.0,     22632.06),
    (20000.0,   216.65, +0.0010,  5474.889),
    (32000.0,   228.65, +0.0028,  868.0187),
    (47000.0,   270.65,  0.0,     110.9063),
    (51000.0,   270.65, -0.0028,  66.93887),
    (71000.0,   214.65, -0.0020,  3.956420),
    (84852.0,   186.95,  0.0,     0.3733836)
]

def us_standard_atmosphere_1976(geometric_alt_m):
    """
    Computes 1976 US Standard Atmosphere properties at a given geometric altitude.

    Parameters:
    -----------
    geometric_alt_m : float
        Altitude above mean sea level (m)

    Returns:
    --------
    dict:
        temperature : float (K)
        pressure : float (Pa)
        density : float (kg/m^3)
        speed_of_sound : float (m/s)
        viscosity : float (Pa*s)
    """
    h = max(float(geometric_alt_m), 0.0)

    # Convert geometric to geopotential altitude
    H = (R_EARTH_GEOPOTENTIAL * h) / (R_EARTH_GEOPOTENTIAL + h)

    # Exosphere / Deep vacuum above 86 km
    if H >= 84852.0:
        # Exponential vacuum decay above mesosphere
        H_ref = 84852.0
        T = 186.95
        scale_height = 6000.0 # m
        P = 0.3733836 * math.exp(-(H - H_ref) / scale_height)
        rho = P / (R_AIR * T)
        a = math.sqrt(GAMMA_AIR * R_AIR * T)
        mu = (1.458e-6 * (T ** 1.5)) / (T + 110.4)
        return {
            "temperature": T,
            "pressure": max(P, 1e-12),
            "density": max(rho, 1e-15),
            "speed_of_sound": a,
            "viscosity": mu
        }

    # Locate atmospheric layer
    for i in range(len(ATMOS_LAYERS) - 1):
        h_base, T_base, L, P_base = ATMOS_LAYERS[i]
        h_next = ATMOS_LAYERS[i+1][0]

        if h_base <= H < h_next:
            dh = H - h_base
            if abs(L) < 1e-10:
                # Isothermal layer
                T = T_base
                P = P_base * math.exp(-G0 * dh / (R_AIR * T_base))
            else:
                # Gradient layer
                T = T_base + L * dh
                P = P_base * (T / T_base) ** (-G0 / (L * R_AIR))

            rho = P / (R_AIR * T)
            a = math.sqrt(GAMMA_AIR * R_AIR * T)
            # Sutherland's law for dynamic viscosity
            mu = (1.458e-6 * (T ** 1.5)) / (T + 110.4)

            return {
                "temperature": T,
                "pressure": P,
                "density": rho,
                "speed_of_sound": a,
                "viscosity": mu
            }

    # Fallback to sea-level
    return {
        "temperature": 288.15,
        "pressure": 101325.0,
        "density": 1.225,
        "speed_of_sound": 340.294,
        "viscosity": 1.789e-5
    }

def gravity_j2(r_vec):
    """
    Computes Earth gravitational acceleration vector including J2 zonal harmonic.

    Parameters:
    -----------
    r_vec : array_like [x, y, z]
        Position vector in Earth-Centered Inertial (ECI) coordinates (m)

    Returns:
    --------
    g_vec : np.ndarray [gx, gy, gz]
        Gravitational acceleration vector (m/s^2)
    """
    r_vec = np.asarray(r_vec, dtype=np.float64)
    r = np.linalg.norm(r_vec)
    if r < 1000.0:
        return np.array([0.0, 0.0, -G0])

    x, y, z = r_vec
    r2 = r * r
    r3 = r2 * r
    r5 = r3 * r2
    z2 = z * z

    # Spherical gravity
    g_sph = -(GM_EARTH / r3) * r_vec

    # J2 oblateness perturbation
    j2_factor = -1.5 * J2_EARTH * GM_EARTH * (R_EARTH_EQUATORIAL ** 2) / r5
    a_j2 = np.array([
        j2_factor * x * (1.0 - 5.0 * (z2 / r2)),
        j2_factor * y * (1.0 - 5.0 * (z2 / r2)),
        j2_factor * z * (3.0 - 5.0 * (z2 / r2))
    ])

    return g_sph + a_j2
