"""
Analytical Benchmark Suite for Physics Verification
===================================================
Tests physics models against exact analytical solutions, conservation laws,
and mathematical limiting cases to verify physical correctness independently
of code implementation.
"""

import unittest
import numpy as np
import math

from src.astrodynamics.constants import (
    MU_EARTH, R_EARTH_EQUATORIAL, OMEGA_EARTH, STANDARD_GRAVITY
)
from src.astrodynamics.frames import eci_to_ecef, ecef_to_geodetic
from src.reentry.constants import SUTTON_GRAVES_K_EARTH
from src.reentry.heating import (
    compute_stagnation_heat_flux,
    compute_radiative_equilibrium_temperature,
    STEFAN_BOLTZMANN_CONSTANT
)


class TestAnalyticalPhysicsBenchmarks(unittest.TestCase):
    """Rigorous analytical benchmarks testing physical laws and conservation."""

    # -------------------------------------------------------------
    # 1. ORBITAL MECHANICS CONSERVATION LAWS
    # -------------------------------------------------------------
    def test_bm_01_two_body_energy_and_momentum_conservation(self):
        """BENCHMARK-01: Verify exact conservation of specific energy and angular momentum."""
        # Initial circular orbit at r = 7000 km
        r0 = np.array([7000000.0, 0.0, 0.0], dtype=np.float64)
        v_circ = math.sqrt(MU_EARTH / 7000000.0)
        v0 = np.array([0.0, v_circ, 0.0], dtype=np.float64)

        # Initial specific orbital energy E = v^2 / 2 - mu / r
        energy_0 = 0.5 * np.dot(v0, v0) - (MU_EARTH / np.linalg.norm(r0))
        # Initial specific angular momentum vector h = r x v
        h_vec_0 = np.cross(r0, v0)
        h_mag_0 = np.linalg.norm(h_vec_0)

        # Propagate simple 2-body motion using small time steps (RK4) over 1000 seconds
        dt = 1.0
        r_curr = r0.copy()
        v_curr = v0.copy()

        def deriv(r, v):
            r_norm = np.linalg.norm(r)
            a_grav = - (MU_EARTH / (r_norm ** 3)) * r
            return v, a_grav

        for _ in range(1000):
            # Classical RK4
            k1_v, k1_a = deriv(r_curr, v_curr)
            k2_v, k2_a = deriv(r_curr + 0.5 * dt * k1_v, v_curr + 0.5 * dt * k1_a)
            k3_v, k3_a = deriv(r_curr + 0.5 * dt * k2_v, v_curr + 0.5 * dt * k2_a)
            k4_v, k4_a = deriv(r_curr + dt * k3_v, v_curr + dt * k3_a)

            r_curr += (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)
            v_curr += (dt / 6.0) * (k1_a + 2.0 * k2_a + 2.0 * k3_a + k4_a)

        # Final energy and momentum
        energy_f = 0.5 * np.dot(v_curr, v_curr) - (MU_EARTH / np.linalg.norm(r_curr))
        h_vec_f = np.cross(r_curr, v_curr)
        h_mag_f = np.linalg.norm(h_vec_f)

        # Fractional energy conservation must be < 1e-7
        fractional_energy_error = abs(energy_f - energy_0) / abs(energy_0)
        self.assertLess(fractional_energy_error, 1e-7)

        # Fractional angular momentum conservation must be < 1e-7
        fractional_momentum_error = abs(h_mag_f - h_mag_0) / h_mag_0
        self.assertLess(fractional_momentum_error, 1e-7)

    # -------------------------------------------------------------
    # 2. ROCKET PROPULSION ANALYTICAL LIMITING CASES
    # -------------------------------------------------------------
    def test_bm_02_tsiolkovsky_rocket_equation_exact_match(self):
        """BENCHMARK-02: Verify integrated variable-mass rocket acceleration matches Tsiolkovsky."""
        m0 = 100000.0  # kg
        isp = 350.0    # s
        thrust = 1000000.0  # N
        g0 = STANDARD_GRAVITY
        mdot = thrust / (isp * g0)
        burn_duration = 50.0  # s

        mf = m0 - mdot * burn_duration
        analytical_delta_v = isp * g0 * math.log(m0 / mf)

        # Numerical integration of dv/dt = F / m(t) with dt = 0.01 s
        dt = 0.01
        steps = int(burn_duration / dt)
        v_num = 0.0
        m_curr = m0

        for _ in range(steps):
            a_curr = thrust / m_curr
            v_num += a_curr * dt
            m_curr -= mdot * dt

        # Numerical delta-v must match analytical Tsiolkovsky to within 0.01%
        rel_error = abs(v_num - analytical_delta_v) / analytical_delta_v
        self.assertLess(rel_error, 1e-4)

    # -------------------------------------------------------------
    # 3. AEROTHERMODYNAMIC SCALING POWER LAWS
    # -------------------------------------------------------------
    def test_bm_03_sutton_graves_cubic_velocity_scaling(self):
        """BENCHMARK-03: Verify heat flux scales exactly with v^3 (doubling v -> 8x flux)."""
        rho = 0.001
        rn = 4.5
        v1 = 3000.0
        v2 = 6000.0  # 2x velocity

        q1 = compute_stagnation_heat_flux(density_kg_m3=rho, speed_relative_ms=v1, nose_radius_m=rn)
        q2 = compute_stagnation_heat_flux(density_kg_m3=rho, speed_relative_ms=v2, nose_radius_m=rn)

        ratio = q2 / q1
        # Analytical ratio: (2)^3 = 8.0
        self.assertAlmostEqual(ratio, 8.0, places=4)

    def test_bm_04_sutton_graves_inverse_square_root_nose_scaling(self):
        """BENCHMARK-04: Verify heat flux scales with 1/sqrt(Rn) (4x nose radius -> 0.5x flux)."""
        rho = 0.001
        v = 5000.0
        rn1 = 1.0
        rn2 = 4.0  # 4x nose radius

        q1 = compute_stagnation_heat_flux(density_kg_m3=rho, speed_relative_ms=v, nose_radius_m=rn1)
        q2 = compute_stagnation_heat_flux(density_kg_m3=rho, speed_relative_ms=v, nose_radius_m=rn2)

        ratio = q2 / q1
        # Analytical ratio: 1 / sqrt(4) = 0.50
        self.assertAlmostEqual(ratio, 0.50, places=4)

    # -------------------------------------------------------------
    # 4. RADIATION EQUILIBRIUM STEFAN-BOLTZMANN INVERSION
    # -------------------------------------------------------------
    def test_bm_05_stefan_boltzmann_quartic_radiation_inversion(self):
        """BENCHMARK-05: Verify exact forward and inverse radiative equilibrium balance."""
        t_known = 1500.0  # K
        emissivity = 0.85
        # Forward flux: q = eps * sigma * T^4
        q_forward = emissivity * STEFAN_BOLTZMANN_CONSTANT * (t_known ** 4.0)

        # Inverse temperature from model
        t_computed = compute_radiative_equilibrium_temperature(q_forward, emissivity=emissivity)

        self.assertAlmostEqual(t_computed, t_known, places=3)

    # -------------------------------------------------------------
    # 5. GEODETIC TRANSFORMATION ROUND-TRIP INVARIANCE
    # -------------------------------------------------------------
    def test_bm_06_wgs84_closed_form_round_trip_precision(self):
        """BENCHMARK-06: Verify Bowring ECEF-to-geodetic round-trip error is < 1 mm globally."""
        test_points = [
            (0.0, 0.0, 0.0),          # Equator sea level
            (45.0, 90.0, 10000.0),     # Mid-latitude 10 km altitude
            (-30.0, -60.0, 120000.0),  # Southern hemisphere 120 km interface
            (89.0, 0.0, 500.0)         # Near polar region
        ]

        for lat_deg, lon_deg, alt_m in test_points:
            # Convert geodetic to ECEF
            phi = math.radians(lat_deg)
            lam = math.radians(lon_deg)
            e2 = 6.69437999014e-3
            n_val = R_EARTH_EQUATORIAL / math.sqrt(1.0 - e2 * (math.sin(phi) ** 2))
            x_ecef = (n_val + alt_m) * math.cos(phi) * math.cos(lam)
            y_ecef = (n_val + alt_m) * math.cos(phi) * math.sin(lam)
            z_ecef = (n_val * (1.0 - e2) + alt_m) * math.sin(phi)
            r_ecef = np.array([x_ecef, y_ecef, z_ecef], dtype=np.float64)

            # Convert back via Bowring
            lat_out, lon_out, alt_out = ecef_to_geodetic(r_ecef)

            self.assertAlmostEqual(lat_out, lat_deg, places=5)
            self.assertAlmostEqual(lon_out, lon_deg, places=5)
            self.assertAlmostEqual(alt_out, alt_m, delta=0.001)  # < 1 mm discrepancy


if __name__ == '__main__':
    unittest.main()
