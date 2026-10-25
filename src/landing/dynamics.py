"""
Planar equations of motion, atmospheric density, aerodynamic forces, and RK4 numerical integrator.
"""

import math
from typing import Tuple, List, Callable, Optional
from src.landing.state import LandingState
from src.landing.vehicle import StarshipLandingVehicle
from src.landing.propulsion import RaptorLandingPropulsion


def get_atmospheric_density(altitude_m: float) -> float:
    """
    Compute atmospheric density for low-altitude terminal flight using
    the 1976 US Standard Atmosphere tropospheric barometric formula.
    Valid from sea level to 11,000 m.
    """
    alt = max(0.0, altitude_m)
    p0 = 101325.0       # Sea level pressure [Pa]
    t0 = 288.15         # Sea level temperature [K]
    lapse_rate = 0.0065 # Temperature lapse rate [K/m]
    r_gas = 287.05287   # Specific gas constant for air [J/(kg*K)]
    g0 = 9.80665        # Gravity acceleration [m/s^2]

    if alt <= 11000.0:
        t = t0 - lapse_rate * alt
        p = p0 * ((t / t0) ** (g0 / (lapse_rate * r_gas)))
    else:
        # Isothermal layer above 11 km
        t11 = t0 - lapse_rate * 11000.0
        p11 = p0 * ((t11 / t0) ** (g0 / (lapse_rate * r_gas)))
        p = p11 * math.exp(-g0 * (alt - 11000.0) / (r_gas * t11))
        t = t11

    return p / (r_gas * t)


def compute_aerodynamic_forces(state: LandingState,
                               vehicle: StarshipLandingVehicle) -> Tuple[float, float, float, float]:
    """
    Compute aerodynamic drag and lift forces in the Local Terminal Frame.
    Returns: (F_aero_x, F_aero_z, drag_magnitude, lift_magnitude)
    """
    rho = get_atmospheric_density(state.z)
    speed = state.speed_mps
    if speed < 1e-4:
        return 0.0, 0.0, 0.0, 0.0

    # Effective aero properties based on vehicle pitch attitude
    a_eff, cd_eff, cl_eff = vehicle.effective_aero_properties(state.pitch_deg)

    q = 0.5 * rho * (speed ** 2)
    drag_mag = q * cd_eff * a_eff
    lift_mag = q * cl_eff * a_eff

    # Drag directly opposes the velocity vector
    drag_x = -drag_mag * (state.vx / speed)
    drag_z = -drag_mag * (state.vz / speed)

    # Lift acts perpendicular to velocity vector (pointing upward / forward)
    # Unit normal to velocity: n_x = -v_z / speed, n_z = v_x / speed
    lift_x = lift_mag * (-state.vz / speed)
    lift_z = lift_mag * (state.vx / speed)

    f_aero_x = drag_x + lift_x
    f_aero_z = drag_z + lift_z

    return f_aero_x, f_aero_z, drag_mag, lift_mag


def rk4_step(state: LandingState,
             vehicle: StarshipLandingVehicle,
             propulsion: RaptorLandingPropulsion,
             dt_s: float,
             pitch_deg: float,
             pitch_rate_deg_s: float,
             mode: str = "prescribed_kinematic_flip",
             applied_torque_Nm: float = 0.0) -> LandingState:
    """
    Advance landing state vector by dt_s using explicit 4th-order Runge-Kutta.
    """
    g0 = 9.80665

    # Static thrust vector and mass flow for this sub-step
    fx_thrust, fz_thrust = propulsion.get_thrust_vector(pitch_deg)
    mass_flow = (propulsion.current_thrust_N / (propulsion.specific_impulse_s * g0)) if propulsion.current_thrust_N > 0 else 0.0

    def derivatives(x, z, vx, vz, m):
        temp_state = LandingState(
            time_s=state.time_s, x=x, z=z, vx=vx, vz=vz, mass_kg=m,
            pitch_deg=pitch_deg, pitch_rate_deg_s=pitch_rate_deg_s
        )
        fax, faz, drag_mag, _ = compute_aerodynamic_forces(temp_state, vehicle)

        ax = (fax + fx_thrust) / max(m, 1.0)
        az = (faz + fz_thrust) / max(m, 1.0) - g0
        dm = -mass_flow
        return vx, vz, ax, az, dm

    # RK4 coefficients
    k1_x, k1_z, k1_vx, k1_vz, k1_m = derivatives(
        state.x, state.z, state.vx, state.vz, state.mass_kg
    )

    k2_x, k2_z, k2_vx, k2_vz, k2_m = derivatives(
        state.x + 0.5 * dt_s * k1_x,
        state.z + 0.5 * dt_s * k1_z,
        state.vx + 0.5 * dt_s * k1_vx,
        state.vz + 0.5 * dt_s * k1_vz,
        state.mass_kg + 0.5 * dt_s * k1_m
    )

    k3_x, k3_z, k3_vx, k3_vz, k3_m = derivatives(
        state.x + 0.5 * dt_s * k2_x,
        state.z + 0.5 * dt_s * k2_z,
        state.vx + 0.5 * dt_s * k2_vx,
        state.vz + 0.5 * dt_s * k2_vz,
        state.mass_kg + 0.5 * dt_s * k2_m
    )

    k4_x, k4_z, k4_vx, k4_vz, k4_m = derivatives(
        state.x + dt_s * k3_x,
        state.z + dt_s * k3_z,
        state.vx + dt_s * k3_vx,
        state.vz + dt_s * k3_vz,
        state.mass_kg + dt_s * k3_m
    )

    # Next translational state
    next_x = state.x + (dt_s / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
    next_z = state.z + (dt_s / 6.0) * (k1_z + 2.0 * k2_z + 2.0 * k3_z + k4_z)
    next_vx = state.vx + (dt_s / 6.0) * (k1_vx + 2.0 * k2_vx + 2.0 * k3_vx + k4_vx)
    next_vz = state.vz + (dt_s / 6.0) * (k1_vz + 2.0 * k2_vz + 2.0 * k3_vz + k4_vz)
    next_m = max(vehicle.dry_mass_kg, state.mass_kg + (dt_s / 6.0) * (k1_m + 2.0 * k2_m + 2.0 * k3_m + k4_m))

    # Rotational state handling
    if mode == "planar_dynamic_flip":
        # Integrate angular acceleration: Iyy * alpha = M_total
        i_yy = vehicle.pitch_inertia(next_m)
        tvc_moment = propulsion.get_tvc_moment_Nm(vehicle.gimbal_arm_m)
        damping_moment = -vehicle.pitch_rate_damping_Nm_s * math.radians(pitch_rate_deg_s)
        total_moment = applied_torque_Nm + tvc_moment + damping_moment

        angular_accel_rad_s2 = total_moment / max(i_yy, 1.0)
        angular_accel_deg_s2 = math.degrees(angular_accel_rad_s2)

        next_pitch_rate = pitch_rate_deg_s + angular_accel_deg_s2 * dt_s
        next_pitch = pitch_deg + next_pitch_rate * dt_s
    else:
        # Prescribed kinematic profile
        next_pitch = pitch_deg
        next_pitch_rate = pitch_rate_deg_s

    # Diagnostic forces and apparent load
    fax, faz, drag_mag, lift_mag = compute_aerodynamic_forces(
        LandingState(time_s=state.time_s + dt_s, x=next_x, z=next_z, vx=next_vx, vz=next_vz, mass_kg=next_m,
                     pitch_deg=next_pitch, pitch_rate_deg_s=next_pitch_rate),
        vehicle
    )
    total_force_x = fax + fx_thrust
    total_force_z = faz + fz_thrust
    apparent_g = math.sqrt(total_force_x ** 2 + total_force_z ** 2) / (next_m * g0)

    return LandingState(
        time_s=state.time_s + dt_s,
        x=next_x,
        z=next_z,
        vx=next_vx,
        vz=next_vz,
        mass_kg=next_m,
        pitch_deg=next_pitch,
        pitch_rate_deg_s=next_pitch_rate,
        thrust_N=propulsion.current_thrust_N,
        throttle=propulsion.current_throttle,
        gimbal_deg=propulsion.current_gimbal_deg,
        engine_state=propulsion.engine_state,
        event=state.event,
        drag_N=drag_mag,
        lift_N=lift_mag,
        apparent_g=apparent_g
    )
