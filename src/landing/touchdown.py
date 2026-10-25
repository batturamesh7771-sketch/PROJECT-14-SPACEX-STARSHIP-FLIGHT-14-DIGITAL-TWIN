"""
Touchdown assessment, recovery metrics evaluation, and outcome classification.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import math
from src.landing.state import LandingState
from src.landing.vehicle import StarshipLandingVehicle


@dataclass
class TouchdownReport:
    """Comprehensive recovery assessment metrics."""
    outcome_classification: str               # SUCCESS_CANDIDATE, HARD_IMPACT, ATTITUDE_FAILURE, etc.
    touchdown_time_s: float
    terminal_vertical_speed_mps: float
    terminal_horizontal_speed_mps: float
    terminal_total_speed_mps: float
    terminal_pitch_deg: float
    terminal_pitch_rate_deg_s: float
    miss_distance_m: float
    propellant_consumed_kg: float
    remaining_usable_prop_kg: float
    burn_duration_s: float
    ignition_delay_altitude_loss_m: float
    peak_apparent_g: float
    max_twr: float
    criteria_checks: Dict[str, bool] = field(default_factory=dict)
    disclaimer: str = (
        "Educational recovery assessment for hypothetical reusable landing scenario. "
        "Does not represent official SpaceX proprietary landing data or Flight 14 ocean splashdown telemetry."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_classification": self.outcome_classification,
            "touchdown_time_s": round(self.touchdown_time_s, 4),
            "terminal_vertical_speed_mps": round(self.terminal_vertical_speed_mps, 3),
            "terminal_horizontal_speed_mps": round(self.terminal_horizontal_speed_mps, 3),
            "terminal_total_speed_mps": round(self.terminal_total_speed_mps, 3),
            "terminal_pitch_deg": round(self.terminal_pitch_deg, 3),
            "terminal_pitch_rate_deg_s": round(self.terminal_pitch_rate_deg_s, 3),
            "miss_distance_m": round(self.miss_distance_m, 2),
            "propellant_consumed_kg": round(self.propellant_consumed_kg, 2),
            "remaining_usable_prop_kg": round(self.remaining_usable_prop_kg, 2),
            "burn_duration_s": round(self.burn_duration_s, 2),
            "ignition_delay_altitude_loss_m": round(self.ignition_delay_altitude_loss_m, 2),
            "peak_apparent_g": round(self.peak_apparent_g, 2),
            "max_twr": round(self.max_twr, 2),
            "criteria_checks": self.criteria_checks,
            "disclaimer": self.disclaimer,
        }


class TouchdownAssessor:
    """Evaluates the simulated touchdown state against engineering acceptance criteria."""

    def __init__(self,
                 max_vertical_speed_mps: float = 3.0,
                 max_horizontal_speed_mps: float = 1.5,
                 max_pitch_error_deg: float = 5.0,
                 max_pitch_rate_deg_s: float = 2.0,
                 max_radial_error_m: float = 25.0):
        self.max_vertical_speed_mps = max_vertical_speed_mps
        self.max_horizontal_speed_mps = max_horizontal_speed_mps
        self.max_pitch_error_deg = max_pitch_error_deg
        self.max_pitch_rate_deg_s = max_pitch_rate_deg_s
        self.max_radial_error_m = max_radial_error_m

    def assess(self,
               touchdown_state: LandingState,
               vehicle: StarshipLandingVehicle,
               propellant_consumed_kg: float,
               burn_duration_s: float,
               ignition_delay_altitude_loss_m: float,
               peak_apparent_g: float,
               max_thrust_N: float) -> TouchdownReport:
        """
        Evaluate touchdown state against criteria and determine classification.
        """
        vz_mag = abs(touchdown_state.vz)
        vx_mag = abs(touchdown_state.vx)
        pitch_err = abs(touchdown_state.pitch_deg)
        pitch_rate = abs(touchdown_state.pitch_rate_deg_s)
        miss_dist = abs(touchdown_state.x)

        remaining_prop = max(0.0, vehicle.usable_propellant_kg - propellant_consumed_kg)
        g0 = 9.80665
        max_twr = max_thrust_N / (touchdown_state.mass_kg * g0)

        # Evaluate individual criteria
        checks = {
            "vertical_speed_acceptable": vz_mag <= self.max_vertical_speed_mps,
            "horizontal_speed_acceptable": vx_mag <= self.max_horizontal_speed_mps,
            "pitch_attitude_acceptable": pitch_err <= self.max_pitch_error_deg,
            "pitch_rate_acceptable": pitch_rate <= self.max_pitch_rate_deg_s,
            "target_radial_acceptable": miss_dist <= self.max_radial_error_m,
            "propellant_margin_acceptable": remaining_prop >= 0.0,
        }

        # Determine outcome classification
        if remaining_prop <= 0.0 and vz_mag > self.max_vertical_speed_mps:
            outcome = "PROPELLANT_MARGIN_FAILURE"
        elif pitch_err > 10.0:
            outcome = "ATTITUDE_FAILURE"
        elif vz_mag > 5.0:
            outcome = "HARD_IMPACT"
        elif miss_dist > 50.0:
            outcome = "MISSED_TARGET"
        elif all(checks.values()):
            outcome = "SUCCESS_CANDIDATE"
        else:
            outcome = "TRAJECTORY_REACHED_SURFACE"

        return TouchdownReport(
            outcome_classification=outcome,
            touchdown_time_s=touchdown_state.time_s,
            terminal_vertical_speed_mps=vz_mag,
            terminal_horizontal_speed_mps=vx_mag,
            terminal_total_speed_mps=touchdown_state.speed_mps,
            terminal_pitch_deg=touchdown_state.pitch_deg,
            terminal_pitch_rate_deg_s=touchdown_state.pitch_rate_deg_s,
            miss_distance_m=miss_dist,
            propellant_consumed_kg=propellant_consumed_kg,
            remaining_usable_prop_kg=remaining_prop,
            burn_duration_s=burn_duration_s,
            ignition_delay_altitude_loss_m=ignition_delay_altitude_loss_m,
            peak_apparent_g=peak_apparent_g,
            max_twr=max_twr,
            criteria_checks=checks,
        )
