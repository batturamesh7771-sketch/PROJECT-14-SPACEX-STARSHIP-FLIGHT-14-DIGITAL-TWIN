"""
Analytical structural mechanics and Roark's formulas for thin-walled pressurized cylindrical shells.
References:
  - Roark's Formulas for Stress and Strain, 8th Edition (Table 13.1, Pressure Vessels).
  - NASA SP-8007: Buckling of Thin-Walled Circular Cylinders.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AnalyticalStressResult:
    """Exact closed-form stress and deformation results from thin-shell theory."""
    pressure_pa: float
    axial_force_N: float
    radius_m: float
    thickness_m: float
    length_m: float
    hoop_stress_pa: float
    axial_stress_pa: float
    von_mises_stress_pa: float
    radial_displacement_m: float
    axial_displacement_m: float
    hoop_strain: float
    axial_strain: float
    safety_factor_yield: float
    margin_of_safety_yield: float
    classical_buckling_stress_pa: float
    critical_buckling_load_N: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pressure_bar": round(self.pressure_pa / 1e5, 3),
            "pressure_MPa": round(self.pressure_pa / 1e6, 3),
            "axial_force_MN": round(self.axial_force_N / 1e6, 3),
            "radius_m": round(self.radius_m, 4),
            "thickness_mm": round(self.thickness_m * 1000.0, 2),
            "radius_to_thickness_ratio": round(self.radius_m / self.thickness_m, 1),
            "hoop_stress_MPa": round(self.hoop_stress_pa / 1e6, 2),
            "axial_stress_MPa": round(self.axial_stress_pa / 1e6, 2),
            "von_mises_stress_MPa": round(self.von_mises_stress_pa / 1e6, 2),
            "radial_displacement_mm": round(self.radial_displacement_m * 1000.0, 3),
            "axial_displacement_mm": round(self.axial_displacement_m * 1000.0, 3),
            "safety_factor_yield": round(self.safety_factor_yield, 3),
            "margin_of_safety_yield": round(self.margin_of_safety_yield, 3),
            "classical_buckling_stress_MPa": round(self.classical_buckling_stress_pa / 1e6, 2),
            "critical_buckling_load_MN": round(self.critical_buckling_load_N / 1e6, 2),
        }


def compute_roark_stresses(radius_m: float = 4.5,
                           thickness_m: float = 0.004,
                           length_m: float = 10.0,
                           pressure_pa: float = 6.0e5,
                           axial_force_N: float = 3.53e6,
                           youngs_modulus_pa: float = 1.93e11,
                           poissons_ratio: float = 0.29,
                           yield_strength_pa: float = 2.90e8) -> AnalyticalStressResult:
    """
    Compute closed-form Roark thin-walled cylindrical shell stresses and deformations.
    radius_m: Shell mean radius [m]
    thickness_m: Shell wall thickness [m]
    length_m: Cylindrical section height [m]
    pressure_pa: Internal ullage/fluid pressure [Pa]
    axial_force_N: Compressive axial force [N] (positive = compression)
    youngs_modulus_pa: Young's Modulus [Pa] (193 GPa for 304L)
    poissons_ratio: Poisson's ratio (0.29 for 304L)
    yield_strength_pa: Material yield stress [Pa] (290 MPa annealed minimum)
    """
    # 1. Classical Hoop Stress (Circumferential Membrane Stress)
    # sigma_h = (p * r) / t
    sigma_hoop = (pressure_pa * radius_m) / thickness_m

    # 2. Longitudinal (Axial) Membrane Stress
    # End-cap tensile pressure contribution: sigma_l_pres = (p * r) / (2 * t)
    # Compressive launch axial load contribution: sigma_l_axial = -F_axial / (2 * pi * r * t)
    circumference = 2.0 * math.pi * radius_m
    cross_section_area = circumference * thickness_m

    sigma_axial_pressure = (pressure_pa * radius_m) / (2.0 * thickness_m)
    sigma_axial_load = -axial_force_N / cross_section_area
    sigma_axial = sigma_axial_pressure + sigma_axial_load

    # 3. Von Mises Equivalent Stress (Plane Stress Assumption, sigma_r ~ 0 on thin membrane)
    # sigma_vm = sqrt(sigma_h^2 - sigma_h * sigma_a + sigma_a^2)
    von_mises = math.sqrt(sigma_hoop ** 2 - sigma_hoop * sigma_axial + sigma_axial ** 2)

    # 4. Elastic Strains and Displacements
    # Generalized Hooke's Law for plane stress:
    # eps_h = (1 / E) * (sigma_h - nu * sigma_a)
    # eps_a = (1 / E) * (sigma_a - nu * sigma_h)
    eps_hoop = (1.0 / youngs_modulus_pa) * (sigma_hoop - poissons_ratio * sigma_axial)
    eps_axial = (1.0 / youngs_modulus_pa) * (sigma_axial - poissons_ratio * sigma_hoop)

    # Radial expansion: delta_r = r * eps_h
    delta_r = radius_m * eps_hoop
    # Axial deflection: delta_L = L * eps_a
    delta_L = length_m * eps_axial

    # 5. Safety Factors
    sf_yield = yield_strength_pa / max(von_mises, 1.0)
    mos_yield = sf_yield - 1.0

    # 6. NASA SP-8007 Classical Elastic Axial Buckling Stress
    buckling_res = compute_nasa_sp8007_buckling_stress(
        radius_m=radius_m,
        thickness_m=thickness_m,
        length_m=length_m,
        pressure_pa=pressure_pa,
        axial_force_N=axial_force_N,
        youngs_modulus_pa=youngs_modulus_pa,
        poissons_ratio=poissons_ratio
    )

    return AnalyticalStressResult(
        pressure_pa=pressure_pa,
        axial_force_N=axial_force_N,
        radius_m=radius_m,
        thickness_m=thickness_m,
        length_m=length_m,
        hoop_stress_pa=sigma_hoop,
        axial_stress_pa=sigma_axial,
        von_mises_stress_pa=von_mises,
        radial_displacement_m=delta_r,
        axial_displacement_m=delta_L,
        hoop_strain=eps_hoop,
        axial_strain=eps_axial,
        safety_factor_yield=sf_yield,
        margin_of_safety_yield=mos_yield,
        classical_buckling_stress_pa=buckling_res["critical_buckling_stress_with_pressure_Pa"],
        critical_buckling_load_N=buckling_res["critical_buckling_load_N"]
    )


def calculate_decay_parameter_beta(radius_m: float, thickness_m: float, nu: float = 0.29) -> float:
    """
    Compute Hetenyi elastic shell decay parameter beta:
      beta = [ 3*(1 - nu^2) / (r^2 * t^2) ]^(1/4)  [m^-1]
    """
    return ((3.0 * (1.0 - nu ** 2)) / ((radius_m ** 2) * (thickness_m ** 2))) ** 0.25


def calculate_boundary_decay_length(radius_m: float, thickness_m: float, nu: float = 0.29) -> float:
    """
    Compute boundary attenuation wave length:
      lambda = pi / beta  [m]
    Edge bending effects decay to negligible levels within approx 1 to 2 lambda.
    """
    beta = calculate_decay_parameter_beta(radius_m, thickness_m, nu)
    return math.pi / beta


def compute_nasa_sp8007_buckling_stress(radius_m: float,
                                        thickness_m: float,
                                        length_m: float,
                                        pressure_pa: float = 0.0,
                                        axial_force_N: float = 0.0,
                                        youngs_modulus_pa: float = 1.93e11,
                                        poissons_ratio: float = 0.29) -> Dict[str, float]:
    """
    Compute thin-walled circular cylinder buckling characteristics according to NASA SP-8007.
    """
    # 1. Classical unpressurized buckling stress:
    # sigma_cl = (E / sqrt(3*(1 - nu^2))) * (t / r)
    sigma_cl = (youngs_modulus_pa / math.sqrt(3.0 * (1.0 - poissons_ratio ** 2))) * (thickness_m / radius_m)

    # 2. Experimental knockdown factor gamma:
    # For thin-walled cylinders (r/t ~ 1000), imperfection sensitivity reduces buckling capacity
    # NASA SP-8007 empirical fit: gamma approx 0.20 to 0.35
    gamma_knockdown = 0.20
    sigma_design_unpres = sigma_cl * gamma_knockdown

    # 3. Internal pressure stabilization contribution (NASA SP-8007 Sec 3.2):
    q_param = (pressure_pa / youngs_modulus_pa) * ((radius_m / thickness_m) ** 2)
    delta_buckling_pressure = 0.10 * q_param * sigma_cl
    total_crit_stress = sigma_design_unpres + delta_buckling_pressure

    cross_section_area = 2.0 * math.pi * radius_m * thickness_m
    crit_load_N = total_crit_stress * cross_section_area

    applied_compressive_stress = axial_force_N / cross_section_area if cross_section_area > 0 else 0.0
    sf_buckling = total_crit_stress / max(applied_compressive_stress, 1.0)

    return {
        "classical_buckling_stress_MPa": sigma_cl / 1e6,
        "knockdown_factor_gamma": gamma_knockdown,
        "design_buckling_stress_unpressurized_MPa": sigma_design_unpres / 1e6,
        "pressure_stabilization_delta_MPa": delta_buckling_pressure / 1e6,
        "critical_buckling_stress_with_pressure_MPa": total_crit_stress / 1e6,
        "critical_buckling_stress_with_pressure_Pa": total_crit_stress,
        "critical_buckling_load_N": crit_load_N,
        "critical_buckling_load_MN": crit_load_N / 1e6,
        "applied_compressive_stress_MPa": applied_compressive_stress / 1e6,
        "safety_factor_buckling": sf_buckling,
    }

