"""
Orbital State Vector Representation & Validation
================================================
Encapsulates 3D Cartesian position, velocity, vehicle mass, epoch, and physical invariant checks.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np

from .constants import MU_EARTH, R_EARTH_EQUATORIAL
from .time_systems import DEFAULT_MISSION_EPOCH, format_iso_epoch
from .frames import eci_to_ecef, ecef_to_geodetic

@dataclass
class OrbitalState:
    """
    Cartesian orbital state vector with physical validation guards.
    """
    r: np.ndarray # Position in meters [x, y, z]
    v: np.ndarray # Velocity in m/s [vx, vy, vz]
    epoch: datetime = field(default_factory=lambda: DEFAULT_MISSION_EPOCH)
    frame: str = "ECI_J2000"
    mass_kg: float = 220850.0
    area_m2: float = 63.617
    cd: float = 2.20

    def __post_init__(self):
        self.r = np.asarray(self.r, dtype=np.float64)
        self.v = np.asarray(self.v, dtype=np.float64)

        if self.r.shape != (3,):
            raise ValueError(f"Position vector r must have shape (3,), got {self.r.shape}")
        if self.v.shape != (3,):
            raise ValueError(f"Velocity vector v must have shape (3,), got {self.v.shape}")

        if not np.all(np.isfinite(self.r)):
            raise ValueError(f"Non-finite values detected in position vector: {self.r}")
        if not np.all(np.isfinite(self.v)):
            raise ValueError(f"Non-finite values detected in velocity vector: {self.v}")

        if self.radius_m < 1.0:
            raise ValueError(f"Unphysical position radius near origin: {self.radius_m} m")

        if self.mass_kg <= 0.0 or not math.isfinite(self.mass_kg):
            raise ValueError(f"Vehicle mass must be strictly positive and finite: {self.mass_kg} kg")

    @property
    def radius_m(self) -> float:
        """Euclidean norm of position vector (m)."""
        return float(np.linalg.norm(self.r))

    @property
    def speed_m_s(self) -> float:
        """Euclidean norm of velocity vector (m/s)."""
        return float(np.linalg.norm(self.v))

    @property
    def altitude_spherical_m(self) -> float:
        """Spherical Earth altitude above equatorial radius (m)."""
        return self.radius_m - R_EARTH_EQUATORIAL

    @property
    def altitude_spherical_km(self) -> float:
        return self.altitude_spherical_m / 1000.0

    def specific_energy(self, mu: float = MU_EARTH) -> float:
        """Specific orbital energy E = v^2 / 2 - mu / r (J/kg)."""
        return (self.speed_m_s**2 / 2.0) - (mu / self.radius_m)

    def angular_momentum_vec(self) -> np.ndarray:
        """Specific angular momentum vector h = r x v (m^2/s)."""
        return np.cross(self.r, self.v)

    def angular_momentum_mag(self) -> float:
        """Magnitude of specific angular momentum (m^2/s)."""
        return float(np.linalg.norm(self.angular_momentum_vec()))

    def is_bound(self, mu: float = MU_EARTH) -> bool:
        """Returns True if orbit is gravitationally bound (E < 0), False if parabolic/hyperbolic."""
        return self.specific_energy(mu) < 0.0

    def geodetic_coordinates(self, theta_gst_rad: float = 0.0):
        """
        Calculates WGS-84 geodetic latitude (deg), longitude (deg), and altitude (m).
        """
        r_ecef, _ = eci_to_ecef(self.r, self.v, theta_gst_rad)
        return ecef_to_geodetic(r_ecef)

    def to_dict(self) -> dict:
        return {
            "epoch_utc": format_iso_epoch(self.epoch),
            "frame": self.frame,
            "x_m": float(self.r[0]),
            "y_m": float(self.r[1]),
            "z_m": float(self.r[2]),
            "vx_m_s": float(self.v[0]),
            "vy_m_s": float(self.v[1]),
            "vz_m_s": float(self.v[2]),
            "radius_km": self.radius_m / 1000.0,
            "speed_km_s": self.speed_m_s / 1000.0,
            "mass_kg": float(self.mass_kg),
            "specific_energy_mj_kg": self.specific_energy() / 1e6,
            "is_bound": self.is_bound()
        }
