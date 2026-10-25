"""
Atmospheric Environment Model
=============================
Phase 6: US Standard Atmosphere 1976 implementation with thermospheric extension,
validity boundaries, density uncertainty scaling, and physical consistency guards.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional

from .constants import (
    SPECIFIC_GAS_CONSTANT_AIR,
    SPECIFIC_HEAT_RATIO_AIR,
    STANDARD_GRAVITY,
    SEA_LEVEL_TEMPERATURE_K,
    SEA_LEVEL_PRESSURE_PA,
    SEA_LEVEL_DENSITY_KG_M3,
    SEA_LEVEL_SPEED_OF_SOUND_MS,
    MAX_ATMOSPHERE_ALTITUDE_M
)


@dataclass
class AtmosphericState:
    """Atmospheric environmental parameters at a given geometric altitude."""
    altitude_m: float
    density_kg_m3: float
    temperature_k: float
    pressure_pa: float
    speed_of_sound_ms: float
    dynamic_viscosity_pa_s: float
    density_scale_factor: float


# US Standard Atmosphere 1976 Geopotential / Geometric Layer Definitions (0 to 86 km)
# Each tuple: (h_base_m, h_top_m, T_base_K, lapse_rate_K_per_m, P_base_Pa)
_ATMOSPHERE_LAYERS = [
    (    0.0, 11000.0, 288.15, -0.0065, 101325.0000),
    (11000.0, 20000.0, 216.65,  0.0000,  22632.0401),
    (20000.0, 32000.0, 216.65,  0.0010,   5474.8774),
    (32000.0, 47000.0, 228.65,  0.0028,    868.0158),
    (47000.0, 51000.0, 270.65,  0.0000,    110.9058),
    (51000.0, 71000.0, 270.65, -0.0028,     66.9385),
    (71000.0, 86000.0, 214.65, -0.0020,      3.9564)
]

# State at mesopause boundary (86 km)
_H_86_M = 86000.0
_T_86_K = 184.65
_P_86_PA = 0.3023
_RHO_86_KG_M3 = _P_86_PA / (SPECIFIC_GAS_CONSTANT_AIR * _T_86_K)  # ~5.704e-6 kg/m^3


class USStandardAtmosphere1976:
    """
    US Standard Atmosphere 1976 with continuous thermospheric continuum extension.
    Provides temperature, pressure, density, sound speed, and dynamic viscosity.
    """

    def __init__(
        self,
        density_scale: float = 1.0,
        temp_offset_k: float = 0.0,
        max_valid_altitude_m: float = MAX_ATMOSPHERE_ALTITUDE_M
    ):
        if density_scale <= 0.0:
            raise ValueError(f"Density scale factor must be strictly positive: {density_scale}")
        self.density_scale = float(density_scale)
        self.temp_offset_k = float(temp_offset_k)
        self.max_valid_altitude_m = float(max_valid_altitude_m)

    def evaluate(self, altitude_m: float) -> AtmosphericState:
        """
        Evaluates atmospheric properties at specified geometric altitude.
        Clamps altitude below sea level and handles high-altitude thermosphere.
        """
        alt = float(altitude_m)

        # Clamping at surface
        if alt <= 0.0:
            t_k = SEA_LEVEL_TEMPERATURE_K + self.temp_offset_k
            p_pa = SEA_LEVEL_PRESSURE_PA
            rho = (p_pa / (SPECIFIC_GAS_CONSTANT_AIR * t_k)) * self.density_scale
            a_ms = math.sqrt(SPECIFIC_HEAT_RATIO_AIR * SPECIFIC_GAS_CONSTANT_AIR * t_k)
            mu = self._sutherland_viscosity(t_k)
            return AtmosphericState(
                altitude_m=alt,
                density_kg_m3=rho,
                temperature_k=t_k,
                pressure_pa=p_pa,
                speed_of_sound_ms=a_ms,
                dynamic_viscosity_pa_s=mu,
                density_scale_factor=self.density_scale
            )

        # Layers 0 to 86 km
        if alt <= _H_86_M:
            t_k, p_pa = self._evaluate_standard_layers(alt)
            t_k += self.temp_offset_k
            rho = (p_pa / (SPECIFIC_GAS_CONSTANT_AIR * t_k)) * self.density_scale
            a_ms = math.sqrt(SPECIFIC_HEAT_RATIO_AIR * SPECIFIC_GAS_CONSTANT_AIR * t_k)
            mu = self._sutherland_viscosity(t_k)
            return AtmosphericState(
                altitude_m=alt,
                density_kg_m3=rho,
                temperature_k=t_k,
                pressure_pa=p_pa,
                speed_of_sound_ms=a_ms,
                dynamic_viscosity_pa_s=mu,
                density_scale_factor=self.density_scale
            )

        # Thermosphere (86 km to 150 km)
        if alt <= self.max_valid_altitude_m:
            # Scale height increases with altitude in thermosphere due to solar heating
            dh = alt - _H_86_M
            # Piecewise scale height fitting US Standard 1976 thermospheric table:
            # at 86 km: H ~ 5.5 km; at 120 km: H ~ 6.5 km; at 150 km: H ~ 12 km
            scale_height_m = 5500.0 + (dh / (_H_86_M)) * 3000.0
            rho = _RHO_86_KG_M3 * math.exp(-dh / scale_height_m) * self.density_scale
            # Temperature increases in thermosphere
            t_k = _T_86_K + (dh / 64000.0) * 450.0 + self.temp_offset_k
            p_pa = rho * SPECIFIC_GAS_CONSTANT_AIR * t_k
            a_ms = math.sqrt(SPECIFIC_HEAT_RATIO_AIR * SPECIFIC_GAS_CONSTANT_AIR * t_k)
            mu = self._sutherland_viscosity(t_k)
            return AtmosphericState(
                altitude_m=alt,
                density_kg_m3=rho,
                temperature_k=t_k,
                pressure_pa=p_pa,
                speed_of_sound_ms=a_ms,
                dynamic_viscosity_pa_s=mu,
                density_scale_factor=self.density_scale
            )

        # Beyond sensible atmosphere (> 150 km)
        t_k = 634.0 + self.temp_offset_k
        return AtmosphericState(
            altitude_m=alt,
            density_kg_m3=0.0,
            temperature_k=t_k,
            pressure_pa=0.0,
            speed_of_sound_ms=math.sqrt(SPECIFIC_HEAT_RATIO_AIR * SPECIFIC_GAS_CONSTANT_AIR * t_k),
            dynamic_viscosity_pa_s=self._sutherland_viscosity(t_k),
            density_scale_factor=self.density_scale
        )

    def _evaluate_standard_layers(self, alt: float) -> Tuple[float, float]:
        """Calculates temperature and pressure within standard layers (0 to 86 km)."""
        for h_base, h_top, t_base, lapse_rate, p_base in _ATMOSPHERE_LAYERS:
            if alt <= h_top:
                dh = alt - h_base
                if abs(lapse_rate) > 1e-12:
                    t_k = t_base + lapse_rate * dh
                    p_pa = p_base * ((t_k / t_base) ** (-STANDARD_GRAVITY / (lapse_rate * SPECIFIC_GAS_CONSTANT_AIR)))
                else:
                    t_k = t_base
                    p_pa = p_base * math.exp(-STANDARD_GRAVITY * dh / (SPECIFIC_GAS_CONSTANT_AIR * t_base))
                return t_k, p_pa

        # Fallback to top of layer 6
        return _T_86_K, _P_86_PA

    @staticmethod
    def _sutherland_viscosity(t_k: float) -> float:
        """Sutherland's formula for dynamic viscosity of air (Pa * s)."""
        beta = 1.458e-6
        s_const = 110.4
        t_clamped = max(t_k, 50.0)
        return (beta * (t_clamped**1.5)) / (t_clamped + s_const)


# Module-level default singleton evaluator
_DEFAULT_ATMOSPHERE = USStandardAtmosphere1976()


def get_atmospheric_state(
    altitude_m: float,
    density_scale: float = 1.0,
    temp_offset_k: float = 0.0
) -> AtmosphericState:
    """Convenience function returning full AtmosphericState."""
    if abs(density_scale - 1.0) < 1e-9 and abs(temp_offset_k) < 1e-9:
        return _DEFAULT_ATMOSPHERE.evaluate(altitude_m)
    atm = USStandardAtmosphere1976(density_scale=density_scale, temp_offset_k=temp_offset_k)
    return atm.evaluate(altitude_m)


def compute_density(altitude_m: float, density_scale: float = 1.0) -> float:
    """Returns atmospheric density (kg / m^3)."""
    return get_atmospheric_state(altitude_m, density_scale=density_scale).density_kg_m3


def compute_speed_of_sound(altitude_m: float) -> float:
    """Returns speed of sound (m / s)."""
    return get_atmospheric_state(altitude_m).speed_of_sound_ms
