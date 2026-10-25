"""
Unit and integration test suite for Phase 10: Digital Engineering Spatial Dashboard (Three.js WebGL).
Starship Flight 14 Digital Engineering Lab.

Tests 15 distinct verification assertions:
 1. Scenario data schema and JSON serialization integrity.
 2. Presence of all 3 mandatory mission profiles (Planned, Observed, Synthetic).
 3. Strict profile isolation and synthetic warning banner verification.
 4. Orthogonal coordinate transformation matrix properties (det = +1.0, R^T R = I).
 5. ECI to Three.js scene vector mapping correctness.
 6. Complete 26-satellite Starlink V3 payload manifest verification.
 7. Planned vs Observed event ledger matching and delta calculation.
 8. Preservation of missing/unmodeled values as null (never fabricated to zero).
 9. Telemetry channel metadata completeness (name, unit, formula, provenance).
 10. High-density virtualized explorer dataset (>5,000 records).
 11. Structural FEA tank section stress integrity (Roark benchmark comparison).
 12. Thermal TPS reentry data and positive bondline margin.
 13. Run manifest schema, metadata, and feature count.
 14. Completeness of all static web application assets on disk.
 15. Programmatic adapter data export functionality.
"""

import unittest
import os
import json
import tempfile
import numpy as np

from src.dashboard.adapter import (
    build_scenario_data,
    export_dashboard_data,
    eci_to_scene,
    get_channel_registry,
    SCENE_SCALE_FACTOR,
    EARTH_RADIUS_M,
)


class TestPhase10Dashboard(unittest.TestCase):
    """15-point verification matrix for Phase 10 Spatial Dashboard."""

    @classmethod
    def setUpClass(cls):
        # Assemble scenario payload once for read-only inspection
        cls.payload = build_scenario_data()

    def test_01_scenario_data_schema(self):
        """1. Scenario data must contain all required top-level digital engineering schema keys."""
        required_keys = [
            "version",
            "project",
            "timestamp",
            "coordinate_conventions",
            "channel_registry",
            "fea_tank_section",
            "satellite_manifest",
            "comparison_events",
            "profiles",
            "virtualized_explorer_records",
        ]
        for k in required_keys:
            self.assertIn(k, self.payload, f"Missing required top-level key: {k}")

    def test_02_all_three_mission_profiles_present(self):
        """2. Must contain Planned Flight 14, Observed Reconstruction, and Synthetic Landing Lab."""
        profiles = self.payload.get("profiles", {})
        self.assertIn("planned_flight14", profiles)
        self.assertIn("observed_reconstruction", profiles)
        self.assertIn("synthetic_landing_lab", profiles)
        self.assertEqual(len(profiles), 3)

    def test_03_strict_profile_isolation_and_synthetic_banner(self):
        """3. Observed profile cannot be synthetic; Synthetic profile MUST have synthetic banner."""
        profiles = self.payload["profiles"]
        obs = profiles["observed_reconstruction"]
        syn = profiles["synthetic_landing_lab"]
        planned = profiles["planned_flight14"]

        self.assertFalse(obs["is_synthetic"], "Observed reconstruction must not be synthetic")
        self.assertFalse(planned["is_synthetic"], "Planned profile must not be synthetic")
        self.assertTrue(syn["is_synthetic"], "Synthetic landing lab must be flagged synthetic")
        self.assertIn("SYNTHETIC — NOT FLIGHT 14 HISTORY", syn.get("synthetic_banner", ""))

    def test_04_coordinate_transformation_orthogonality(self):
        """4. Coordinate transform matrix must have det(R) = +1.0 and R^T R = I."""
        matrix = np.array(self.payload["coordinate_conventions"]["matrix"])
        det = np.linalg.det(matrix)
        identity = np.dot(matrix.T, matrix)

        self.assertAlmostEqual(det, 1.0, places=6, msg="Matrix must be a proper rotation (det = +1.0)")
        np.testing.assert_allclose(identity, np.eye(3), atol=1e-6, err_msg="Matrix must be orthogonal")

    def test_05_eci_to_scene_vector_mapping(self):
        """5. ECI (X, Y, Z) must transform to (X, Z, -Y) * scale."""
        x, y, z = 1000000.0, 2000000.0, 3000000.0
        scene_pos = eci_to_scene(x, y, z)

        expected_x = round(x * SCENE_SCALE_FACTOR, 6)
        expected_y = round(z * SCENE_SCALE_FACTOR, 6)
        expected_z = round(-y * SCENE_SCALE_FACTOR, 6)

        self.assertEqual(scene_pos, [expected_x, expected_y, expected_z])

    def test_06_all_26_starlink_v3_satellites_present(self):
        """6. Manifest must contain exactly 26 Starlink V3 satellites with valid masses and deploy times."""
        sats = self.payload["satellite_manifest"]
        self.assertEqual(len(sats), 26, "Must contain exactly 26 Starlink V3 satellites")
        for s in sats:
            self.assertGreater(s["satellite_number"], 0)
            self.assertLessEqual(s["satellite_number"], 26)
            self.assertEqual(s["mass_kg"], 1750.0)
            self.assertGreater(s["deploy_time_s"], 0.0)

    def test_07_planned_vs_observed_comparison_events(self):
        """7. Event comparison ledger must contain matched planned and actual events with deltas."""
        events = self.payload["comparison_events"]
        self.assertGreater(len(events), 5)
        # Verify delta is correctly computed
        for ev in events:
            if ev["planned_time_s"] is not None and ev["actual_time_s"] is not None:
                expected_delta = round(ev["actual_time_s"] - ev["planned_time_s"], 2)
                self.assertAlmostEqual(ev["delta_s"], expected_delta, places=2)

    def test_08_missing_values_preserved_as_null_not_zero(self):
        """8. Missing or unmodeled telemetry parameters must serialize as None/null, never 0."""
        records = self.payload["virtualized_explorer_records"]
        # In orbital phase records, aerodynamic dynamic pressure is unmodeled / not present
        orbit_recs = [r for r in records if r["phase"] == "ORBIT"]
        self.assertGreater(len(orbit_recs), 0)
        # Check that unmodeled heat flux in ascent or orbit isn't falsely invented
        has_null = any(r.get("heat_flux_mw_m2") is None for r in orbit_recs)
        self.assertTrue(has_null, "Unmodeled values must be preserved as null")

    def test_09_channel_registry_completeness(self):
        """9. Telemetry channel registry must contain all standard channels with full metadata."""
        channels = self.payload["channel_registry"]
        expected_channels = [
            "time_s", "altitude_km", "velocity_km_s", "mach",
            "dynamic_pressure_kpa", "apparent_g", "thrust_mn", "mass_tonnes",
            "heat_flux_mw_m2", "surface_temp_k", "bondline_temp_k",
            "hoop_stress_mpa", "von_mises_mpa", "pitch_deg"
        ]
        for ch in expected_channels:
            self.assertIn(ch, channels, f"Missing channel: {ch}")
            meta = channels[ch]
            self.assertIn("name", meta)
            self.assertIn("unit", meta)
            self.assertIn("formula", meta)
            self.assertIn("provenance", meta)
            self.assertIn("description", meta)

    def test_10_virtualized_explorer_records_density(self):
        """10. Virtualized explorer must contain > 5000 high-density simulation records."""
        records = self.payload["virtualized_explorer_records"]
        self.assertGreater(len(records), 5000, "Virtualized explorer dataset must exceed 5000 records")

    def test_11_fea_tank_section_stress_values(self):
        """11. Structural FEA summary must reflect verified 6.0 bar pressure and Roark hoop stress."""
        fea = self.payload["fea_tank_section"]
        self.assertEqual(fea["pressure_bar"], 6.0)
        self.assertAlmostEqual(fea["fea_hoop_stress_MPa"], 675.0, places=1)
        self.assertAlmostEqual(fea["roark_hoop_stress_MPa"], 675.0, places=1)
        self.assertGreater(fea["factor_of_safety"], 1.5)

    def test_12_thermal_tps_parameters_and_margin(self):
        """12. Reentry thermal trajectory must maintain positive bondline margin."""
        obs_traj = self.payload["profiles"]["observed_reconstruction"]["trajectory"]
        reentry_pts = [p for p in obs_traj if p.get("phase") == "REENTRY"]
        self.assertGreater(len(reentry_pts), 0)
        for pt in reentry_pts:
            self.assertLess(pt["bondline_temp_k"], 533.15, "Bondline must not exceed 533.15 K limit")
            self.assertGreater(pt["surface_temp_k"], 200.0)

    def test_13_run_manifest_schema_and_metadata(self):
        """13. Exported run_manifest.json must contain correct verification properties."""
        with tempfile.TemporaryDirectory() as tmpdir:
            s_path, m_path = export_dashboard_data(tmpdir)
            self.assertTrue(os.path.isfile(m_path))
            with open(m_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self.assertEqual(manifest["satellites_count"], 26)
            self.assertEqual(len(manifest["profiles"]), 3)
            self.assertEqual(manifest["coordinate_transform_status"], "VERIFIED_ORTHOGONAL_DET_PLUS_1")

    def test_14_static_web_assets_exist(self):
        """14. All dashboard frontend static files must exist on disk."""
        base_dir = os.path.join(os.path.dirname(__file__), "..", "src", "dashboard", "static")
        expected_files = [
            "index.html",
            os.path.join("css", "dashboard.css"),
            os.path.join("js", "scene.js"),
            os.path.join("js", "timeline.js"),
            os.path.join("js", "hud.js"),
            os.path.join("js", "charts.js"),
            os.path.join("js", "explorer.js"),
            os.path.join("vendor", "three.min.js"),
            os.path.join("vendor", "OrbitControls.js"),
            os.path.join("data", "scenario_data.json"),
            os.path.join("data", "scenario_data_embedded.js"),
            os.path.join("data", "run_manifest.json"),
        ]
        for rel in expected_files:
            full_path = os.path.join(base_dir, rel)
            self.assertTrue(os.path.isfile(full_path), f"Missing web asset: {rel}")

    def test_15_adapter_export_functionality(self):
        """15. export_dashboard_data must write scenario_data.json without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            s_path, m_path = export_dashboard_data(tmpdir)
            self.assertTrue(os.path.isfile(s_path))
            self.assertTrue(os.path.isfile(m_path))
            self.assertGreater(os.path.getsize(s_path), 1_000_000)

    def test_16_embedded_scenario_data_fallback(self):
        """16. scenario_data_embedded.js must exist, be > 1MB, and start with window.EMBEDDED_SCENARIO_DATA."""
        emb_path = os.path.join(os.path.dirname(__file__), "..", "src", "dashboard", "static", "data", "scenario_data_embedded.js")
        self.assertTrue(os.path.isfile(emb_path))
        self.assertGreater(os.path.getsize(emb_path), 1_000_000)
        with open(emb_path, "r", encoding="utf-8") as f:
            header = f.read(50)
        self.assertTrue(header.startswith("window.EMBEDDED_SCENARIO_DATA = {"))

    def test_17_dashboard_launchers_exist(self):
        """17. Both Windows batch (run_dashboard.bat) and PowerShell (run_dashboard.ps1) launchers must exist."""
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        bat = os.path.join(root, "run_dashboard.bat")
        ps1 = os.path.join(root, "run_dashboard.ps1")
        self.assertTrue(os.path.isfile(bat), "run_dashboard.bat must exist in repo root")
        self.assertTrue(os.path.isfile(ps1), "run_dashboard.ps1 must exist in repo root")

    def test_18_mach_dimensionless_unit(self):
        """18. Mach number unit in channel registry must be dimensionless '[-]', never 'M' (meters)."""
        mach_meta = self.payload["channel_registry"]["mach"]
        self.assertNotEqual(mach_meta["unit"], "M", "Mach number must not be labeled in meters ('M')")
        self.assertIn(mach_meta["unit"], ["[-]", "dimensionless", ""])


if __name__ == "__main__":
    unittest.main()
