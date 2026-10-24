import os
import sys
import math
import numpy as np

sys.path.insert(0, os.path.abspath("."))
from src.environment.atmosphere_1976 import us_standard_atmosphere_1976, gravity_j2, R_EARTH_EQUATORIAL, OMEGA_EARTH
from src.propulsion.raptor3_model import Raptor3Engine, G0
from src.numerics.rk4_solver import rk4_solve

def fine_tune():
    r_mag0 = R_EARTH_EQUATORIAL + 3.0
    lat_rad = math.radians(25.996)
    lon_rad = math.radians(-97.155)
    r0 = np.array([r_mag0 * math.cos(lat_rad) * math.cos(lon_rad),
                   r_mag0 * math.cos(lat_rad) * math.sin(lon_rad),
                   r_mag0 * math.sin(lat_rad)])
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH])
    v0 = np.cross(omega_vec, r0)
    m0 = 4939800.0
    y0 = np.hstack([r0, v0, m0])

    engine = Raptor3Engine(variant="SL")

    def get_throttle(t):
        if t < 0: return 0.0
        if t < 2.0: return 0.90 + 0.10 * (t / 2.0)
        if t < 28.0: return 1.00 # Initial vertical boost
        if t < 68.0: return 0.58 # Max-Q throttle bucket
        if t < 132.0: return 0.72 # Acceleration management
        if t <= 140.0:
            # 3 center engines maintain thrust for hot-staging separation
            return 0.12 * ((140.0 - t) / 8.0) + 0.091
        return 0.0

    def ode(t, y):
        r_vec = y[0:3]
        v_vec = y[3:6]
        m = y[6]
        r_mag = np.linalg.norm(r_vec)
        alt = r_mag - R_EARTH_EQUATORIAL

        atmos = us_standard_atmosphere_1976(alt)
        rho = atmos["density"]
        p_amb = atmos["pressure"]
        a_sound = atmos["speed_of_sound"]

        v_rel = v_vec - np.cross(omega_vec, r_vec)
        v_rel_mag = np.linalg.norm(v_rel)
        q = 0.5 * rho * (v_rel_mag**2)

        up_unit = r_vec / r_mag
        east_unit = np.array([-math.sin(math.atan2(r_vec[1], r_vec[0])),
                               math.cos(math.atan2(r_vec[1], r_vec[0])), 0.0])
        north_unit = np.cross(up_unit, east_unit)
        az_rad = math.radians(97.0)
        horiz_dir = math.sin(az_rad) * east_unit + math.cos(az_rad) * north_unit
        horiz_dir = horiz_dir / np.linalg.norm(horiz_dir)

        if t < 12.0:
            pitch_deg = 90.0
        elif t <= 140.0:
            frac = (t - 12.0) / 128.0
            # Pitch down to 26 deg at MECO
            pitch_deg = 90.0 - 64.0 * (frac ** 0.58)
        else:
            pitch_deg = 26.0

        pitch_rad = math.radians(pitch_deg)
        thrust_unit = math.sin(pitch_rad) * up_unit + math.cos(pitch_rad) * horiz_dir
        thrust_unit = thrust_unit / np.linalg.norm(thrust_unit)

        mach = v_rel_mag / a_sound if a_sound > 0 else 0
        if mach < 0.8:
            cd = 0.28
        elif mach < 1.2:
            cd = 0.28 + 0.35 * (math.sin(math.pi * (mach - 0.8) / 0.8) ** 2)
        elif mach < 5.0:
            cd = 0.28 + 0.35 / (1.0 + 0.5 * (mach - 1.2))
        else:
            cd = 0.32

        drag_vec = -0.5 * rho * v_rel_mag * cd * 63.617 * v_rel if v_rel_mag > 1e-3 else np.zeros(3)

        th = get_throttle(t)
        f_single, _, mdot_single = engine.compute_performance(p_amb, th)
        thrust_total = 33.0 * f_single
        mdot_total = 33.0 * mdot_single

        accel = (thrust_total * thrust_unit + drag_vec) / m + gravity_j2(r_vec)
        return np.hstack([v_vec, accel, -mdot_total])

    t_hist, y_hist = rk4_solve(ode, (0.0, 140.0), y0, 0.05)

    max_q = 0.0
    t_max_q = 0.0
    alt_max_q = 0.0
    mach_max_q = 0.0

    for t, y in zip(t_hist, y_hist):
        r_mag = np.linalg.norm(y[0:3])
        alt = (r_mag - R_EARTH_EQUATORIAL) / 1000.0
        v_rel = np.linalg.norm(y[3:6] - np.cross(omega_vec, y[0:3]))
        atmos = us_standard_atmosphere_1976(alt * 1000.0)
        q = (0.5 * atmos["density"] * (v_rel**2)) / 1000.0
        mach = v_rel / atmos["speed_of_sound"]
        if q > max_q:
            max_q = q
            t_max_q = t
            alt_max_q = alt
            mach_max_q = mach

    y_final = y_hist[-1]
    alt_meco = (np.linalg.norm(y_final[0:3]) - R_EARTH_EQUATORIAL) / 1000.0
    v_rel_meco = np.linalg.norm(y_final[3:6] - np.cross(omega_vec, y_final[0:3]))
    v_inertial_meco = np.linalg.norm(y_final[3:6])
    m_final = y_final[6] / 1000.0

    cos_ang = np.dot(r0, y_final[0:3]) / (np.linalg.norm(r0) * np.linalg.norm(y_final[0:3]))
    downrange_meco = (R_EARTH_EQUATORIAL * math.acos(cos_ang)) / 1000.0

    print("=" * 60)
    print("FINE-TUNED STARSHIP FLIGHT 14 ASCENT TRAJECTORY:")
    print("=" * 60)
    print(f"Max-Q:          {max_q:.2f} kPa at T+{t_max_q:.1f} s | Alt: {alt_max_q:.2f} km | Mach: {mach_max_q:.2f}")
    print(f"MECO Alt:       {alt_meco:.2f} km")
    print(f"MECO Downrange: {downrange_meco:.2f} km")
    print(f"MECO V_rel:     {v_rel_meco:.1f} m/s")
    print(f"MECO V_inertial:{v_inertial_meco:.1f} m/s")
    print(f"MECO Mass:      {m_final:.2f} tonnes (Propellant burned: {4939.8 - m_final:.2f} t)")
    print("=" * 60)

fine_tune()
