"""
Temperature-dependent thermophysical material properties for Starship Thermal Protection System (TPS).
Includes ceramic silica tiles (TUFI/LI-900 equivalent), SIP felt, RTV silicone adhesive, and 304L stainless skin.
References:
  - NASA CR-166560: Shuttle TPS Material Property Models.
  - NASA TP-2005-212806: Aerothermal Environment and Thermal Protection for Planetary Entry.
"""

from dataclasses import dataclass
from typing import Callable, Optional
import math

# Fundamental physical constants
STEFAN_BOLTZMANN = 5.670374419e-8  # Stefan-Boltzmann constant [W / (m^2 * K^4)]
RTV_BONDLINE_LIMIT_K = 533.15       # Maximum allowable continuous RTV bondline temp [K] (260 deg C / 500 deg F)
SILICA_REUSABLE_LIMIT_K = 1650.0   # Reusable surface operating limit for RCG-coated silica [K]


@dataclass
class MaterialProperties:
    """Thermophysical material definitions with temperature-dependent functions."""
    name: str
    density_kg_m3: float
    conductivity_func: Callable[[float], float]   # k(T) [W / (m * K)]
    specific_heat_func: Callable[[float], float]  # c_p(T) [J / (kg * K)]
    emissivity: float = 0.85
    max_allowable_temp_k: float = 1650.0

    def get_conductivity(self, temp_k: float) -> float:
        """Evaluate thermal conductivity k at temperature T [K]."""
        t_clamped = max(100.0, min(temp_k, 2500.0))
        return self.conductivity_func(t_clamped)

    def get_specific_heat(self, temp_k: float) -> float:
        """Evaluate specific heat capacity c_p at temperature T [K]."""
        t_clamped = max(100.0, min(temp_k, 2500.0))
        return self.specific_heat_func(t_clamped)

    def get_thermal_diffusivity(self, temp_k: float) -> float:
        """Evaluate thermal diffusivity alpha = k / (rho * c_p) [m^2 / s]."""
        k = self.get_conductivity(temp_k)
        cp = self.get_specific_heat(temp_k)
        return k / (self.density_kg_m3 * cp)


def _silica_conductivity(t: float) -> float:
    """
    Effective thermal conductivity of high-porosity fibrous silica tile in air.
    Accounts for gas conduction and internal radiative pore scattering:
      k(T) = k0 + a1*(T/1000) + a2*(T/1000)^3
    """
    theta = t / 1000.0
    # At 300K: ~0.048 W/(m*K); at 1600K: ~0.185 W/(m*K)
    return 0.032 + 0.025 * theta + 0.028 * (theta ** 3)


def _silica_specific_heat(t: float) -> float:
    """
    Specific heat capacity of amorphous fused silica:
      c_p(T) rises rapidly from 300K and approaches Dulong-Petit asymptotic limit.
    """
    # At 300K: ~730 J/(kg*K); at 1200K+: ~1240 J/(kg*K)
    return 1260.0 - 900.0 * math.exp(-t / 380.0)


def get_silica_tile_properties(density_kg_m3: float = 190.0,
                               emissivity: float = 0.85) -> MaterialProperties:
    """Return RCG-coated porous ceramic silica tile material properties."""
    return MaterialProperties(
        name="Ceramic_Silica_Tile",
        density_kg_m3=density_kg_m3,
        conductivity_func=_silica_conductivity,
        specific_heat_func=_silica_specific_heat,
        emissivity=emissivity,
        max_allowable_temp_k=SILICA_REUSABLE_LIMIT_K
    )


def _sip_conductivity(t: float) -> float:
    """Thermal conductivity of Nomex / quartz felt Strain Isolation Pad."""
    theta = t / 1000.0
    return 0.040 + 0.035 * theta


def _sip_specific_heat(t: float) -> float:
    """Specific heat capacity of SIP felt layer."""
    return 800.0 + 0.5 * t


def get_sip_felt_properties(density_kg_m3: float = 250.0) -> MaterialProperties:
    """Return Strain Isolation Pad (SIP) felt properties."""
    return MaterialProperties(
        name="SIP_Felt_Adhesive",
        density_kg_m3=density_kg_m3,
        conductivity_func=_sip_conductivity,
        specific_heat_func=_sip_specific_heat,
        emissivity=0.80,
        max_allowable_temp_k=RTV_BONDLINE_LIMIT_K
    )


def _steel_conductivity(t: float) -> float:
    """Thermal conductivity of AISI 304L stainless steel."""
    # 15.0 W/(m*K) at 300K, rises to ~21.0 W/(m*K) at 1000K
    return 14.0 + 0.0075 * t


def _steel_specific_heat(t: float) -> float:
    """Specific heat of 304L stainless steel."""
    # 490 J/(kg*K) at 300K, ~600 J/(kg*K) at 1000K
    return 450.0 + 0.15 * t


def get_stainless_steel_properties(density_kg_m3: float = 7900.0) -> MaterialProperties:
    """Return AISI 304L structural skin properties."""
    return MaterialProperties(
        name="AISI_304L_Steel",
        density_kg_m3=density_kg_m3,
        conductivity_func=_steel_conductivity,
        specific_heat_func=_steel_specific_heat,
        emissivity=0.30,
        max_allowable_temp_k=1100.0
    )
