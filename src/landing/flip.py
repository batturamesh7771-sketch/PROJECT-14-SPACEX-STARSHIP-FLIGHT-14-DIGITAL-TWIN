"""
Aerodynamic flip maneuver implementation supporting both prescribed kinematic and planar dynamic modes.
"""

from dataclasses import dataclass
import math
from typing import Tuple, Optional


@dataclass
class AerodynamicFlipManeuver:
    """Controls the transition from belly-down horizontal descent to upright vertical orientation."""
    mode: str = "prescribed_kinematic_flip"   # "prescribed_kinematic_flip" or "planar_dynamic_flip"
    trigger_altitude_m: float = 800.0         # Altitude to command flip initiation [m]
    duration_s: float = 4.0                   # Nominal maneuver duration [s]
    target_pitch_deg: float = 0.0             # Upright vertical attitude [deg]
    kp_pitch: float = 3.5e6                   # Pitch attitude proportional gain [N*m/rad] (L2 mode)
    kd_pitch: float = 1.2e6                   # Pitch rate derivative gain [N*m*s/rad] (L2 mode)

    # Runtime state
    is_triggered: bool = False
    trigger_time_s: Optional[float] = None
    is_completed: bool = False
    initial_pitch_deg: float = -90.0

    def check_trigger(self, altitude_m: float, time_s: float, current_pitch_deg: float) -> bool:
        """Check if altitude condition has been crossed to initiate flip."""
        if not self.is_triggered and altitude_m <= self.trigger_altitude_m:
            self.is_triggered = True
            self.trigger_time_s = time_s
            self.initial_pitch_deg = current_pitch_deg
            return True
        return False

    def get_kinematic_pitch(self, current_time_s: float) -> Tuple[float, float]:
        """
        Evaluate smooth kinematic pitch profile and pitch rate.
        Uses a cubic smoothstep profile S(tau) = 3*tau^2 - 2*tau^3.
        Returns: (pitch_deg, pitch_rate_deg_s)
        """
        if not self.is_triggered or self.trigger_time_s is None:
            return self.initial_pitch_deg, 0.0

        elapsed = current_time_s - self.trigger_time_s
        if elapsed >= self.duration_s:
            self.is_completed = True
            return self.target_pitch_deg, 0.0

        tau = elapsed / self.duration_s
        # Smoothstep curve from 0 to 1
        s_tau = 3.0 * (tau ** 2) - 2.0 * (tau ** 3)
        # Time derivative dS/dt = (6*tau - 6*tau^2) / duration
        ds_dt = (6.0 * tau - 6.0 * (tau ** 2)) / self.duration_s

        delta_pitch = self.target_pitch_deg - self.initial_pitch_deg
        pitch_deg = self.initial_pitch_deg + s_tau * delta_pitch
        pitch_rate_deg_s = ds_dt * delta_pitch

        return pitch_deg, pitch_rate_deg_s

    def compute_dynamic_torque(self, current_pitch_deg: float, current_pitch_rate_deg_s: float,
                               max_control_torque_Nm: float) -> float:
        """
        Compute commanded active control torque for L2 planar dynamic flip mode.
        Returns: M_control [N*m]
        """
        if not self.is_triggered:
            # Maintain belly-flop orientation prior to trigger
            target = self.initial_pitch_deg
        else:
            target = self.target_pitch_deg

        pitch_err_rad = math.radians(target - current_pitch_deg)
        rate_rad_s = math.radians(current_pitch_rate_deg_s)

        raw_torque = self.kp_pitch * pitch_err_rad - self.kd_pitch * rate_rad_s
        clamped_torque = max(-max_control_torque_Nm, min(max_control_torque_Nm, raw_torque))
        return clamped_torque
