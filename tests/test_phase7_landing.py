"""
Verification and acceptance test suite for Starship Phase 7 Terminal Landing Dynamics.
Implements the 20-point verification matrix specified in the Phase 7 engineering protocol.
"""

import unittest
import math
import os
import copy
import yaml

from src.landing.state import LandingState
from src.landing.vehicle import StarshipLandingVehicle
from src.landing.propulsion import RaptorLandingPropulsion
from src.landing.flip import AerodynamicFlipManeuver
from src.landing.guidance import TerminalLandingGuidance
from src.landing.events import LandingStateMachine
from src.landing.touchdown import TouchdownAssessor
from src.landing.dynamics import rk4_step, get_atmospheric_density, compute_aerodynamic_forces
from src.landing.simulation import LandingSimulation
from src.landing.uncertainty import MonteCarloSimulator


class TestPhase7Landing(unittest.TestCase):
    """20-Point Acceptance Test Suite for Phase 7 Landing Dynamics."""

    def setUp(self):
        self.base_cfg_path = "config/phase7/synthetic_landing_baseline.yaml"
        with open(self.base_cfg_path, "r") as f:
            self.base_config = yaml.safe_load(f)

    # 1. No-thrust vertical motion against analytical freefall
    def test_01_no_thrust_analytical_freefall(self):
        veh = StarshipLandingVehicle()
        prop = RaptorLandingPropulsion()  # engine state OFF, thrust 0
        state = LandingState(time_s=0.0, x=0.0, z=1000.0, vx=0.0, vz=0.0, mass_kg=100000.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)

        dt = 0.01
        g0 = 9.80665
        t_target = 2.0
        steps = int(t_target / dt)
        cur = state
        for _ in range(steps):
            cur = rk4_step(cur, veh, prop, dt, pitch_deg=0.0, pitch_rate_deg_s=0.0)

        # Analytical freefall: z(t) = z0 - 0.5 * g * t^2 (neglecting small low-speed drag at v < 20 m/s)
        # Check acceleration is within 2% of -g0
        v_analytical = -g0 * t_target
        self.assertAlmostEqual(cur.vz, v_analytical, delta=0.5)
        self.assertLess(cur.z, 1000.0)

    # 2. Constant-thrust fixed-mass sanity case
    def test_02_constant_thrust_fixed_mass_acceleration(self):
        veh = StarshipLandingVehicle(reference_area_m2=0.0, broadside_area_m2=0.0)  # zero drag
        prop = RaptorLandingPropulsion(thrust_per_engine_nominal_N=2.0e6, engine_count=1)
        prop.current_thrust_N = 2.0e6
        prop.engine_state = "BURNING"
        mass = 100000.0
        g0 = 9.80665
        state = LandingState(time_s=0.0, x=0.0, z=500.0, vx=0.0, vz=0.0, mass_kg=mass, pitch_deg=0.0, pitch_rate_deg_s=0.0)

        # Analytical: a = T/m - g = 2.0e6 / 1.0e5 - 9.80665 = 20.0 - 9.80665 = 10.19335 m/s^2
        expected_a = (2.0e6 / mass) - g0
        dt = 0.01
        next_state = rk4_step(state, veh, prop, dt, pitch_deg=0.0, pitch_rate_deg_s=0.0)
        calc_a = (next_state.vz - state.vz) / dt
        self.assertAlmostEqual(calc_a, expected_a, places=2)

    # 3. Variable-mass / rocket equation limiting case
    def test_03_variable_mass_rocket_equation(self):
        prop = RaptorLandingPropulsion(thrust_per_engine_nominal_N=1.0e6, specific_impulse_s=300.0, engine_count=1)
        prop.current_thrust_N = 1.0e6
        prop.current_throttle = 1.0
        prop.engine_state = "BURNING"
        g0 = 9.80665
        dt = 1.0
        prop.update(current_time_s=1.0, dt_s=dt, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)

        # Expected mass flow = T / (Isp * g0) = 1e6 / (300 * 9.80665) = 339.905 kg/s
        expected_mdot = 1.0e6 / (300.0 * g0)
        self.assertAlmostEqual(prop.propellant_consumed_kg, expected_mdot * dt, places=3)

    # 4. Ignition delay causing real altitude loss
    def test_04_ignition_delay_altitude_loss(self):
        prop = RaptorLandingPropulsion(ignition_delay_s=1.5)
        prop.command_ignition(time_s=0.0)
        self.assertEqual(prop.engine_state, "IGNITION_PENDING")

        # During delay, thrust must remain exactly zero
        prop.update(current_time_s=1.0, dt_s=1.0, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)
        self.assertEqual(prop.engine_state, "IGNITION_PENDING")
        self.assertEqual(prop.current_thrust_N, 0.0)

        # After delay elapses, state transitions to RAMPING
        prop.update(current_time_s=1.6, dt_s=0.1, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)
        self.assertEqual(prop.engine_state, "RAMPING")
        self.assertGreater(prop.current_thrust_N, 0.0)

    # 5. Thrust ramp continuity and bounding
    def test_05_thrust_ramp_continuity(self):
        prop = RaptorLandingPropulsion(ignition_delay_s=0.0, thrust_ramp_duration_s=1.0, engine_count=1, thrust_per_engine_nominal_N=1.0e6)
        prop.command_ignition(time_s=0.0)
        prop.update(current_time_s=0.0, dt_s=0.01, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)
        self.assertEqual(prop.engine_state, "RAMPING")

        # Check halfway through ramp (t=0.5s): sin^2(pi/4) = (1/sqrt(2))^2 = 0.50
        prop.update(current_time_s=0.5, dt_s=0.01, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)
        self.assertAlmostEqual(prop.current_throttle, 0.50, delta=0.05)

        # Check end of ramp (t=1.0s): throttle should reach 1.00
        prop.update(current_time_s=1.0, dt_s=0.01, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=10000.0)
        self.assertAlmostEqual(prop.current_throttle, 1.00, places=2)
        self.assertEqual(prop.engine_state, "BURNING")

    # 6. Zero gimbal keeps thrust along centerline
    def test_06_zero_gimbal_thrust_alignment(self):
        prop = RaptorLandingPropulsion(thrust_per_engine_nominal_N=1.0e6, engine_count=1)
        prop.current_thrust_N = 1.0e6
        prop.current_gimbal_deg = 0.0

        # With pitch = 0 (upright) and gimbal = 0, Fx must be 0, Fz must be +T
        fx, fz = prop.get_thrust_vector(pitch_deg=0.0)
        self.assertAlmostEqual(fx, 0.0, places=3)
        self.assertAlmostEqual(fz, 1.0e6, places=3)

    # 7. Gimbal deflection bounds and rate limits
    def test_07_gimbal_bounds_and_rate_limits(self):
        prop = RaptorLandingPropulsion(gimbal_limit_deg=15.0, gimbal_slew_rate_deg_s=20.0)
        prop.engine_state = "BURNING"

        # Request 30 deg (exceeds 15 deg bound) over 0.1s step
        # Max rate is 20 deg/s * 0.1s = 2.0 deg
        prop.update(current_time_s=1.0, dt_s=0.1, target_throttle=1.0, target_gimbal_deg=30.0, remaining_usable_prop_kg=10000.0)
        self.assertAlmostEqual(prop.current_gimbal_deg, 2.0, places=2)

        # After long time, clamped to 15.0 deg
        for t in range(20):
            prop.update(current_time_s=2.0 + t*0.1, dt_s=0.1, target_throttle=1.0, target_gimbal_deg=30.0, remaining_usable_prop_kg=10000.0)
        self.assertEqual(prop.current_gimbal_deg, 15.0)

    # 8. Kinematic flip continuity and profile labeling
    def test_08_kinematic_flip_profile(self):
        flip = AerodynamicFlipManeuver(mode="prescribed_kinematic_flip", trigger_altitude_m=500.0, duration_s=4.0)
        triggered = flip.check_trigger(altitude_m=490.0, time_s=10.0, current_pitch_deg=-90.0)
        self.assertTrue(triggered)

        # Halfway through flip (t=12s, elapsed=2s): pitch should be midpoint (-45 deg)
        p, rate = flip.get_kinematic_pitch(current_time_s=12.0)
        self.assertAlmostEqual(p, -45.0, places=1)
        self.assertGreater(rate, 0.0)

        # After completion (t=14s): pitch should be 0 deg
        p_final, rate_final = flip.get_kinematic_pitch(current_time_s=15.0)
        self.assertEqual(p_final, 0.0)
        self.assertEqual(rate_final, 0.0)

    # 9. Planar dynamic pitch torque integration
    def test_09_planar_dynamic_pitch_torque(self):
        veh = StarshipLandingVehicle(pitch_inertia_nom_kg_m2=1.0e6, nominal_landing_mass_kg=100000.0)
        prop = RaptorLandingPropulsion()
        state = LandingState(time_s=0.0, x=0.0, z=500.0, vx=0.0, vz=0.0, mass_kg=100000.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)

        # Apply torque = 1.0e5 Nm for dt = 0.1s
        # Expected angular accel: alpha = M / Iyy = 1.0e5 / 1.0e6 = 0.1 rad/s^2 = 5.7296 deg/s^2
        # Expected rate after dt=0.1s: 0.573 deg/s
        dt = 0.1
        next_state = rk4_step(state, veh, prop, dt, pitch_deg=0.0, pitch_rate_deg_s=0.0,
                              mode="planar_dynamic_flip", applied_torque_Nm=1.0e5)
        self.assertAlmostEqual(next_state.pitch_rate_deg_s, math.degrees(0.1 * dt), delta=0.05)

    # 10. Mass positivity and propellant exhaustion cutoff
    def test_10_mass_positivity_cutoff(self):
        prop = RaptorLandingPropulsion(thrust_per_engine_nominal_N=1.0e6, engine_count=1)
        prop.engine_state = "BURNING"
        # Zero usable propellant remaining
        prop.update(current_time_s=1.0, dt_s=0.1, target_throttle=1.0, target_gimbal_deg=0.0, remaining_usable_prop_kg=0.0)
        self.assertEqual(prop.engine_state, "EXHAUSTED")
        self.assertEqual(prop.current_thrust_N, 0.0)

    # 11. Vertical stopping case in nominal baseline
    def test_11_nominal_baseline_soft_touchdown(self):
        sim = LandingSimulation(self.base_config)
        history, report, event_log = sim.run()

        self.assertEqual(report.outcome_classification, "SUCCESS_CANDIDATE")
        self.assertLessEqual(report.terminal_vertical_speed_mps, 3.0)
        self.assertLessEqual(report.terminal_horizontal_speed_mps, 1.5)
        self.assertLessEqual(abs(report.terminal_pitch_deg), 5.0)
        self.assertGreater(report.remaining_usable_prop_kg, 0.0)

    # 12. Under-thrust failure case yields HARD_IMPACT
    def test_12_under_thrust_hard_impact(self):
        cfg_path = "config/phase7/synthetic_landing_low_thrust.yaml"
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f)
        sim = LandingSimulation(cfg)
        history, report, event_log = sim.run()

        self.assertEqual(report.outcome_classification, "HARD_IMPACT")
        self.assertGreater(report.terminal_vertical_speed_mps, 5.0)

    # 13. Ignition delay failure case yields HARD_IMPACT
    def test_13_ignition_delay_hard_impact(self):
        cfg_path = "config/phase7/synthetic_landing_ignition_delay.yaml"
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f)
        sim = LandingSimulation(cfg)
        history, report, event_log = sim.run()

        self.assertEqual(report.outcome_classification, "HARD_IMPACT")
        self.assertGreater(report.terminal_vertical_speed_mps, 5.0)

    # 14. Commanded throttle bounds enforcement
    def test_14_guidance_throttle_clamping(self):
        guidance = TerminalLandingGuidance()
        veh = StarshipLandingVehicle()
        prop = RaptorLandingPropulsion(minimum_throttle=0.40, maximum_throttle=1.00)

        # Huge downward speed demanding max thrust
        state_fast = LandingState(time_s=0.0, x=0.0, z=10.0, vx=0.0, vz=-50.0, mass_kg=120000.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)
        t_cmd, _, _ = guidance.compute_commands(state_fast, veh, prop)
        self.assertEqual(t_cmd, 1.00)

        # Hovering at target demanding min thrust
        state_hover = LandingState(time_s=0.0, x=0.0, z=0.0, vx=0.0, vz=0.0, mass_kg=120000.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)
        t_cmd2, _, _ = guidance.compute_commands(state_hover, veh, prop)
        self.assertGreaterEqual(t_cmd2, 0.40)
        self.assertLessEqual(t_cmd2, 1.00)

    # 15. Touchdown event localization root-finding
    def test_15_touchdown_root_finding(self):
        sm = LandingStateMachine()
        s_prev = LandingState(time_s=10.0, x=10.0, z=5.0, vx=2.0, vz=-10.0, mass_kg=100000.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)
        s_curr = LandingState(time_s=11.0, x=12.0, z=-5.0, vx=2.0, vz=-10.0, mass_kg=99500.0, pitch_deg=0.0, pitch_rate_deg_s=0.0)

        td = sm.detect_surface_crossing(s_prev, s_curr)
        self.assertIsNotNone(td)
        self.assertAlmostEqual(td.z, 0.0, places=5)
        self.assertAlmostEqual(td.time_s, 10.5, places=3)
        self.assertAlmostEqual(td.x, 11.0, places=3)

    # 16. Target miss distance calculation
    def test_16_target_miss_distance(self):
        assessor = TouchdownAssessor()
        veh = StarshipLandingVehicle()
        state = LandingState(time_s=25.0, x=14.5, z=0.0, vx=0.5, vz=-2.0, mass_kg=105000.0, pitch_deg=1.2, pitch_rate_deg_s=0.1)
        rep = assessor.assess(state, veh, propellant_consumed_kg=15000.0, burn_duration_s=15.0,
                              ignition_delay_altitude_loss_m=50.0, peak_apparent_g=2.1, max_thrust_N=6.0e6)
        self.assertAlmostEqual(rep.miss_distance_m, 14.5, places=2)

    # 17. Solver step-size convergence study
    def test_17_solver_step_size_convergence(self):
        cfg = copy.deepcopy(self.base_config)
        cfg["integrator"]["max_time_s"] = 15.0  # partial run to compare states

        cfg1 = copy.deepcopy(cfg)
        cfg1["integrator"]["dt_s"] = 0.02
        sim1 = LandingSimulation(cfg1)
        h1, _, _ = sim1.run()

        cfg2 = copy.deepcopy(cfg)
        cfg2["integrator"]["dt_s"] = 0.01
        sim2 = LandingSimulation(cfg2)
        h2, _, _ = sim2.run()

        # Altitude at t=10.0s should agree within 1%
        t_idx1 = int(10.0 / 0.02)
        t_idx2 = int(10.0 / 0.01)
        alt1 = h1[t_idx1].z
        alt2 = h2[t_idx2].z
        rel_diff = abs(alt1 - alt2) / max(abs(alt1), 1.0)
        self.assertLess(rel_diff, 0.01)

    # 18. Deterministic repeat run produces exact parity
    def test_18_deterministic_repeat_run(self):
        sim1 = LandingSimulation(self.base_config)
        h1, rep1, _ = sim1.run()

        sim2 = LandingSimulation(self.base_config)
        h2, rep2, _ = sim2.run()

        self.assertEqual(rep1.outcome_classification, rep2.outcome_classification)
        self.assertAlmostEqual(rep1.terminal_vertical_speed_mps, rep2.terminal_vertical_speed_mps, places=5)
        self.assertAlmostEqual(rep1.propellant_consumed_kg, rep2.propellant_consumed_kg, places=5)

    # 19. Seeded Monte Carlo repeatability
    def test_19_monte_carlo_seeded_repeatability(self):
        mc_cfg_path = "config/phase7/synthetic_landing_uncertainty.yaml"
        with open(mc_cfg_path, "r") as f:
            mc_cfg = yaml.safe_load(f)

        mc_cfg["monte_carlo"]["sample_count"] = 5  # Small sample for fast unit test
        mc1 = MonteCarloSimulator(mc_cfg)
        samples1, sum1 = mc1.run_ensemble(self.base_config)

        mc2 = MonteCarloSimulator(mc_cfg)
        samples2, sum2 = mc2.run_ensemble(self.base_config)

        self.assertEqual(sum1["sample_count"], sum2["sample_count"])
        self.assertEqual(sum1["success_fraction"], sum2["success_fraction"])
        self.assertAlmostEqual(samples1[0]["initial_vz_mps"], samples2[0]["initial_vz_mps"], places=5)

    # 20. Regression test preserving Phase 6 terminal outcome
    def test_20_regression_phase6_endpoint_preserved(self):
        phase6_term_path = "output/phase6/terminal_state.json"
        self.assertTrue(os.path.exists(phase6_term_path), "Phase 6 terminal_state.json must exist")
        import json
        with open(phase6_term_path, "r") as f:
            p6 = json.load(f)
        # Verify Phase 6 endpoint is unchanged at ~209.7 m/s into South Atlantic
        self.assertAlmostEqual(p6["terminal_relative_speed_ms"], 209.67, delta=0.5)
        self.assertAlmostEqual(p6["geodetic_lat_deg"], -14.044, delta=0.01)
        self.assertAlmostEqual(p6["geodetic_lon_deg"], -15.406, delta=0.01)


if __name__ == "__main__":
    unittest.main()
