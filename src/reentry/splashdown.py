"""
Earth-Fixed Terminal State & Ocean Splashdown Assessment
========================================================
Phase 6: Transforms terminal propagated state to Earth-fixed geodetic coordinates,
evaluates miss distance from modeled target corridor, and classifies splashdown outcomes.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np

from .constants import (
    R_EARTH_EQUATORIAL,
    DEFAULT_TARGET_LAT_DEG,
    DEFAULT_TARGET_LON_DEG,
    DEFAULT_TARGET_RADIUS_M
)
from src.astrodynamics.frames import eci_to_ecef, ecef_to_geodetic


@dataclass
class TerminalSplashdownAssessment:
    """Rigorous evaluation of vehicle terminal impact / splashdown state."""
    impact_time_s: float
    impact_epoch_utc: str
    geodetic_lat_deg: float
    geodetic_lon_deg: float
    geodetic_alt_m: float
    terminal_inertial_speed_ms: float
    terminal_relative_speed_ms: float
    terminal_flight_path_angle_deg: float
    terminal_dynamic_pressure_pa: float
    target_lat_deg: float
    target_lon_deg: float
    target_radius_m: float
    miss_distance_m: float
    miss_distance_km: float
    crossrange_error_km: float
    downrange_error_km: float
    outcome_classification: str
    target_within_corridor: bool
    cumulative_heat_load_mj_m2: float
    peak_dynamic_pressure_pa: float
    peak_apparent_g_load: float
    peak_stagnation_heat_flux_mw_m2: float
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        """Serializes terminal assessment to machine-readable dictionary."""
        return {
            "impact_time_s": self.impact_time_s,
            "impact_epoch_utc": self.impact_epoch_utc,
            "geodetic_lat_deg": self.geodetic_lat_deg,
            "geodetic_lon_deg": self.geodetic_lon_deg,
            "geodetic_alt_m": self.geodetic_alt_m,
            "terminal_inertial_speed_ms": self.terminal_inertial_speed_ms,
            "terminal_relative_speed_ms": self.terminal_relative_speed_ms,
            "terminal_flight_path_angle_deg": self.terminal_flight_path_angle_deg,
            "terminal_dynamic_pressure_pa": self.terminal_dynamic_pressure_pa,
            "target_lat_deg": self.target_lat_deg,
            "target_lon_deg": self.target_lon_deg,
            "miss_distance_km": self.miss_distance_km,
            "crossrange_error_km": self.crossrange_error_km,
            "downrange_error_km": self.downrange_error_km,
            "target_within_corridor": self.target_within_corridor,
            "outcome_classification": self.outcome_classification,
            "cumulative_heat_load_mj_m2": self.cumulative_heat_load_mj_m2,
            "peak_dynamic_pressure_pa": self.peak_dynamic_pressure_pa,
            "peak_apparent_g_load": self.peak_apparent_g_load,
            "peak_stagnation_heat_flux_mw_m2": self.peak_stagnation_heat_flux_mw_m2,
            "disclaimer": self.disclaimer
        }


def great_circle_distance_m(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float
) -> float:
    """
    Computes Great-Circle surface distance between two points on Earth using Haversine formula.
    """
    phi1, phi2 = math.radians(lat1_deg), math.radians(lat2_deg)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2_deg - lon1_deg)

    a = (math.sin(dphi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(min(max(a, 0.0), 1.0)), math.sqrt(max(0.0, 1.0 - a)))
    return R_EARTH_EQUATORIAL * c


def compute_crossrange_and_downrange_error(
    current_lat_deg: float,
    current_lon_deg: float,
    target_lat_deg: float,
    target_lon_deg: float,
    entry_lat_deg: float,
    entry_lon_deg: float
) -> Tuple[float, float]:
    """
    Computes cross-track (crossrange) and along-track (downrange) error relative to
    the nominal great-circle trajectory plane passing from entry point to target.
    """
    # Total distance to target
    d_total = great_circle_distance_m(current_lat_deg, current_lon_deg, target_lat_deg, target_lon_deg)

    # Azimuth from entry to target
    phi_e = math.radians(entry_lat_deg)
    phi_t = math.radians(target_lat_deg)
    dlam_et = math.radians(target_lon_deg - entry_lon_deg)
    y_et = math.sin(dlam_et) * math.cos(phi_t)
    x_et = math.cos(phi_e) * math.sin(phi_t) - math.sin(phi_e) * math.cos(phi_t) * math.cos(dlam_et)
    az_et = math.atan2(y_et, x_et)

    # Azimuth from entry to current
    phi_c = math.radians(current_lat_deg)
    dlam_ec = math.radians(current_lon_deg - entry_lon_deg)
    y_ec = math.sin(dlam_ec) * math.cos(phi_c)
    x_ec = math.cos(phi_e) * math.sin(phi_c) - math.sin(phi_e) * math.cos(phi_c) * math.cos(dlam_ec)
    az_ec = math.atan2(y_ec, x_ec)

    # Distance from entry to current
    d_ec = great_circle_distance_m(entry_lat_deg, entry_lon_deg, current_lat_deg, current_lon_deg)

    # Cross-track distance
    d_az = az_ec - az_et
    # normalize to [-pi, pi]
    d_az = (d_az + math.pi) % (2.0 * math.pi) - math.pi
    crossrange_m = d_ec * math.sin(d_az)
    downrange_err_m = d_total * math.copysign(1.0, math.cos(d_az))

    return crossrange_m / 1000.0, downrange_err_m / 1000.0


def assess_terminal_splashdown(
    r_eci: np.ndarray,
    v_eci: np.ndarray,
    impact_time_s: float,
    impact_epoch_utc: str,
    theta_gst_rad: float,
    target_lat_deg: float = DEFAULT_TARGET_LAT_DEG,
    target_lon_deg: float = DEFAULT_TARGET_LON_DEG,
    target_radius_m: float = DEFAULT_TARGET_RADIUS_M,
    entry_lat_deg: float = 7.1084,
    entry_lon_deg: float = -58.3341,
    cumulative_heat_load_mj_m2: float = 0.0,
    peak_dynamic_pressure_pa: float = 0.0,
    peak_apparent_g_load: float = 0.0,
    peak_stagnation_heat_flux_mw_m2: float = 0.0
) -> TerminalSplashdownAssessment:
    """
    Transforms terminal ECI state to Earth-fixed geodetic coordinates, evaluates
    target miss vector, and classifies splashdown outcome.
    """
    # 1. Transform to ECEF accounting for Earth rotation
    r_ecef, v_ecef = eci_to_ecef(r_eci, v_eci, theta_gst_rad=theta_gst_rad)

    # 2. Convert to WGS-84 geodetic coordinates
    lat_deg, lon_deg, alt_m = ecef_to_geodetic(r_ecef)

    # 3. Kinematic speeds and angles
    v_inertial_mag = float(np.linalg.norm(v_eci))
    v_rel_mag = float(np.linalg.norm(v_ecef))

    # Atmospheric-relative flight-path angle
    r_norm = float(np.linalg.norm(r_ecef))
    gamma_rad = math.asin(min(max(float(np.dot(r_ecef, v_ecef)) / (r_norm * max(v_rel_mag, 1e-6)), -1.0), 1.0))
    gamma_deg = math.degrees(gamma_rad)

    # Terminal dynamic pressure
    from .atmosphere import compute_density
    rho_term = compute_density(max(alt_m, 0.0))
    q_term = 0.5 * rho_term * (v_rel_mag ** 2)

    # 4. Target miss distance
    miss_dist_m = great_circle_distance_m(lat_deg, lon_deg, target_lat_deg, target_lon_deg)
    miss_dist_km = miss_dist_m / 1000.0

    # Crossrange and downrange errors
    cross_km, down_km = compute_crossrange_and_downrange_error(
        current_lat_deg=lat_deg,
        current_lon_deg=lon_deg,
        target_lat_deg=target_lat_deg,
        target_lon_deg=target_lon_deg,
        entry_lat_deg=entry_lat_deg,
        entry_lon_deg=entry_lon_deg
    )

    within_corridor = bool(miss_dist_m <= target_radius_m)
    if within_corridor:
        outcome = "TARGET_REGION_REACHED"
    else:
        outcome = "TARGET_REGION_MISSED"

    disclaimer = (
        "Educational trajectory simulation reaching ocean surface datum. "
        "Surface intersection does not model terminal flip, landing burn relight, "
        "or structural survivability; not an official SpaceX splashdown certification."
    )

    return TerminalSplashdownAssessment(
        impact_time_s=float(impact_time_s),
        impact_epoch_utc=impact_epoch_utc,
        geodetic_lat_deg=float(lat_deg),
        geodetic_lon_deg=float(lon_deg),
        geodetic_alt_m=float(alt_m),
        terminal_inertial_speed_ms=v_inertial_mag,
        terminal_relative_speed_ms=v_rel_mag,
        terminal_flight_path_angle_deg=gamma_deg,
        terminal_dynamic_pressure_pa=q_term,
        target_lat_deg=float(target_lat_deg),
        target_lon_deg=float(target_lon_deg),
        target_radius_m=float(target_radius_m),
        miss_distance_m=miss_dist_m,
        miss_distance_km=miss_dist_km,
        crossrange_error_km=cross_km,
        downrange_error_km=down_km,
        outcome_classification=outcome,
        target_within_corridor=within_corridor,
        cumulative_heat_load_mj_m2=float(cumulative_heat_load_mj_m2),
        peak_dynamic_pressure_pa=float(peak_dynamic_pressure_pa),
        peak_apparent_g_load=float(peak_apparent_g_load),
        peak_stagnation_heat_flux_mw_m2=float(peak_stagnation_heat_flux_mw_m2),
        disclaimer=disclaimer
    )
