"""
Reentry Flight Dynamics & Trajectory Propagation Engine
========================================================
Phase 6: 3-DOF numerical equations of motion, atmospheric drag and lift integration,
closed-loop guidance coupling, heat load accumulation, and terminal surface detection.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple, Callable
import numpy as np

try:
    from scipy.integrate import solve_ivp
    HAS_SCIPY = True
except ImportError:
    solve_ivp = None
    HAS_SCIPY = False

from .constants import (
    OMEGA_EARTH,
    STANDARD_GRAVITY,
    DEFAULT_TARGET_LAT_DEG,
    DEFAULT_TARGET_LON_DEG,
    DEFAULT_TARGET_RADIUS_M
)
from .atmosphere import USStandardAtmosphere1976, get_atmospheric_state
from .vehicle import ReentryVehicleConfig
from .aerodynamics import compute_aerodynamic_forces, AerodynamicForces
from .heating import compute_stagnation_heat_flux, evaluate_heating_state
from .guidance import CrossrangeBankGuidanceController, GuidanceCommand
from .splashdown import assess_terminal_splashdown, TerminalSplashdownAssessment
from .events import make_surface_intersection_event, ReentryEventRecord
from src.astrodynamics.gravity import compute_gravitational_acceleration
from src.astrodynamics.frames import eci_to_ecef, ecef_to_geodetic
from src.astrodynamics.state import OrbitalState


@dataclass
class ReentryTrajectoryStep:
    """Complete physical state snapshot at a single simulation time step."""
    time_s: float
    epoch_utc: str
    r_eci: np.ndarray
    v_eci: np.ndarray
    v_rel_eci: np.ndarray
    altitude_m: float
    geodetic_lat_deg: float
    geodetic_lon_deg: float
    speed_inertial_ms: float
    speed_relative_ms: float
    mach: float
    flight_path_angle_deg: float
    dynamic_pressure_pa: float
    density_kg_m3: float
    temperature_k: float
    pressure_pa: float
    drag_force_n: float
    lift_force_n: float
    drag_accel_ms2: float
    lift_accel_ms2: float
    total_accel_ms2: float
    apparent_g_load: float
    stagnation_heat_flux_mw_m2: float
    windward_heat_flux_mw_m2: float
    cumulative_heat_load_mj_m2: float
    radiative_equilibrium_temp_deg_c: float
    bank_angle_cmd_deg: float
    angle_of_attack_deg: float
    crossrange_error_km: float
    downrange_error_km: float
    guidance_active: bool


@dataclass
class ReentrySimulationResult:
    """Full outcome record of a completed atmospheric reentry simulation."""
    success: bool
    status_message: str
    scenario_id: str
    steps: List[ReentryTrajectoryStep]
    events: List[ReentryEventRecord]
    terminal_assessment: TerminalSplashdownAssessment
    peak_dynamic_pressure_pa: float
    peak_apparent_g_load: float
    peak_stagnation_heat_flux_mw_m2: float
    total_heat_load_mj_m2: float
    impact_time_s: float
    terminal_relative_speed_ms: float
    miss_distance_km: float
    times_s: np.ndarray
    altitudes_km: np.ndarray
    speeds_km_s: np.ndarray
    mach_history: np.ndarray
    q_dyn_kpa: np.ndarray
    g_loads: np.ndarray
    heat_fluxes_mw_m2: np.ndarray
    heat_loads_mj_m2: np.ndarray
    bank_angles_deg: np.ndarray


def _reentry_dynamics_derivatives(
    t: float,
    y: np.ndarray,
    theta_gst_0_rad: float,
    vehicle_config: ReentryVehicleConfig,
    atmosphere: USStandardAtmosphere1976,
    guidance: Optional[CrossrangeBankGuidanceController] = None,
    enable_j2: bool = True
) -> np.ndarray:
    """
    Evaluates 7-element state derivatives dy/dt = [vx, vy, vz, ax, ay, az, q_dot_stag].
    """
    r_eci = y[0:3]
    v_eci = y[3:6]
    # Q = y[6]  (heat load integrated directly)

    # 1. Earth rotation and geodetic altitude
    theta_gst = theta_gst_0_rad + OMEGA_EARTH * t
    cos_t = math.cos(theta_gst)
    sin_t = math.sin(theta_gst)
    r_ecef = np.array([
        cos_t * r_eci[0] + sin_t * r_eci[1],
        -sin_t * r_eci[0] + cos_t * r_eci[1],
        r_eci[2]
    ], dtype=np.float64)

    lat_deg, lon_deg, alt_m = ecef_to_geodetic(r_ecef)

    # 2. Atmospheric-relative velocity: v_rel = v_eci - omega x r_eci
    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    v_rel_eci = v_eci - np.cross(omega_vec, r_eci)
    v_rel_mag = float(np.linalg.norm(v_rel_eci))

    # 3. Atmosphere properties
    atm_state = atmosphere.evaluate(alt_m)

    # 4. Guidance controller
    q_dyn_est = 0.5 * atm_state.density_kg_m3 * (v_rel_mag ** 2)
    if guidance is not None and guidance.enabled:
        cmd = guidance.compute_command(
            time_s=t,
            current_lat_deg=lat_deg,
            current_lon_deg=lon_deg,
            current_alt_m=alt_m,
            dynamic_pressure_pa=q_dyn_est
        )
        bank_deg = cmd.bank_angle_cmd_deg
        aoa_deg = cmd.angle_of_attack_cmd_deg
    else:
        bank_deg = 0.0
        aoa_deg = vehicle_config.nominal_angle_of_attack_deg

    # 5. Aerodynamic forces and accelerations
    aero = compute_aerodynamic_forces(
        r_vec=r_eci,
        v_rel_vec=v_rel_eci,
        density_kg_m3=atm_state.density_kg_m3,
        speed_of_sound_ms=atm_state.speed_of_sound_ms,
        config=vehicle_config,
        bank_angle_deg=bank_deg,
        angle_of_attack_deg=aoa_deg
    )

    # 6. Gravitational acceleration (point-mass + J2)
    a_grav = compute_gravitational_acceleration(r_eci, enable_j2=enable_j2)

    # Total kinematic acceleration
    a_total = a_grav + aero.a_aero_vec_ms2

    # 7. Heat flux rate of change dQ/dt = q_dot_stag
    q_dot_stag = compute_stagnation_heat_flux(
        density_kg_m3=atm_state.density_kg_m3,
        speed_relative_ms=v_rel_mag,
        nose_radius_m=vehicle_config.nose_radius_m
    )

    return np.array([
        v_eci[0], v_eci[1], v_eci[2],
        a_total[0], a_total[1], a_total[2],
        q_dot_stag
    ], dtype=np.float64)


def propagate_reentry(
    initial_state: OrbitalState,
    vehicle_config: ReentryVehicleConfig,
    atmosphere: Optional[USStandardAtmosphere1976] = None,
    guidance: Optional[CrossrangeBankGuidanceController] = None,
    enable_j2: bool = True,
    max_duration_s: float = 1800.0,
    eval_step_s: float = 1.0,
    integrator: str = "DOP853",
    rtol: float = 1e-8,
    atol: float = 1e-10,
    target_lat_deg: float = DEFAULT_TARGET_LAT_DEG,
    target_lon_deg: float = DEFAULT_TARGET_LON_DEG,
    target_radius_m: float = DEFAULT_TARGET_RADIUS_M,
    scenario_id: str = "SYNTHETIC_REENTRY_BASELINE"
) -> ReentrySimulationResult:
    """
    Unified entry point for atmospheric reentry propagation.
    Integrates 3-DOF trajectory from entry interface to ocean surface.
    """
    atm = atmosphere if atmosphere is not None else USStandardAtmosphere1976()
    if guidance is not None:
        guidance.reset()

    # Initial epoch & GST angle
    if isinstance(initial_state.epoch, (int, float)):
        epoch_ref = datetime(2026, 9, 28, 14, 0, 0, tzinfo=timezone.utc)
        start_epoch_dt = epoch_ref + timedelta(seconds=float(initial_state.epoch))
        elapsed_mission_start_s = float(initial_state.epoch)
    elif isinstance(initial_state.epoch, datetime):
        start_epoch_dt = initial_state.epoch
        # Mission start reference: 2026-09-28T14:00:00Z
        t0_ref = datetime(2026, 9, 28, 14, 0, 0, tzinfo=timezone.utc)
        elapsed_mission_start_s = (start_epoch_dt - t0_ref).total_seconds()
    else:
        start_epoch_dt = datetime(2026, 9, 28, 15, 48, 47, tzinfo=timezone.utc)
        elapsed_mission_start_s = 6527.315

    theta_gst_0 = OMEGA_EARTH * elapsed_mission_start_s

    # Compute entry geodetic coordinates
    cos_0 = math.cos(theta_gst_0)
    sin_0 = math.sin(theta_gst_0)
    r_ecef_0 = np.array([
        cos_0 * initial_state.r[0] + sin_0 * initial_state.r[1],
        -sin_0 * initial_state.r[0] + cos_0 * initial_state.r[1],
        initial_state.r[2]
    ], dtype=np.float64)
    entry_lat, entry_lon, _ = ecef_to_geodetic(r_ecef_0)

    # Initial state vector y0 = [rx, ry, rz, vx, vy, vz, Q=0]
    y0 = np.concatenate([initial_state.r, initial_state.v, [0.0]])

    def deriv_fn(t_curr: float, y_curr: np.ndarray) -> np.ndarray:
        return _reentry_dynamics_derivatives(
            t=t_curr,
            y=y_curr,
            theta_gst_0_rad=theta_gst_0,
            vehicle_config=vehicle_config,
            atmosphere=atm,
            guidance=guidance,
            enable_j2=enable_j2
        )

    surface_event = make_surface_intersection_event(h_surface_m=0.0, theta_gst_0_rad=theta_gst_0)

    # Integration execution
    if HAS_SCIPY and integrator.upper() != "RK4_FIXED":
        # Adaptive integration via solve_ivp
        sol = solve_ivp(
            fun=deriv_fn,
            t_span=(0.0, max_duration_s),
            y0=y0,
            method=integrator,
            events=[surface_event],
            rtol=rtol,
            atol=atol,
            max_step=max(eval_step_s * 5.0, 10.0),
            dense_output=True
        )
        t_final = sol.t[-1]
        # Evaluate dense trajectory at uniform intervals
        n_pts = max(int(math.ceil(t_final / eval_step_s)) + 1, 2)
        t_eval = np.linspace(0.0, t_final, n_pts)
        y_eval = sol.sol(t_eval)  # Shape (7, n_pts)
        t_arr = t_eval
        y_arr = y_eval.T         # Shape (n_pts, 7)
    else:
        # Classical RK4 integration with bisection surface event detection
        step_dt = eval_step_s if eval_step_s > 0 else 1.0
        t_list = [0.0]
        y_list = [y0.copy()]
        y_curr = y0.copy()
        t_curr = 0.0

        while t_curr < max_duration_s:
            # Check surface crossing
            h_val = surface_event(t_curr, y_curr)
            if h_val <= 0.0 and len(t_list) > 1:
                break

            h = min(step_dt, max_duration_s - t_curr)
            k1 = deriv_fn(t_curr, y_curr)
            k2 = deriv_fn(t_curr + 0.5 * h, y_curr + 0.5 * h * k1)
            k3 = deriv_fn(t_curr + 0.5 * h, y_curr + 0.5 * h * k2)
            k4 = deriv_fn(t_curr + h, y_curr + h * k3)
            y_next = y_curr + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            t_next = t_curr + h

            # Check if next step penetrates surface
            h_next = surface_event(t_next, y_next)
            if h_next <= 0.0:
                # Bisection root finding to pinpoint exact surface intersection
                t_low, t_high = t_curr, t_next
                y_low, y_high = y_curr.copy(), y_next.copy()
                for _ in range(25):
                    t_mid = 0.5 * (t_low + t_high)
                    h_mid_step = t_mid - t_curr
                    km1 = deriv_fn(t_curr, y_curr)
                    km2 = deriv_fn(t_curr + 0.5 * h_mid_step, y_curr + 0.5 * h_mid_step * km1)
                    km3 = deriv_fn(t_curr + 0.5 * h_mid_step, y_curr + 0.5 * h_mid_step * km2)
                    km4 = deriv_fn(t_curr + h_mid_step, y_curr + h_mid_step * km3)
                    y_mid = y_curr + (h_mid_step / 6.0) * (km1 + 2.0 * km2 + 2.0 * km3 + km4)
                    h_mid_val = surface_event(t_mid, y_mid)
                    if abs(h_mid_val) < 0.1:
                        t_next, y_next = t_mid, y_mid
                        break
                    if h_mid_val > 0.0:
                        t_low, y_low = t_mid, y_mid
                    else:
                        t_high, y_high = t_mid, y_mid
                t_list.append(t_next)
                y_list.append(y_next)
                break

            t_curr = t_next
            y_curr = y_next
            t_list.append(t_curr)
            y_list.append(y_curr.copy())

        t_arr = np.array(t_list, dtype=np.float64)
        y_arr = np.array(y_list, dtype=np.float64)

    # Build detailed TrajectorySteps and record events
    steps: List[ReentryTrajectoryStep] = []
    events: List[ReentryEventRecord] = []
    n_steps = len(t_arr)

    omega_vec = np.array([0.0, 0.0, OMEGA_EARTH], dtype=np.float64)
    peak_q_pa = 0.0
    peak_g = 0.0
    peak_heat_mw = 0.0

    for i in range(n_steps):
        t_i = float(t_arr[i])
        r_i = y_arr[i, 0:3]
        v_i = y_arr[i, 3:6]
        q_load_i = float(y_arr[i, 6])

        step_epoch_dt = start_epoch_dt + timedelta(seconds=t_i)
        step_epoch_str = step_epoch_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        theta_i = theta_gst_0 + OMEGA_EARTH * t_i
        cos_i = math.cos(theta_i)
        sin_i = math.sin(theta_i)
        r_ecef_i = np.array([
            cos_i * r_i[0] + sin_i * r_i[1],
            -sin_i * r_i[0] + cos_i * r_i[1],
            r_i[2]
        ], dtype=np.float64)
        lat_i, lon_i, alt_i = ecef_to_geodetic(r_ecef_i)

        v_rel_i = v_i - np.cross(omega_vec, r_i)
        v_rel_mag_i = float(np.linalg.norm(v_rel_i))
        v_inertial_mag_i = float(np.linalg.norm(v_i))

        # Relative flight-path angle
        r_mag_i = float(np.linalg.norm(r_i))
        gamma_rad_i = math.asin(min(max(float(np.dot(r_i, v_rel_i)) / (r_mag_i * max(v_rel_mag_i, 1e-6)), -1.0), 1.0))
        gamma_deg_i = math.degrees(gamma_rad_i)

        atm_i = atm.evaluate(alt_i)
        q_dyn_est_i = 0.5 * atm_i.density_kg_m3 * (v_rel_mag_i ** 2)

        if guidance is not None and guidance.enabled:
            cmd_i = guidance.compute_command(
                time_s=t_i,
                current_lat_deg=lat_i,
                current_lon_deg=lon_i,
                current_alt_m=alt_i,
                dynamic_pressure_pa=q_dyn_est_i
            )
            bank_deg_i = cmd_i.bank_angle_cmd_deg
            aoa_deg_i = cmd_i.angle_of_attack_cmd_deg
            cross_km_i = cmd_i.crossrange_error_km
            down_km_i = cmd_i.downrange_error_km
            g_active_i = cmd_i.guidance_active
        else:
            bank_deg_i = 0.0
            aoa_deg_i = vehicle_config.nominal_angle_of_attack_deg
            cross_km_i = 0.0
            down_km_i = 0.0
            g_active_i = False

        aero_i = compute_aerodynamic_forces(
            r_vec=r_i,
            v_rel_vec=v_rel_i,
            density_kg_m3=atm_i.density_kg_m3,
            speed_of_sound_ms=atm_i.speed_of_sound_ms,
            config=vehicle_config,
            bank_angle_deg=bank_deg_i,
            angle_of_attack_deg=aoa_deg_i
        )

        heat_i = evaluate_heating_state(
            density_kg_m3=atm_i.density_kg_m3,
            speed_relative_ms=v_rel_mag_i,
            cumulative_heat_load_j_m2=q_load_i,
            nose_radius_m=vehicle_config.nose_radius_m
        )

        if aero_i.dynamic_pressure_pa > peak_q_pa:
            peak_q_pa = aero_i.dynamic_pressure_pa
        if aero_i.apparent_g_load > peak_g:
            peak_g = aero_i.apparent_g_load
        if heat_i.stagnation_heat_flux_mw_m2 > peak_heat_mw:
            peak_heat_mw = heat_i.stagnation_heat_flux_mw_m2

        f_drag_mag_i = float(np.linalg.norm(aero_i.f_drag_vec_n))
        f_lift_mag_i = float(np.linalg.norm(aero_i.f_lift_vec_n))
        a_drag_mag_i = f_drag_mag_i / vehicle_config.mass_kg
        a_lift_mag_i = f_lift_mag_i / vehicle_config.mass_kg
        a_total_mag_i = float(np.linalg.norm(aero_i.a_aero_vec_ms2))

        step_obj = ReentryTrajectoryStep(
            time_s=t_i,
            epoch_utc=step_epoch_str,
            r_eci=r_i,
            v_eci=v_i,
            v_rel_eci=v_rel_i,
            altitude_m=alt_i,
            geodetic_lat_deg=lat_i,
            geodetic_lon_deg=lon_i,
            speed_inertial_ms=v_inertial_mag_i,
            speed_relative_ms=v_rel_mag_i,
            mach=aero_i.mach,
            flight_path_angle_deg=gamma_deg_i,
            dynamic_pressure_pa=aero_i.dynamic_pressure_pa,
            density_kg_m3=atm_i.density_kg_m3,
            temperature_k=atm_i.temperature_k,
            pressure_pa=atm_i.pressure_pa,
            drag_force_n=f_drag_mag_i,
            lift_force_n=f_lift_mag_i,
            drag_accel_ms2=a_drag_mag_i,
            lift_accel_ms2=a_lift_mag_i,
            total_accel_ms2=a_total_mag_i,
            apparent_g_load=aero_i.apparent_g_load,
            stagnation_heat_flux_mw_m2=heat_i.stagnation_heat_flux_mw_m2,
            windward_heat_flux_mw_m2=heat_i.windward_heat_flux_mw_m2,
            cumulative_heat_load_mj_m2=heat_i.cumulative_heat_load_mj_m2,
            radiative_equilibrium_temp_deg_c=heat_i.radiative_equilibrium_temp_deg_c,
            bank_angle_cmd_deg=bank_deg_i,
            angle_of_attack_deg=aoa_deg_i,
            crossrange_error_km=cross_km_i,
            downrange_error_km=down_km_i,
            guidance_active=g_active_i
        )
        steps.append(step_obj)

    # Assess Terminal Impact
    last_step = steps[-1]
    terminal_assessment = assess_terminal_splashdown(
        r_eci=last_step.r_eci,
        v_eci=last_step.v_eci,
        impact_time_s=last_step.time_s,
        impact_epoch_utc=last_step.epoch_utc,
        theta_gst_rad=theta_gst_0 + OMEGA_EARTH * last_step.time_s,
        target_lat_deg=target_lat_deg,
        target_lon_deg=target_lon_deg,
        target_radius_m=target_radius_m,
        entry_lat_deg=entry_lat,
        entry_lon_deg=entry_lon,
        cumulative_heat_load_mj_m2=last_step.cumulative_heat_load_mj_m2,
        peak_dynamic_pressure_pa=peak_q_pa,
        peak_apparent_g_load=peak_g,
        peak_stagnation_heat_flux_mw_m2=peak_heat_mw
    )

    # Event recording for key peaks and milestones
    events.append(ReentryEventRecord(
        time_s=0.0,
        event_name="atmospheric_entry_interface_120km",
        altitude_m=steps[0].altitude_m,
        geodetic_lat_deg=steps[0].geodetic_lat_deg,
        geodetic_lon_deg=steps[0].geodetic_lon_deg,
        speed_rel_ms=steps[0].speed_relative_ms,
        mach=steps[0].mach,
        dynamic_pressure_pa=steps[0].dynamic_pressure_pa,
        apparent_g_load=steps[0].apparent_g_load,
        stagnation_heat_flux_mw_m2=steps[0].stagnation_heat_flux_mw_m2,
        cumulative_heat_load_mj_m2=steps[0].cumulative_heat_load_mj_m2,
        r_eci=steps[0].r_eci,
        v_eci=steps[0].v_eci
    ))

    # Identify step of peak heating
    idx_peak_heat = int(np.argmax([s.stagnation_heat_flux_mw_m2 for s in steps]))
    events.append(ReentryEventRecord(
        time_s=steps[idx_peak_heat].time_s,
        event_name="peak_stagnation_heat_flux",
        altitude_m=steps[idx_peak_heat].altitude_m,
        geodetic_lat_deg=steps[idx_peak_heat].geodetic_lat_deg,
        geodetic_lon_deg=steps[idx_peak_heat].geodetic_lon_deg,
        speed_rel_ms=steps[idx_peak_heat].speed_relative_ms,
        mach=steps[idx_peak_heat].mach,
        dynamic_pressure_pa=steps[idx_peak_heat].dynamic_pressure_pa,
        apparent_g_load=steps[idx_peak_heat].apparent_g_load,
        stagnation_heat_flux_mw_m2=steps[idx_peak_heat].stagnation_heat_flux_mw_m2,
        cumulative_heat_load_mj_m2=steps[idx_peak_heat].cumulative_heat_load_mj_m2,
        r_eci=steps[idx_peak_heat].r_eci,
        v_eci=steps[idx_peak_heat].v_eci
    ))

    # Identify step of peak dynamic pressure
    idx_peak_q = int(np.argmax([s.dynamic_pressure_pa for s in steps]))
    events.append(ReentryEventRecord(
        time_s=steps[idx_peak_q].time_s,
        event_name="peak_dynamic_pressure",
        altitude_m=steps[idx_peak_q].altitude_m,
        geodetic_lat_deg=steps[idx_peak_q].geodetic_lat_deg,
        geodetic_lon_deg=steps[idx_peak_q].geodetic_lon_deg,
        speed_rel_ms=steps[idx_peak_q].speed_relative_ms,
        mach=steps[idx_peak_q].mach,
        dynamic_pressure_pa=steps[idx_peak_q].dynamic_pressure_pa,
        apparent_g_load=steps[idx_peak_q].apparent_g_load,
        stagnation_heat_flux_mw_m2=steps[idx_peak_q].stagnation_heat_flux_mw_m2,
        cumulative_heat_load_mj_m2=steps[idx_peak_q].cumulative_heat_load_mj_m2,
        r_eci=steps[idx_peak_q].r_eci,
        v_eci=steps[idx_peak_q].v_eci
    ))

    # Terminal splashdown event
    events.append(ReentryEventRecord(
        time_s=last_step.time_s,
        event_name="ocean_surface_splashdown_datum",
        altitude_m=last_step.altitude_m,
        geodetic_lat_deg=last_step.geodetic_lat_deg,
        geodetic_lon_deg=last_step.geodetic_lon_deg,
        speed_rel_ms=last_step.speed_relative_ms,
        mach=last_step.mach,
        dynamic_pressure_pa=last_step.dynamic_pressure_pa,
        apparent_g_load=last_step.apparent_g_load,
        stagnation_heat_flux_mw_m2=last_step.stagnation_heat_flux_mw_m2,
        cumulative_heat_load_mj_m2=last_step.cumulative_heat_load_mj_m2,
        r_eci=last_step.r_eci,
        v_eci=last_step.v_eci
    ))

    # Vectorized arrays for rapid plotting and analytical post-processing
    return ReentrySimulationResult(
        success=True,
        status_message="Atmospheric reentry simulation completed successfully to ocean surface",
        scenario_id=scenario_id,
        steps=steps,
        events=events,
        terminal_assessment=terminal_assessment,
        peak_dynamic_pressure_pa=peak_q_pa,
        peak_apparent_g_load=peak_g,
        peak_stagnation_heat_flux_mw_m2=peak_heat_mw,
        total_heat_load_mj_m2=last_step.cumulative_heat_load_mj_m2,
        impact_time_s=last_step.time_s,
        terminal_relative_speed_ms=last_step.speed_relative_ms,
        miss_distance_km=terminal_assessment.miss_distance_km,
        times_s=t_arr,
        altitudes_km=np.array([s.altitude_m / 1000.0 for s in steps]),
        speeds_km_s=np.array([s.speed_relative_ms / 1000.0 for s in steps]),
        mach_history=np.array([s.mach for s in steps]),
        q_dyn_kpa=np.array([s.dynamic_pressure_pa / 1000.0 for s in steps]),
        g_loads=np.array([s.apparent_g_load for s in steps]),
        heat_fluxes_mw_m2=np.array([s.stagnation_heat_flux_mw_m2 for s in steps]),
        heat_loads_mj_m2=np.array([s.cumulative_heat_load_mj_m2 for s in steps]),
        bank_angles_deg=np.array([s.bank_angle_cmd_deg for s in steps])
    )
