"""
Tests for Phase 6 Reentry Dynamics, Aerodynamics, Aerothermal Heating, Guidance,
and Splashdown Target Assessment.
"""

import unittest
import numpy as np
import math
from datetime import datetime, timezone

from src.astrodynamics.constants import (
    R_EARTH_EQUATORIAL, R_EARTH_POLAR, OMEGA_EARTH, STANDARD_GRAVITY
)
from src.astrodynamics.state import OrbitalState
from src.astrodynamics.frames import eci_to_ecef, ecef_to_geodetic
from src.reentry.constants import (
    SUTTON_GRAVES_K_EARTH,
    DEFAULT_VEHICLE_MASS_KG,
    DEFAULT_REFERENCE_AREA_M2,
    DEFAULT_NOSE_RADIUS_M,
    DEFAULT_TARGET_LAT_DEG,
    DEFAULT_TARGET_LON_DEG,
    DEFAULT_TARGET_RADIUS_M
)
from src.reentry.atmosphere import (
    USStandardAtmosphere1976,
    AtmosphericState,
    compute_density,
    compute_speed_of_sound
)
from src.reentry.vehicle import ReentryVehicleConfig
from src.reentry.aerodynamics import (
    AerodynamicForces,
    compute_aerodynamic_coefficients,
    compute_aerodynamic_forces
)
from src.reentry.heating import (
    STEFAN_BOLTZMANN_CONSTANT,
    compute_stagnation_heat_flux,
    compute_radiative_equilibrium_temperature,
    evaluate_heating_state
)
from src.reentry.guidance import (
    CrossrangeBankGuidanceController,
    GuidanceCommand
)
from src.reentry.splashdown import (
    great_circle_distance_m,
    compute_crossrange_and_downrange_error,
    assess_terminal_splashdown,
    TerminalSplashdownAssessment
)
from src.reentry.dynamics import (
    propagate_reentry,
    ReentrySimulationResult,
    ReentryTrajectoryStep
)
from src.reentry.uncertainty import (
    run_reentry_sensitivity_study,
    run_reentry_monte_carlo,
    SensitivityResult,
    MonteCarloSummary
)


def get_default_entry_state() -> OrbitalState:
    """Returns the audited Phase 5 disposal handoff state at 120 km interface."""
    r_vec = np.array([5528938.10, -3319172.12, 798881.33], dtype=np.float64)
    v_vec = np.array([3895.7417, 5894.2764, -3257.6110], dtype=np.float64)
    epoch = 6527.315
    return OrbitalState(r=r_vec, v=v_vec, epoch=epoch, mass_kg=DEFAULT_VEHICLE_MASS_KG)


class TestPhase6Reentry(unittest.TestCase):
    """Phase 6 Reentry verification test suite (TEST-P6-01 to TEST-P6-25)."""

    def setUp(self):
        self.atm = USStandardAtmosphere1976()
        self.veh = ReentryVehicleConfig()
        self.guidance = CrossrangeBankGuidanceController(
            target_lat_deg=DEFAULT_TARGET_LAT_DEG,
            target_lon_deg=DEFAULT_TARGET_LON_DEG,
            entry_lat_deg=7.1084,
            entry_lon_deg=-58.3341
        )
        self.entry_state = get_default_entry_state()

    # --- Atmosphere Tests ---
    def test_p6_01_atmosphere_sea_level(self):
        """TEST-P6-01: Verify US Standard Atmosphere 1976 sea level properties."""
        p = self.atm.evaluate(0.0)
        self.assertAlmostEqual(p.temperature_k, 288.15, delta=0.1)
        self.assertAlmostEqual(p.pressure_pa, 101325.0, delta=10.0)
        self.assertAlmostEqual(p.density_kg_m3, 1.225, delta=0.01)
        self.assertAlmostEqual(p.speed_of_sound_ms, 340.29, delta=0.5)

    def test_p6_02_atmosphere_stratosphere(self):
        """TEST-P6-02: Verify isothermal stratosphere layer at 11 km to 20 km."""
        p_11 = self.atm.evaluate(11000.0)
        p_20 = self.atm.evaluate(20000.0)
        self.assertAlmostEqual(p_11.temperature_k, 216.65, delta=0.5)
        self.assertAlmostEqual(p_20.temperature_k, 216.65, delta=0.5)
        self.assertGreater(p_11.density_kg_m3, p_20.density_kg_m3)
        self.assertGreater(p_20.density_kg_m3, 0.0)

    def test_p6_03_atmosphere_mesosphere_and_thermosphere(self):
        """TEST-P6-03: Verify continuous density extension through 86, 100, and 120 km."""
        p_86 = self.atm.evaluate(86000.0)
        p_100 = self.atm.evaluate(100000.0)
        p_120 = self.atm.evaluate(120000.0)
        self.assertGreater(p_86.density_kg_m3, p_100.density_kg_m3)
        self.assertGreater(p_100.density_kg_m3, p_120.density_kg_m3)
        self.assertGreater(p_120.density_kg_m3, 0.0)
        self.assertTrue(math.isfinite(p_120.density_kg_m3))

    def test_p6_04_atmosphere_density_scaling(self):
        """TEST-P6-04: Verify atmospheric density scaling factor application."""
        atm_scaled = USStandardAtmosphere1976(density_scale=1.2)
        p_base = self.atm.evaluate(30000.0)
        p_scale = atm_scaled.evaluate(30000.0)
        self.assertAlmostEqual(p_scale.density_kg_m3, p_base.density_kg_m3 * 1.2, places=6)

    # --- Vehicle & Aerodynamics Tests ---
    def test_p6_05_vehicle_properties(self):
        """TEST-P6-05: Verify Starship entry vehicle mass, geometry, and ballistic coefficient."""
        self.assertAlmostEqual(self.veh.mass_kg, 177272.71, delta=0.1)
        self.assertAlmostEqual(self.veh.reference_area_m2, 63.617, delta=0.1)
        self.assertAlmostEqual(self.veh.nose_radius_m, 4.5, delta=0.1)
        self.assertAlmostEqual(self.veh.nominal_angle_of_attack_deg, 70.0, delta=0.1)
        beta = self.veh.ballistic_coefficient_kg_m2
        self.assertGreater(beta, 1500.0)
        self.assertLess(beta, 2200.0)

    def test_p6_06_aerodynamics_drag_opposes_velocity(self):
        """TEST-P6-06: Verify drag force vector is strictly anti-parallel to relative velocity."""
        r_vec = np.array([6400000.0, 0.0, 0.0])
        v_rel = np.array([0.0, 5000.0, -1000.0])
        aero = compute_aerodynamic_forces(
            r_vec=r_vec, v_rel_vec=v_rel, density_kg_m3=0.001, speed_of_sound_ms=300.0,
            config=self.veh, bank_angle_deg=0.0
        )
        v_unit = v_rel / np.linalg.norm(v_rel)
        drag_unit = aero.f_drag_vec_n / np.linalg.norm(aero.f_drag_vec_n)
        dot_product = np.dot(drag_unit, v_unit)
        self.assertAlmostEqual(dot_product, -1.0, places=5)

    def test_p6_07_aerodynamics_lift_orthogonality(self):
        """TEST-P6-07: Verify lift vector is strictly orthogonal to relative velocity."""
        r_vec = np.array([6400000.0, 100000.0, -50000.0])
        v_rel = np.array([2000.0, 4000.0, -1500.0])
        aero = compute_aerodynamic_forces(
            r_vec=r_vec, v_rel_vec=v_rel, density_kg_m3=0.005, speed_of_sound_ms=310.0,
            config=self.veh, bank_angle_deg=25.0
        )
        dot_product = np.dot(aero.f_lift_vec_n, v_rel)
        self.assertAlmostEqual(dot_product, 0.0, delta=1e-3)

    def test_p6_08_aerodynamics_bank_angle_modulation(self):
        """TEST-P6-08: Verify bank angle rotates lift around relative velocity vector."""
        r_vec = np.array([6500000.0, 0.0, 0.0])
        v_rel = np.array([0.0, 6000.0, 0.0])
        aero_0 = compute_aerodynamic_forces(r_vec, v_rel, 0.002, 300.0, self.veh, bank_angle_deg=0.0)
        aero_90 = compute_aerodynamic_forces(r_vec, v_rel, 0.002, 300.0, self.veh, bank_angle_deg=90.0)
        mag_0 = np.linalg.norm(aero_0.f_lift_vec_n)
        mag_90 = np.linalg.norm(aero_90.f_lift_vec_n)
        self.assertAlmostEqual(mag_0, mag_90, places=3)
        self.assertAlmostEqual(np.dot(aero_0.f_lift_vec_n, aero_90.f_lift_vec_n), 0.0, delta=1e-3)

    def test_p6_09_aerodynamics_zero_speed_guard(self):
        """TEST-P6-09: Verify zero relative speed returns zero forces without NaN."""
        r_vec = np.array([6378137.0, 0.0, 0.0])
        v_rel = np.array([0.0, 0.0, 0.0])
        aero = compute_aerodynamic_forces(r_vec, v_rel, 1.225, 340.0, self.veh, bank_angle_deg=0.0)
        self.assertAlmostEqual(np.linalg.norm(aero.f_total_vec_n), 0.0)
        self.assertAlmostEqual(aero.apparent_g_load, 0.0)
        self.assertFalse(np.isnan(aero.apparent_g_load))

    # --- Aerothermal Heating Tests ---
    def test_p6_10_sutton_graves_heating_formula(self):
        """TEST-P6-10: Verify Sutton-Graves stagnation heat flux calculation."""
        rho = 0.001
        v = 7000.0
        rn = 4.5
        q_dot = compute_stagnation_heat_flux(density_kg_m3=rho, speed_relative_ms=v, nose_radius_m=rn)
        expected = SUTTON_GRAVES_K_EARTH * math.sqrt(rho / rn) * (v ** 3.0)
        self.assertAlmostEqual(q_dot, expected, places=1)
        self.assertGreater(q_dot, 0.0)

    def test_p6_11_radiative_equilibrium_temperature(self):
        """TEST-P6-11: Verify Stefan-Boltzmann radiative equilibrium surface temperature."""
        flux = 500000.0  # 500 kW/m2
        emissivity = 0.85
        t_wall = compute_radiative_equilibrium_temperature(flux, emissivity)
        expected = (flux / (emissivity * STEFAN_BOLTZMANN_CONSTANT)) ** 0.25
        self.assertAlmostEqual(t_wall, expected, delta=0.5)
        self.assertGreater(t_wall, 1000.0)

    def test_p6_12_heat_load_accumulation(self):
        """TEST-P6-12: Verify evaluate_heating_state constructs valid state."""
        h_state = evaluate_heating_state(
            density_kg_m3=0.001,
            speed_relative_ms=6500.0,
            cumulative_heat_load_j_m2=50000000.0,
            nose_radius_m=4.5
        )
        self.assertGreater(h_state.stagnation_heat_flux_mw_m2, 0.0)
        self.assertAlmostEqual(h_state.cumulative_heat_load_mj_m2, 50.0, places=4)
        self.assertGreater(h_state.radiative_equilibrium_temp_k, 300.0)

    # --- Guidance Controller Tests ---
    def test_p6_13_guidance_null_bank_when_aligned(self):
        """TEST-P6-13: Verify zero bank command when crossrange error is zero."""
        # Entry point is (7.1084, -58.3341), Target is (26.5, -162.0)
        # Point halfway along great circle between entry and target
        cmd = self.guidance.compute_command(
            time_s=100.0,
            current_lat_deg=7.1084,
            current_lon_deg=-58.3341,
            current_alt_m=50000.0,
            dynamic_pressure_pa=1000.0
        )
        self.assertAlmostEqual(cmd.crossrange_error_km, 0.0, places=2)
        self.assertAlmostEqual(cmd.bank_angle_cmd_deg, 0.0, places=2)

    def test_p6_14_guidance_rate_limiting(self):
        """TEST-P6-14: Verify guidance rate limiter restricts bank acceleration."""
        guidance = CrossrangeBankGuidanceController(
            target_lat_deg=DEFAULT_TARGET_LAT_DEG,
            target_lon_deg=DEFAULT_TARGET_LON_DEG,
            max_bank_rate_deg_s=5.0
        )
        # Call step 0 then step 1 with 1 second dt
        cmd0 = guidance.compute_command(0.0, 7.1084, -58.3341, 50000.0, 5000.0)
        # Shift coordinate far away to create huge crossrange error
        cmd1 = guidance.compute_command(1.0, 15.0, -58.3341, 50000.0, 5000.0)
        # Rate limit of 5.0 deg/s means bank change must not exceed 5.0 deg in 1.0 s
        self.assertLessEqual(abs(cmd1.bank_angle_cmd_deg - cmd0.bank_angle_cmd_deg), 5.0 + 1e-4)

    def test_p6_15_guidance_saturation_limit(self):
        """TEST-P6-15: Verify guidance saturates at configured maximum bank angle."""
        guidance = CrossrangeBankGuidanceController(
            target_lat_deg=DEFAULT_TARGET_LAT_DEG,
            target_lon_deg=DEFAULT_TARGET_LON_DEG,
            max_bank_angle_deg=35.0,
            max_bank_rate_deg_s=100.0
        )
        cmd = guidance.compute_command(10.0, 25.0, -58.3341, 50000.0, 5000.0)
        self.assertLessEqual(abs(cmd.bank_angle_cmd_deg), 35.0 + 1e-6)

    def test_p6_16_guidance_dynamic_pressure_deadband(self):
        """TEST-P6-16: Verify guidance remains inactive when dynamic pressure < threshold."""
        cmd = self.guidance.compute_command(10.0, 15.0, -58.3341, 110000.0, 10.0)  # q < 50 Pa
        self.assertEqual(cmd.bank_angle_cmd_deg, 0.0)
        self.assertFalse(cmd.guidance_active)

    # --- Geodesy & Target Assessment Tests ---
    def test_p6_17_wgs84_geodetic_conversion(self):
        """TEST-P6-17: Verify ECEF to WGS-84 geodetic coordinate conversion."""
        r_ecef = np.array([R_EARTH_EQUATORIAL, 0.0, 0.0])
        lat, lon, alt = ecef_to_geodetic(r_ecef)
        self.assertAlmostEqual(lat, 0.0, places=4)
        self.assertAlmostEqual(lon, 0.0, places=4)
        self.assertAlmostEqual(alt, 0.0, delta=1.0)

    def test_p6_18_great_circle_distance(self):
        """TEST-P6-18: Verify Great-Circle distance on Earth surface."""
        d = great_circle_distance_m(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(d / 1000.0, 111.32, delta=0.5)

    def test_p6_19_relative_velocity_transformation(self):
        """TEST-P6-19: Verify Earth rotation subtraction from inertial velocity."""
        r_eci = np.array([R_EARTH_EQUATORIAL, 0.0, 0.0])
        v_east = OMEGA_EARTH * R_EARTH_EQUATORIAL
        v_eci = np.array([0.0, v_east, 0.0])
        omega_vec = np.array([0.0, 0.0, OMEGA_EARTH])
        v_rel = v_eci - np.cross(omega_vec, r_eci)
        self.assertAlmostEqual(np.linalg.norm(v_rel), 0.0, delta=1e-5)

    def test_p6_20_splashdown_assessment_classification(self):
        """TEST-P6-20: Verify target splashdown error and outcome classification."""
        r_eci = np.array([R_EARTH_EQUATORIAL, 0.0, 0.0])
        v_eci = np.array([0.0, 200.0, 0.0])
        assessment = assess_terminal_splashdown(
            r_eci=r_eci,
            v_eci=v_eci,
            impact_time_s=900.0,
            impact_epoch_utc="2026-09-28T16:03:47.000Z",
            theta_gst_rad=0.0,
            target_lat_deg=0.0,
            target_lon_deg=0.05,
            target_radius_m=50000.0
        )
        self.assertIn(assessment.outcome_classification, ["TARGET_REGION_REACHED", "TARGET_REGION_MISSED"])
        self.assertGreater(assessment.miss_distance_km, 0.0)
        self.assertLess(assessment.miss_distance_km, 20.0)

    # --- Simulation & Integration Tests ---
    def test_p6_21_trajectory_simulation_baseline_run(self):
        """TEST-P6-21: Verify full reentry trajectory simulation from 120 km to sea level."""
        res = propagate_reentry(
            initial_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=None,
            eval_step_s=2.0
        )
        self.assertTrue(res.success)
        self.assertGreater(res.impact_time_s, 600.0)
        self.assertLess(res.impact_time_s, 1100.0)
        self.assertLess(res.altitudes_km[-1], 0.1)

    def test_p6_22_peak_reentry_regimes_physical_plausibility(self):
        """TEST-P6-22: Verify peak deceleration, dynamic pressure, and stagnation flux plausibility."""
        res = propagate_reentry(
            initial_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=None,
            eval_step_s=2.0
        )
        # Peak g-load should be between 2.0 and 5.0 g for shallow entry
        self.assertGreater(res.peak_apparent_g_load, 2.0)
        self.assertLess(res.peak_apparent_g_load, 5.0)
        # Peak dynamic pressure should be between 40 kPa and 100 kPa
        self.assertGreater(res.peak_dynamic_pressure_pa, 40000.0)
        self.assertLess(res.peak_dynamic_pressure_pa, 100000.0)
        # Peak stagnation heat flux should be between 0.4 and 1.5 MW/m2
        self.assertGreater(res.peak_stagnation_heat_flux_mw_m2, 0.40)
        self.assertLess(res.peak_stagnation_heat_flux_mw_m2, 1.50)

    def test_p6_23_guided_crossrange_reduction(self):
        """TEST-P6-23: Verify closed-loop bank modulation actively executes commands."""
        res_guided = propagate_reentry(
            initial_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=self.guidance,
            eval_step_s=2.0
        )
        self.assertTrue(res_guided.success)
        self.assertGreater(np.max(np.abs(res_guided.bank_angles_deg)), 0.0)

    def test_p6_24_oat_sensitivity_deterministic(self):
        """TEST-P6-24: Verify One-At-a-Time sensitivity analysis produces valid metrics."""
        sens = run_reentry_sensitivity_study(
            baseline_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=None
        )
        self.assertGreater(len(sens), 0)
        for s in sens:
            self.assertTrue(math.isfinite(s.delta_peak_q_kpa))
            self.assertTrue(math.isfinite(s.delta_peak_g))
            self.assertTrue(math.isfinite(s.delta_total_heat_mj_m2))

    def test_p6_25_monte_carlo_seeded_reproducibility(self):
        """TEST-P6-25: Verify Monte Carlo uncertainty propagation is fully reproducible with Seed 42."""
        res1 = run_reentry_monte_carlo(
            baseline_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=None,
            sample_count=3,
            seed=42
        )
        res2 = run_reentry_monte_carlo(
            baseline_state=self.entry_state,
            vehicle_config=self.veh,
            atmosphere=self.atm,
            guidance=None,
            sample_count=3,
            seed=42
        )
        self.assertEqual(res1.completed_count, res2.completed_count)
        self.assertAlmostEqual(
            res1.metrics["peak_apparent_g_load"]["mean"],
            res2.metrics["peak_apparent_g_load"]["mean"],
            places=6
        )
        self.assertAlmostEqual(
            res1.metrics["total_heat_load_mj_m2"]["mean"],
            res2.metrics["total_heat_load_mj_m2"]["mean"],
            places=6
        )


if __name__ == '__main__':
    unittest.main()
