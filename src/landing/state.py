"""
State data models and records for terminal landing simulation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math


@dataclass
class LandingState:
    """Instantaneous state of the vehicle in the Local Terminal Frame (LTF)."""
    time_s: float
    x: float                     # Downrange distance from target pad [m]
    z: float                     # Altitude above landing datum [m]
    vx: float                    # Horizontal velocity [m/s]
    vz: float                    # Vertical velocity [m/s]
    mass_kg: float               # Vehicle instantaneous mass [kg]
    pitch_deg: float             # Body pitch angle relative to vertical [deg] (0 = vertical, -90 = belly-down)
    pitch_rate_deg_s: float      # Pitch angular rate [deg/s]
    thrust_N: float = 0.0        # Total instantaneous thrust [N]
    throttle: float = 0.0        # Commanded throttle fraction [0.0 - 1.0]
    gimbal_deg: float = 0.0      # TVC gimbal deflection [deg]
    engine_state: str = "OFF"    # Propulsion state
    event: str = "NONE"          # Active mission state machine event
    drag_N: float = 0.0          # Aerodynamic drag force [N]
    lift_N: float = 0.0          # Aerodynamic lift force [N]
    apparent_g: float = 1.0      # Apparent deceleration load [g]

    @property
    def speed_mps(self) -> float:
        """Total relative airspeed magnitude [m/s]."""
        return math.sqrt(self.vx * self.vx + self.vz * self.vz)

    @property
    def flight_path_angle_deg(self) -> float:
        """Flight path angle gamma relative to horizontal [deg]."""
        return math.degrees(math.atan2(self.vz, self.vx))

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to serializable dictionary."""
        return {
            "time_s": round(self.time_s, 4),
            "x_m": round(self.x, 3),
            "z_m": round(self.z, 3),
            "vx_mps": round(self.vx, 3),
            "vz_mps": round(self.vz, 3),
            "speed_mps": round(self.speed_mps, 3),
            "mass_kg": round(self.mass_kg, 2),
            "pitch_deg": round(self.pitch_deg, 3),
            "pitch_rate_deg_s": round(self.pitch_rate_deg_s, 3),
            "thrust_N": round(self.thrust_N, 1),
            "throttle": round(self.throttle, 4),
            "gimbal_deg": round(self.gimbal_deg, 3),
            "engine_state": self.engine_state,
            "event": self.event,
            "drag_N": round(self.drag_N, 1),
            "apparent_g": round(self.apparent_g, 3),
        }


@dataclass
class EventRecord:
    """Discrete state machine transition record."""
    event_id: str
    time_s: float
    altitude_m: float
    vertical_speed_mps: float
    horizontal_speed_mps: float
    pitch_deg: float
    mass_kg: float
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "time_s": round(self.time_s, 4),
            "altitude_m": round(self.altitude_m, 2),
            "vertical_speed_mps": round(self.vertical_speed_mps, 2),
            "horizontal_speed_mps": round(self.horizontal_speed_mps, 2),
            "pitch_deg": round(self.pitch_deg, 2),
            "mass_kg": round(self.mass_kg, 1),
            "details": self.details,
        }
