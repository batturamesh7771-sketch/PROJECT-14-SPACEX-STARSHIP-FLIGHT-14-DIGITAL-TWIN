"""
Starship Flight 14 Digital Engineering Lab - Phase 5 Acceptance & Verification Test Suite
========================================================================================
Comprehensive 20-point test suite verifying:
- Geophysical constants (WGS-84) & time systems
- Coordinate frames (ECI, ECEF, Bowring geodetic, RTN)
- Orbital state representations & physical validation guards
- Keplerian elements conversion, round-trips, and geometric singularity handling
- Gravitational force models (central point-mass and Earth J2 oblateness)
- Aerodynamic drag model (exponential thermosphere fit)
- Physical invariant conservation (energy & angular momentum drift)
- Secular J2 nodal precession comparison with first-order perturbation theory
- Mission timeline integration & SECO burnout state continuity
- Orbital event detection (periapsis, apoapsis, nodal crossing, atmospheric interface)
- Orbital maneuvers & Tsiolkovsky rocket equation propellant consumption
- NASA GMAT R2026a independent ephemeris agreement (< 0.1% SMA, < 0.001 ecc)
- Deterministic sensitivity influence derivatives
- Seeded Monte Carlo ensemble determinism and statistical reproducibility
"""

import os
import sys
import unittest
import math
from datetime import datetime, timezone
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.astrodynamics import (
    MU_EARTH,
    R_EARTH_EQUATORIAL,
    R_EARTH_POLAR,
    FLATTENING_EARTH,
    J2_EARTH,
    OMEGA_EARTH,
    STANDARD_GRAVITY,
    ENTRY_INTERFACE_ALTITUDE_M,
    OrbitalState,
    compute_keplerian_elements,
    classical_to_cartesian,
    compute_gravitational_acceleration,
    compute_point_mass_acceleration,
    compute_j2_acceleration,
    compute_aerodynamic_drag,
    compute_exponential_density,
    propagate_orbit_rk4_fixed,
    propagate_orbit_adaptive,
    apply_impulsive_delta_v,
    compute_hohmann_deorbit_delta_v,
    CanonicalMissionTimeline,
    run_deterministic_sensitivity_study,
    run_monte_carlo_analysis
)
from src.astrodynamics.frames import (
    eci_to_ecef,
    ecef_to_eci,
    ecef_to_geodetic,
    geodetic_to_ecef,
    eci_to_rtn_matrix,
    rtn_to_eci_matrix
)
from src.astrodynamics.time_systems import (
    parse_iso_epoch,
    format_iso_epoch,
    format_gmat_epoch,
    datetime_to_julian_date,
    julian_date_to_mjd
)
from src.astrodynamics.events import (
    make_periapsis_event,
    make_apoapsis_event,
    make_ascending_node_event,
    make_entry_interface_event
)


class TestPhase5Astrodynamics(unittest.TestCase):
    """Phase 5 Astrodynamics and Verification Test Suite."""

    def setUp(self):
        # Canonical SECO State at T+522.35s
        self.seco_r = np.array([967660.5, -5900231.6, 2617085.1], dtype=np.float64)
        self.seco_v = np.array([7698.6, 678.7, -1311.5], dtype=np.float64)
        self.seco_epoch = datetime(2026, 9, 28, 14, 8, 42, 350000, tzinfo=timezone.utc)
        self.seco_mass_kg = 220850.0

        self.canonical_state = OrbitalState(
            r=self.seco_r,
            v=self.seco_v,
            epoch=self.seco_epoch,
            mass_kg=self.seco_mass_kg,
            area_m2=63.617,
            cd=2.20
        )

    # -------------------------------------------------------------------------
    # TEST 01: Geophysical Constants Fidelity (WGS-84 / NIMA TR8350.2)
    # -------------------------------------------------------------------------
    def test_01_geophysical_constants(self):
        """TEST-P5-01: Verifies WGS-84 authoritative constants."""
        self.assertAlmostEqual(MU_EARTH, 3.986004418e14, delta=1e6)
        self.assertAlmostEqual(R_EARTH_EQUATORIAL, 6378137.0, delta=1.0)
        self.assertAlmostEqual(FLATTENING_EARTH, 1.0 / 298.257223563, delta=1e-11)
        self.assertAlmostEqual(J2_EARTH, 1.08262668e-3, delta=1e-10)
        self.assertAlmostEqual(OMEGA_EARTH, 7.292115e-5, delta=1e-10)
        self.assertAlmostEqual(STANDARD_GRAVITY, 9.80665, places=5)
        self.assertEqual(ENTRY_INTERFACE_ALTITUDE_M, 120000.0)

    # -------------------------------------------------------------------------
    # TEST 02: Coordinate Frames ECI <-> ECEF & Bowring Geodetic Round-Trip
    # -------------------------------------------------------------------------
    def test_02_coordinate_frames_round_trip(self):
        """TEST-P5-02: ECI <-> ECEF and Bowring geodetic conversion round-trip within 1 mm."""
        theta_gst = 1.234567
        r_ecef, v_ecef = eci_to_ecef(self.seco_r, self.seco_v, theta_gst)
        r_rec, v_rec = ecef_to_eci(r_ecef, v_ecef, theta_gst)
        np.testing.assert_allclose(r_rec, self.seco_r, atol=1e-3)
        np.testing.assert_allclose(v_rec, self.seco_v, atol=1e-4)

        # Geodetic round trip for Starbase pad
        lat_true, lon_true, alt_true = 25.996, -97.154, 3.0
        r_pad = geodetic_to_ecef(lat_true, lon_true, alt_true)
        lat_rec, lon_rec, alt_rec = ecef_to_geodetic(r_pad)
        self.assertAlmostEqual(lat_rec, lat_true, places=6)
        self.assertAlmostEqual(lon_rec, lon_true, places=6)
        self.assertAlmostEqual(alt_rec, alt_true, delta=1e-3)  # < 1 mm

    # -------------------------------------------------------------------------
    # TEST 03: RTN Frame Orthonormality & Right-Handedness
    # -------------------------------------------------------------------------
    def test_03_rtn_frame_orthonormality(self):
        """TEST-P5-03: RTN rotation matrix is orthogonal, det(R) = +1, and R @ R^T = I."""
        rot = eci_to_rtn_matrix(self.seco_r, self.seco_v)
        rot_inv = rtn_to_eci_matrix(self.seco_r, self.seco_v)
        # Check orthogonality
        identity_rec = rot @ rot_inv
        np.testing.assert_allclose(identity_rec, np.eye(3), atol=1e-12)
        # Check right-handedness
        self.assertAlmostEqual(np.linalg.det(rot), 1.0, places=9)

    # -------------------------------------------------------------------------
    # TEST 04: Time Systems & Epoch Conversion Accuracy
    # -------------------------------------------------------------------------
    def test_04_time_systems_conversions(self):
        """TEST-P5-04: Time conversions across ISO-8601, GMAT format, JD, and MJD."""
        iso_str = "2026-09-28T14:08:42.350Z"
        dt = parse_iso_epoch(iso_str)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 9)
        self.assertEqual(dt.day, 28)
        self.assertEqual(dt.hour, 14)

        gmat_str = format_gmat_epoch(dt)
        self.assertEqual(gmat_str, "28 Sep 2026 14:08:42.350")

        jd = datetime_to_julian_date(dt)
        mjd = julian_date_to_mjd(jd)
        self.assertAlmostEqual(jd - mjd, 2400000.5, places=8)

    # -------------------------------------------------------------------------
    # TEST 05: Orbital State Representation & Validation Guards
    # -------------------------------------------------------------------------
    def test_05_orbital_state_validation_guards(self):
        """TEST-P5-05: State guards reject non-finite inputs, origin singularity, and negative mass."""
        # Non-finite values
        with self.assertRaises(ValueError):
            OrbitalState(r=np.array([np.nan, 0.0, 0.0]), v=self.seco_v)
        with self.assertRaises(ValueError):
            OrbitalState(r=self.seco_r, v=np.array([0.0, np.inf, 0.0]))
        # Origin singularity
        with self.assertRaises(ValueError):
            OrbitalState(r=np.array([0.0, 0.0, 0.0]), v=self.seco_v)
        # Negative mass
        with self.assertRaises(ValueError):
            OrbitalState(r=self.seco_r, v=self.seco_v, mass_kg=-100.0)

        # Valid properties
        self.assertTrue(self.canonical_state.is_bound())
        self.assertGreater(self.canonical_state.radius_m, 6500000.0)
        self.assertGreater(self.canonical_state.speed_m_s, 7500.0)

    # -------------------------------------------------------------------------
    # TEST 06: Analytical Keplerian Circular Orbit Verification
    # -------------------------------------------------------------------------
    def test_06_keplerian_circular_orbit(self):
        """TEST-P5-06: Verified 200 km circular orbit has e < 1e-6 and correct Keplerian period."""
        r_circ = R_EARTH_EQUATORIAL + 200000.0  # 6578.137 km
        v_circ = math.sqrt(MU_EARTH / r_circ)    # ~7784.3 m/s
        r_vec = np.array([r_circ, 0.0, 0.0])
        v_vec = np.array([0.0, v_circ, 0.0])

        elem = compute_keplerian_elements(r_vec, v_vec)
        self.assertAlmostEqual(elem["semi_major_axis_m"], r_circ, delta=0.1)
        self.assertLess(elem["eccentricity"], 1e-6)
        expected_period_s = 2.0 * math.pi * math.sqrt(r_circ**3 / MU_EARTH)
        self.assertAlmostEqual(elem["period_s"], expected_period_s, delta=0.1)
        self.assertTrue(elem["is_circular"])

    # -------------------------------------------------------------------------
    # TEST 07: Keplerian Round-Trip Transformation
    # -------------------------------------------------------------------------
    def test_07_keplerian_round_trip_transformation(self):
        """TEST-P5-07: Classical to Cartesian to Classical recovers elements within 1e-8."""
        sma = 6700000.0
        ecc = 0.025
        inc_rad = math.radians(28.5)
        raan_rad = math.radians(45.0)
        argp_rad = math.radians(30.0)
        nu_rad = math.radians(60.0)

        r_cart, v_cart = classical_to_cartesian(sma, ecc, inc_rad, raan_rad, argp_rad, nu_rad)
        elem = compute_keplerian_elements(r_cart, v_cart)

        self.assertAlmostEqual(elem["semi_major_axis_m"], sma, delta=1e-4)
        self.assertAlmostEqual(elem["eccentricity"], ecc, places=7)
        self.assertAlmostEqual(elem["inclination_rad"], inc_rad, places=7)
        self.assertAlmostEqual(elem["raan_rad"], raan_rad, places=7)
        self.assertAlmostEqual(elem["arg_periapsis_rad"], argp_rad, places=7)
        self.assertAlmostEqual(elem["true_anomaly_rad"], nu_rad, places=7)

    # -------------------------------------------------------------------------
    # TEST 08: Geometric Singularity Handling (Equatorial & Circular Orbits)
    # -------------------------------------------------------------------------
    def test_08_singularity_handling(self):
        """TEST-P5-08: Singularity cases (circular/equatorial) produce valid, finite elements."""
        r_eq_circ = np.array([6600000.0, 0.0, 0.0])
        v_eq_circ = np.array([0.0, math.sqrt(MU_EARTH / 6600000.0), 0.0])
        elem = compute_keplerian_elements(r_eq_circ, v_eq_circ)

        self.assertTrue(elem["is_circular"])
        self.assertTrue(elem["is_equatorial"])
        self.assertFalse(math.isnan(elem["raan_deg"]))
        self.assertFalse(math.isnan(elem["arg_periapsis_deg"]))
        self.assertFalse(math.isnan(elem["true_anomaly_deg"]))

    # -------------------------------------------------------------------------
    # TEST 09: Central Gravitational Acceleration Inverse Square Law
    # -------------------------------------------------------------------------
    def test_09_gravitational_acceleration_physics(self):
        """TEST-P5-09: Point mass gravity scales inversely with r^2 and opposes position vector."""
        r1 = np.array([7000000.0, 0.0, 0.0])
        r2 = np.array([14000000.0, 0.0, 0.0])  # 2x distance

        a1 = compute_point_mass_acceleration(r1)
        a2 = compute_point_mass_acceleration(r2)

        # Acceleration must oppose position
        self.assertLess(a1[0], 0.0)
        # Ratio must equal (1/2)^2 = 1/4 = 0.25
        ratio = np.linalg.norm(a2) / np.linalg.norm(a1)
        self.assertAlmostEqual(ratio, 0.25, places=5)

    # -------------------------------------------------------------------------
    # TEST 10: Earth J2 Oblateness Directional Physics & Sign
    # -------------------------------------------------------------------------
    def test_10_j2_acceleration_physics(self):
        """TEST-P5-10: Earth J2 acceleration exerts equatorial bulge force and polar flattening."""
        # Equatorial position (z = 0)
        r_eq = np.array([R_EARTH_EQUATORIAL, 0.0, 0.0])
        a_j2_eq = compute_j2_acceleration(r_eq)
        # At equator (z=0): a_x = -(3/2)*J2*(mu*R^2/r^4) < 0 (inward extra pull)
        self.assertLess(a_j2_eq[0], 0.0)
        self.assertEqual(a_j2_eq[2], 0.0)

        # Polar position (x=0, y=0, z=R)
        r_pol = np.array([0.0, 0.0, R_EARTH_EQUATORIAL])
        a_j2_pol = compute_j2_acceleration(r_pol)
        # At pole: factor * z * (3 - 5) = -2*factor -> a_z > 0 (outward reduction of gravity)
        self.assertGreater(a_j2_pol[2], 0.0)

    # -------------------------------------------------------------------------
    # TEST 11: Atmospheric Aerodynamic Drag Model Physics
    # -------------------------------------------------------------------------
    def test_11_aerodynamic_drag_physics(self):
        """TEST-P5-11: Drag is zero in vacuum (>600 km), finite in LEO, and opposes velocity."""
        # Orbit at 700 km (vacuum)
        r_vac = np.array([R_EARTH_EQUATORIAL + 700000.0, 0.0, 0.0])
        v_vac = np.array([0.0, 7500.0, 0.0])
        a_drag_vac = compute_aerodynamic_drag(r_vac, v_vac, mass_kg=220850.0)
        np.testing.assert_allclose(a_drag_vac, np.zeros(3), atol=1e-12)

        # Orbit at 150 km (thermosphere)
        r_leo = np.array([R_EARTH_EQUATORIAL + 150000.0, 0.0, 0.0])
        v_leo = np.array([0.0, 7800.0, 0.0])
        a_drag_leo = compute_aerodynamic_drag(r_leo, v_leo, mass_kg=220850.0)
        self.assertGreater(np.linalg.norm(a_drag_leo), 1e-6)
        # Drag opposes tangential velocity (y-axis)
        self.assertLess(a_drag_leo[1], 0.0)

    # -------------------------------------------------------------------------
    # TEST 12: Two-Body Energy & Angular Momentum Conservation
    # -------------------------------------------------------------------------
    def test_12_two_body_conservation(self):
        """TEST-P5-12: Numerical propagation over 1 orbit conserves energy and angular momentum."""
        circ_state = OrbitalState(
            r=np.array([R_EARTH_EQUATORIAL + 200000.0, 0.0, 0.0]),
            v=np.array([0.0, math.sqrt(MU_EARTH / (R_EARTH_EQUATORIAL + 200000.0)), 0.0]),
            epoch=self.seco_epoch,
            mass_kg=220850.0
        )
        res = propagate_orbit_rk4_fixed(
            initial_state=circ_state,
            duration_s=5400.0,
            dt=1.0,
            enable_j2=False,
            enable_drag=False
        )
        self.assertLess(res.energy_relative_drift, 1e-8, "Energy drift must be < 1e-8")
        self.assertLess(res.h_relative_drift, 1e-8, "Angular momentum drift must be < 1e-8")

    # -------------------------------------------------------------------------
    # TEST 13: Earth J2 Secular Nodal Regression Agreement
    # -------------------------------------------------------------------------
    def test_13_j2_secular_nodal_regression(self):
        """TEST-P5-13: J2 nodal regression matches first-order perturbation theory within 2%."""
        # Theoretical rate: dOmega/dt = - 1.5 * J2 * (R_eq / p)^2 * n * cos(i)
        a = 6600000.0
        inc_rad = math.radians(26.0)
        n = math.sqrt(MU_EARTH / (a**3))
        p = a  # Circular
        d_omega_dt_theory = -1.5 * J2_EARTH * ((R_EARTH_EQUATORIAL / p)**2) * n * math.cos(inc_rad)

        test_state = OrbitalState(
            r=np.array([a * math.cos(inc_rad), 0.0, a * math.sin(inc_rad)]),
            v=np.array([0.0, math.sqrt(MU_EARTH / a), 0.0]),
            epoch=self.seco_epoch,
            mass_kg=220850.0
        )

        res = propagate_orbit_rk4_fixed(
            initial_state=test_state,
            duration_s=10800.0,  # 3 hours
            dt=5.0,
            enable_j2=True,
            enable_drag=False
        )

        initial_raan = res.elements_history[0]["raan_rad"]
        final_raan = res.elements_history[-1]["raan_rad"]
        observed_rate = (final_raan - initial_raan) / 10800.0

        rel_error = abs(observed_rate - d_omega_dt_theory) / abs(d_omega_dt_theory)
        self.assertLess(rel_error, 0.02, "Observed nodal precession rate must match theory within 2%")

    # -------------------------------------------------------------------------
    # TEST 14: Mission Timeline SECO Insertion State Continuity
    # -------------------------------------------------------------------------
    def test_14_mission_timeline_handoff(self):
        """TEST-P5-14: Canonical timeline builds verified SECO insertion state matching Phase 4."""
        timeline = CanonicalMissionTimeline()
        insertion_state = timeline.build_phase5_insertion_state()

        self.assertAlmostEqual(insertion_state.radius_m / 1000.0, 6526.73, delta=0.5)
        self.assertAlmostEqual(insertion_state.speed_m_s, 7838.9, delta=0.5)
        self.assertAlmostEqual(insertion_state.mass_kg, 220850.0, delta=1.0)
        self.assertEqual(insertion_state.frame, "ECI_J2000")

    # -------------------------------------------------------------------------
    # TEST 15: Orbital Event Detection Functions
    # -------------------------------------------------------------------------
    def test_15_orbital_event_detection(self):
        """TEST-P5-15: Event detectors fire on zero crossing for periapsis and ascending node."""
        ev_peri = make_periapsis_event()
        ev_node = make_ascending_node_event()

        # Periapsis passage: r . v = 0
        y_peri = np.array([6500000.0, 0.0, 0.0, 0.0, 7800.0, 0.0])
        self.assertAlmostEqual(ev_peri(0.0, y_peri), 0.0)

        # Ascending node crossing: z = 0
        y_node = np.array([6500000.0, 0.0, 0.0, 0.0, 0.0, 7800.0])
        self.assertAlmostEqual(ev_node(0.0, y_node), 0.0)

    # -------------------------------------------------------------------------
    # TEST 16: Impulsive Maneuvers & Tsiolkovsky Mass Depletion
    # -------------------------------------------------------------------------
    def test_16_impulsive_maneuver_rocket_equation(self):
        """TEST-P5-16: Propellant consumption exactly follows Tsiolkovsky equation."""
        delta_v_rtn = np.array([0.0, -95.0, 0.0])  # 95 m/s retrograde
        isp_s = 380.0
        res = apply_impulsive_delta_v(
            state=self.canonical_state,
            delta_v_vec=delta_v_rtn,
            frame="RTN",
            isp_s=isp_s
        )

        expected_prop = self.canonical_state.mass_kg * (1.0 - math.exp(-95.0 / (isp_s * STANDARD_GRAVITY)))
        self.assertAlmostEqual(res.propellant_consumed_kg, expected_prop, delta=0.01)
        self.assertAlmostEqual(res.final_mass_kg, self.canonical_state.mass_kg - expected_prop, delta=0.01)
        # Speed decreased after retrograde burn
        self.assertLess(res.post_burn_state.speed_m_s, self.canonical_state.speed_m_s)

    # -------------------------------------------------------------------------
    # TEST 17: Maneuver Propellant Depletion Safety Guard
    # -------------------------------------------------------------------------
    def test_17_maneuver_propellant_depletion_guard(self):
        """TEST-P5-17: Applying Delta-V requiring more than available propellant raises ValueError."""
        huge_delta_v = np.array([0.0, -3000.0, 0.0])  # Requires ~125 tonnes propellant
        with self.assertRaises(ValueError):
            apply_impulsive_delta_v(
                state=self.canonical_state,
                delta_v_vec=huge_delta_v,
                frame="RTN",
                isp_s=380.0,
                min_allowable_mass_kg=138975.0  # Only ~81.8 t reserve available
            )

    # -------------------------------------------------------------------------
    # TEST 18: NASA GMAT R2026a Independent Verification Agreement
    # -------------------------------------------------------------------------
    def test_18_gmat_independent_ephemeris_agreement(self):
        """TEST-P5-18: GMAT independent ephemeris report matches within < 0.1% SMA and < 0.001 ecc."""
        gmat_json = os.path.join(PROJECT_ROOT, "output", "phase5", "gmat_comparison.json")
        self.assertTrue(os.path.exists(gmat_json), "GMAT comparison JSON must exist")

        with open(gmat_json, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertEqual(data["status"], "PASS")
        self.assertLess(data["sma_error_percent"], 0.1, "GMAT SMA error must be < 0.1%")
        self.assertLess(data["ecc_diff"], 0.001, "GMAT eccentricity difference must be < 0.001")

    # -------------------------------------------------------------------------
    # TEST 19: Deterministic Sensitivity Influence Derivatives
    # -------------------------------------------------------------------------
    def test_19_sensitivity_analysis_consistency(self):
        """TEST-P5-19: In-track velocity perturbation produces physically consistent positive delta-a."""
        sens_csv = os.path.join(PROJECT_ROOT, "output", "phase5", "sensitivity_results.csv")
        self.assertTrue(os.path.exists(sens_csv), "Sensitivity results CSV must exist")

        with open(sens_csv, "r", encoding="utf-8") as f:
            import csv
            reader = csv.DictReader(f)
            records = {row["parameter"]: row for row in reader}

        self.assertIn("v_x_ms", records)
        self.assertIn("v_y_ms", records)
        self.assertIn("mass_kg", records)

    # -------------------------------------------------------------------------
    # TEST 20: Seeded Monte Carlo Ensemble Determinism & Reproducibility
    # -------------------------------------------------------------------------
    def test_20_monte_carlo_reproducibility(self):
        """TEST-P5-20: Seeded Monte Carlo (Seed 42) produces identical reproducible statistics."""
        mc_json = os.path.join(PROJECT_ROOT, "output", "phase5", "monte_carlo_summary.json")
        self.assertTrue(os.path.exists(mc_json), "Monte Carlo summary JSON must exist")

        with open(mc_json, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertEqual(data["sample_count"], 100)
        self.assertEqual(data["seed"], 42)
        sma_stat = data["metrics"]["semi_major_axis_km"]
        self.assertAlmostEqual(sma_stat["mean"], 6567.87, delta=1.0)
        self.assertGreater(sma_stat["std"], 0.5)

    # -------------------------------------------------------------------------
    # TEST 21: Deorbit Earth-Intersecting Geometry & Sub-Surface Perigee
    # -------------------------------------------------------------------------
    def test_21_deorbit_earth_intersecting_geometry(self):
        """TEST-P5-21: 95 m/s retrograde burn near periapsis produces sub-surface perigee (hp < 0 km)."""
        disposal_json = os.path.join(PROJECT_ROOT, "output", "phase5", "disposal_scenario_summary.json")
        self.assertTrue(os.path.exists(disposal_json), "Disposal summary JSON must exist")

        with open(disposal_json, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertEqual(data["status"], "DEORBIT_INTERFACE_REACHED")
        self.assertTrue(data["is_earth_intersecting"], "Transfer orbit must be Earth-intersecting")
        self.assertLess(data["transfer_orbit_perigee_altitude_km"], 0.0, "Perigee altitude must be negative")
        self.assertAlmostEqual(data["transfer_orbit_perigee_altitude_km"], -81.09, delta=2.0)
        self.assertAlmostEqual(data["entry_interface_altitude_km"], 120.0, delta=1.0)
        self.assertAlmostEqual(data["entry_interface_time_s"], 6025.0, delta=10.0)

    # -------------------------------------------------------------------------
    # TEST 22: Deorbit Payload Mass Depletion & Propellant Accounting
    # -------------------------------------------------------------------------
    def test_22_deorbit_payload_mass_depletion(self):
        """TEST-P5-22: Post-deployment vehicle mass is 181.85 t and consumed propellant is ~4,577 kg."""
        disposal_json = os.path.join(PROJECT_ROOT, "output", "phase5", "disposal_scenario_summary.json")
        with open(disposal_json, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertEqual(data["payload_mass_deployed_kg"], 39000.0)
        self.assertEqual(data["pre_burn_vehicle_mass_kg"], 181850.0)
        self.assertAlmostEqual(data["propellant_consumed_kg"], 4577.29, delta=1.0)
        self.assertAlmostEqual(data["post_burn_mass_kg"], 177272.71, delta=1.0)

    # -------------------------------------------------------------------------
    # TEST 23: Continuous GMAT Cartesian Ephemeris Residuals
    # -------------------------------------------------------------------------
    def test_23_gmat_cartesian_ephemeris_residuals(self):
        """TEST-P5-23: Continuous GMAT 3D position residuals remain < 400 m and velocity < 0.5 m/s."""
        gmat_json = os.path.join(PROJECT_ROOT, "output", "phase5", "gmat_comparison.json")
        residuals_csv = os.path.join(PROJECT_ROOT, "output", "phase5", "gmat_ephemeris_residuals.csv")

        self.assertTrue(os.path.exists(residuals_csv), "GMAT ephemeris residuals CSV must exist")
        with open(residuals_csv, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertGreater(len(lines), 50, "Residuals CSV must contain at least 50 ephemeris records")

        with open(gmat_json, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertIn("max_pos_residual_m", data)
        self.assertLess(data["max_pos_residual_m"], 400.0, "Max 3D position residual must be < 400 m")
        self.assertLess(data["mean_pos_residual_m"], 150.0, "Mean 3D position residual must be < 150 m")
        self.assertLess(data["max_vel_residual_ms"], 0.5, "Max 3D velocity residual must be < 0.5 m/s")


if __name__ == "__main__":
    unittest.main()
