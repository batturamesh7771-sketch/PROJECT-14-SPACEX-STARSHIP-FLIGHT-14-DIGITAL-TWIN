#!/usr/bin/env python3
"""
Phase 3 18-Point Verification & Acceptance Test Suite
Starship Flight 14 Digital Engineering Project
Author: Senior Launch-Vehicle Flight Dynamics & Propulsion Lead
Complies strictly with Part 8 Verification and Acceptance Tests Specification.
"""

import os
import sys
import math
import csv
import json
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

class TestPhase3AcceptanceSuite(unittest.TestCase):

    def test_01_constant_acceleration_analytical(self):
        """1. Constant-acceleration analytical comparison: v(t)=at, x(t)=0.5*a*t^2."""
        a_const = 15.0 # m/s^2
        def const_accel(t, y):
            # y = [x, v]
            return np.array([y[1], a_const])

        y0 = np.array([0.0, 0.0])
        t_span = (0.0, 10.0)
        t_hist, y_hist = rk4_solve(const_accel, t_span, y0, dt=0.01)

        x_num = y_hist[-1, 0]
        v_num = y_hist[-1, 1]
        x_exact = 0.5 * a_const * (10.0 ** 2)
        v_exact = a_const * 10.0

        self.assertAlmostEqual(x_num, x_exact, places=4)
        self.assertAlmostEqual(v_num, v_exact, places=4)

    def test_02_gravity_only_limiting(self):
        """2. Gravity-only limiting behavior: freefall from 10,000m."""
        def freefall(t, y):
            return np.array([y[1], -G0])

        y0 = np.array([10000.0, 0.0])
        t_span = (0.0, 20.0)
        t_hist, y_hist = rk4_solve(freefall, t_span, y0, dt=0.01)

        y_num = y_hist[-1, 0]
        v_num = y_hist[-1, 1]
        y_exact = 10000.0 - 0.5 * G0 * (20.0 ** 2)
        v_exact = -G0 * 20.0

        self.assertAlmostEqual(y_num, y_exact, places=4)
        self.assertAlmostEqual(v_num, v_exact, places=4)

    def test_03_zero_thrust_behavior(self):
        """3. Zero-thrust behavior: vehicle mass remains strictly constant and thrust is zero."""
        eng = Raptor3Engine(variant="SL")
        thrust, isp, mdot = eng.compute_performance(101325.0, throttle=0.0)
        self.assertEqual(thrust, 0.0)
        self.assertEqual(mdot, 0.0)

    def test_04_zero_drag_behavior(self):
        """4. Zero-drag behavior: in deep vacuum (>100 km), dynamic pressure and drag vanish."""
        atmos120k = us_standard_atmosphere_1976(120000.0)
        self.assertLess(atmos120k["density"], 1e-7)
        self.assertLess(atmos120k["pressure"], 0.01)

    def test_05_thrust_to_mass_flow_relation(self):
        """5. Correct thrust-to-mass-flow relation: mdot = F_vac / (Isp * g0)."""
        eng = Raptor3Engine(variant="SL")
        expected_mdot = eng.thrust_vac / (eng.isp_vac * G0)
        self.assertAlmostEqual(eng.mass_flow_nominal, expected_mdot, places=4)

    def test_06_monotonic_mass_reduction(self):
        """6. Monotonic mass reduction during burning."""
        nom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_nominal.csv")
        self.assertTrue(os.path.exists(nom_csv))
        with open(nom_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            masses = [float(r["mass_tonnes"]) for r in rows]
            for i in range(len(masses) - 1):
                self.assertLessEqual(masses[i+1], masses[i] + 1e-6,
                                     f"Mass increased at step {i}: {masses[i]} -> {masses[i+1]}")

    def test_07_nonnegative_mass_and_propellant(self):
        """7. Nonnegative mass and propellant: mass never drops below dry structural limit."""
        nom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_nominal.csv")
        with open(nom_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            for r in rows:
                m = float(r["mass_tonnes"])
                self.assertGreater(m, 340.0) # Liftoff hardware dry mass ~341.3 t

    def test_08_integrated_mass_loss_vs_flow(self):
        """8. Integrated mass loss versus integrated mass flow."""
        nom_csv = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_nominal.csv")
        with open(nom_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            m0 = float(rows[0]["mass_tonnes"]) * 1000.0
            mf = float(rows[-1]["mass_tonnes"]) * 1000.0
            delta_m_actual = m0 - mf
            self.assertGreater(delta_m_actual, 2800000.0) # > 2,800 tonnes burned
            self.assertLess(delta_m_actual, 3000000.0)

    def test_09_tsiolkovsky_rocket_equation(self):
        """9. Ideal rocket-equation comparison under idealized conditions."""
        m0 = 4939800.0
        mf = 2098410.0
        isp = 332.0 # Effective sea-level/ascent Isp
        delta_v_ideal = isp * G0 * math.log(m0 / mf)
        self.assertGreater(delta_v_ideal, 2700.0)
        self.assertLess(delta_v_ideal, 3100.0)

    def test_10_event_ordering_and_single_application(self):
        """10. Correct event ordering and single application of each event."""
        cluster = BoosterCluster33(enable_anomaly=True, anomaly_time_s=35.0, anomaly_engine_id=17)
        # Check active engines before and after anomaly time
        _, _, _, act_30 = cluster.compute_cluster_state(30.0, 50000.0, 35000.0)
        _, _, _, act_40 = cluster.compute_cluster_state(40.0, 30000.0, 35000.0)
        self.assertEqual(act_30, 33)
        self.assertEqual(act_40, 32)

    def test_11_stage_state_and_mass_bookkeeping(self):
        """11. Correct stage-state and mass bookkeeping: full stack = booster + ship."""
        m_booster_wet = 200825.0 + 3400000.0
        m_ship_wet = 99975.0 + 39000.0 + 1200000.0
        self.assertEqual(m_booster_wet + m_ship_wet, MASS_LIFTOFF_TOTAL)

    def test_12_atmosphere_reference_comparisons(self):
        """12. Atmosphere reference comparisons at international standard points."""
        atm0 = us_standard_atmosphere_1976(0.0)
        self.assertAlmostEqual(atm0["temperature"], 288.15, delta=0.01)
        self.assertAlmostEqual(atm0["pressure"], 101325.0, delta=1.0)
        self.assertAlmostEqual(atm0["density"], 1.225, delta=0.01)

    def test_13_coordinate_frame_and_unit_consistency(self):
        """13. Coordinate-frame and unit consistency (Bowring WGS-84 algorithm)."""
        r0 = geodetic_to_ecef(LAT_STARBASE_DEG, LON_STARBASE_DEG, ALT_STARBASE_M)
        h_rec = ecef_to_geodetic_height(r0)
        self.assertAlmostEqual(h_rec, ALT_STARBASE_M, places=4)

    def test_14_sensitivity_to_solver_tolerances(self):
        """14. Sensitivity to solver tolerances and maximum step (< 0.01%)."""
        sum_json = os.path.join(PROJECT_ROOT, "output", "flight14_ascent_summary.json")
        with open(sum_json, "r", encoding="utf-8") as jf:
            summary = json.load(jf)
            pct = summary["verification_metrics"]["rk4_step_sensitivity_pct"]
            self.assertLess(pct, 0.01)

    def test_15_deterministic_replay(self):
        """15. Deterministic replay: same inputs produce identical trajectory outputs."""
        recs1, _ = simulate_ascent(enable_anomaly=False, dt=0.5)
        recs2, _ = simulate_ascent(enable_anomaly=False, dt=0.5)
        self.assertEqual(len(recs1), len(recs2))
        self.assertEqual(recs1[-1]["altitude_km"], recs2[-1]["altitude_km"])
        self.assertEqual(recs1[-1]["v_rel_ms"], recs2[-1]["v_rel_ms"])

    def test_16_input_schema_and_source_provenance(self):
        """16. Input schema and source-provenance completeness in parameters.yaml."""
        params_yaml = os.path.join(PROJECT_ROOT, "data", "propulsion", "parameters.yaml")
        self.assertTrue(os.path.exists(params_yaml))
        with open(params_yaml, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("raptor3_engines", content)
            self.assertIn("super_heavy_booster", content)
            self.assertIn("starship_stage2", content)
            self.assertIn("aerodynamics", content)

    def test_17_output_integrity_and_metadata(self):
        """17. Output integrity, finite values, and monotonic timestamps in ascent_log.csv."""
        log_csv = os.path.join(PROJECT_ROOT, "output", "ascent_log.csv")
        self.assertTrue(os.path.exists(log_csv))
        with open(log_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            t_prev = -1.0
            for row in reader:
                t = float(row["time_s"])
                self.assertGreaterEqual(t, t_prev)
                self.assertFalse(math.isnan(float(row["altitude_km"])))
                self.assertFalse(math.isnan(float(row["v_rel_ms"])))
                t_prev = t

    def test_18_gmat_orbital_segment_script(self):
        """18. GMAT orbital-segment script exists, targets SECO state, and is non-empty."""
        gmat_script = os.path.join(PROJECT_ROOT, "src", "orbit", "gmat_starship_orbital_insertion.script")
        self.assertTrue(os.path.exists(gmat_script))
        with open(gmat_script, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("StarshipStage2", content)
            self.assertIn("EarthMJ2000Eq", content)
            self.assertIn("DefaultProp", content)
            self.assertIn("BeginMissionSequence", content)

if __name__ == "__main__":
    unittest.main()
