"""
Unit & Integration Test Suite — Phase 2: FreeCAD Engineering CAD Automation
===========================================================================
Verifies that all CAD models, assemblies, kinematic joints, drawings, BOMs,
and 100k-part scaling benchmarks satisfy the quantitative acceptance criteria
specified in docs/phase2_acceptance_tests.md.
"""

import os
import sys
import json
import csv
import sqlite3
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestPhase2CADIntegrity(unittest.TestCase):

    def test_cad_smoke_test(self):
        """TEST-CAD-SMOKE-01 to 06: Minimal parametric macro verification."""
        log_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "output", "smoke_test_execution_log.json")
        fcstd_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "output", "smoke_test_model.FCStd")
        step_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "output", "smoke_test_model.step")

        self.assertTrue(os.path.exists(log_path), "Smoke test execution log missing")
        self.assertTrue(os.path.exists(fcstd_path), "Smoke test FCStd file missing")
        self.assertTrue(os.path.exists(step_path), "Smoke test STEP file missing")
        self.assertGreater(os.path.getsize(fcstd_path), 2000, "FCStd size too small")
        self.assertGreater(os.path.getsize(step_path), 5000, "STEP size too small")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["overall_status"], "VERIFIED_SUCCESS")
        self.assertAlmostEqual(data["steps"][4]["volume_residual_pct"], 0.0, places=4)

    def test_master_skeleton_and_datums(self):
        """TEST-CAD-SKEL-01 & 02: Master vehicle skeleton & datum planes."""
        log_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "skeleton", "master_skeleton_build_log.json")
        fcstd_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "skeleton", "Starship_Master_Skeleton.FCStd")
        step_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "skeleton", "Starship_Master_Skeleton.step")

        self.assertTrue(os.path.exists(log_path), "Master skeleton build log missing")
        self.assertTrue(os.path.exists(fcstd_path), "Master skeleton FCStd missing")
        self.assertTrue(os.path.exists(step_path), "Master skeleton STEP missing")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["overall_status"], "VERIFIED_SUCCESS")
        self.assertEqual(data["datum_planes_count"], 14, "Expected 14 datum planes")
        self.assertEqual(data["oml_solids_count"], 15, "Expected 15 OML parametric solids")
        self.assertAlmostEqual(data["total_volume_m3"], 8331.61, places=1)

    def test_subsystem_parts(self):
        """TEST-CAD-ASY-01: Modular subsystem parts exist as FCStd and STEP."""
        log_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "parts", "subsystem_parts_build_log.json")
        self.assertTrue(os.path.exists(log_path), "Parts build log missing")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parts = data["parts_generated"]
        self.assertEqual(len(parts), 12, "Expected 12 distinct subsystem parts")

        for p in parts:
            self.assertTrue(os.path.exists(p["fcstd_file"]), f"Missing FCStd for {p['part_name']}")
            self.assertTrue(os.path.exists(p["step_file"]), f"Missing STEP for {p['part_name']}")
            self.assertGreater(p["cad_volume_m3"], 0.0, f"Volume non-positive for {p['part_name']}")
            self.assertGreater(p["design_mass_kg"], 0.0, f"Mass non-positive for {p['part_name']}")

    def test_modular_assemblies(self):
        """TEST-CAD-ASY-02: Hierarchical engineering assemblies."""
        log_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "assemblies", "assembly_build_log.json")
        self.assertTrue(os.path.exists(log_path), "Assembly build log missing")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        asms = {a["assembly_name"]: a for a in data["assemblies"]}
        self.assertIn("Assembly_Booster_Stage1", asms)
        self.assertIn("Assembly_Starship_Stage2", asms)
        self.assertIn("Assembly_Flight14_FullStack", asms)

        # Check booster occurrences
        bst = asms["Assembly_Booster_Stage1"]
        self.assertEqual(bst["engine_count"], 33, "Booster must have exactly 33 engines")
        self.assertEqual(bst["gridfin_count"], 4, "Booster must have 4 grid fins")

        # Check ship occurrences
        shp = asms["Assembly_Starship_Stage2"]
        self.assertEqual(shp["engine_count"], 6, "Ship must have 6 engines (3 SL, 3 Vac)")
        self.assertEqual(shp["flap_count"], 4, "Ship must have 4 flaps")

        # Check full stack
        fs = asms["Assembly_Flight14_FullStack"]
        self.assertEqual(fs["payload_count"], 26, "Full stack must contain 26 Starlink satellites")

    def test_kinematic_mechanisms(self):
        """TEST-CAD-JNT-01 & 02: Kinematic joints & motion sweeps."""
        log_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "mechanisms", "kinematic_motion_verification.json")
        fcstd_path = os.path.join(PROJECT_ROOT, "cad", "freecad", "mechanisms", "Starship_Flight14_Mechanisms.FCStd")

        self.assertTrue(os.path.exists(log_path), "Kinematic motion log missing")
        self.assertTrue(os.path.exists(fcstd_path), "Mechanisms FCStd missing")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        joints = {j["joint_name"]: j for j in data["joints_defined"]}
        self.assertIn("Joint_Flap_Fwd_Port", joints)
        self.assertIn("Joint_Flap_Fwd_Starboard", joints)
        self.assertIn("Joint_Flap_Aft_Port", joints)
        self.assertIn("Joint_Flap_Aft_Starboard", joints)
        self.assertIn("Joint_Gimbal_Booster_Center", joints)
        self.assertIn("Joint_Stage_Separation_Slider", joints)

        # Check flap limits
        fwd_port = joints["Joint_Flap_Fwd_Port"]
        self.assertEqual(fwd_port["angle_min_deg"], -30.0)
        self.assertEqual(fwd_port["angle_max_deg"], 60.0)

        aft_port = joints["Joint_Flap_Aft_Port"]
        self.assertEqual(aft_port["angle_min_deg"], -20.0)
        self.assertEqual(aft_port["angle_max_deg"], 70.0)

        # Check sweeps
        self.assertGreaterEqual(len(data["kinematic_sweeps"]), 20, "Expected at least 20 sweep verification steps")

    def test_drawings_and_bom(self):
        """TEST-CAD-DRW-01 & BOM-01: Professional drawings and BOM."""
        deliv_dir = os.path.join(PROJECT_ROOT, "cad", "freecad", "deliverables")
        svg_path = os.path.join(deliv_dir, "Starship_Flight14_General_Arrangement.svg")
        dxf_path = os.path.join(deliv_dir, "Starship_Flight14_General_Arrangement.dxf")
        bom_csv_path = os.path.join(deliv_dir, "starship_flight14_bom.csv")
        bom_json_path = os.path.join(deliv_dir, "starship_flight14_bom.json")

        self.assertTrue(os.path.exists(svg_path), "Drawing SVG missing")
        self.assertTrue(os.path.exists(dxf_path), "Drawing DXF missing")
        self.assertTrue(os.path.exists(bom_csv_path), "BOM CSV missing")
        self.assertTrue(os.path.exists(bom_json_path), "BOM JSON missing")

        self.assertGreater(os.path.getsize(svg_path), 1000, "Drawing SVG too small")
        self.assertGreater(os.path.getsize(dxf_path), 1000, "Drawing DXF too small")

        with open(bom_json_path, "r", encoding="utf-8") as f:
            bom = json.load(f)

        self.assertEqual(bom["total_line_items"], 13)
        self.assertEqual(bom["total_physical_occurrences"], 79)
        self.assertEqual(bom["mass_breakdown_kg"]["payload_manifest_mass"], 39000.0)
        self.assertEqual(bom["mass_breakdown_kg"]["total_stack_liftoff_hardware_mass"], 341300.0)

    def test_100k_scaling_benchmark(self):
        """TEST-CAD-SCL-01: 100,000+ component multi-resolution architecture."""
        scaling_dir = os.path.join(PROJECT_ROOT, "cad", "freecad", "scaling")
        db_path = os.path.join(scaling_dir, "starship_100k_part_registry.db")
        report_path = os.path.join(scaling_dir, "benchmark_100k_report.json")

        self.assertTrue(os.path.exists(db_path), "100k SQLite DB missing")
        self.assertTrue(os.path.exists(report_path), "100k benchmark report missing")

        # Check DB row count directly
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM components")
        count = cur.fetchone()[0]
        conn.close()

        self.assertGreaterEqual(count, 100000, f"Expected >= 100,000 components, got {count}")

        # Check benchmark report
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        self.assertTrue(rep["system_resources"]["passed_memory_ceiling"], "RAM exceeded 2,048 MB ceiling")
        self.assertLess(rep["system_resources"]["peak_ram_mb"], 2048.0, "RAM exceeded 2,048 MB")
        self.assertLess(rep["query_performance"]["query_1_nose_tps_tiles"]["latency_ms"], 50.0, "Query latency too high")

if __name__ == "__main__":
    unittest.main()
