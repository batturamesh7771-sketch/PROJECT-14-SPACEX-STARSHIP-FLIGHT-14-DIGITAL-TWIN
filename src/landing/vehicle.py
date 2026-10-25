"""
Vehicle structural and aerodynamic parameter definitions.
"""

from dataclasses import dataclass
import math
from typing import Tuple


@dataclass
class StarshipLandingVehicle:
    """Starship upper stage physical, aerodynamic, and structural configuration."""
    dry_mass_kg: float = 99980.0
    usable_propellant_kg: float = 25000.0
    reserve_propellant_kg: float = 1500.0
    reference_area_m2: float = 63.62             # Axial reference area (pi * 4.5^2) [m^2]
    broadside_area_m2: float = 450.0             # Broadside projected area (~50m x 9m) [m^2]
    axial_drag_coeff: float = 0.30               # Drag coefficient for nose-first / tail-first flow
    crossflow_drag_coeff: float = 1.15           # Drag coefficient in belly-flop attitude
    lift_coeff_max: float = 0.25                 # Maximum body/flap aerodynamic lift coefficient
    pitch_inertia_nom_kg_m2: float = 2.5e7       # Nominal pitch moment of inertia [kg*m^2]
    nominal_landing_mass_kg: float = 124980.0    # Reference mass for inertia scaling [kg]
    gimbal_arm_m: float = 20.0                   # Distance from center-of-mass to gimbal pivot [m]
    max_control_torque_Nm: float = 5.0e6         # Maximum control moment authority [N*m]
    pitch_rate_damping_Nm_s: float = 8.0e5       # Pitch rate aerodynamic/control damping [N*m*s]

    @property
    def total_initial_mass_kg(self) -> float:
        return self.dry_mass_kg + self.usable_propellant_kg

    def effective_aero_properties(self, pitch_deg: float) -> Tuple[float, float, float]:
        """
        Compute effective aerodynamic reference area, drag coefficient, and lift coefficient
        based on vehicle pitch angle relative to airflow.
        pitch_deg: -90 deg is belly-down (crossflow), 0 deg is upright vertical (axial).
        Returns: (A_eff_m2, Cd_eff, Cl_eff)
        """
        # Angle of attack proxy: alpha is relative to vertical flow
        # In vertical descent with theta = -90 (horizontal), alpha = 90 deg -> crossflow
        # With theta = 0 (vertical), alpha = 0 deg -> axial
        theta_rad = math.radians(pitch_deg)
        cross_factor = abs(math.sin(theta_rad))  # 1.0 at -90 deg, 0.0 at 0 deg

        # Smooth blend between axial and broadside projections
        a_eff = self.reference_area_m2 + cross_factor * (self.broadside_area_m2 - self.reference_area_m2)
        cd_eff = self.axial_drag_coeff + cross_factor * (self.crossflow_drag_coeff - self.axial_drag_coeff)

        # Lift is zero at pure 0 deg (axial) and pure 90 deg (symmetric crossflow),
        # peaking around 45 deg attitude tilt
        cl_eff = self.lift_coeff_max * math.sin(2.0 * theta_rad)

        return a_eff, cd_eff, cl_eff

    def pitch_inertia(self, current_mass_kg: float) -> float:
        """Dynamically scale pitch moment of inertia with vehicle mass depletion."""
        ratio = max(current_mass_kg / self.nominal_landing_mass_kg, 0.70)
        return self.pitch_inertia_nom_kg_m2 * ratio
