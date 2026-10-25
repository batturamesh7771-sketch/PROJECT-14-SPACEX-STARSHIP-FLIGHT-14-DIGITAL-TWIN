"""
Reentry Trajectory Guidance & Bank-Angle Control Model
======================================================
Phase 6: Closed-loop bank-angle modulation for cross-track error nulling
and energy management during hypersonic atmospheric reentry.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np

from .constants import (
    DEFAULT_TARGET_LAT_DEG,
    DEFAULT_TARGET_LON_DEG,
    DEFAULT_TARGET_RADIUS_M
)
from .splashdown import compute_crossrange_and_downrange_error


@dataclass
class GuidanceCommand:
    """Guidance controller output at a given trajectory epoch."""
    time_s: float
    bank_angle_cmd_deg: float
    angle_of_attack_cmd_deg: float
    crossrange_error_km: float
    downrange_error_km: float
    guidance_active: bool
    saturation_flag: bool


class CrossrangeBankGuidanceController:
    """
    Closed-loop proportional-derivative bank-angle modulation guidance controller.
    Steers the vehicle towards the target corridor by tilting the aerodynamic lift vector.
    """

    def __init__(
        self,
        target_lat_deg: float = DEFAULT_TARGET_LAT_DEG,
        target_lon_deg: float = DEFAULT_TARGET_LON_DEG,
        entry_lat_deg: float = 7.1084,
        entry_lon_deg: float = -58.3341,
        nominal_aoa_deg: float = 70.0,
        max_bank_angle_deg: float = 45.0,
        max_bank_rate_deg_s: float = 10.0,
        min_control_dynamic_pressure_pa: float = 50.0,
        activation_altitude_m: float = 100000.0,
        termination_altitude_m: float = 15000.0,
        kp_bank_deg_per_km: float = 0.50,
        kd_bank_s_per_km: float = 0.05,
        enabled: bool = True
    ):
        self.target_lat_deg = float(target_lat_deg)
        self.target_lon_deg = float(target_lon_deg)
        self.entry_lat_deg = float(entry_lat_deg)
        self.entry_lon_deg = float(entry_lon_deg)
        self.nominal_aoa_deg = float(nominal_aoa_deg)
        self.max_bank_deg = float(max_bank_angle_deg)
        self.max_bank_rate_deg_s = float(max_bank_rate_deg_s)
        self.min_q_pa = float(min_control_dynamic_pressure_pa)
        self.act_alt_m = float(activation_altitude_m)
        self.term_alt_m = float(termination_altitude_m)
        self.kp = float(kp_bank_deg_per_km)
        self.kd = float(kd_bank_s_per_km)
        self.enabled = bool(enabled)

        # Internal state
        self._last_time_s: Optional[float] = None
        self._last_bank_cmd_deg: float = 0.0
        self._last_crossrange_km: Optional[float] = None

    def reset(self):
        """Resets controller state between simulation runs."""
        self._last_time_s = None
        self._last_bank_cmd_deg = 0.0
        self._last_crossrange_km = None

    def compute_command(
        self,
        time_s: float,
        current_lat_deg: float,
        current_lon_deg: float,
        current_alt_m: float,
        dynamic_pressure_pa: float
    ) -> GuidanceCommand:
        """
        Computes commanded bank angle and angle of attack based on current state.
        Enforces rate limits, dynamic pressure thresholds, and saturation bounds.
        """
        cross_km, down_km = compute_crossrange_and_downrange_error(
            current_lat_deg=current_lat_deg,
            current_lon_deg=current_lon_deg,
            target_lat_deg=self.target_lat_deg,
            target_lon_deg=self.target_lon_deg,
            entry_lat_deg=self.entry_lat_deg,
            entry_lon_deg=self.entry_lon_deg
        )

        # Uncontrolled or out-of-boundary check
        if (
            not self.enabled
            or current_alt_m > self.act_alt_m
            or current_alt_m < self.term_alt_m
            or dynamic_pressure_pa < self.min_q_pa
        ):
            # Inactive or disabled guidance: return zero bank
            self._last_time_s = time_s
            self._last_bank_cmd_deg = 0.0
            self._last_crossrange_km = cross_km
            return GuidanceCommand(
                time_s=time_s,
                bank_angle_cmd_deg=0.0,
                angle_of_attack_cmd_deg=self.nominal_aoa_deg,
                crossrange_error_km=cross_km,
                downrange_error_km=down_km,
                guidance_active=False,
                saturation_flag=False
            )

        # Estimate crossrange rate (derivative)
        dt = (time_s - self._last_time_s) if self._last_time_s is not None else 1.0
        dt = max(dt, 1e-3)
        if self._last_crossrange_km is not None:
            cross_rate_km_s = (cross_km - self._last_crossrange_km) / dt
        else:
            cross_rate_km_s = 0.0

        # Guidance law: Bank left if right of track (cross_km > 0 => bank < 0)
        # Bank right if left of track (cross_km < 0 => bank > 0)
        raw_bank_cmd = -(self.kp * cross_km + self.kd * cross_rate_km_s)

        # Rate limiting
        max_delta = self.max_bank_rate_deg_s * dt
        delta = min(max(raw_bank_cmd - self._last_bank_cmd_deg, -max_delta), max_delta)
        rate_limited_bank = self._last_bank_cmd_deg + delta

        # Magnitude saturation
        saturated = False
        if abs(rate_limited_bank) > self.max_bank_deg:
            saturated = True
            final_bank = math.copysign(self.max_bank_deg, rate_limited_bank)
        else:
            final_bank = rate_limited_bank

        self._last_time_s = time_s
        self._last_bank_cmd_deg = final_bank
        self._last_crossrange_km = cross_km

        return GuidanceCommand(
            time_s=time_s,
            bank_angle_cmd_deg=final_bank,
            angle_of_attack_cmd_deg=self.nominal_aoa_deg,
            crossrange_error_km=cross_km,
            downrange_error_km=down_km,
            guidance_active=True,
            saturation_flag=saturated
        )
