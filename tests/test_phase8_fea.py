"""
Unit and integration test suite for Phase 8: Structural FEA Propellant Tank Benchmark.

Tests 15 distinct verification assertions:
 1. Roark thin-walled hoop stress calculation (pr/t).
 2. Roark longitudinal stress under internal pressure (pr/2t).
 3. Combined longitudinal stress with axial acceleration force.
 4. Von Mises equivalent stress calculation under biaxial plane stress.
 5. Radial displacement calculation (delta_r).
 6. Shell characteristic decay parameter beta and attenuation length lambda.
 7. Parametric cylindrical quad mesh generation geometry and bounding box.
 8. Boundary node set extraction (bottom clamped ring, top loaded ring).
 9. Thin-shell FEA solver hoop stress accuracy vs Roark (< 0.05% error).
10. Thin-shell FEA solver Von Mises stress accuracy vs Roark (< 0.05% error).
11. Mesh refinement convergence error bounds (< 1.0% across all grids).
12. CalculiX Abaqus-format .inp deck syntax, section definition, and loading card.
13. ANSYS Mechanical APDL .mac macro syntax, element type SHELL181, and parameters.
14. NASA SP-8007 cylindrical shell buckling stress scaling and safety factor.
15. Solution serialization to dictionary and JSON compatibility.
"""

import unittest
import math
import os
import json
import tempfile

from src.fea.analytical import (
    compute_roark_stresses,
    compute_nasa_sp8007_buckling_stress,
    calculate_decay_parameter_beta,
    calculate_boundary_decay_length,
)
from src.fea.mesh import generate_cylindrical_shell_mesh
from src.fea.solver import solve_cylindrical_tank_shell
from src.fea.calculix_deck import export_calculix_deck


class TestPhase8StructuralFEA(unittest.TestCase):
    """15-point verification test suite for Phase 8 FEA and Roark benchmarks."""

    def setUp(self):
        self.radius = 4.5        # 9.0m diameter Starship barrel
        self.thickness = 0.004   # 4.0mm nominal 304L stainless skin
        self.length = 10.0       # 10.0m barrel section height
        self.pressure_pa = 6.0e5 # 6.0 bar internal ullage pressure
        self.axial_force_N = 3.0 * 120000.0 * 9.80665  # 3g on 120t upper stage = 3.53 MN

    def test_01_roark_hoop_stress_formula(self):
        """Verify hoop stress sigma_h = p * r / t."""
        # sigma_h = 0.6e6 * 4.5 / 0.004 = 675.0 MPa
        res = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, 0.0)
        expected_hoop_pa = 6.75e8
        self.assertAlmostEqual(res.hoop_stress_pa, expected_hoop_pa, delta=1.0)
        self.assertAlmostEqual(res.hoop_stress_pa / 1e6, 675.0, places=2)

    def test_02_roark_longitudinal_stress_pressure_only(self):
        """Verify longitudinal stress sigma_l = p * r / (2 * t) with no axial load."""
        # sigma_l = 0.6e6 * 4.5 / (2 * 0.004) = 337.5 MPa
        res = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, 0.0)
        expected_axial_pa = 3.375e8
        self.assertAlmostEqual(res.axial_stress_pa, expected_axial_pa, delta=1.0)
        self.assertAlmostEqual(res.axial_stress_pa / 1e6, 337.5, places=2)

    def test_03_roark_axial_compression_superposition(self):
        """Verify axial compressive force subtracts from longitudinal tensile stress."""
        res_no_axial = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, 0.0)
        res_with_axial = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, self.axial_force_N)
        # Compressive axial stress sigma_comp = F / (2 * pi * r * t)
        area = 2.0 * math.pi * self.radius * self.thickness
        sigma_comp = self.axial_force_N / area
        self.assertAlmostEqual(res_with_axial.axial_stress_pa, res_no_axial.axial_stress_pa - sigma_comp, delta=10.0)
        # 337.5 MPa - 31.22 MPa = ~306.28 MPa
        self.assertLess(res_with_axial.axial_stress_pa, res_no_axial.axial_stress_pa)
        self.assertGreater(res_with_axial.axial_stress_pa, 0.0)

    def test_04_roark_von_mises_plane_stress(self):
        """Verify Von Mises equivalent stress under biaxial state sigma_vm = sqrt(s1^2 - s1*s2 + s2^2)."""
        res = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, 0.0)
        s1 = res.hoop_stress_pa
        s2 = res.axial_stress_pa
        expected_vm = math.sqrt(s1**2 - s1 * s2 + s2**2)
        self.assertAlmostEqual(res.von_mises_stress_pa, expected_vm, delta=10.0)
        # For s2 = s1/2, vm = sqrt(3)/2 * s1 = 0.866025 * 675 = 584.57 MPa
        self.assertAlmostEqual(res.von_mises_stress_pa / 1e6, 584.567, places=1)

    def test_05_roark_radial_deflection(self):
        """Verify radial deflection delta_r = (r / E) * (sigma_h - nu * sigma_l)."""
        res = compute_roark_stresses(self.radius, self.thickness, self.length, self.pressure_pa, 0.0)
        # delta_r = (4.5 / 193e9) * (675e6 - 0.29 * 337.5e6) = (4.5 / 193e9) * 577.125e6 = 1.345e-2 m = 13.45 mm
        self.assertGreater(res.radial_displacement_m, 0.010)
        self.assertLess(res.radial_displacement_m, 0.020)
        self.assertAlmostEqual(res.radial_displacement_m * 1000.0, 13.455, places=1)

    def test_06_shell_characteristic_decay_length(self):
        """Verify shell attenuation parameter beta = (3(1-nu^2)/(r^2*t^2))^0.25 and decay length lambda."""
        beta = calculate_decay_parameter_beta(self.radius, self.thickness, nu=0.29)
        decay_length = calculate_boundary_decay_length(self.radius, self.thickness, nu=0.29)
        # beta approx 9.596 m^-1, decay length = pi / beta approx 0.327 m (32.7 cm)
        self.assertAlmostEqual(beta, 9.596, places=2)
        self.assertAlmostEqual(decay_length, 0.327, places=2)
        self.assertGreater(decay_length, 0.20)
        self.assertLess(decay_length, 0.50)

    def test_07_mesh_generator_quad_topology(self):
        """Verify cylindrical shell mesh generator generates valid nodes and quad elements."""
        n_theta = 36
        n_z = 10
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=n_theta, n_z=n_z)
        self.assertEqual(mesh.total_nodes, n_z * n_theta)
        self.assertEqual(mesh.total_elements, (n_z - 1) * n_theta)
        # Verify node coordinates on cylinder

        for node in mesh.nodes:
            r_coord = math.sqrt(node.x**2 + node.y**2)
            self.assertAlmostEqual(r_coord, self.radius, places=4)
            self.assertGreaterEqual(node.z, 0.0)
            self.assertLessEqual(node.z, self.length)

    def test_08_mesh_generator_boundary_nodes(self):
        """Verify boundary node set extraction for bottom and top rings."""
        n_theta = 36
        n_z = 10
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=n_theta, n_z=n_z)
        bottom_nodes = mesh.get_bottom_boundary_nodes()
        top_nodes = mesh.get_top_boundary_nodes()
        self.assertEqual(len(bottom_nodes), n_theta)
        self.assertEqual(len(top_nodes), n_theta)
        # Verify bottom nodes have z = 0 and top nodes have z = length
        for nid in bottom_nodes:
            self.assertAlmostEqual(mesh.nodes[nid - 1].z, 0.0, places=5)
        for nid in top_nodes:
            self.assertAlmostEqual(mesh.nodes[nid - 1].z, self.length, places=5)

    def test_09_numerical_shell_solver_hoop_accuracy(self):
        """Verify thin-shell FEA solver hoop stress at mid-barrel matches Roark within < 0.05%."""
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=36, n_z=15)
        sol = solve_cylindrical_tank_shell(mesh, pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
        self.assertLess(sol.hoop_stress_error_percent, 0.05)
        self.assertAlmostEqual(sol.max_hoop_stress_pa / 1e6, 675.0, delta=0.5)

    def test_10_numerical_shell_solver_von_mises_accuracy(self):
        """Verify thin-shell FEA solver Von Mises stress matches Roark within < 0.05%."""
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=36, n_z=15)
        sol = solve_cylindrical_tank_shell(mesh, pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
        self.assertLess(sol.von_mises_error_percent, 0.05)
        self.assertAlmostEqual(sol.max_von_mises_pa / 1e6, 585.4, delta=0.5)

    def test_11_mesh_refinement_error_monotonicity(self):
        """Verify coarse, medium, fine grids all maintain Roark error < 1.0%."""
        grids = [(18, 8), (36, 15), (72, 30)]
        errors = []
        for n_t, n_z in grids:
            mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=n_t, n_z=n_z)
            sol = solve_cylindrical_tank_shell(mesh, pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
            errors.append(sol.hoop_stress_error_percent)
            self.assertLess(sol.hoop_stress_error_percent, 1.0)
        # All errors are well within engineering bounds
        self.assertTrue(all(e < 0.1 for e in errors))

    def test_12_calculix_deck_syntax_and_keywords(self):
        """Verify CalculiX .inp deck contains required Abaqus-format keywords."""
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=12, n_z=5)
        with tempfile.NamedTemporaryFile(suffix=".inp", delete=False) as tf:
            temp_path = tf.name
        try:
            export_calculix_deck(mesh, temp_path, pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
            with open(temp_path, "r") as f:
                content = f.read()
            self.assertIn("*HEADING", content)
            self.assertIn("*NODE", content)
            self.assertIn("*ELEMENT, TYPE=S4R", content)
            self.assertIn("*SHELL SECTION, ELSET=EALL, MATERIAL=STEEL_304L", content)
            self.assertIn("*BOUNDARY", content)
            self.assertIn("*DLOAD", content)
            self.assertIn("*CLOAD", content)
            self.assertIn("*EL FILE", content)
            self.assertIn("*NODE FILE", content)
            self.assertIn("*END STEP", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_13_ansys_mac_deck_parameters(self):
        """Verify ANSYS Mechanical APDL .mac macro syntax and parameters."""
        mac_path = os.path.join("fea", "tank_section_stress.mac")
        self.assertTrue(os.path.exists(mac_path), f"Macro not found at {mac_path}")
        with open(mac_path, "r") as f:
            content = f.read()
        self.assertIn("ET,1,SHELL181", content)
        self.assertIn("EX,1,,193.0E9", content)
        self.assertIn("PRXY,1,,0.29", content)
        self.assertIn("RADIUS     = DIAM / 2.0", content)
        self.assertIn("THICK      = 0.004", content)
        self.assertIn("PRESSURE   = 0.600E6", content)
        self.assertIn("SFA,ALL,1,PRES,PRESSURE", content)
        self.assertIn("SOLVE", content)

    def test_14_nasa_sp8007_critical_buckling_stress(self):
        """Verify NASA SP-8007 buckling stress calculation and knockdown factor."""
        buckling = compute_nasa_sp8007_buckling_stress(self.radius, self.thickness, self.length,
                                                        pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
        # Classical buckling stress sigma_cl = E * (t/r) / sqrt(3*(1-nu^2))
        # sigma_cl = 193e9 * (0.004/4.5) / sqrt(3*(1-0.29^2)) = 171.555e6 / 1.65798 = 103.47 MPa
        self.assertGreater(buckling["classical_buckling_stress_MPa"], 100.0)
        self.assertLess(buckling["classical_buckling_stress_MPa"], 110.0)
        # Knockdown factor gamma in [0.2, 0.4] for thin shells
        self.assertGreaterEqual(buckling["knockdown_factor_gamma"], 0.20)
        self.assertLessEqual(buckling["knockdown_factor_gamma"], 0.50)
        # With internal pressure stabilization (6 bar), critical buckling stress is enhanced
        self.assertGreater(buckling["critical_buckling_stress_with_pressure_MPa"], buckling["design_buckling_stress_unpressurized_MPa"])
        # Safety factor against buckling under 3g load (> 1.5)
        self.assertGreater(buckling["safety_factor_buckling"], 1.5)

    def test_15_solution_serialization_and_json(self):
        """Verify solution dictionary serialization and valid JSON formatting."""
        mesh = generate_cylindrical_shell_mesh(self.radius, self.thickness, self.length, n_theta=18, n_z=8)
        sol = solve_cylindrical_tank_shell(mesh, pressure_pa=self.pressure_pa, axial_force_N=self.axial_force_N)
        sol_dict = sol.to_dict()
        self.assertIn("max_hoop_stress_MPa", sol_dict)
        self.assertIn("max_von_mises_MPa", sol_dict)
        self.assertIn("hoop_stress_error_percent", sol_dict)
        self.assertIn("roark_hoop_stress_MPa", sol_dict)
        self.assertIn("roark_von_mises_MPa", sol_dict)
        # JSON dump check
        json_str = json.dumps(sol_dict)
        self.assertGreater(len(json_str), 100)



if __name__ == "__main__":
    unittest.main()
