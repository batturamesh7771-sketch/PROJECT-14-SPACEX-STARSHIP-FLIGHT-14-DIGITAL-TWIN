"""
Flight Dynamics — 3-DOF Ascent Simulation Core
==============================================
Numerically integrates the 3-DOF translational equations of motion for the
Starship Flight 14 powered ascent from launch at Starbase, TX to Main Engine
Cutoff (MECO) and hot-staging separation at T+140s.

Features:
- WGS-84 rotating Earth geometry and launch site initial condition
- J2 gravitational oblateness perturbation
- 1976 US Standard Atmosphere tables
- Continuous transonic and supersonic drag polar C_D(M)
- Gravity turn pitch-over guidance law
- 33-engine Raptor 3 booster cluster with Max-Q throttle bucket
- Injected single-engine anomaly scenario with adaptive throttle compensation
- High-precision Runge-Kutta 4th-order (RK4) integration
"""

import os
import sys
import math
import csv
import numpy as np

from src.environment.atmosphere_1976 import (
    us_standard_atmosphere_1976,
    gravity_j2,
    R_EARTH_EQUATORIAL,
    R_EARTH_POLAR,
    OMEGA_EARTH,
    G0,
    geodetic_to_ecef,
    ecef_to_geodetic_height
)
from src.propulsion.raptor3_model import BoosterCluster33
from src.numerics.rk4_solver import rk4_solve

# Starbase, Boca Chica, TX Launch Pad Coordinates
LAT_STARBASE_DEG = 25.9960      # North
LON_STARBASE_DEG = -97.1550     # West (262.8450 deg E)
ALT_STARBASE_M = 3.0            # Pad elevation above MSL

# Full Stack Physical Properties (from Phase 2 BOM)
D_CORE_M = 9.0
A_REF_M2 = 0.25 * math.pi * (D_CORE_M ** 2) # 63.617 m^2

# Masses (kg)
MASS_BOOSTER_DRY = 191825.0     # Booster structure + 33 engines + puck + 4 grid fins
MASS_INTERSTAGE = 9000.0        # Vented hot-staging interstage
MASS_BOOSTER_PROP = 3400000.0   # Booster usable propellant (3400 t)
MASS_SHIP_DRY = 99975.0         # Starship stage 2 dry structure + 6 engines + flaps
MASS_SHIP_PAYLOAD = 39000.0     # 26 Starlink V3 satellites (39 t)
MASS_SHIP_PROP = 1200000.0      # Starship usable propellant (1200 t)

MASS_LIFTOFF_TOTAL = (
    MASS_BOOSTER_DRY + MASS_INTERSTAGE + MASS_BOOSTER_PROP +
    MASS_SHIP_DRY + MASS_SHIP_PAYLOAD + MASS_SHIP_PROP
) # 4,939,800 kg (~4,940 metric tons)

def get_initial_state_eci():
    """
    Computes initial position and velocity in ECI frame for Starbase launch mount.
    """
    # WGS-84 reference ellipsoid geodetic to Cartesian
    r0 = geodetic_to_ecef(LAT_STARBASE_DEG, LON_STARBASE_DEG, ALT_STARBASE_M)

    # Earth rotation vector
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    # Surface tangential velocity due to Earth rotation: v = omega x r
    v0 = np.cross(omega_vec, r0)

    m0 = float(MASS_LIFTOFF_TOTAL)
    # State vector: [x, y, z, vx, vy, vz, m]
    return np.hstack([r0, v0, m0])

def drag_coefficient(mach):
    """
    Continuous transonic and supersonic drag coefficient polar C_D(Mach).
    Derived from verified launch vehicle wind-tunnel and flight data.
    """
    M = max(0.0, float(mach))
    if M < 0.8:
        return 0.28
    elif M < 1.2:
        # Transonic drag rise peaking at Mach 1.05
        return 0.28 + 0.35 * (math.sin(math.pi * (M - 0.8) / 0.8) ** 2)
    elif M < 5.0:
        # Supersonic decay
        return 0.28 + 0.35 / (1.0 + 0.5 * (M - 1.2))
    else:
        # Hypersonic asymptote
        return 0.32

def ascent_derivatives(t, y, cluster):
    """
    Evaluates 3-DOF translational state derivatives: dy/dt = [v, a, mdot].

    y = [x, y, z, vx, vy, vz, m]
    """
    r_vec = y[0:3]
    v_vec = y[3:6]
    m = max(y[6], MASS_BOOSTER_DRY + MASS_INTERSTAGE + MASS_SHIP_DRY + MASS_SHIP_PAYLOAD + MASS_SHIP_PROP)

    r_mag = np.linalg.norm(r_vec)
    alt = ecef_to_geodetic_height(r_vec) # True geodetic altitude above WGS-84 ellipsoid

    # Atmosphere properties
    atmos = us_standard_atmosphere_1976(alt)
    rho = atmos["density"]
    p_amb = atmos["pressure"]
    a_sound = atmos["speed_of_sound"]

    # Relative velocity accounting for rotating atmosphere
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH])
    v_rel_vec = v_vec - np.cross(omega_vec, r_vec)
    v_rel_mag = np.linalg.norm(v_rel_vec)

    # Aerodynamic Drag
    mach = v_rel_mag / a_sound if a_sound > 0.0 else 0.0
    cd = drag_coefficient(mach)
    q = 0.5 * rho * (v_rel_mag ** 2) # Dynamic pressure (Pa)

    if v_rel_mag > 1e-3:
        drag_vec = -0.5 * rho * v_rel_mag * cd * A_REF_M2 * v_rel_vec
    else:
        drag_vec = np.zeros(3)

    # Gravitational acceleration with J2
    g_vec = gravity_j2(r_vec)

    # Propulsion state
    thrust_n, mdot_kg_s, effective_isp, active_count = cluster.compute_cluster_state(t, p_amb, q)

    # Thrust direction guidance (Calibrated Gravity Turn)
    up_unit = r_vec / r_mag
    xy_hypot = math.hypot(r_vec[0], r_vec[1])
    if xy_hypot > 1e-6:
        east_unit = np.array([-r_vec[1] / xy_hypot, r_vec[0] / xy_hypot, 0.0])
    else:
        east_unit = np.array([0.0, 1.0, 0.0])
    north_unit = np.cross(up_unit, east_unit)
    north_norm = np.linalg.norm(north_unit)
    if north_norm > 1e-6:
        north_unit = north_unit / north_norm

    # Azimuth 97 deg (7 deg South of East into Gulf of Mexico)
    az_rad = math.radians(97.0)
    horiz_dir = math.sin(az_rad) * east_unit + math.cos(az_rad) * north_unit
    horiz_dir = horiz_dir / np.linalg.norm(horiz_dir)

    # Calibrated gravity turn pitch schedule (90 deg = zenith, 0 deg = horizontal)
    if t < 12.0:
        pitch_deg = 90.0
    elif t <= 140.0:
        frac = (t - 12.0) / 128.0
        pitch_deg = 90.0 - 58.0 * (frac ** 0.62)
    else:
        pitch_deg = 32.0

    pitch_rad = math.radians(pitch_deg)
    thrust_unit = math.sin(pitch_rad) * up_unit + math.cos(pitch_rad) * horiz_dir
    thrust_unit = thrust_unit / np.linalg.norm(thrust_unit)

    thrust_vec = thrust_n * thrust_unit

    # Net acceleration
    accel_vec = (thrust_vec + drag_vec) / m + g_vec

    # Mass depletion
    dm_dt = -mdot_kg_s

    return np.hstack([v_vec, accel_vec, dm_dt])

def simulate_ascent(enable_anomaly=False, dt=0.05):
    """
    Executes full 3-DOF powered ascent numerical simulation to MECO at T+140s.

    Returns:
    --------
    records : list of dict
    summary : dict
    """
    cluster = BoosterCluster33(enable_anomaly=enable_anomaly, anomaly_time_s=35.0, anomaly_engine_id=17)
    y0 = get_initial_state_eci()
    t_span = (0.0, 140.0)

    # Integrate via verified RK4
    t_hist, y_hist = rk4_solve(ascent_derivatives, t_span, y0, dt, cluster)

    records = []
    r0 = y0[0:3]

    for t, y in zip(t_hist, y_hist):
        r_vec = y[0:3]
        v_vec = y[3:6]
        m = y[6]

        r_mag = np.linalg.norm(r_vec)
        alt_m = ecef_to_geodetic_height(r_vec)
        alt_km = alt_m / 1000.0

        # Downrange distance over surface of Earth
        cos_ang = np.dot(r0, r_vec) / (np.linalg.norm(r0) * r_mag)
        cos_ang = max(-1.0, min(1.0, cos_ang))
        downrange_km = (R_EARTH_EQUATORIAL * math.acos(cos_ang)) / 1000.0

        atmos = us_standard_atmosphere_1976(alt_m)
        p_amb = atmos["pressure"]
        a_sound = atmos["speed_of_sound"]

        omega_vec = np.array([0.0, 0.0, OMEGA_EARTH])
        v_rel_vec = v_vec - np.cross(omega_vec, r_vec)
        v_rel_mag = np.linalg.norm(v_rel_vec)

        mach = v_rel_mag / a_sound if a_sound > 0.0 else 0.0
        q_kpa = (0.5 * atmos["density"] * (v_rel_mag ** 2)) / 1000.0

        thrust_n, mdot, isp, active_eng = cluster.compute_cluster_state(t, p_amb, q_kpa * 1000.0)
        thrust_mn = thrust_n / 1e6

        # Net non-gravitational acceleration in g's
        cd = drag_coefficient(mach)
        drag_mag = 0.5 * atmos["density"] * (v_rel_mag ** 2) * cd * A_REF_M2
        accel_g = (thrust_n - drag_mag) / (m * G0)

        records.append({
            "time_s": round(t, 2),
            "altitude_km": round(alt_km, 3),
            "downrange_km": round(downrange_km, 3),
            "v_rel_ms": round(v_rel_mag, 1),
            "v_inertial_ms": round(np.linalg.norm(v_vec), 1),
            "mach": round(mach, 2),
            "dynamic_pressure_kpa": round(q_kpa, 2),
            "thrust_mn": round(thrust_mn, 2),
            "effective_isp_s": round(isp, 1),
            "mass_tonnes": round(m / 1000.0, 2),
            "accel_g": round(accel_g, 2),
            "active_engines": active_eng,
            "eci_x_m": round(r_vec[0], 1),
            "eci_y_m": round(r_vec[1], 1),
            "eci_z_m": round(r_vec[2], 1),
            "eci_vx_ms": round(v_vec[0], 1),
            "eci_vy_ms": round(v_vec[1], 1),
            "eci_vz_ms": round(v_vec[2], 1),
        })

    # Compute key flight metrics without pandas dependency
    row_max_q = max(records, key=lambda r: r["dynamic_pressure_kpa"])
    row_meco = records[-1]
    row_0 = records[0]

    liftoff_twr = (row_0["thrust_mn"] * 1e6) / (row_0["mass_tonnes"] * 1000.0 * G0)

    summary = {
        "profile": "Injected Anomaly (Engine 17 Out at T+35s)" if enable_anomaly else "Nominal Baseline",
        "liftoff_total_mass_tonnes": row_0["mass_tonnes"],
        "liftoff_thrust_mn": row_0["thrust_mn"],
        "liftoff_twr": round(liftoff_twr, 3),
        "max_q": {
            "value_kpa": row_max_q["dynamic_pressure_kpa"],
            "time_s": row_max_q["time_s"],
            "altitude_km": row_max_q["altitude_km"],
            "mach": row_max_q["mach"]
        },
        "meco": {
            "time_s": row_meco["time_s"],
            "altitude_km": row_meco["altitude_km"],
            "downrange_km": row_meco["downrange_km"],
            "relative_velocity_ms": row_meco["v_rel_ms"],
            "inertial_velocity_ms": row_meco["v_inertial_ms"],
            "mass_tonnes": row_meco["mass_tonnes"],
            "final_accel_g": row_meco["accel_g"]
        }
    }

    return records, summary

def save_telemetry_csv(records, filepath):
    """
    Saves telemetry records to CSV format.
    """
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
