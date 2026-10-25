"""
Raptor landing propulsion cluster model with ignition transients, throttle bounds, and TVC.
"""

from dataclasses import dataclass, field
import math
from typing import Tuple, Optional


@dataclass
class RaptorLandingPropulsion:
    """Models the center gimbaling Raptor landing engine cluster."""
    engine_count: int = 3
    thrust_per_engine_nominal_N: float = 2250000.0   # 2.25 MN nominal sea level
    specific_impulse_s: float = 327.0                # Nominal sea level Isp
    minimum_throttle: float = 0.40                   # Deep throttle floor
    maximum_throttle: float = 1.00                   # 100% rated thrust
    throttle_slew_rate_limit: float = 0.60           # Max throttle change per second (1/s)
    ignition_delay_s: float = 1.0                    # Turbopump spin-up and line chill delay [s]
    thrust_ramp_duration_s: float = 0.8              # S-curve thrust ramp duration [s]
    gimbal_limit_deg: float = 15.0                   # Max TVC deflection [deg]
    gimbal_slew_rate_deg_s: float = 20.0             # Max TVC slew rate [deg/s]

    # Internal runtime state
    ignition_commanded: bool = False
    ignition_time_s: Optional[float] = None
    actual_burn_start_s: Optional[float] = None
    current_throttle: float = 0.0
    current_gimbal_deg: float = 0.0
    current_thrust_N: float = 0.0
    engine_state: str = "OFF"                        # OFF, IGNITION_PENDING, RAMPING, BURNING, EXHAUSTED, SHUTDOWN
    propellant_consumed_kg: float = 0.0

    @property
    def max_cluster_thrust_N(self) -> float:
        """Total maximum thrust available with all configured engines at 100% throttle."""
        return self.engine_count * self.thrust_per_engine_nominal_N

    def command_ignition(self, time_s: float) -> None:
        """Issue engine relight command."""
        if not self.ignition_commanded:
            self.ignition_commanded = True
            self.ignition_time_s = time_s
            self.engine_state = "IGNITION_PENDING"

    def shutdown(self) -> None:
        """Command engine cutoff."""
        self.engine_state = "SHUTDOWN"
        self.current_throttle = 0.0
        self.current_thrust_N = 0.0

    def update(self, current_time_s: float, dt_s: float,
               target_throttle: float, target_gimbal_deg: float,
               remaining_usable_prop_kg: float) -> None:
        """
        Propagate engine state over time step dt_s.
        Clamps throttle, applies slew rate limits, enforces ignition delay and ramp transients.
        """
        # Check fuel exhaustion
        if remaining_usable_prop_kg <= 0.0 and self.engine_state in ("RAMPING", "BURNING"):
            self.engine_state = "EXHAUSTED"
            self.current_throttle = 0.0
            self.current_thrust_N = 0.0
            return

        if self.engine_state in ("OFF", "SHUTDOWN", "EXHAUSTED"):
            self.current_thrust_N = 0.0
            self.current_throttle = 0.0
            return

        # Check ignition delay
        if self.engine_state == "IGNITION_PENDING":
            if self.ignition_time_s is not None and (current_time_s - self.ignition_time_s) >= self.ignition_delay_s:
                self.engine_state = "RAMPING"
                self.actual_burn_start_s = self.ignition_time_s + self.ignition_delay_s
            else:
                self.current_thrust_N = 0.0
                self.current_throttle = 0.0
                return

        # Bounded target throttle
        clamped_target_throttle = max(self.minimum_throttle, min(self.maximum_throttle, target_throttle))

        # Check ramp progress
        if self.engine_state == "RAMPING":
            burn_start = self.actual_burn_start_s if self.actual_burn_start_s is not None else current_time_s
            elapsed_ramp = current_time_s - burn_start
            if elapsed_ramp >= self.thrust_ramp_duration_s:
                self.engine_state = "BURNING"
                ramp_factor = 1.0
            else:
                # S-curve ramp factor: sin^2(pi/2 * t / ramp)
                frac = max(0.0, elapsed_ramp / self.thrust_ramp_duration_s)
                ramp_factor = math.sin(0.5 * math.pi * frac) ** 2

            # Ramp up from 0 to clamped target throttle
            self.current_throttle = clamped_target_throttle * ramp_factor
        elif self.engine_state == "BURNING":
            # Apply throttle slew rate limits
            delta_throttle = clamped_target_throttle - self.current_throttle
            max_delta = self.throttle_slew_rate_limit * dt_s
            if abs(delta_throttle) <= max_delta:
                self.current_throttle = clamped_target_throttle
            else:
                self.current_throttle += math.copysign(max_delta, delta_throttle)

        # Update TVC gimbal angle with rate limits
        clamped_target_gimbal = max(-self.gimbal_limit_deg, min(self.gimbal_limit_deg, target_gimbal_deg))
        delta_gimbal = clamped_target_gimbal - self.current_gimbal_deg
        max_gimbal_delta = self.gimbal_slew_rate_deg_s * dt_s
        if abs(delta_gimbal) <= max_gimbal_delta:
            self.current_gimbal_deg = clamped_target_gimbal
        else:
            self.current_gimbal_deg += math.copysign(max_gimbal_delta, delta_gimbal)

        # Calculate instantaneous thrust magnitude
        self.current_thrust_N = self.current_throttle * self.max_cluster_thrust_N

        # Integrate propellant consumed
        g0 = 9.80665
        mass_flow_rate = self.current_thrust_N / (self.specific_impulse_s * g0)
        self.propellant_consumed_kg += mass_flow_rate * dt_s

    def get_thrust_vector(self, pitch_deg: float) -> Tuple[float, float]:
        """
        Compute thrust components in Local Terminal Frame [Fx, Fz] [N].
        pitch_deg: vehicle pitch relative to vertical (0 = upright, -90 = horizontal).
        Effective thrust angle: psi = pitch_deg + gimbal_deg.
        Thrust acts along the nozzle exhaust direction (opposite exhaust velocity).
        When upright (pitch=0, gimbal=0): Fz = +T, Fx = 0.
        When tilted pitch > 0 (tilted right): nozzle tilts right, Fx pushes left (-T*sin(psi)).
        """
        psi_rad = math.radians(pitch_deg + self.current_gimbal_deg)
        fz = self.current_thrust_N * math.cos(psi_rad)
        fx = -self.current_thrust_N * math.sin(psi_rad)
        return fx, fz

    def get_tvc_moment_Nm(self, gimbal_arm_m: float) -> float:
        """
        Compute pitching moment produced by TVC gimbal deflection [N*m].
        M_tvc = T * sin(gimbal) * arm.
        Positive gimbal deflection produces a restoring / corrective pitching moment.
        """
        gimbal_rad = math.radians(self.current_gimbal_deg)
        return self.current_thrust_N * math.sin(gimbal_rad) * gimbal_arm_m
