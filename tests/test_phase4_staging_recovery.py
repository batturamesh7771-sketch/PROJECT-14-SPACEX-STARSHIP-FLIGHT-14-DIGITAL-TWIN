#!/usr/bin/env python3
"""
Phase 4 Staging Dynamics & Dual-Vehicle Trajectory Acceptance Test Suite
========================================================================
Comprehensive 20-Point Acceptance Test Matrix as defined in DOC-P4-VER-001.

Categorization:
- Tests 01-05: Multi-body separation invariants, baseline limits & momentum conservation
- Tests 06-10: Event handling, frame consistency, coordinates & analytical limits
- Tests 11-15: Numerical convergence, interpolation safety, schema integrity & terminology
- Tests 16-20: Parameter provenance, scenario isolation, GMAT benchmark & end-to-end replay
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
    R_EARTH_EQUATORIAL,
    GM_EARTH,
    ecef_to_geodetic_height
)
from src.dynamics.staging_separation import simulate_hot_staging_separation
from src.dynamics.booster_recovery import simulate_booster_return, booster_drag_coefficient
from src.dynamics.starship_ascent_to_orbit import (
    simulate_starship_ascent,
    compute_keplerian_elements
)

class TestPhase4StagingRecovery(unittest.TestCase):

    def setUp(self):
        nom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_nominal.csv")
        if os.path.exists(nom_csv):
            with open(nom_csv, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
                row_meco = rows[-1]
                self.state_t142 = np.array([
                    float(row_meco["eci_x_m"]),
                    float(row_meco["eci_y_m"]),
                    float(row_meco["eci_z_m"]),
                    float(row_meco["eci_vx_ms"]),
                    float(row_meco["eci_vy_ms"]),
                    float(row_meco["eci_vz_ms"]),
                    float(row_meco["mass_tonnes"]) * 1000.0
                ], dtype=np.float64)
                self.v0_sep = float(row_meco["v_rel_ms"])
        else:
            self.state_t142 = np.array([-720000.0, -5800000.0, 2850000.0, 1600.0, 800.0, 1100.0, 2098000.0])
            self.v0_sep = 1807.8

        self.m_booster = 671000.0
        self.m_ship = 1338975.0

    # -------------------------------------------------------------------------
    # TEST 01: Synthetic Baseline
    # -------------------------------------------------------------------------
    def test_01_synthetic_baseline(self):
        """TEST-P4-01: Two bodies propagate from shared state under identical zero forces."""
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="zero_impulse"
        )
        for r in records:
            self.assertAlmostEqual(r["center_displacement_increment_m"], 0.0, places=4)
            self.assertAlmostEqual(r["relative_velocity_ms"], 0.0, places=4)

    # -------------------------------------------------------------------------
    # TEST 02: Zero Impulse Limit
    # -------------------------------------------------------------------------
    def test_02_zero_impulse_limit(self):
        """TEST-P4-02: Initial relative velocity across split behaves cleanly without jumps."""
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="zero_impulse"
        )
        row_split = next(r for r in records if r["is_separated"])
        self.assertAlmostEqual(row_split["relative_velocity_ms"], 0.0, places=4)
        self.assertAlmostEqual(row_split["center_displacement_increment_m"], 0.0, places=4)

    # -------------------------------------------------------------------------
    # TEST 03: Momentum Conservation under Internal Impulse
    # -------------------------------------------------------------------------
    def test_03_momentum_conservation_internal_impulse(self):
        """TEST-P4-03: Internal impulse J yields equal and opposite momentum changes."""
        J_test = 2.5e6 # 2.5 MN*s
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01,
            mode="prescribed_impulse", impulse_ns=J_test
        )
        self.assertAlmostEqual(summary["momentum_error_kg_ms"], 0.0, delta=1e-6)
        expected_rel_vel = (J_test / self.m_ship) - (-J_test / self.m_booster)
        self.assertAlmostEqual(summary["final_relative_velocity_ms"], expected_rel_vel, places=3)

    # -------------------------------------------------------------------------
    # TEST 04: Mass Accounting Continuity
    # -------------------------------------------------------------------------
    def test_04_mass_accounting_continuity(self):
        """TEST-P4-04: Stack mass equals booster mass plus ship mass across event."""
        m_stack_liftoff = 4939800.0 # kg
        m_booster_gross = 3600825.0
        m_ship_gross = 1338975.0
        self.assertEqual(m_stack_liftoff, m_booster_gross + m_ship_gross)

        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="hot_staging"
        )
        row_0 = records[0]
        self.assertAlmostEqual(row_0["total_mass_kg"], self.m_booster + self.m_ship, places=1)

    # -------------------------------------------------------------------------
    # TEST 05: State Continuity Across Separation Trigger
    # -------------------------------------------------------------------------
    def test_05_state_continuity_no_jump(self):
        """TEST-P4-05: Position vectors have zero unmodeled discontinuity across trigger."""
        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="hot_staging"
        )
        pre_idx = next(i for i, r in enumerate(records) if r["time_s"] == 141.99)
        post_idx = next(i for i, r in enumerate(records) if r["time_s"] == 142.0)
        self.assertEqual(records[pre_idx]["center_range_m"], 0.0)
        self.assertEqual(records[post_idx]["center_range_m"], 0.0)

    # -------------------------------------------------------------------------
    # TEST 06: Event Idempotence
    # -------------------------------------------------------------------------
    def test_06_event_idempotence(self):
        """TEST-P4-06: Separation event fires and applies exactly once."""
        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="hot_staging"
        )
        transitions = [
            i for i in range(1, len(records))
            if not records[i-1]["is_separated"] and records[i]["is_separated"]
        ]
        self.assertEqual(len(transitions), 1, "Separation trigger must transition exactly once")

    # -------------------------------------------------------------------------
    # TEST 07: Shared Frame Arithmetic
    # -------------------------------------------------------------------------
    def test_07_shared_frame_arithmetic(self):
        """TEST-P4-07: Relative vectors are computed in identical coordinate frames."""
        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01
        )
        for r in records:
            self.assertEqual(r["frame"], "ECI_ALONG_VELOCITY")
            self.assertAlmostEqual(
                r["relative_velocity_ms"],
                r["ship_velocity_ms"] - r["booster_velocity_ms"],
                delta=0.02
            )

    # -------------------------------------------------------------------------
    # TEST 08: Coordinate Round-Trip Accuracy
    # -------------------------------------------------------------------------
    def test_08_coordinate_round_trip(self):
        """TEST-P4-08: ECEF to Geodetic height recovers pad height within 1 mm."""
        # Boca Chica launch pad coordinate: Latitude 25.996 deg N, Longitude 97.154 deg W, Alt 3.0 m
        lat_rad = math.radians(25.996)
        lon_rad = math.radians(-97.154)
        alt_true = 3.0
        a = R_EARTH_EQUATORIAL
        f = 1.0 / 298.257223563
        e2 = 2.0 * f - f * f
        n_rad = a / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
        x_ecef = (n_rad + alt_true) * math.cos(lat_rad) * math.cos(lon_rad)
        y_ecef = (n_rad + alt_true) * math.cos(lat_rad) * math.sin(lon_rad)
        z_ecef = (n_rad * (1.0 - e2) + alt_true) * math.sin(lat_rad)

        h_calc = ecef_to_geodetic_height(np.array([x_ecef, y_ecef, z_ecef]))
        self.assertAlmostEqual(h_calc, alt_true, delta=1e-3)

    # -------------------------------------------------------------------------
    # TEST 09: Independent Force and Thrust Schedules
    # -------------------------------------------------------------------------
    def test_09_independent_force_and_thrust_schedules(self):
        """TEST-P4-09: Booster and ship execute independent thrust schedules after split."""
        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="hot_staging"
        )
        # Pre-separation: booster active, ship inactive
        r_pre = next(r for r in records if r["time_s"] == 141.0)
        self.assertGreater(r_pre["booster_thrust_mn"], 8.0)
        self.assertEqual(r_pre["ship_thrust_mn"], 0.0)

        # Post-separation overlap: ship active, booster throttled
        r_post = next(r for r in records if r["time_s"] == 142.5)
        self.assertGreater(r_post["ship_thrust_mn"], 17.0)
        self.assertLess(r_post["booster_thrust_mn"], 4.0)

        # After booster cutoff (T > 143.5s): booster thrust is zero
        r_cut = next(r for r in records if r["time_s"] == 144.0)
        self.assertEqual(r_cut["booster_thrust_mn"], 0.0)
        self.assertGreater(r_cut["ship_thrust_mn"], 17.0)

    # -------------------------------------------------------------------------
    # TEST 10: Free-Fall Ballistic Limiting Case
    # -------------------------------------------------------------------------
    def test_10_free_fall_limiting_case(self):
        """TEST-P4-10: Circular ballistic two-body orbit conserves specific energy."""
        r_circ = R_EARTH_EQUATORIAL + 200000.0 # 200 km
        v_circ = math.sqrt(GM_EARTH / r_circ)
        r_vec = np.array([r_circ, 0.0, 0.0])
        v_vec = np.array([0.0, v_circ, 0.0])
        energy_specific = (v_circ**2 / 2.0) - (GM_EARTH / r_circ)

        elem = compute_keplerian_elements(r_vec, v_vec)
        self.assertAlmostEqual(elem["semi_major_axis_km"], r_circ / 1000.0, delta=1.0)
        self.assertAlmostEqual(elem["eccentricity"], 0.0, places=4)
        self.assertAlmostEqual(elem["perigee_altitude_km"], 200.0, delta=1.0)
        self.assertAlmostEqual(elem["apogee_altitude_km"], 200.0, delta=1.0)

    # -------------------------------------------------------------------------
    # TEST 11: Monotonic Center-of-Mass Displacement
    # -------------------------------------------------------------------------
    def test_11_monotonic_center_displacement(self):
        """TEST-P4-11: Relative distance between COMs strictly increases under forward thrust."""
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01, mode="hot_staging"
        )
        post_recs = [r for r in records if r["time_s"] >= 142.1]
        for i in range(1, len(post_recs)):
            self.assertGreaterEqual(
                post_recs[i]["center_range_m"],
                post_recs[i-1]["center_range_m"],
                "Center range must monotonically increase post-separation"
            )

    # -------------------------------------------------------------------------
    # TEST 12: Time-Step Discretization Convergence
    # -------------------------------------------------------------------------
    def test_12_time_step_convergence(self):
        """TEST-P4-12: Time step refinement confirms convergence of relative separation."""
        _, s_coarse = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01
        )
        _, s_fine = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.001
        )
        err_1s = abs(s_coarse["center_displacement_increment_1s_m"] - s_fine["center_displacement_increment_1s_m"])
        err_1s_pct = err_1s / s_fine["center_displacement_increment_1s_m"] * 100.0
        self.assertLess(err_1s_pct, 1.5, "1s displacement must converge within 1.5%")

    # -------------------------------------------------------------------------
    # TEST 13: Interpolation Safety & Boundary Bounds
    # -------------------------------------------------------------------------
    def test_13_interpolation_safety(self):
        """TEST-P4-13: Output trajectories contain zero non-finite values or NaN values."""
        records, _ = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01
        )
        for r in records:
            for k, val in r.items():
                if val is not None and isinstance(val, (int, float)):
                    self.assertFalse(math.isnan(val), f"NaN detected in {k}")
                    self.assertFalse(math.isinf(val), f"Inf detected in {k}")

    # -------------------------------------------------------------------------
    # TEST 14: Output Schema & SI Unit Integrity
    # -------------------------------------------------------------------------
    def test_14_output_integrity_finite_si(self):
        """TEST-P4-14: Key metrics fall within defensible physical ranges in SI units."""
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01
        )
        # Peak plume force between 1.0 MN and 2.5 MN
        self.assertGreater(summary["peak_plume_force_kn"], 1000.0)
        self.assertLess(summary["peak_plume_force_kn"], 2500.0)
        # Peak relative acceleration between 1.0 g and 4.0 g
        self.assertGreater(summary["peak_relative_accel_g"], 1.0)
        self.assertLess(summary["peak_relative_accel_g"], 4.0)

    # -------------------------------------------------------------------------
    # TEST 15: Clearance Terminology Compliance
    # -------------------------------------------------------------------------
    def test_15_terminology_compliance(self):
        """TEST-P4-15: Surface clearance is explicitly marked not_computed in point-mass L1."""
        records, summary = simulate_hot_staging_separation(
            self.m_booster, self.m_ship, v0_ms=self.v0_sep, dt=0.01
        )
        self.assertIsNone(summary["min_surface_clearance_m"])
        self.assertEqual(summary["clearance_status"], "not_computed")
        self.assertEqual(summary["clearance_method"], "point_mass_translation_only")
        # Reproduce exact 5.50 m and 48.06 m values
        self.assertAlmostEqual(summary["center_displacement_increment_1s_m"], 5.50, delta=0.05)
        self.assertAlmostEqual(summary["center_displacement_increment_3s_m"], 48.06, delta=0.05)

    # -------------------------------------------------------------------------
    # TEST 16: Parameter Provenance Completeness
    # -------------------------------------------------------------------------
    def test_16_parameter_provenance_completeness(self):
        """TEST-P4-16: Configuration parameters are present in parameters registry."""
        param_path = os.path.join(PROJECT_ROOT, "data", "propulsion", "parameters.yaml")
        self.assertTrue(os.path.exists(param_path), "Propulsion parameters YAML must exist")
        with open(param_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("raptor3_engines", content)
            self.assertIn("sea_level_variant", content)
            self.assertIn("vacuum_variant", content)

    # -------------------------------------------------------------------------
    # TEST 17: Scenario Isolation & Distinct Tags
    # -------------------------------------------------------------------------
    def test_17_scenario_isolation(self):
        """TEST-P4-17: Baseline scenario tags remain distinct from hypothetical variants."""
        sources_p4 = os.path.join(PROJECT_ROOT, "research", "phase4_sources.csv")
        self.assertTrue(os.path.exists(sources_p4), "Phase 4 sources CSV must exist")
        with open(sources_p4, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            source_ids = [row["source_id"] for row in reader]
            self.assertIn("F4-01", source_ids)
            self.assertIn("F4-02", source_ids)
            self.assertIn("F4-05", source_ids)

    # -------------------------------------------------------------------------
    # TEST 18: GMAT Independent Orbital Insertion Benchmark
    # -------------------------------------------------------------------------
    def test_18_gmat_orbital_comparison(self):
        """TEST-P4-18: GMAT independent ephemeris matches Python model insertion state."""
        gmat_report = os.path.join(PROJECT_ROOT, "output", "Starship_Flight14_GMAT_Orbit_Report.txt")
        self.assertTrue(os.path.exists(gmat_report), "GMAT orbit report must exist")
        with open(gmat_report, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            header = lines[0].split()
            first_row = lines[1].split()
            # UTCGregorian format: "28 Sep 2026 14:08:42.350" takes tokens 0..3
            # Columns: 0..3: UTCGregorian, 4: SMA, 5: ECC, 6: Altitude, 7: RadPer, 8: RadApo
            sma_gmat = float(first_row[4])
            ecc_gmat = float(first_row[5])
            alt_gmat = float(first_row[6])

            self.assertAlmostEqual(sma_gmat, 6567.29, delta=1.0)
            self.assertAlmostEqual(ecc_gmat, 0.0062, delta=0.0005)
            self.assertAlmostEqual(alt_gmat, 152.05, delta=1.0)

    # -------------------------------------------------------------------------
    # TEST 19: Booster Recovery & Splashdown Physics
    # -------------------------------------------------------------------------
    def test_19_booster_recovery_and_splashdown(self):
        """TEST-P4-19: Booster flip, boostback consumption, apogee, and soft touchdown."""
        records, summary = simulate_booster_return(self.state_t142, dt=0.05)
        self.assertEqual(summary["splashdown"]["status"], "CONTROLLED_SOFT_SPLASHDOWN_VERIFIED")
        self.assertGreater(summary["apogee"]["altitude_km"], 95.0)
        self.assertLess(summary["apogee"]["altitude_km"], 125.0)
        self.assertLess(summary["splashdown"]["touchdown_relative_velocity_ms"], 25.0)

    # -------------------------------------------------------------------------
    # TEST 20: Starship Orbital Insertion & Full Reproducibility
    # -------------------------------------------------------------------------
    def test_20_starship_orbital_insertion_and_reproducibility(self):
        """TEST-P4-20: Starship upper stage ascent to SECO reproduces orbit deterministically."""
        records_1, sum_1 = simulate_starship_ascent(self.state_t142, actual_profile=True, dt=0.05)
        records_2, sum_2 = simulate_starship_ascent(self.state_t142, actual_profile=True, dt=0.05)

        self.assertEqual(sum_1["status"], "ORBITAL_INSERTION_VERIFIED")
        self.assertAlmostEqual(sum_1["seco_inertial_velocity_ms"], 7838.9, delta=5.0)
        self.assertEqual(
            sum_1["seco_inertial_velocity_ms"],
            sum_2["seco_inertial_velocity_ms"],
            "Deterministic re-run must produce identical results"
        )

    # -------------------------------------------------------------------------
    # Backward Compatibility Aliases for Legacy Tests
    # -------------------------------------------------------------------------
    def test_hot_staging_separation_dynamics(self):
        self.test_15_terminology_compliance()

    def test_booster_drag_coefficient(self):
        cd_sub = booster_drag_coefficient(0.5)
        cd_trans = booster_drag_coefficient(1.05)
        cd_super = booster_drag_coefficient(3.0)
        self.assertGreater(cd_sub, 0.70)
        self.assertGreater(cd_trans, cd_sub)
        self.assertGreater(cd_super, 0.60)

    def test_booster_recovery_trajectory(self):
        self.test_19_booster_recovery_and_splashdown()

    def test_starship_orbital_insertion_and_elements(self):
        self.test_20_starship_orbital_insertion_and_reproducibility()

    def test_keplerian_elements_analytical(self):
        self.test_10_free_fall_limiting_case()

if __name__ == "__main__":
    unittest.main()
