"""
Terminal landing guidance and closed-loop feedback flight controller.
"""

from dataclasses import dataclass
import math
from typing import Tuple
from src.landing.state import LandingState
from src.landing.vehicle import StarshipLandingVehicle
from src.landing.propulsion import RaptorLandingPropulsion


@dataclass
class TerminalLandingGuidance:
    """Computes commanded engine throttle and TVC gimbal angle to guide the vehicle to a soft touchdown."""
    target_x_m: float = 0.0                      # Target landing pad downrange coordinate [m]
    target_z_m: float = 0.0                      # Target surface datum [m]
    target_deceleration_mps2: float = 12.0       # Target constant deceleration profile [m/s^2]
    touchdown_velocity_mps: float = 1.5          # Target terminal descent speed at contact [m/s]
    kp_vertical: float = 0.40                    # Vertical position error gain
    kd_vertical: float = 0.80                    # Vertical velocity damping gain
    kp_horizontal: float = 0.05                  # Horizontal position error gain
    kd_horizontal: float = 0.15                  # Horizontal velocity damping gain
    max_tilt_deg: float = 10.0                   # Maximum allowed vehicle tilt for lateral translation [deg]

    def compute_desired_vertical_velocity(self, current_altitude_m: float) -> float:
        """
        Compute desired vertical velocity profile:
        - Above 30 m: parabolic deceleration profile vz_des = -sqrt(2 * a_target * alt) - vz_td
        - Below 30 m: constant velocity descent vz_des = -vz_td
        """
        alt = max(0.0, current_altitude_m - self.target_z_m)
        if alt <= 30.0:
            return -self.touchdown_velocity_mps
        v_sq = 2.0 * self.target_deceleration_mps2 * alt
        return -math.sqrt(v_sq) - self.touchdown_velocity_mps

    def compute_commands(self, state: LandingState,
                         vehicle: StarshipLandingVehicle,
                         propulsion: RaptorLandingPropulsion) -> Tuple[float, float, float]:
        """
        Evaluate guidance law to determine throttle and TVC gimbal commands.
        Returns: (throttle_cmd, gimbal_cmd_deg, desired_vz_mps)
        """
        g0 = 9.80665
        alt = max(0.0, state.z - self.target_z_m)
        vz_des = self.compute_desired_vertical_velocity(state.z)
        vz_error = vz_des - state.vz

        # Vertical channel
        if alt <= 30.0:
            az_cmd = 1.5 * vz_error
        else:
            az_cmd = self.target_deceleration_mps2 + self.kd_vertical * vz_error

        # Required vertical thrust: m * (g0 + az_cmd)
        required_fz = state.mass_kg * (g0 + az_cmd)
        required_thrust = max(0.0, required_fz / max(math.cos(math.radians(state.pitch_deg)), 0.1))

        # Commanded throttle fraction
        raw_throttle = required_thrust / max(propulsion.max_cluster_thrust_N, 1.0)
        throttle_cmd = max(propulsion.minimum_throttle, min(propulsion.maximum_throttle, raw_throttle))

        # Horizontal channel: null lateral drift to pad center
        ax_cmd = self.kp_horizontal * (self.target_x_m - state.x) + self.kd_horizontal * (0.0 - state.vx)

        # Required thrust tilt angle: tan(tilt) ~ -ax_cmd / g0
        tilt_target_rad = -math.atan2(ax_cmd, g0)
        tilt_target_deg = math.degrees(tilt_target_rad)
        clamped_tilt_deg = max(-self.max_tilt_deg, min(self.max_tilt_deg, tilt_target_deg))

        # TVC gimbal command aims to steer thrust vector toward clamped tilt target
        raw_gimbal_deg = clamped_tilt_deg - state.pitch_deg
        gimbal_cmd_deg = max(-propulsion.gimbal_limit_deg, min(propulsion.gimbal_limit_deg, raw_gimbal_deg))

        return throttle_cmd, gimbal_cmd_deg, vz_des
