"""
Numerical Orbit Propagator & Invariant Monitoring
=================================================
High-precision numerical orbit propagation supporting:
- Classical 4th-order Runge-Kutta (RK4) with fixed time-step
- SciPy solve_ivp adaptive integrators (DOP853, RK45)
- Gravitational point-mass and Earth J2 zonal harmonic accelerations
- Upper atmospheric drag acceleration (exponential thermosphere fit)
- Physical invariant tracking (specific energy, angular momentum)
- Event detection (periapsis, apoapsis, nodal crossings, atmospheric entry interface)
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Tuple
import numpy as np

try:
    from scipy.integrate import solve_ivp
    HAS_SCIPY = True
except ImportError:
    solve_ivp = None
    HAS_SCIPY = False

from .constants import MU_EARTH, R_EARTH_EQUATORIAL, J2_EARTH, ENTRY_INTERFACE_ALTITUDE_M
from .state import OrbitalState
from .gravity import compute_gravitational_acceleration
from .drag import compute_aerodynamic_drag
from .orbit_elements import compute_keplerian_elements
from .events import get_standard_orbital_events


@dataclass
class PropagationStep:
    """Snapshot of propagated orbit state at a discrete simulation epoch."""
    time_s: float
    epoch: datetime
    r: np.ndarray
    v: np.ndarray
    mass_kg: float
    altitude_spherical_km: float
    speed_km_s: float
    specific_energy_mj_kg: float
    angular_momentum_mag: float
    elements: Dict[str, float]


@dataclass
class PropagationEventRecord:
    """Record of an event triggered during propagation."""
    time_s: float
    epoch: datetime
    event_name: str
    r: np.ndarray
    v: np.ndarray
    altitude_spherical_km: float


@dataclass
class PropagationResult:
    """Complete trajectory and diagnostics result container."""
    success: bool
    status_message: str
    times_s: np.ndarray
    epochs: List[datetime]
    states_r: np.ndarray  # Shape (N, 3)
    states_v: np.ndarray  # Shape (N, 3)
    masses_kg: np.ndarray
    altitudes_km: np.ndarray
    speeds_km_s: np.ndarray
    energies_mj_kg: np.ndarray
    angular_momenta: np.ndarray
    elements_history: List[Dict[str, float]]
    events: List[PropagationEventRecord]
    
    # Invariant diagnostics
    initial_energy_j_kg: float
    final_energy_j_kg: float
    energy_relative_drift: float
    initial_h_mag: float
    final_h_mag: float
    h_relative_drift: float

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns structured dictionary summary of propagation run."""
        final_idx = -1 if len(self.times_s) > 0 else 0
        final_elem = self.elements_history[-1] if self.elements_history else {}
        return {
            "success": self.success,
            "status_message": self.status_message,
            "duration_s": float(self.times_s[-1]) if len(self.times_s) > 0 else 0.0,
            "step_count": len(self.times_s),
            "final_epoch_utc": self.epochs[-1].isoformat() if self.epochs else None,
            "final_altitude_km": float(self.altitudes_km[final_idx]) if len(self.altitudes_km) > 0 else None,
            "final_speed_km_s": float(self.speeds_km_s[final_idx]) if len(self.speeds_km_s) > 0 else None,
            "final_elements": final_elem,
            "energy_relative_drift": float(self.energy_relative_drift),
            "angular_momentum_relative_drift": float(self.h_relative_drift),
            "events_triggered": len(self.events),
            "event_summary": [
                {
                    "event": ev.event_name,
                    "time_s": ev.time_s,
                    "altitude_km": ev.altitude_spherical_km,
                    "epoch_utc": ev.epoch.isoformat()
                }
                for ev in self.events
            ]
        }


def _dynamics_derivatives(
    t: float,
    y: np.ndarray,
    mu: float,
    enable_j2: bool,
    j2_coeff: float,
    r_eq: float,
    enable_drag: bool,
    mass_kg: float,
    area_m2: float,
    cd: float,
    thrust_accel_fn: Optional[Callable[[float, np.ndarray, np.ndarray], np.ndarray]] = None
) -> np.ndarray:
    """
    Computes [dr/dt, dv/dt] state derivative vector in ECI frame.
    y = [x, y, z, vx, vy, vz]
    """
    r_vec = y[0:3]
    v_vec = y[3:6]

    # Gravitational acceleration
    a_grav = compute_gravitational_acceleration(
        r_vec=r_vec,
        mu=mu,
        enable_j2=enable_j2,
        j2_coeff=j2_coeff,
        r_eq=r_eq
    )

    # Aerodynamic drag acceleration
    if enable_drag:
        a_drag = compute_aerodynamic_drag(
            r_eci=r_vec,
            v_eci=v_vec,
            mass_kg=mass_kg,
            area_m2=area_m2,
            cd=cd
        )
    else:
        a_drag = np.zeros(3, dtype=np.float64)

    # Optional thrust acceleration
    if thrust_accel_fn is not None:
        a_thrust = thrust_accel_fn(t, r_vec, v_vec)
    else:
        a_thrust = np.zeros(3, dtype=np.float64)

    a_total = a_grav + a_drag + a_thrust

    return np.array([
        v_vec[0], v_vec[1], v_vec[2],
        a_total[0], a_total[1], a_total[2]
    ], dtype=np.float64)


def propagate_orbit_rk4_fixed(
    initial_state: OrbitalState,
    duration_s: float,
    dt: float = 1.0,
    mu: float = MU_EARTH,
    enable_j2: bool = False,
    j2_coeff: float = J2_EARTH,
    enable_drag: bool = False,
    thrust_accel_fn: Optional[Callable[[float, np.ndarray, np.ndarray], np.ndarray]] = None
) -> PropagationResult:
    """
    Propagates orbit using classic 4th-order Runge-Kutta with constant step size dt.
    Used for convergence studies, baseline verification, and deterministic benchmarks.
    """
    if dt <= 0.0:
        raise ValueError(f"Step size dt must be positive: {dt} s")
    if duration_s < 0.0:
        raise ValueError(f"Duration must be non-negative: {duration_s} s")

    num_steps = int(math.ceil(duration_s / dt)) + 1
    t_span = np.linspace(0.0, duration_s, num_steps)

    y = np.zeros(6, dtype=np.float64)
    y[0:3] = initial_state.r
    y[3:6] = initial_state.v

    states_r = np.zeros((num_steps, 3), dtype=np.float64)
    states_v = np.zeros((num_steps, 3), dtype=np.float64)
    masses = np.full(num_steps, initial_state.mass_kg, dtype=np.float64)
    altitudes = np.zeros(num_steps, dtype=np.float64)
    speeds = np.zeros(num_steps, dtype=np.float64)
    energies = np.zeros(num_steps, dtype=np.float64)
    momenta = np.zeros(num_steps, dtype=np.float64)
    epochs: List[datetime] = []
    elements_hist: List[Dict[str, float]] = []

    def deriv_fn(t_curr: float, state_y: np.ndarray) -> np.ndarray:
        return _dynamics_derivatives(
            t=t_curr,
            y=state_y,
            mu=mu,
            enable_j2=enable_j2,
            j2_coeff=j2_coeff,
            r_eq=R_EARTH_EQUATORIAL,
            enable_drag=enable_drag,
            mass_kg=initial_state.mass_kg,
            area_m2=initial_state.area_m2,
            cd=initial_state.cd,
            thrust_accel_fn=thrust_accel_fn
        )

    for i in range(num_steps):
        t_curr = t_span[i]
        states_r[i] = y[0:3]
        states_v[i] = y[3:6]
        
        r_norm = float(np.linalg.norm(y[0:3]))
        v_norm = float(np.linalg.norm(y[3:6]))
        altitudes[i] = (r_norm - R_EARTH_EQUATORIAL) / 1000.0
        speeds[i] = v_norm / 1000.0
        
        spec_e = (0.5 * v_norm**2) - (mu / r_norm)
        energies[i] = spec_e / 1e6
        h_vec = np.cross(y[0:3], y[3:6])
        momenta[i] = float(np.linalg.norm(h_vec))
        
        curr_epoch = initial_state.epoch + timedelta(seconds=float(t_curr))
        epochs.append(curr_epoch)

        try:
            elem = compute_keplerian_elements(y[0:3], y[3:6], mu=mu)
        except Exception:
            elem = {}
        elements_hist.append(elem)

        if i < num_steps - 1:
            h = t_span[i + 1] - t_curr
            k1 = deriv_fn(t_curr, y)
            k2 = deriv_fn(t_curr + 0.5 * h, y + 0.5 * h * k1)
            k3 = deriv_fn(t_curr + 0.5 * h, y + 0.5 * h * k2)
            k4 = deriv_fn(t_curr + h, y + h * k3)
            y = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    initial_e = energies[0] * 1e6
    final_e = energies[-1] * 1e6
    e_drift = abs(final_e - initial_e) / max(abs(initial_e), 1e-12)

    initial_h = momenta[0]
    final_h = momenta[-1]
    h_drift = abs(final_h - initial_h) / max(abs(initial_h), 1e-12)

    return PropagationResult(
        success=True,
        status_message="RK4 fixed-step propagation completed",
        times_s=t_span,
        epochs=epochs,
        states_r=states_r,
        states_v=states_v,
        masses_kg=masses,
        altitudes_km=altitudes,
        speeds_km_s=speeds,
        energies_mj_kg=energies,
        angular_momenta=momenta,
        elements_history=elements_hist,
        events=[],
        initial_energy_j_kg=initial_e,
        final_energy_j_kg=final_e,
        energy_relative_drift=e_drift,
        initial_h_mag=initial_h,
        final_h_mag=final_h,
        h_relative_drift=h_drift
    )


def propagate_orbit_adaptive(
    initial_state: OrbitalState,
    duration_s: float,
    method: str = "DOP853",
    rtol: float = 1e-11,
    atol: float = 1e-12,
    max_step: float = 30.0,
    mu: float = MU_EARTH,
    enable_j2: bool = False,
    j2_coeff: float = J2_EARTH,
    enable_drag: bool = False,
    detect_events: bool = True,
    terminal_entry: bool = False,
    entry_alt_m: float = ENTRY_INTERFACE_ALTITUDE_M,
    eval_step_s: Optional[float] = 10.0,
    thrust_accel_fn: Optional[Callable[[float, np.ndarray, np.ndarray], np.ndarray]] = None
) -> PropagationResult:
    """
    High-precision adaptive orbital propagation using SciPy solve_ivp (default DOP853).
    Includes continuous dense output / uniform grid interpolation and event crossing detection.
    """
    y0 = np.concatenate([initial_state.r, initial_state.v])

    def deriv_fn(t_curr: float, state_y: np.ndarray) -> np.ndarray:
        return _dynamics_derivatives(
            t=t_curr,
            y=state_y,
            mu=mu,
            enable_j2=enable_j2,
            j2_coeff=j2_coeff,
            r_eq=R_EARTH_EQUATORIAL,
            enable_drag=enable_drag,
            mass_kg=initial_state.mass_kg,
            area_m2=initial_state.area_m2,
            cd=initial_state.cd,
            thrust_accel_fn=thrust_accel_fn
        )

    events_list = get_standard_orbital_events(
        terminal_entry=terminal_entry,
        entry_alt_m=entry_alt_m
    ) if detect_events else None

    if solve_ivp is None:
        # High-precision fallback when SciPy is not available in environment
        step_dt = eval_step_s if eval_step_s is not None and eval_step_s > 0 else 5.0
        num_steps = int(math.ceil(duration_s / step_dt)) + 1
        t_span = np.linspace(0.0, duration_s, num_steps)

        y = y0.copy()
        t_list = [0.0]
        y_list = [y.copy()]
        event_records: List[PropagationEventRecord] = []
        last_ev_vals = [ev(0.0, y) for ev in events_list] if events_list else []

        for i in range(num_steps - 1):
            t_curr = t_span[i]
            h = t_span[i + 1] - t_curr
            k1 = deriv_fn(t_curr, y)
            k2 = deriv_fn(t_curr + 0.5 * h, y + 0.5 * h * k1)
            k3 = deriv_fn(t_curr + 0.5 * h, y + 0.5 * h * k2)
            k4 = deriv_fn(t_curr + h, y + h * k3)
            y_next = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            t_next = t_span[i + 1]

            terminated = False
            if events_list:
                curr_ev_vals = [ev(t_next, y_next) for ev in events_list]
                for ev_idx, ev_fn in enumerate(events_list):
                    v_prev = last_ev_vals[ev_idx]
                    v_curr = curr_ev_vals[ev_idx]
                    ev_dir = getattr(ev_fn, "direction", 0)
                    ev_name = getattr(ev_fn, "name", "event")
                    ev_term = getattr(ev_fn, "terminal", False)

                    crossed = False
                    if ev_dir > 0 and v_prev <= 0 and v_curr > 0:
                        crossed = True
                    elif ev_dir < 0 and v_prev >= 0 and v_curr < 0:
                        crossed = True
                    elif ev_dir == 0 and (v_prev * v_curr < 0):
                        crossed = True

                    if crossed:
                        denom = (v_curr - v_prev) if abs(v_curr - v_prev) > 1e-12 else 1.0
                        frac = max(0.0, min(1.0, -v_prev / denom))
                        t_ev = t_curr + frac * h
                        y_ev = y + frac * (y_next - y)
                        r_ev = y_ev[0:3]
                        v_ev = y_ev[3:6]
                        alt_ev = (float(np.linalg.norm(r_ev)) - R_EARTH_EQUATORIAL) / 1000.0
                        epoch_ev = initial_state.epoch + timedelta(seconds=float(t_ev))
                        event_records.append(PropagationEventRecord(
                            time_s=float(t_ev),
                            epoch=epoch_ev,
                            event_name=ev_name,
                            r=r_ev,
                            v=v_ev,
                            altitude_spherical_km=alt_ev
                        ))
                        if ev_term:
                            t_list.append(t_ev)
                            y_list.append(y_ev.copy())
                            terminated = True
                            break
                last_ev_vals = curr_ev_vals

            if terminated:
                break
            y = y_next
            t_list.append(t_next)
            y_list.append(y.copy())

        t_arr = np.array(t_list, dtype=np.float64)
        states_all = np.array(y_list, dtype=np.float64)
        states_r = states_all[:, 0:3]
        states_v = states_all[:, 3:6]
        sol_success = True
        sol_message = "RK4 internal fallback propagation completed"
    else:
        sol = solve_ivp(
            fun=deriv_fn,
            t_span=(0.0, duration_s),
            y0=y0,
            method=method,
            t_eval=t_eval,
            events=events_list,
            rtol=rtol,
            atol=atol,
            max_step=max_step,
            dense_output=True
        )

        t_arr = sol.t
        states_r = sol.y[0:3, :].T  # Shape (N, 3)
        states_v = sol.y[3:6, :].T  # Shape (N, 3)
        sol_success = sol.success
        sol_message = sol.message

    n_pts = len(t_arr)
    masses = np.full(n_pts, initial_state.mass_kg, dtype=np.float64)
    r_norms = np.linalg.norm(states_r, axis=1)
    v_norms = np.linalg.norm(states_v, axis=1)

    altitudes = (r_norms - R_EARTH_EQUATORIAL) / 1000.0
    speeds = v_norms / 1000.0

    energies_j = (0.5 * v_norms**2) - (mu / r_norms)
    energies_mj = energies_j / 1e6

    h_vecs = np.cross(states_r, states_v)
    momenta = np.linalg.norm(h_vecs, axis=1)

    epochs: List[datetime] = [
        initial_state.epoch + timedelta(seconds=float(t)) for t in t_arr
    ]

    elements_hist: List[Dict[str, float]] = []
    for i in range(n_pts):
        try:
            elem = compute_keplerian_elements(states_r[i], states_v[i], mu=mu)
        except Exception:
            elem = {}
        elements_hist.append(elem)

    # Process events triggered
    if solve_ivp is not None:
        event_records = []
        if sol.t_events is not None and events_list is not None:
            for ev_fn, t_event_arr, y_event_arr in zip(events_list, sol.t_events, sol.y_events):
                ev_name = getattr(ev_fn, "name", "unknown_event")
                for t_ev, y_ev in zip(t_event_arr, y_event_arr):
                    r_ev = y_ev[0:3]
                    v_ev = y_ev[3:6]
                    alt_ev = (float(np.linalg.norm(r_ev)) - R_EARTH_EQUATORIAL) / 1000.0

                epoch_ev = initial_state.epoch + timedelta(seconds=float(t_ev))
                event_records.append(PropagationEventRecord(
                    time_s=float(t_ev),
                    epoch=epoch_ev,
                    event_name=ev_name,
                    r=r_ev,
                    v=v_ev,
                    altitude_spherical_km=alt_ev
                ))

    # Sort events by time
    event_records.sort(key=lambda ev: ev.time_s)

    initial_e = float(energies_j[0])
    final_e = float(energies_j[-1])
    e_drift = abs(final_e - initial_e) / max(abs(initial_e), 1e-12)

    initial_h = float(momenta[0])
    final_h = float(momenta[-1])
    h_drift = abs(final_h - initial_h) / max(abs(initial_h), 1e-12)

    return PropagationResult(
        success=sol_success,
        status_message=sol_message,
        times_s=t_arr,
        epochs=epochs,
        states_r=states_r,
        states_v=states_v,
        masses_kg=masses,
        altitudes_km=altitudes,
        speeds_km_s=speeds,
        energies_mj_kg=energies_mj,
        angular_momenta=momenta,
        elements_history=elements_hist,
        events=event_records,
        initial_energy_j_kg=initial_e,
        final_energy_j_kg=final_e,
        energy_relative_drift=e_drift,
        initial_h_mag=initial_h,
        final_h_mag=final_h,
        h_relative_drift=h_drift
    )


def propagate_orbit(
    initial_state: OrbitalState,
    duration_s: float,
    dt: Optional[float] = None,
    integrator: str = "DOP853",
    enable_j2: bool = False,
    j2_coeff: float = J2_EARTH,
    enable_drag: bool = False,
    mu: float = MU_EARTH,
    detect_events: bool = True,
    terminal_entry: bool = False,
    entry_alt_m: float = ENTRY_INTERFACE_ALTITUDE_M,
    rtol: float = 1e-11,
    atol: float = 1e-12,
    thrust_accel_fn: Optional[Callable[[float, np.ndarray, np.ndarray], np.ndarray]] = None
) -> PropagationResult:
    """
    Unified entry point for orbit propagation.
    If integrator == 'RK4_FIXED', uses fixed-step RK4 with step size dt (default 1.0 s).
    Otherwise, uses adaptive solve_ivp with specified method (e.g. 'DOP853', 'RK45').
    """
    if integrator.upper() == "RK4_FIXED":
        step_dt = dt if dt is not None and dt > 0 else 1.0
        return propagate_orbit_rk4_fixed(
            initial_state=initial_state,
            duration_s=duration_s,
            dt=step_dt,
            mu=mu,
            enable_j2=enable_j2,
            j2_coeff=j2_coeff,
            enable_drag=enable_drag,
            thrust_accel_fn=thrust_accel_fn
        )
    else:
        eval_dt = dt if dt is not None and dt > 0 else 10.0
        return propagate_orbit_adaptive(
            initial_state=initial_state,
            duration_s=duration_s,
            method=integrator,
            rtol=rtol,
            atol=atol,
            mu=mu,
            enable_j2=enable_j2,
            j2_coeff=j2_coeff,
            enable_drag=enable_drag,
            detect_events=detect_events,
            terminal_entry=terminal_entry,
            entry_alt_m=entry_alt_m,
            eval_step_s=eval_dt,
            thrust_accel_fn=thrust_accel_fn
        )
