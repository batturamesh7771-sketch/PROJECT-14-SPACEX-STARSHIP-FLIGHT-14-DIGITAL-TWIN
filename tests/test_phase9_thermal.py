"""
Unit and integration test suite for Phase 9: Aerothermal Reentry & Thermal Protection System (TPS).

Tests 15 distinct verification assertions:
 1. Sutton-Graves convective stagnation heat flux analytical formula.
 2. Detra-Kemp-Riddell (DKR) stagnation correlation.
 3. Windward acreage heat flux angle-of-attack pitch scaling.
 4. Surface radiative equilibrium temperature with Stefan-Boltzmann balance.
 5. Temperature-dependent porous silica tile thermal conductivity k(T).
 6. Temperature-dependent porous silica tile specific heat capacity cp(T).
 7. Thermal stack spatial mesh discretization and layer interface tagging.
 8. TDMA (Thomas algorithm) tridiagonal linear system solver accuracy.
 9. 1D transient conduction conservation and steady-state recovery.
10. Physical heat soak thermal diffusion lag (bondline peak occurs after surface peak).
11. Nominal 28mm tile RTV bondline safety margin against 533.15 K limit.
12. Monotonic bondline temperature reduction with increasing tile thickness.
13. Atmospheric density perturbation sensitivity (+/- 20%).
14. Entry trajectory CSV data loading and synchronization.
15. Margin assessment serialization and valid JSON formatting.
"""

import unittest
import math
import os
import json
import numpy as np

from src.thermal.material_properties import (
    get_silica_tile_properties,
    get_sip_felt_properties,
    get_stainless_steel_properties,
    STEFAN_BOLTZMANN,
    RTV_BONDLINE_LIMIT_K,
)
from src.thermal.aerothermal_flux import (
    compute_sutton_graves_heat_flux,
    compute_detra_kemp_riddell_flux,
    compute_windward_acreage_flux,
    compute_radiative_equilibrium_temp,
    C_SUTTON_GRAVES_EARTH,
)
from src.thermal.conduction_1d import (
    generate_thermal_stack_mesh,
    TransientThermalSolver1D,
    ThermalSolution1D,
)
from src.thermal.margin_analysis import (
    evaluate_bondline_margins,
    run_tile_thickness_trade_study,
    run_density_sensitivity_study,
)
from src.phase9 import load_reentry_trajectory_data


class TestPhase9AerothermalTPS(unittest.TestCase):
    """15-point verification test suite for Phase 9 TPS and aerothermal models."""

    def setUp(self):
        self.rho_test = 1.0e-4      # kg/m^3 (~65 km altitude)
        self.v_test = 7000.0        # m/s (~Mach 22)
        self.rn_test = 4.5          # m (Starship nose radius)

    def test_01_sutton_graves_formula(self):
        """Verify Sutton-Graves stagnation heat flux formula: q = C * sqrt(rho / Rn) * v^3."""
        # Expected: 1.74153e-4 * sqrt(1e-4 / 4.5) * (7000^3)
        # sqrt(2.2222e-5) = 4.7140e-3
        # 1.74153e-4 * 4.7140e-3 * 3.43e11 = 281600 W/m^2 = 0.2816 MW/m^2
        q = compute_sutton_graves_heat_flux(self.rho_test, self.v_test, self.rn_test)
        expected = C_SUTTON_GRAVES_EARTH * math.sqrt(self.rho_test / self.rn_test) * (self.v_test ** 3)
        self.assertAlmostEqual(q, expected, places=1)
        self.assertGreater(q, 2.5e5)
        self.assertLess(q, 3.2e5)

    def test_02_detra_kemp_riddell_formula(self):
        """Verify Detra-Kemp-Riddell stagnation correlation computes positive realistic flux."""
        q_dkr = compute_detra_kemp_riddell_flux(self.rho_test, self.v_test, self.rn_test)
        self.assertGreater(q_dkr, 0.0)
        # DKR scales with v^3.15, should be within factor of 1.5 of Sutton-Graves
        q_sg = compute_sutton_graves_heat_flux(self.rho_test, self.v_test, self.rn_test)
        ratio = q_dkr / q_sg
        self.assertGreater(ratio, 0.5)
        self.assertLess(ratio, 2.0)

    def test_03_windward_acreage_pitch_scaling(self):
        """Verify windward belly flux scaling with angle of attack: q_wind = q_stag * sin(alpha)^1.6 * f."""
        q_stag = 1.0e6  # 1 MW/m^2
        # At alpha = 40 deg: sin(40) = 0.6427876, 0.6427876^1.6 = 0.4934
        # For f_body = 0.40, q_wind = 1.0e6 * 0.4934 * 0.40 = 197360 W/m^2
        q_wind = compute_windward_acreage_flux(q_stag, angle_of_attack_deg=40.0, body_position_factor=0.40)
        self.assertAlmostEqual(q_wind, 197360.0, delta=500.0)
        # Verify alpha = 0 gives 0 flux and alpha = 90 gives q_stag * f_body
        self.assertEqual(compute_windward_acreage_flux(q_stag, angle_of_attack_deg=0.0), 0.0)
        self.assertAlmostEqual(compute_windward_acreage_flux(q_stag, angle_of_attack_deg=90.0, body_position_factor=0.40), 400000.0, delta=10.0)

    def test_04_radiative_equilibrium_temperature(self):
        """Verify surface radiative equilibrium temperature: T_rad = ((q / (eps * sigma)) + T_inf^4)^0.25."""
        q_wind = 2.0e5  # 200 kW/m^2
        eps = 0.85
        t_amb = 220.0
        t_rad = compute_radiative_equilibrium_temp(q_wind, emissivity=eps, ambient_temp_k=t_amb)
        expected = ((q_wind / (eps * STEFAN_BOLTZMANN)) + (t_amb ** 4)) ** 0.25
        self.assertAlmostEqual(t_rad, expected, places=2)
        # For 200 kW/m^2, T_rad should be ~1427 K (~1154 deg C)
        self.assertGreater(t_rad, 1400.0)
        self.assertLess(t_rad, 1460.0)

    def test_05_silica_conductivity_temperature_dependence(self):
        """Verify porous silica tile thermal conductivity k(T) increases with temperature."""
        tile = get_silica_tile_properties()
        k_300 = tile.get_conductivity(300.0)
        k_800 = tile.get_conductivity(800.0)
        k_1500 = tile.get_conductivity(1500.0)
        # Values should increase due to internal pore radiation
        self.assertLess(k_300, k_800)
        self.assertLess(k_800, k_1500)
        self.assertGreater(k_300, 0.035)
        self.assertLess(k_300, 0.065)
        self.assertGreater(k_1500, 0.14)
        self.assertLess(k_1500, 0.25)

    def test_06_silica_specific_heat_temperature_dependence(self):
        """Verify porous silica tile specific heat capacity cp(T) increases toward asymptotic limit."""
        tile = get_silica_tile_properties()
        cp_300 = tile.get_specific_heat(300.0)
        cp_800 = tile.get_specific_heat(800.0)
        cp_1500 = tile.get_specific_heat(1500.0)
        self.assertLess(cp_300, cp_800)
        self.assertLess(cp_800, cp_1500)
        self.assertGreater(cp_300, 700.0)
        self.assertLess(cp_1500, 1300.0)

    def test_07_thermal_stack_mesh_generation(self):
        """Verify thermal stack mesh discretization across tile, SIP, and steel layers."""
        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.028, sip_thickness_m=0.0025, steel_thickness_m=0.0040,
                                           n_tile=35, n_sip=10, n_steel=10)
        self.assertEqual(len(mesh.layers), 3)
        expected_thickness = 0.028 + 0.0025 + 0.0040
        self.assertAlmostEqual(mesh.total_thickness_m, expected_thickness, places=6)
        # Bondline node should be at x = 0.028m (end of tile)
        self.assertAlmostEqual(mesh.node_x[mesh.bondline_node_idx], 0.028, places=6)
        # Backface node should be at total thickness
        self.assertAlmostEqual(mesh.node_x[mesh.steel_backface_node_idx], expected_thickness, places=6)

    def test_08_tdma_linear_solver_accuracy(self):
        """Verify Thomas algorithm (TDMA) accurately solves tridiagonal matrix."""
        # Simple test matrix: [2 -1; -1 2] * [x1; x2] = [1; 2] => x = [4/3; 5/3]
        a = np.array([0.0, -1.0])
        b = np.array([2.0, 2.0])
        c = np.array([-1.0, 0.0])
        d = np.array([1.0, 2.0])
        x = TransientThermalSolver1D._solve_tridiagonal(a, b, c, d)
        self.assertAlmostEqual(x[0], 4.0 / 3.0, places=6)
        self.assertAlmostEqual(x[1], 5.0 / 3.0, places=6)

    def test_09_1d_conduction_steady_state_recovery(self):
        """Verify 1D conduction solver runs stably without energy creation or unbounded divergence."""
        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.020, n_tile=15, n_sip=5, n_steel=5)
        solver = TransientThermalSolver1D(mesh, initial_temp_k=300.0)
        times = [float(i) for i in range(50)]
        fluxes = [0.0] * 50  # Zero heat flux
        sol = solver.solve_trajectory(times, fluxes, ambient_temp_k=300.0)
        # Without heating, temperature must stay at initial 300K
        for t_surf in sol.surface_temp_history_k:
            self.assertAlmostEqual(t_surf, 300.0, delta=1.0)
        for t_bond in sol.bondline_temp_history_k:
            self.assertAlmostEqual(t_bond, 300.0, delta=1.0)

    def test_10_heat_soak_diffusion_lag(self):
        """Verify physical heat soak diffusion delay (bondline peaks significantly after surface peak)."""
        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.028)
        solver = TransientThermalSolver1D(mesh, initial_temp_k=293.15)
        # Gaussian heat pulse centered at t = 200s
        times = [float(t) for t in range(0, 1000, 10)]
        fluxes = [1.5e5 * math.exp(-((t - 200.0) / 80.0) ** 2) for t in times]
        sol = solver.solve_trajectory(times, fluxes)
        # Peak surface must occur near pulse peak (t ~ 200s)
        self.assertAlmostEqual(sol.time_of_peak_surface_s, 200.0, delta=25.0)
        # Peak bondline must occur later due to diffusion lag
        self.assertGreater(sol.time_of_peak_bondline_s, sol.time_of_peak_surface_s)
        self.assertGreater(sol.heat_soak_lag_s, 100.0)

    def test_11_nominal_rtv_bondline_margin(self):
        """Verify nominal 28mm tile preserves positive bondline margin against 533.15 K limit."""
        traj = load_reentry_trajectory_data()
        times = [r["time_s"] for r in traj]
        fluxes = [compute_windward_acreage_flux(compute_sutton_graves_heat_flux(r["density_kg_m3"], r["speed_relative_ms"])) for r in traj]

        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.028)
        solver = TransientThermalSolver1D(mesh)
        sol = solver.solve_trajectory(times, fluxes)
        assessment = evaluate_bondline_margins(sol)

        self.assertTrue(assessment.is_acceptable)
        self.assertGreater(assessment.temperature_margin_k, 50.0)
        self.assertLess(assessment.peak_bondline_temp_k, RTV_BONDLINE_LIMIT_K)

    def test_12_tile_thickness_trade_monotonicity(self):
        """Verify thicker tiles result in monotonically lower peak bondline temperatures."""
        times = [float(t) for t in range(0, 800, 10)]
        fluxes = [1.8e5 * math.exp(-((t - 200.0) / 100.0) ** 2) for t in times]
        thicknesses = [18.0, 24.0, 30.0, 36.0]
        results = run_tile_thickness_trade_study(times, fluxes, thicknesses)
        peak_bonds = [r["peak_bondline_temp_K"] for r in results]
        # Verify strictly decreasing: 18mm > 24mm > 30mm > 36mm
        for i in range(len(peak_bonds) - 1):
            self.assertGreater(peak_bonds[i], peak_bonds[i + 1])

    def test_13_atmospheric_density_sensitivity(self):
        """Verify positive density perturbation produces higher peak flux and heat load."""
        traj = load_reentry_trajectory_data()
        results = run_density_sensitivity_study(traj, [0.80, 1.00, 1.20])
        # Fluxes: 80% < 100% < 120%
        self.assertLess(results[0]["peak_heat_flux_MW_m2"], results[1]["peak_heat_flux_MW_m2"])
        self.assertLess(results[1]["peak_heat_flux_MW_m2"], results[2]["peak_heat_flux_MW_m2"])
        # Heat load: 80% < 100% < 120%
        self.assertLess(results[0]["integrated_heat_load_MJ_m2"], results[1]["integrated_heat_load_MJ_m2"])
        self.assertLess(results[1]["integrated_heat_load_MJ_m2"], results[2]["integrated_heat_load_MJ_m2"])

    def test_14_trajectory_data_ingestion(self):
        """Verify load_reentry_trajectory_data parses rows and keys properly."""
        traj = load_reentry_trajectory_data()
        self.assertGreater(len(traj), 100)
        row0 = traj[0]
        self.assertIn("time_s", row0)
        self.assertIn("altitude_km", row0)
        self.assertIn("speed_relative_ms", row0)
        self.assertIn("density_kg_m3", row0)
        self.assertGreater(row0["speed_relative_ms"], 5000.0)

    def test_15_cli_and_json_serialization(self):
        """Verify solution dictionary and JSON serialization."""
        mesh = generate_thermal_stack_mesh(tile_thickness_m=0.025, n_tile=10, n_sip=5, n_steel=5)
        solver = TransientThermalSolver1D(mesh)
        times = [0.0, 10.0, 20.0]
        fluxes = [1e4, 2e4, 1e4]
        sol = solver.solve_trajectory(times, fluxes)
        assessment = evaluate_bondline_margins(sol)
        d = assessment.to_dict()
        self.assertIn("peak_surface_temp_K", d)
        self.assertIn("peak_bondline_temp_K", d)
        self.assertIn("temperature_margin_K", d)
        # JSON dump verification
        json_str = json.dumps(d)
        self.assertGreater(len(json_str), 50)


if __name__ == "__main__":
    unittest.main()
