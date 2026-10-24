#!/usr/bin/env python3
"""
Phase 1 Data Integrity and Schema Verification Test Suite
Starship Flight 14 Digital Engineering Project
Author: Senior Aerospace Verification Lead
"""

import os
import csv
import unittest
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCES_CSV = os.path.join(PROJECT_ROOT, "research", "sources.csv")
CLAIMS_CSV = os.path.join(PROJECT_ROOT, "research", "claims.csv")
PLANNED_EVENTS_CSV = os.path.join(PROJECT_ROOT, "data", "mission", "flight14_planned_events.csv")
ACTUAL_EVENTS_CSV = os.path.join(PROJECT_ROOT, "data", "mission", "flight14_actual_events.csv")
SATELLITE_MANIFEST_CSV = os.path.join(PROJECT_ROOT, "data", "mission", "satellite_manifest.csv")
VEHICLE_PARAMS_YAML = os.path.join(PROJECT_ROOT, "data", "config", "vehicle_parameters.yaml")
ASSUMPTIONS_YAML = os.path.join(PROJECT_ROOT, "data", "config", "assumptions.yaml")

class TestPhase1DataIntegrity(unittest.TestCase):

    def setUp(self):
        self.sources = {}
        if os.path.exists(SOURCES_CSV):
            with open(SOURCES_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.sources[row["source_id"]] = row

    def test_sources_csv_integrity(self):
        """Verify sources.csv schema, non-empty IDs, and uniqueness."""
        self.assertTrue(os.path.exists(SOURCES_CSV), f"Missing: {SOURCES_CSV}")
        required_cols = [
            "source_id", "title", "organization", "author",
            "publication_date", "accessed_date", "source_url",
            "source_tier", "format", "license_or_terms"
        ]
        with open(SOURCES_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for col in required_cols:
                self.assertIn(col, fieldnames, f"Missing column '{col}' in sources.csv")
            
            seen_ids = set()
            for row in reader:
                sid = row["source_id"]
                self.assertTrue(sid, "Found empty source_id")
                self.assertNotIn(sid, seen_ids, f"Duplicate source_id detected: {sid}")
                seen_ids.add(sid)
                self.assertIn(row["source_tier"], ["primary", "peer_reviewed", "secondary", "community_lead"],
                              f"Invalid source_tier in {sid}")

    def test_claims_csv_integrity(self):
        """Verify claims.csv links to valid source IDs and valid status enums."""
        self.assertTrue(os.path.exists(CLAIMS_CSV), f"Missing: {CLAIMS_CSV}")
        valid_statuses = ["VERIFIED_FACT", "OBSERVED_EVENT", "DERIVED", "ASSUMPTION", "CONFLICTING"]
        with open(CLAIMS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_claims = set()
            for row in reader:
                cid = row["claim_id"]
                self.assertNotIn(cid, seen_claims, f"Duplicate claim_id: {cid}")
                seen_claims.add(cid)
                
                # Verify source reference
                psid = row["primary_source_id"]
                self.assertIn(psid, self.sources, f"Claim {cid} references unknown source_id '{psid}'")
                
                ssid = row.get("secondary_source_id", "").strip()
                if ssid:
                    self.assertIn(ssid, self.sources, f"Claim {cid} references unknown secondary source_id '{ssid}'")
                
                self.assertIn(row["claim_status"], valid_statuses, f"Invalid claim_status in {cid}")

    def test_planned_events_integrity(self):
        """Verify planned events chronology, monotonicity, and schema."""
        self.assertTrue(os.path.exists(PLANNED_EVENTS_CSV), f"Missing: {PLANNED_EVENTS_CSV}")
        with open(PLANNED_EVENTS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_events = set()
            last_t = -999999.0
            found_long_duration = False
            for row in reader:
                eid = row["event_id"]
                self.assertNotIn(eid, seen_events, f"Duplicate event_id in planned events: {eid}")
                seen_events.add(eid)
                
                t = float(row["t_plus_seconds"])
                self.assertGreaterEqual(t, last_t, f"Non-monotonic timestamp in planned events: {eid} (t={t} < {last_t})")
                last_t = t
                
                if t >= 30000.0:
                    found_long_duration = True
                
                sid = row["source_id"]
                self.assertIn(sid, self.sources, f"Event {eid} references unknown source_id '{sid}'")
            
            self.assertTrue(found_long_duration, "Planned profile must reflect nominal ~10h profile (t > 30000s)")

    def test_actual_events_integrity_and_duration_isolation(self):
        """Verify flown actual events reflect shortened ~3h flight with no 10h contamination."""
        self.assertTrue(os.path.exists(ACTUAL_EVENTS_CSV), f"Missing: {ACTUAL_EVENTS_CSV}")
        with open(ACTUAL_EVENTS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_events = set()
            last_t = -999999.0
            max_t = 0.0
            found_booster_splashdown = False
            found_ship_splashdown = False
            found_engine_anomaly = False
            
            for row in reader:
                eid = row["event_id"]
                self.assertNotIn(eid, seen_events, f"Duplicate event_id in actual events: {eid}")
                seen_events.add(eid)
                
                t = float(row["t_plus_seconds"])
                self.assertGreaterEqual(t, last_t, f"Non-monotonic timestamp in actual events: {eid} (t={t} < {last_t})")
                last_t = t
                if t > max_t:
                    max_t = t
                
                name = row["event_name"].lower()
                if "gulf" in name and "splashdown" in name:
                    found_booster_splashdown = True
                if "pacific" in name and "splashdown" in name:
                    found_ship_splashdown = True
                if "anomaly" in name or "shutdown" in name:
                    found_engine_anomaly = True
                
                sid = row["source_id"]
                self.assertIn(sid, self.sources, f"Actual event {eid} references unknown source_id '{sid}'")
            
            # Critical Invariant: Flight 14 was shortened to ~3h 8m (~11,280 s).
            # It MUST NOT exceed 4.0 hours (14,400 s).
            self.assertLess(max_t, 14400.0, f"Actual profile exceeded 4 hours! Max t = {max_t}s (Contamination from planned 10h profile!)")
            self.assertGreater(max_t, 10000.0, f"Actual profile suspiciously short! Max t = {max_t}s")
            self.assertTrue(found_booster_splashdown, "Missing Booster Gulf splashdown event in actual profile")
            self.assertTrue(found_ship_splashdown, "Missing Ship Pacific splashdown event in actual profile")
            self.assertTrue(found_engine_anomaly, "Missing in-flight engine anomaly event in actual profile")

    def test_satellite_manifest(self):
        """Verify 26 Starlink V3 payload satellites and valid physical separation values."""
        self.assertTrue(os.path.exists(SATELLITE_MANIFEST_CSV), f"Missing: {SATELLITE_MANIFEST_CSV}")
        with open(SATELLITE_MANIFEST_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            satellites = list(reader)
            self.assertEqual(len(satellites), 26, f"Expected exactly 26 satellites, found {len(satellites)}")
            
            seen_ids = set()
            for idx, sat in enumerate(satellites, start=1):
                sid = sat["satellite_id"]
                self.assertNotIn(sid, seen_ids, f"Duplicate satellite_id: {sid}")
                seen_ids.add(sid)
                
                seq = int(sat["deployment_sequence"])
                self.assertEqual(seq, idx, f"Out of order sequence: {seq} != {idx}")
                
                v_sep = float(sat["separation_velocity_mps"])
                self.assertGreater(v_sep, 0.05, f"Unphysical low separation velocity: {v_sep}")
                self.assertLess(v_sep, 5.0, f"Unphysical high separation velocity: {v_sep}")
                
                mass = float(sat["mass_kg"])
                self.assertGreaterEqual(mass, 1000.0, f"Unphysical satellite mass: {mass}")
                
                src = sat["source_id"]
                self.assertIn(src, self.sources, f"Satellite {sid} references unknown source_id '{src}'")

    def test_vehicle_parameters_yaml(self):
        """Verify vehicle_parameters.yaml structure, units, and status enums."""
        self.assertTrue(os.path.exists(VEHICLE_PARAMS_YAML), f"Missing: {VEHICLE_PARAMS_YAML}")
        with open(VEHICLE_PARAMS_YAML, mode="r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        valid_statuses = ["public_fact", "observed_event", "derived", "assumption", "unknown"]
        sections = ["geometry", "mass_properties", "propulsion", "structural_materials"]
        
        for sec in sections:
            self.assertIn(sec, data, f"Missing section '{sec}' in vehicle_parameters.yaml")
            for param_key, param in data[sec].items():
                self.assertIn("name", param, f"Missing 'name' in {sec}.{param_key}")
                self.assertIn("value", param, f"Missing 'value' in {sec}.{param_key}")
                self.assertIn("unit", param, f"Missing 'unit' in {sec}.{param_key}")
                self.assertIn("status", param, f"Missing 'status' in {sec}.{param_key}")
                self.assertIn(param["status"], valid_statuses, f"Invalid status '{param['status']}' in {sec}.{param_key}")
                self.assertIn("source_id", param, f"Missing 'source_id' in {sec}.{param_key}")
                self.assertIn(param["source_id"], self.sources, f"Parameter {sec}.{param_key} references unknown source_id '{param['source_id']}'")

    def test_assumptions_yaml(self):
        """Verify assumptions.yaml structure and uncertainty ranges."""
        self.assertTrue(os.path.exists(ASSUMPTIONS_YAML), f"Missing: {ASSUMPTIONS_YAML}")
        with open(ASSUMPTIONS_YAML, mode="r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        self.assertIn("assumptions", data)
        for asm_id, asm in data["assumptions"].items():
            self.assertIn("parameter", asm)
            self.assertIn("assumed_value", asm)
            self.assertIn("unit", asm)
            self.assertIn("uncertainty_range", asm)
            self.assertEqual(len(asm["uncertainty_range"]), 2, f"Expected [min, max] range in {asm_id}")
            self.assertLessEqual(asm["uncertainty_range"][0], asm["uncertainty_range"][1])

if __name__ == "__main__":
    unittest.main()
