"""
Vehicle Configuration & Aerodynamic Property Definitions
========================================================
Phase 6: Encapsulates Starship-like blunt-body vehicle mass, geometric reference properties,
aerodynamic limits, and parameter validation guards for atmospheric reentry.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from .constants import (
    DEFAULT_VEHICLE_MASS_KG,
    DEFAULT_REFERENCE_AREA_M2,
    DEFAULT_REFERENCE_LENGTH_M,
    DEFAULT_NOSE_RADIUS_M
)


@dataclass
class ReentryVehicleConfig:
    """
    Parametric aerodynamic and physical configuration for Starship reentry.
    """
    vehicle_id: str = "Starship_Flight14_UpperStage"
    scenario_id: str = "SYNTHETIC_REENTRY_BASELINE"
    mass_kg: float = DEFAULT_VEHICLE_MASS_KG
    reference_area_m2: float = DEFAULT_REFERENCE_AREA_M2
    reference_length_m: float = DEFAULT_REFERENCE_LENGTH_M
    nose_radius_m: float = DEFAULT_NOSE_RADIUS_M

    # Aerodynamic Trim and Control Limits
    nominal_angle_of_attack_deg: float = 70.0  # Hypersonic belly-flop trim angle of attack
    max_bank_angle_deg: float = 45.0           # Maximum roll / bank angle command
    max_bank_rate_deg_s: float = 10.0          # Flap-actuated roll rate limit (deg / s)
    min_control_dynamic_pressure_pa: float = 50.0  # Minimum q_bar for aerodynamic control

    # Aerodynamic Polar Coefficients at High Angle of Attack
    cd_hypersonic_70deg: float = 1.50          # Hypersonic blunt-body drag coefficient
    cl_hypersonic_70deg: float = 0.40          # Hypersonic lift coefficient (L/D ~ 0.27)
    cd_subsonic: float = 1.20                  # Subsonic terminal cross-flow drag coefficient

    def __post_init__(self):
        if self.mass_kg <= 0.0 or not math.isfinite(self.mass_kg):
            raise ValueError(f"Vehicle mass must be strictly positive and finite: {self.mass_kg} kg")
        if self.reference_area_m2 <= 0.0 or not math.isfinite(self.reference_area_m2):
            raise ValueError(f"Reference area must be strictly positive: {self.reference_area_m2} m^2")
        if self.reference_length_m <= 0.0 or not math.isfinite(self.reference_length_m):
            raise ValueError(f"Reference length must be strictly positive: {self.reference_length_m} m")
        if self.nose_radius_m <= 0.0 or not math.isfinite(self.nose_radius_m):
            raise ValueError(f"Nose radius must be strictly positive: {self.nose_radius_m} m")
        if not (0.0 <= self.nominal_angle_of_attack_deg <= 90.0):
            raise ValueError(f"Angle of attack must be between 0 and 90 deg: {self.nominal_angle_of_attack_deg}")
        if self.max_bank_angle_deg <= 0.0 or self.max_bank_angle_deg > 90.0:
            raise ValueError(f"Max bank angle must be in (0, 90] deg: {self.max_bank_angle_deg}")

    @property
    def ballistic_coefficient_kg_m2(self) -> float:
        """Hypersonic ballistic coefficient beta = m / (Cd * A_ref) [kg / m^2]."""
        return self.mass_kg / (self.cd_hypersonic_70deg * self.reference_area_m2)

    @property
    def lift_to_drag_ratio(self) -> float:
        """Nominal hypersonic lift-to-drag ratio L/D."""
        return self.cl_hypersonic_70deg / self.cd_hypersonic_70deg

    def to_dict(self) -> Dict[str, Any]:
        """Serializes vehicle configuration to dictionary."""
        return {
            "vehicle_id": self.vehicle_id,
            "scenario_id": self.scenario_id,
            "mass_kg": self.mass_kg,
            "reference_area_m2": self.reference_area_m2,
            "reference_length_m": self.reference_length_m,
            "nose_radius_m": self.nose_radius_m,
            "ballistic_coefficient_kg_m2": self.ballistic_coefficient_kg_m2,
            "nominal_aoa_deg": self.nominal_angle_of_attack_deg,
            "lift_to_drag_ratio": self.lift_to_drag_ratio,
            "cd_hypersonic": self.cd_hypersonic_70deg,
            "cl_hypersonic": self.cl_hypersonic_70deg,
            "max_bank_angle_deg": self.max_bank_angle_deg
        }
