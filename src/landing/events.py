"""
Discrete event state machine and continuous surface-contact event localization.
"""

from typing import List, Optional
from src.landing.state import LandingState, EventRecord


class LandingStateMachine:
    """Manages the 16-state discrete mission automaton and event transitions."""

    def __init__(self):
        self.current_state: str = "APPROACH"
        self.event_log: List[EventRecord] = []
        self.ignition_commanded: bool = False
        self.touchdown_occurred: bool = False

    def record_transition(self, new_state: str, state: LandingState, details: str = "") -> None:
        """Log state machine transition and record event fixture."""
        self.current_state = new_state
        record = EventRecord(
            event_id=new_state,
            time_s=state.time_s,
            altitude_m=state.z,
            vertical_speed_mps=state.vz,
            horizontal_speed_mps=state.vx,
            pitch_deg=state.pitch_deg,
            mass_kg=state.mass_kg,
            details=details
        )
        self.event_log.append(record)

    def update(self, state: LandingState,
               flip_triggered: bool,
               flip_completed: bool,
               engine_state: str,
               usable_propellant_kg: float) -> str:
        """
        Evaluate transitions based on instantaneous state and subsystem signals.
        Returns the active state label.
        """
        # Global failure condition: propellant exhausted during burn
        if usable_propellant_kg <= 0.0 and self.current_state in ("THRUST_RAMP", "POWERED_DECELERATION", "TERMINAL_DESCENT"):
            if self.current_state != "PROPELLANT_MARGIN_FAILURE":
                self.record_transition("PROPELLANT_MARGIN_FAILURE", state, "Usable propellant exhausted before touchdown")
            return self.current_state

        # Sequential nominal state transitions
        if self.current_state == "APPROACH":
            if flip_triggered:
                self.record_transition("FLIP_INITIATION", state, "Flip maneuver commanded at trigger altitude")
                self.current_state = "FLIP_ROTATION"

        elif self.current_state in ("FLIP_INITIATION", "FLIP_ROTATION"):
            if abs(state.pitch_deg) <= 15.0 or flip_completed:
                self.record_transition("VERTICAL_ALIGNMENT", state, "Vehicle oriented within 15 deg of local vertical")

        elif self.current_state == "VERTICAL_ALIGNMENT":
            if engine_state == "IGNITION_PENDING":
                self.record_transition("ENGINE_IGNITION_PENDING", state, "Engine relight command issued; awaiting spin-up")
            elif engine_state == "RAMPING":
                self.record_transition("THRUST_RAMP", state, "Engines lit; thrust ramping up to commanded level")

        elif self.current_state == "ENGINE_IGNITION_PENDING":
            if engine_state == "RAMPING":
                self.record_transition("THRUST_RAMP", state, "Engines lit; thrust ramping up to commanded level")

        elif self.current_state == "THRUST_RAMP":
            if engine_state == "BURNING":
                self.record_transition("POWERED_DECELERATION", state, "Thrust ramp complete; closed-loop powered descent active")

        elif self.current_state == "POWERED_DECELERATION":
            if state.z <= 30.0:
                self.record_transition("TERMINAL_DESCENT", state, "Terminal descent phase entered below 30 m")

        return self.current_state

    def detect_surface_crossing(self, prev_state: LandingState, current_state: LandingState) -> Optional[LandingState]:
        """
        Detect continuous surface crossing where altitude passes z = 0.
        Uses linear root-finding to interpolate exact state at z = 0.
        """
        if prev_state.z > 0.0 and current_state.z <= 0.0:
            dz = current_state.z - prev_state.z
            if abs(dz) < 1e-6:
                frac = 0.0
            else:
                frac = (0.0 - prev_state.z) / dz
            frac = max(0.0, min(1.0, frac))

            dt = current_state.time_s - prev_state.time_s
            exact_time = prev_state.time_s + frac * dt
            exact_x = prev_state.x + frac * (current_state.x - prev_state.x)
            exact_vx = prev_state.vx + frac * (current_state.vx - prev_state.vx)
            exact_vz = prev_state.vz + frac * (current_state.vz - prev_state.vz)
            exact_m = prev_state.mass_kg + frac * (current_state.mass_kg - prev_state.mass_kg)
            exact_pitch = prev_state.pitch_deg + frac * (current_state.pitch_deg - prev_state.pitch_deg)
            exact_rate = prev_state.pitch_rate_deg_s + frac * (current_state.pitch_rate_deg_s - prev_state.pitch_rate_deg_s)

            touchdown_state = LandingState(
                time_s=exact_time,
                x=exact_x,
                z=0.0,
                vx=exact_vx,
                vz=exact_vz,
                mass_kg=exact_m,
                pitch_deg=exact_pitch,
                pitch_rate_deg_s=exact_rate,
                thrust_N=current_state.thrust_N,
                throttle=current_state.throttle,
                gimbal_deg=current_state.gimbal_deg,
                engine_state="TOUCHDOWN",
                event="TOUCHDOWN_EVENT",
                drag_N=current_state.drag_N,
                apparent_g=current_state.apparent_g
            )
            self.touchdown_occurred = True
            self.record_transition("TOUCHDOWN_EVENT", touchdown_state, "Surface datum crossing localized via root-finding")
            return touchdown_state

        return None
