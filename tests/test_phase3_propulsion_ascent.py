#!/usr/bin/env python3
"""
Phase 3 Propulsion & 3-DOF Ascent Dynamics Test Suite
Starship Flight 14 Digital Engineering Project
Author: Senior Aerospace Systems & Verification Lead
"""

import os
import sys
import math
import json
import csv
import unittest
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.environment.atmosphere_1976 import (
    us_standard_atmosphere_1976,
    gravity_j2,
    geodetic_to_ecef,
    ecef_to_geodetic_height,
    R_EARTH_EQUATORIAL,
    R_EARTH_POLAR,
    GM_EARTH,
    G0
)
from src.propulsion.raptor3_model import Raptor3Engine, BoosterCluster33
from src.numerics.rk4_solver import rk4_step, rk4_solve
from src.dynamics.ascent_3dof import (
    get_initial_state_eci,
    drag_coefficient,
    ascent_derivatives,
    simulate_ascent,
    LAT_STARBASE_DEG,
    LON_STARBASE_DEG,
    ALT_STARBASE_M,
    MASS_LIFTOFF_TOTAL
)

class TestPhase3PropulsionAscent(unittest.TestCase):

    def test_atmosphere_1976_sea_level(self):
        """Verify 1976 Standard Atmosphere matches international standard values at sea level."""
        atmos0 = us_standard_atmosphere_1976(0.0)
        self.assertAlmostEqual(atmos0["temperature"], 288.15, places=2)
        self.assertAlmostEqual(atmos0["pressure"], 101325.0, delta=1.0)
        self.assertAlmostEqual(atmos0["density"], 1.225, delta=0.005)
        self.assertAlmostEqual(atmos0["speed_of_sound"], 340.294, delta=0.5)
        self.assertAlmostEqual(atmos0["viscosity"], 1.789e-5, delta=1e-7)

    def test_atmosphere_1976_altitude_layers(self):
        """Verify atmosphere layer temperatures and pressures across tropopause and stratosphere."""
        # 11 km Geometric Altitude (~10,981 m Geopotential Altitude)
        atmos11k = us_standard_atmosphere_1976(11000.0)
        self.assertAlmostEqual(atmos11k["temperature"], 216.65, delta=0.5)
        self.assertAlmostEqual(atmos11k["pressure"], 22632.06, delta=500.0)

        # 25 km (Middle Stratosphere)
        atmos25k = us_standard_atmosphere_1976(25000.0)
        self.assertGreater(atmos25k["temperature"], 216.0)
        self.assertLess(atmos25k["pressure"], 5000.0)

        # 50 km (Stratopause)
        atmos50k = us_standard_atmosphere_1976(50000.0)
        self.assertAlmostEqual(atmos50k["temperature"], 270.65, delta=5.0)

        # Exosphere / Vacuum (> 86 km)
        atmos90k = us_standard_atmosphere_1976(90000.0)
        self.assertGreater(atmos90k["pressure"], 0.0)
        self.assertLess(atmos90k["pressure"], 1.0)
        self.assertGreater(atmos90k["density"], 0.0)
        self.assertLess(atmos90k["density"], 1e-4)

    def test_wgs84_geodetic_transformations(self):
        """Verify Bowring closed-form geodetic transformation invertibility at Starbase launch mount."""
        r0 = geodetic_to_ecef(LAT_STARBASE_DEG, LON_STARBASE_DEG, ALT_STARBASE_M)
        self.assertIsInstance(r0, np.ndarray)
        self.assertEqual(len(r0), 3)

        # Roundtrip height check
        h_recovered = ecef_to_geodetic_height(r0)
        self.assertAlmostEqual(h_recovered, ALT_STARBASE_M, places=4,
                               msg=f"Bowring height {h_recovered} m did not match pad elevation {ALT_STARBASE_M} m")

        # Elevation at 100 km altitude above pad
        r_100k = geodetic_to_ecef(LAT_STARBASE_DEG, LON_STARBASE_DEG, 100000.0)
        h_100k_rec = ecef_to_geodetic_height(r_100k)
        self.assertAlmostEqual(h_100k_rec, 100000.0, places=3)

    def test_gravity_j2_acceleration(self):
        """Verify WGS-84 gravitational acceleration vector magnitude and J2 perturbation."""
        r_eq = np.array([R_EARTH_EQUATORIAL, 0.0, 0.0])
        g_eq = gravity_j2(r_eq)
        g_mag_eq = np.linalg.norm(g_eq)

        # Sea-level gravity should be within [9.78, 9.83] m/s^2
        self.assertGreater(g_mag_eq, 9.75)
        self.assertLess(g_mag_eq, 9.85)

        # Acceleration vector points strictly inward toward origin
        unit_r = r_eq / np.linalg.norm(r_eq)
        unit_g = g_eq / g_mag_eq
        dot_product = np.dot(unit_r, unit_g)
        self.assertAlmostEqual(dot_product, -1.0, places=5)

    def test_raptor3_engine_thermodynamics(self):
        """Verify Raptor 3 SL and VAC thrust, Isp, and mass flow rate equations."""
        eng_sl = Raptor3Engine(variant="SL")
        eng_vac = Raptor3Engine(variant="VAC")

        # SL engine at 1 atm (101,325 Pa)
        f_sl, isp_sl, mdot_sl = eng_sl.compute_performance(101325.0, throttle=1.0)
        self.assertAlmostEqual(f_sl / 1e6, 2.766, delta=0.02)
        self.assertAlmostEqual(isp_sl, 333.8, delta=2.0)
        self.assertAlmostEqual(mdot_sl, 844.9, delta=5.0)

        # SL engine in vacuum (0 Pa)
        f_vac, isp_vac, mdot_vac = eng_sl.compute_performance(0.0, throttle=1.0)
        self.assertAlmostEqual(f_vac / 1e6, 2.90, delta=0.01)
        self.assertAlmostEqual(isp_vac, 350.0, delta=0.1)
        self.assertAlmostEqual(mdot_vac, mdot_sl, delta=0.01)

        # VAC engine in vacuum
        f_v2, isp_v2, mdot_v2 = eng_vac.compute_performance(0.0, throttle=1.0)
        self.assertAlmostEqual(f_v2 / 1e6, 2.90, delta=0.01)
        self.assertAlmostEqual(isp_v2, 380.0, delta=0.1)

        # Zero throttle check
        f_zero, isp_zero, mdot_zero = eng_sl.compute_performance(101325.0, throttle=0.0)
        self.assertEqual(f_zero, 0.0)
        self.assertEqual(isp_zero, 0.0)
        self.assertEqual(mdot_zero, 0.0)

    def test_booster_cluster_33_and_anomaly(self):
        """Verify 33-Raptor cluster liftoff thrust and single-engine failure response."""
        cluster_nom = BoosterCluster33(enable_anomaly=False)
        cluster_anom = BoosterCluster33(enable_anomaly=True, anomaly_time_s=35.0, anomaly_engine_id=17)

        # At liftoff (t=0s), ambient pressure = 1 atm
        thrust0, mdot0, isp0, act0 = cluster_nom.compute_cluster_state(0.0, 101325.0, 0.0)
        self.assertEqual(act0, 33)
        self.assertGreater(thrust0 / 1e6, 80.0) # > 80 MN

        # At full thrust (t=10s)
        thrust10, mdot10, isp10, act10 = cluster_nom.compute_cluster_state(10.0, 95000.0, 5000.0)
        self.assertEqual(act10, 33)
        self.assertGreater(thrust10 / 1e6, 90.0) # ~91 MN

        # Prior to anomaly (t=30s)
        _, _, _, act_before = cluster_anom.compute_cluster_state(30.0, 50000.0, 35000.0)
        self.assertEqual(act_before, 33)

        # After anomaly (t=40s)
        thrust_anom, mdot_anom, isp_anom, act_after = cluster_anom.compute_cluster_state(40.0, 30000.0, 35000.0)
        self.assertEqual(act_after, 32, "Engine 17 should be shut down after T+35s")

    def test_drag_polar_continuity(self):
        """Verify drag coefficient polar is positive, continuous, and exhibits transonic rise."""
        cd_sub = drag_coefficient(0.5)
        cd_trans = drag_coefficient(1.05)
        cd_super = drag_coefficient(2.5)
        cd_hyper = drag_coefficient(8.0)

        self.assertEqual(cd_sub, 0.28)
        self.assertGreater(cd_trans, cd_sub, "Transonic drag should exceed subsonic drag")
        self.assertLess(cd_super, cd_trans, "Supersonic drag should decay from transonic peak")
        self.assertEqual(cd_hyper, 0.32)

    def test_rk4_single_step_analytical(self):
        """Verify RK4 single step on analytical exponential decay ODE: dy/dt = -k*y."""
        k = 0.5
        def decay(t, y):
            return -k * y

        y0 = np.array([10.0])
        dt = 0.1
        y1_num = rk4_step(decay, 0.0, y0, dt)
        y1_exact = y0 * math.exp(-k * dt)
        error = abs(y1_num[0] - y1_exact[0])
        self.assertLess(error, 5e-8, "RK4 step error exceeds O(dt^5) tolerance")

    def test_output_telemetry_files_and_summary(self):
        """Verify generated telemetry CSV files and summary JSON report exist and meet specifications."""
        nom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_nominal.csv")
        anom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_anomaly.csv")
        sum_json = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_summary.json")

        self.assertTrue(os.path.exists(nom_csv), f"Missing: {nom_csv}")
        self.assertTrue(os.path.exists(anom_csv), f"Missing: {anom_csv}")
        self.assertTrue(os.path.exists(sum_json), f"Missing: {sum_json}")

        # Check nominal CSV rows and columns
        with open(nom_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertGreaterEqual(len(rows), 2800)
            self.assertIn("altitude_km", reader.fieldnames)
            self.assertIn("downrange_km", reader.fieldnames)
            self.assertIn("v_rel_ms", reader.fieldnames)
            self.assertIn("dynamic_pressure_kpa", reader.fieldnames)

            # Altitude at launch should be positive and close to pad elevation (0.003 km)
            alt_t0 = float(rows[0]["altitude_km"])
            self.assertAlmostEqual(alt_t0, 0.003, places=2)

            # Altitude at MECO should be >= 60 km
            alt_meco = float(rows[-1]["altitude_km"])
            self.assertGreater(alt_meco, 60.0)

            # Velocity at MECO should be in expected range [1600, 2400] m/s
            v_meco = float(rows[-1]["v_rel_ms"])
            self.assertGreater(v_meco, 1600.0)
            self.assertLess(v_meco, 2400.0)

            # Vehicle mass at MECO should be >= 2000 tonnes (propellant retained for boostback/landing)
            m_meco = float(rows[-1]["mass_tonnes"])
            self.assertGreater(m_meco, 2000.0)

        # Check JSON summary verification metrics
        with open(sum_json, "r", encoding="utf-8") as jf:
            summary = json.load(jf)
            v_metrics = summary["verification_metrics"]
            self.assertEqual(v_metrics["status"], "ALL_TESTS_VERIFIED")
            self.assertLess(v_metrics["rk4_step_sensitivity_pct"], 0.01)
            self.assertLess(v_metrics["keplerian_energy_drift"], 1e-5)

if __name__ == "__main__":
    unittest.main()
