"""
Phase 9: Aerothermal Reentry & Thermal Protection System (TPS) Package.
Couples trajectory states to stagnation/windward heat flux correlations and 1D transient conduction.
"""

from src.thermal.material_properties import (
    MaterialProperties,
    get_silica_tile_properties,
    get_sip_felt_properties,
    get_stainless_steel_properties,
    STEFAN_BOLTZMANN,
)
from src.thermal.aerothermal_flux import (
    compute_sutton_graves_heat_flux,
    compute_detra_kemp_riddell_flux,
    compute_windward_acreage_flux,
    compute_radiative_equilibrium_temp,
)
from src.thermal.conduction_1d import (
    ThermalStackLayer,
    ThermalStackMesh,
    TransientThermalSolver1D,
    ThermalSolution1D,
)
from src.thermal.margin_analysis import (
    evaluate_bondline_margins,
    run_density_sensitivity_study,
)

__all__ = [
    "MaterialProperties",
    "get_silica_tile_properties",
    "get_sip_felt_properties",
    "get_stainless_steel_properties",
    "STEFAN_BOLTZMANN",
    "compute_sutton_graves_heat_flux",
    "compute_detra_kemp_riddell_flux",
    "compute_windward_acreage_flux",
    "compute_radiative_equilibrium_temp",
    "ThermalStackLayer",
    "ThermalStackMesh",
    "TransientThermalSolver1D",
    "ThermalSolution1D",
    "evaluate_bondline_margins",
    "run_density_sensitivity_study",
]
