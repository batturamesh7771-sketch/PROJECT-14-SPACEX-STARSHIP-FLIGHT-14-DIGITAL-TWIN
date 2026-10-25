"""
Plotting and summary report generator for Phase 8 structural FEA benchmarks.
"""

import os
import json
import csv
from typing import List, Dict, Any, Optional
from src.fea.solver import ShellStressSolution


def generate_fea_plots(solution: ShellStressSolution,
                       output_path: str,
                       title: str = "Starship Tank Section FEA Benchmark") -> Optional[str]:
    """
    Generate 4-panel structural stress and deformation verification figures.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[WARNING] Matplotlib not found; skipping FEA plot rendering.")
        return None

    mesh = solution.mesh
    dz = mesh.length_m / max(mesh.n_z - 1, 1)
    z_nodes = [j * dz for j in range(mesh.n_z)]

    # Extract sample profile along one meridian (theta = 0)
    ur_profile = [solution.nodal_ur_m[j * mesh.n_theta] * 1000.0 for j in range(mesh.n_z)]
    uz_profile = [solution.nodal_uz_m[j * mesh.n_theta] * 1000.0 for j in range(mesh.n_z)]

    # Element stresses along one meridian
    elem_z = [(j + 0.5) * dz for j in range(mesh.n_z - 1)]
    hoop_profile = [solution.element_hoop_stress_pa[j * mesh.n_theta] / 1e6 for j in range(mesh.n_z - 1)]
    axial_profile = [solution.element_axial_stress_pa[j * mesh.n_theta] / 1e6 for j in range(mesh.n_z - 1)]
    vm_profile = [solution.element_von_mises_pa[j * mesh.n_theta] / 1e6 for j in range(mesh.n_z - 1)]

    roark_hoop = solution.analytical_benchmark.hoop_stress_pa / 1e6
    roark_axial = solution.analytical_benchmark.axial_stress_pa / 1e6
    roark_vm = solution.analytical_benchmark.von_mises_stress_pa / 1e6
    roark_ur = solution.analytical_benchmark.radial_displacement_m * 1000.0

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{title}\nPressure: {solution.pressure_pa/1e5:.1f} bar | Axial Load: {solution.axial_force_N/1e6:.2f} MN", fontsize=14, fontweight="bold")

    # 1. Radial Displacement Profile
    axs[0, 0].plot(z_nodes, ur_profile, "b-o", markersize=4, label="FEA Nodal ur")
    axs[0, 0].axhline(roark_ur, color="r", linestyle="--", label=f"Roark Membrane: {roark_ur:.2f} mm")
    axs[0, 0].set_ylabel("Radial Displacement [mm]")
    axs[0, 0].set_xlabel("Axial Position z [m]")
    axs[0, 0].grid(True, alpha=0.3)
    axs[0, 0].legend()
    axs[0, 0].set_title("Radial Expansion Profile (Boundary Attenuation)")

    # 2. Hoop Stress Profile
    axs[0, 1].plot(elem_z, hoop_profile, "m-s", markersize=4, label="FEA Hoop Stress")
    axs[0, 1].axhline(roark_hoop, color="k", linestyle="--", label=f"Roark (p*r/t): {roark_hoop:.1f} MPa")
    axs[0, 1].set_ylabel("Circumferential Hoop Stress [MPa]")
    axs[0, 1].set_xlabel("Axial Position z [m]")
    axs[0, 1].grid(True, alpha=0.3)
    axs[0, 1].legend()
    axs[0, 1].set_title(f"Hoop Stress Distribution (Error: {solution.hoop_stress_error_percent:.2f}%)")

    # 3. Longitudinal (Axial) Stress Profile
    axs[1, 0].plot(elem_z, axial_profile, "g-^", markersize=4, label="FEA Axial Stress")
    axs[1, 0].axhline(roark_axial, color="k", linestyle="--", label=f"Roark Axial: {roark_axial:.1f} MPa")
    axs[1, 0].set_ylabel("Longitudinal Stress [MPa]")
    axs[1, 0].set_xlabel("Axial Position z [m]")
    axs[1, 0].grid(True, alpha=0.3)
    axs[1, 0].legend()
    axs[1, 0].set_title("Longitudinal Stress Profile")

    # 4. Von Mises Stress vs Yield Strength
    axs[1, 1].plot(elem_z, vm_profile, "tab:red", linewidth=2, label="Von Mises Stress")
    axs[1, 1].axhline(roark_vm, color="k", linestyle="--", label=f"Roark VM: {roark_vm:.1f} MPa")
    axs[1, 1].axhline(290.0, color="gray", linestyle=":", label="304L Min Yield (290 MPa)")
    axs[1, 1].set_ylabel("Von Mises Equivalent Stress [MPa]")
    axs[1, 1].set_xlabel("Axial Position z [m]")
    axs[1, 1].grid(True, alpha=0.3)
    axs[1, 1].legend()
    axs[1, 1].set_title(f"Yield Margin (SF_y: {solution.analytical_benchmark.safety_factor_yield:.2f})")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path


def export_convergence_results(convergence_records: List[Dict[str, Any]],
                               output_dir: str) -> str:
    """Export mesh convergence study table to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "mesh_convergence_study.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "mesh_level", "n_theta", "n_z", "total_nodes", "total_elements",
            "element_size_mm", "max_hoop_MPa", "roark_hoop_MPa",
            "hoop_error_percent", "max_von_mises_MPa", "von_mises_error_percent"
        ])
        writer.writeheader()
        for r in convergence_records:
            writer.writerow(r)
    return csv_path
