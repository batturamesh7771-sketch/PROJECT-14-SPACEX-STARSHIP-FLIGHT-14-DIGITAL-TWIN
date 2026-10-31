"""
Unit and integration test suite for Starship Flight 14 Cinematic Mission Replay.
Starship Flight 14 Digital Engineering Lab.

Verifies:
  1. Static file completeness on disk for cinematic replay module and documentation.
  2. Minimal additive link in dashboard navigation without breaking existing views.
  3. Strict profile isolation: Observed Reconstruction, Planned, and Synthetic Sandbox.
  4. Authoritative mission elapsed duration: ~11,364s - 11,732s (~3h 09m - 3h 15m) for Flight 14 observed.
  5. 26 Starlink V3 payload manifest and deployment event timeline.
  6. 21 Broadcast camera choreography states completeness.
  7. CSS namespace isolation (.cfr-* pattern adherence).
  8. Replay HTML DOM structure and interactive control IDs.
"""

import unittest
import os
import re
import json

from src.dashboard.adapter import build_scenario_data


class TestCinematicReplay(unittest.TestCase):
    """Verification suite for Cinematic Mission Replay feature."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.static_dir = os.path.join(cls.repo_root, "src", "dashboard", "static")
        cls.cinematic_dir = os.path.join(cls.static_dir, "cinematic")
        cls.docs_dir = os.path.join(cls.repo_root, "docs")
        cls.scenario_data = build_scenario_data()

    def test_01_static_files_completeness(self):
        """1. Verify all cinematic replay code, stylesheets, and documentation exist on disk."""
        required_files = [
            os.path.join(self.static_dir, "replay.html"),
            os.path.join(self.cinematic_dir, "css", "cinematic_replay.css"),
            os.path.join(self.cinematic_dir, "js", "replay_controller.js"),
            os.path.join(self.cinematic_dir, "js", "camera_director.js"),
            os.path.join(self.cinematic_dir, "js", "launchpad_scene.js"),
            os.path.join(self.cinematic_dir, "js", "ocean_splashdown.js"),
            os.path.join(self.cinematic_dir, "js", "cinematic_app.js"),
            os.path.join(self.docs_dir, "cinematic_replay_baseline.md"),
            os.path.join(self.docs_dir, "cinematic_replay_data_sources_and_assumptions.md"),
            os.path.join(self.docs_dir, "cinematic_replay_camera_and_event_timeline.md"),
        ]

        for path in required_files:
            self.assertTrue(os.path.isfile(path), f"Missing required file: {path}")
            self.assertGreater(os.path.getsize(path), 0, f"File is empty: {path}")

    def test_02_minimal_additive_navigation(self):
        """2. Verify index.html contains an additive link to replay.html without altering existing tabs."""
        index_path = os.path.join(self.static_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("replay.html", content, "Link to replay.html missing in index.html")
        self.assertIn("CINEMATIC REPLAY", content, "Cinematic replay nav text missing in index.html")
        # Ensure existing tabs are intact
        self.assertIn('data-nav="overview"', content)
        self.assertIn('data-nav="3d"', content)
        self.assertIn('data-nav="telemetry"', content)
        self.assertIn('data-nav="settings"', content)

    def test_03_profile_isolation(self):
        """3. Verify strict profile isolation and parameters."""
        profiles = self.scenario_data.get("profiles", {})
        aliases = self.scenario_data.get("profile_aliases", {})

        # Verify 3 distinct profiles
        self.assertIn("observed_reconstruction", profiles)
        self.assertIn("planned_flight14", profiles)
        self.assertIn("synthetic_landing_lab", profiles)

        # Verify canonical alias mappings
        self.assertEqual(aliases.get("flight14_observed_reconstruction"), "observed_reconstruction")
        self.assertEqual(aliases.get("flight14_planned"), "planned_flight14")
        self.assertEqual(aliases.get("synthetic_engineering_test"), "synthetic_landing_lab")

        obs = profiles["observed_reconstruction"]
        planned = profiles["planned_flight14"]
        synth = profiles["synthetic_landing_lab"]

        # Synthetic must be explicitly flagged
        self.assertTrue(synth.get("is_synthetic", False))
        self.assertFalse(obs.get("is_synthetic", False))
        self.assertFalse(planned.get("is_synthetic", False))

        # Check durations
        self.assertAlmostEqual(obs["duration_s"], 11500.0, delta=600.0)
        self.assertGreaterEqual(planned["duration_s"], 30000.0)

    def test_04_starlink_satellite_manifest(self):
        """4. Verify 26 Starlink V3 satellites manifest."""
        satellites = self.scenario_data.get("satellite_manifest", [])
        self.assertEqual(len(satellites), 26, f"Expected 26 satellites, got {len(satellites)}")

        for i, s in enumerate(satellites, start=1):
            self.assertEqual(s["satellite_number"], i)
            self.assertTrue(s["id"].startswith("SAT-F14-") or s["id"].startswith("STARLINK-"))
            self.assertGreaterEqual(s["deploy_time_s"], 1320.0)
            self.assertLessEqual(s["deploy_time_s"], 1680.0)

    def test_05_camera_choreography_states(self):
        """5. Verify all 21 broadcast camera choreography states in camera_director.js."""
        director_path = os.path.join(self.cinematic_dir, "js", "camera_director.js")
        with open(director_path, "r", encoding="utf-8") as f:
            code = f.read()

        expected_states = [
            "PAD_WIDE",
            "PAD_LOW_ANGLE",
            "IGNITION_TRACK",
            "ASCENT_CHASE",
            "ASCENT_LONG_LENS",
            "STAGING_WIDE",
            "STAGING_CLOSE",
            "BOOSTER_RETURN_CHASE",
            "BOOSTER_GULF_WIDE",
            "SHIP_SPACE_CHASE",
            "ORBIT_OVERVIEW",
            "SATELLITE_DEPLOY_CLOSE",
            "SATELLITE_TRAIN_WIDE",
            "ORBITAL_EARTH_LIMB",
            "DEORBIT_CHASE",
            "ENTRY_LONG_LENS",
            "ENTRY_DRONE_TRACK",
            "PACIFIC_APPROACH",
            "SPLASHDOWN_WIDE",
            "SPLASHDOWN_WATER_LEVEL",
            "POST_SPLASHDOWN_HOLD",
        ]

        self.assertEqual(len(expected_states), 21)
        for state in expected_states:
            self.assertIn(state, code, f"State {state} missing from camera_director.js")

    def test_06_css_namespace_isolation(self):
        """6. Verify all CSS classes in cinematic_replay.css are strictly scoped under .cfr-*."""
        css_path = os.path.join(self.cinematic_dir, "css", "cinematic_replay.css")
        with open(css_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        class_selector_regex = re.compile(r"^\.([a-zA-Z0-9_\-]+)")
        for line in lines:
            line_str = line.strip()
            match = class_selector_regex.match(line_str)
            if match:
                class_name = match.group(1)
                self.assertTrue(
                    class_name.startswith("cfr-"),
                    f"Global style pollution detected: .{class_name} does not start with .cfr-",
                )

    def test_07_replay_html_dom_elements(self):
        """7. Verify critical replay HTML DOM structure and elements."""
        replay_path = os.path.join(self.static_dir, "replay.html")
        with open(replay_path, "r", encoding="utf-8") as f:
            html = f.read()

        required_ids = [
            "cfr-webgl-canvas",
            "cfr-clock-display",
            "cfr-synthetic-banner",
            "cfr-chapter-ribbon",
            "cfr-m-alt",
            "cfr-m-vel",
            "cfr-m-q",
            "cfr-m-heat",
            "cfr-m-g",
            "cfr-m-thrust",
            "cfr-m-mass",
            "cfr-m-pitch",
            "cfr-sat-count",
            "cfr-lt-title",
            "cfr-lt-desc",
            "cfr-timeline-scrub",
            "cfr-btn-play",
            "cfr-btn-restart",
            "cfr-camera-select",
            "cfr-mission-complete-modal",
        ]

        for element_id in required_ids:
            self.assertIn(f'id="{element_id}"', html, f'Element with id="{element_id}" missing from replay.html')


if __name__ == "__main__":
    unittest.main()
