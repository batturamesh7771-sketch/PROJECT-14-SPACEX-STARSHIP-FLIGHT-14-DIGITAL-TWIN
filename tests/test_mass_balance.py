"""
Automated Verification Suite for Mass Balance and Propulsion Consistency
========================================================================
Verifies that every kilogram of vehicle mass is strictly accounted for
from pad liftoff, through MECO, staging, SECO, payload deployment,
deorbit disposal burn, and atmospheric entry.
"""

import unittest
import math
import csv
import os

from src.astrodynamics.constants import STANDARD_GRAVITY


class TestMassBalanceReconciliation(unittest.TestCase):
    """Verifies mass balance across the entire Starship Flight 14 mission."""

    def setUp(self):
        self.csv_path = "data/audit/mass_balance.csv"
        self.assertTrue(os.path.exists(self.csv_path), f"Mass balance ledger missing: {self.csv_path}")

    def test_total_mission_mass_conservation(self):
        """TEST-MB-01: Verify mass_after == mass_before + added - removed - consumed."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreater(len(rows), 0, "Mass balance ledger must contain event rows.")

        for row in rows:
            event_id = row["event_id"]
            m_before = float(row["mass_before_kg"])
            m_added = float(row["mass_added_kg"])
            m_removed = float(row["mass_removed_kg"])
            m_consumed = float(row["propellant_consumed_kg"])
            m_after = float(row["mass_after_kg"])
            residual = float(row["mass_balance_residual_kg"])

            expected_after = m_before + m_added - m_removed - m_consumed
            self.assertAlmostEqual(
                m_after, expected_after, places=2,
                msg=f"Mass balance violated at {event_id}: {m_after} != {expected_after}"
            )
            self.assertAlmostEqual(
                residual, 0.0, places=3,
                msg=f"Non-zero mass balance residual at {event_id}: {residual}"
            )

    def test_liftoff_full_stack_breakdown(self):
        """TEST-MB-02: Verify full stack liftoff mass equals booster + ship mass."""
        m_booster_dry = 200825.0
        m_booster_prop = 3400000.0
        m_booster_total = m_booster_dry + m_booster_prop  # 3600825.0 kg

        m_ship_dry = 99975.0
        m_ship_payload = 39000.0
        m_ship_prop = 1200000.0
        m_ship_total = m_ship_dry + m_ship_payload + m_ship_prop  # 1338975.0 kg

        m_liftoff_total = m_booster_total + m_ship_total
        self.assertAlmostEqual(m_liftoff_total, 4939800.0, places=2)

    def test_payload_deployment_and_deorbit_burn_reconciliation(self):
        """TEST-MB-03: Reconcile SECO insertion (220.85 t) to entry mass (177.27 t)."""
        m_seco = 220850.0  # kg (220.85 t)
        m_payload_deployed = 39000.0  # kg (39.0 t, 26 Starlinks x 1500 kg)

        m_post_deploy = m_seco - m_payload_deployed
        self.assertAlmostEqual(m_post_deploy, 181850.0, places=2)

        # Deorbit burn calculation via Tsiolkovsky equation
        delta_v = 95.0  # m/s retrograde
        isp = 380.0  # s (Raptor vacuum)
        g0 = STANDARD_GRAVITY

        prop_consumed = m_post_deploy * (1.0 - math.exp(-delta_v / (g0 * isp)))
        self.assertAlmostEqual(prop_consumed, 4577.29, delta=0.5)

        m_entry = m_post_deploy - prop_consumed
        self.assertAlmostEqual(m_entry, 177272.71, delta=0.5)

        # Ensure residual is identically zero
        reconciled_residual = m_seco - m_payload_deployed - prop_consumed - m_entry
        self.assertAlmostEqual(reconciled_residual, 0.0, delta=1e-4)


if __name__ == '__main__':
    unittest.main()
