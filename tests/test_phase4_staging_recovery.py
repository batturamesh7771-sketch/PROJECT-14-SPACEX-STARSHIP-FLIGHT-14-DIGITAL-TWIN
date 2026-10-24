#!/usr/bin/env python3
"""
Phase 4 Staging Dynamics & Dual-Vehicle Trajectory Test Suite
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

from src.environment.atmosphere_1976 import R_EARTH_EQUATORIAL, GM_EARTH
from src.dynamics.staging_separation import simulate_hot_staging_separation
from src.dynamics.booster_recovery import simulate_booster_return, booster_drag_coefficient
from src.dynamics.starship_ascent_to_orbit import (
    simulate_starship_ascent,
    compute_keplerian_elements,
    MASS_SHIP_DRY_HARDWARE,
    MASS_PAYLOAD_26_SATS
)

class TestPhase4StagingRecovery(unittest.TestCase):

    def setUp(self):
        # Representative state at T=142s (from Phase 3 simulation output)
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
            # Fallback realistic state
            self.state_t142 = np.array([-720000.0, -5800000.0, 2850000.0, 1600.0, 800.0, 1100.0, 2098000.0])
            self.v0_sep = 1808.0

    def test_hot_staging_separation_dynamics(self):
        """Verify dual-vehicle clearance, plume backpressure, and relative velocity during separation."""
        m_booster = 671000.0
        m_ship = 1338975.0

        records, summary = simulate_hot_staging_separation(
            m_booster, m_ship, v0_ms=self.v0_sep, dt=0.01, t_span=(140.0, 150.0)
        )

        self.assertEqual(summary["status"], "CLEAN_SEPARATION_VERIFIED")

        # 1. Before release (T < 142s): relative distance is zero
        row_141 = next(r for r in records if r["time_s"] == 141.0)
        self.assertFalse(row_141["is_separated"])
        self.assertEqual(row_141["relative_distance_m"], 0.0)

        # 2. At 1s post-separation (T=143s): clearance > 3.0 m
        self.assertGreater(summary["separation_clearance_1s_m"], 3.0)

        # 3. At 3s post-separation (T=145s): clearance > 20.0 m
        self.assertGreater(summary["separation_clearance_3s_m"], 20.0)

        # 4. Final separation distance at 10s > 100 m
        self.assertGreater(summary["final_relative_distance_m"], 100.0)

        # 5. Peak plume force is positive and bounded
        self.assertGreater(summary["peak_plume_force_kn"], 1000.0)
        self.assertLess(summary["peak_plume_force_kn"], 2500.0)

    def test_booster_drag_coefficient(self):
        """Verify booster base-first drag polar with deployed grid fins."""
        cd_sub = booster_drag_coefficient(0.5)
        cd_trans = booster_drag_coefficient(1.05)
        cd_super = booster_drag_coefficient(3.0)

        self.assertGreater(cd_sub, 0.70)
        self.assertGreater(cd_trans, cd_sub)
        self.assertGreater(cd_super, 0.60)

    def test_booster_recovery_trajectory(self):
        """Verify booster flip, boostback propellant consumption, apogee, and soft splashdown."""
        records, summary = simulate_booster_return(self.state_t142, dt=0.05)

        self.assertEqual(summary["splashdown"]["status"], "CONTROLLED_SOFT_SPLASHDOWN_VERIFIED")

        # Apogee altitude between 95 and 125 km
        apogee_alt = summary["apogee"]["altitude_km"]
        self.assertGreater(apogee_alt, 95.0)
        self.assertLess(apogee_alt, 125.0)

        # Boostback propellant consumption between 350 and 460 tonnes
        bb_prop = summary["boostback_shutdown"]["propellant_consumed_tonnes"]
        self.assertGreater(bb_prop, 350.0)
        self.assertLess(bb_prop, 460.0)

        # Soft touchdown relative velocity < 25 m/s
        v_touchdown = summary["splashdown"]["touchdown_relative_velocity_ms"]
        self.assertLess(v_touchdown, 25.0)

        # Splashdown altitude at MSL (0 km)
        self.assertAlmostEqual(summary["splashdown"]["altitude_km"], 0.0, delta=0.5)

    def test_starship_orbital_insertion_and_elements(self):
        """Verify Starship upper stage ascent to SECO, velocity, and Keplerian orbital parameters."""
        records, summary = simulate_starship_ascent(self.state_t142, actual_profile=True, dt=0.05)

        self.assertEqual(summary["status"], "ORBITAL_INSERTION_VERIFIED")
        self.assertAlmostEqual(summary["seco_timestamp_s"], 525.0, delta=5.0)

        # Inertial velocity at SECO ~ 7750 m/s
        v_inertial = summary["seco_inertial_velocity_ms"]
        self.assertGreater(v_inertial, 7650.0)
        self.assertLess(v_inertial, 7850.0)

        # Orbital elements
        kepler = summary["orbital_elements"]
        self.assertGreater(kepler["perigee_altitude_km"], 120.0, "Perigee must be above atmospheric dense boundary")
        self.assertLess(kepler["perigee_altitude_km"], 200.0)
        self.assertGreater(kepler["apogee_altitude_km"], 200.0)
        self.assertLess(kepler["apogee_altitude_km"], 300.0)

        # Inclination should be consistent with 25.996 deg latitude Starbase launch (~26.5 deg)
        self.assertGreater(kepler["inclination_deg"], 25.5)
        self.assertLess(kepler["inclination_deg"], 27.5)

        # Eccentricity should be small low Earth orbit (< 0.02)
        self.assertLess(kepler["eccentricity"], 0.02)

        # Reserve propellant for deorbit burn should be >= 30 tonnes
        self.assertGreater(summary["reserve_propellant_tonnes"], 30.0)

    def test_keplerian_elements_analytical(self):
        """Verify Keplerian elements calculation on standard known circular orbit."""
        r_circ = R_EARTH_EQUATORIAL + 200000.0 # 200 km
        v_circ = math.sqrt(GM_EARTH / r_circ)
        r_vec = np.array([r_circ, 0.0, 0.0])
        v_vec = np.array([0.0, v_circ, 0.0])

        elem = compute_keplerian_elements(r_vec, v_vec)
        self.assertAlmostEqual(elem["semi_major_axis_km"], r_circ / 1000.0, delta=1.0)
        self.assertAlmostEqual(elem["eccentricity"], 0.0, places=4)
        self.assertAlmostEqual(elem["perigee_altitude_km"], 200.0, delta=1.0)
        self.assertAlmostEqual(elem["apogee_altitude_km"], 200.0, delta=1.0)
        self.assertAlmostEqual(elem["inclination_deg"], 0.0, places=2)

if __name__ == "__main__":
    unittest.main()
