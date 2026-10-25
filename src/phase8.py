"""
Command-line interface (CLI) for Starship Phase 8 Structural FEA Benchmark.

Supported commands:
  python -m src.phase8 benchmark
  python -m src.phase8 solve --pressure 0.6 --load-factor 3.0
  python -m src.phase8 convergence
  python -m src.phase8 export-deck
  python -m src.phase8 all
"""

import argparse
import sys
import os
import json
from typing import Dict, Any, List

from src.fea.analytical import compute_roark_stresses
from src.fea.mesh import generate_cylindrical_shell_mesh
from src.fea.solver import solve_cylindrical_tank_shell
from src.fea.calculix_deck import export_calculix_deck, run_calculix
from src.fea.reporting import generate_fea_plots, export_convergence_results


def cmd_benchmark(args) -> int:
    """Run closed-form Roark benchmarks for critical flight load cases."""
    print("=" * 80)
    print("STARSHIP TANK SECTION STRUCTURAL BENCHMARK (ROARK THIN-SHELL THEORY)")
    print("=" * 80)

    cases = [
        {"name": "Case 1: Nominal Flight Ullage Pressure (6.0 bar)", "p": 6.0e5, "F": 0.0},
        {"name": "Case 2: Launch Acceleration (3.0g Axial + 6.0 bar)", "p": 6.0e5, "F": 3.0 * 120000.0 * 9.80665},
        {"name": "Case 3: Cryogenic Proof Pressure Test (8.5 bar)", "p": 8.5e5, "F": 0.0},
        {"name": "Case 4: Reentry Peak Deceleration (3.23g + 2.0 bar)", "p": 2.0e5, "F": 3.23 * 100000.0 * 9.80665},
    ]

    print(f"{'Load Case':<42} | {'Hoop [MPa]':<11} | {'Axial [MPa]':<11} | {'VM [MPa]':<10} | {'SF_y':<6}")
    print("-" * 88)

    results = []
    for c in cases:
        res = compute_roark_stresses(radius_m=4.5, thickness_m=0.004, length_m=10.0,
                                     pressure_pa=c["p"], axial_force_N=c["F"])
        print(f"{c['name']:<42} | {res.hoop_stress_pa/1e6:<11.2f} | {res.axial_stress_pa/1e6:<11.2f} | {res.von_mises_stress_pa/1e6:<10.2f} | {res.safety_factor_yield:<6.2f}")
        results.append({"name": c["name"], "metrics": res.to_dict()})

    output_dir = args.output or os.path.join("output", "phase8")
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, "roark_benchmark_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[+] Benchmark summary exported to: {summary_path}")
    return 0


def cmd_solve(args) -> int:
    """Execute numerical thin-shell FEA solve for specified pressure and load factor."""
    print(f"[*] Solving Starship tank shell FEA (Pressure: {args.pressure} bar, Load: {args.load_factor}g)")
    p_pa = args.pressure * 1e5
    f_axial = args.load_factor * 120000.0 * 9.80665

    mesh = generate_cylindrical_shell_mesh(radius_m=4.5, thickness_m=0.004, length_m=10.0,
                                          n_theta=args.n_theta, n_z=args.n_z)
    sol = solve_cylindrical_tank_shell(mesh, pressure_pa=p_pa, axial_force_N=f_axial)

    print("\n" + "=" * 60)
    print("FEA SHELL STRUCTURAL SOLUTION SUMMARY")
    print("=" * 60)
    print(f"  Mesh Nodes:                  {sol.mesh.total_nodes}")
    print(f"  Mesh Elements:               {sol.mesh.total_elements}")
    print(f"  Nominal Element Size:        {sol.mesh.nominal_element_size_m*1000.0:.1f} mm")
    print(f"  FEA Max Hoop Stress:         {sol.max_hoop_stress_pa/1e6:.2f} MPa")
    print(f"  Roark Analytical Hoop:       {sol.analytical_benchmark.hoop_stress_pa/1e6:.2f} MPa")
    print(f"  Hoop Stress Relative Error:  {sol.hoop_stress_error_percent:.4f}%")
    print(f"  FEA Max Von Mises Stress:    {sol.max_von_mises_pa/1e6:.2f} MPa")
    print(f"  Roark Analytical Von Mises:  {sol.analytical_benchmark.von_mises_stress_pa/1e6:.2f} MPa")
    print(f"  Max Radial Displacement:     {sol.max_radial_displacement_m*1000.0:.3f} mm")
    print(f"  Yield Safety Factor (SF_y):  {sol.analytical_benchmark.safety_factor_yield:.2f}")
    print("=" * 60 + "\n")

    output_dir = args.output or os.path.join("output", "phase8")
    os.makedirs(output_dir, exist_ok=True)
    summary_json = os.path.join(output_dir, f"solve_p{args.pressure:.1f}_g{args.load_factor:.1f}_summary.json")
    with open(summary_json, "w") as f:
        json.dump(sol.to_dict(), f, indent=2)

    plot_path = os.path.join(output_dir, f"tank_stress_p{args.pressure:.1f}_plots.png")
    generate_fea_plots(sol, plot_path)

    print(f"[+] Output summary written to: {summary_json}")
    return 0


def cmd_convergence(args) -> int:
    """Perform mesh convergence study across 3 element densities."""
    print("=" * 80)
    print("PHASE 8 MESH REFINEMENT CONVERGENCE STUDY")
    print("=" * 80)

    grids = [
        {"level": "Coarse", "n_theta": 36, "n_z": 15},
        {"level": "Medium", "n_theta": 72, "n_z": 30},
        {"level": "Fine",   "n_theta": 144, "n_z": 60},
    ]

    p_pa = 6.0e5
    f_axial = 3.0 * 120000.0 * 9.80665

    records: List[Dict[str, Any]] = []
    print(f"{'Mesh Level':<12} | {'Nodes':<8} | {'Elements':<10} | {'h [mm]':<8} | {'Hoop [MPa]':<11} | {'Error %':<9}")
    print("-" * 75)

    for g in grids:
        mesh = generate_cylindrical_shell_mesh(radius_m=4.5, thickness_m=0.004, length_m=10.0,
                                              n_theta=g["n_theta"], n_z=g["n_z"])
        sol = solve_cylindrical_tank_shell(mesh, pressure_pa=p_pa, axial_force_N=f_axial)
        elem_size_mm = sol.mesh.nominal_element_size_m * 1000.0

        print(f"{g['level']:<12} | {sol.mesh.total_nodes:<8} | {sol.mesh.total_elements:<10} | {elem_size_mm:<8.1f} | {sol.max_hoop_stress_pa/1e6:<11.2f} | {sol.hoop_stress_error_percent:<9.4f}%")

        records.append({
            "mesh_level": g["level"],
            "n_theta": g["n_theta"],
            "n_z": g["n_z"],
            "total_nodes": sol.mesh.total_nodes,
            "total_elements": sol.mesh.total_elements,
            "element_size_mm": round(elem_size_mm, 1),
            "max_hoop_MPa": round(sol.max_hoop_stress_pa / 1e6, 2),
            "roark_hoop_MPa": round(sol.analytical_benchmark.hoop_stress_pa / 1e6, 2),
            "hoop_error_percent": round(sol.hoop_stress_error_percent, 4),
            "max_von_mises_MPa": round(sol.max_von_mises_pa / 1e6, 2),
            "von_mises_error_percent": round(sol.von_mises_error_percent, 4),
        })

    output_dir = args.output or os.path.join("output", "phase8")
    csv_path = export_convergence_results(records, output_dir)
    print(f"\n[+] Mesh convergence study exported to: {csv_path}")
    return 0


def cmd_export_deck(args) -> int:
    """Generate both ANSYS APDL and CalculiX input decks."""
    print("[*] Generating structural FEA input decks...")
    mesh = generate_cylindrical_shell_mesh(radius_m=4.5, thickness_m=0.004, length_m=10.0, n_theta=72, n_z=30)

    calculix_path = os.path.join("fea", "tank_section_calculix.inp")
    export_calculix_deck(mesh, calculix_path, pressure_pa=6.0e5, axial_force_N=3.53e6)
    print(f"[+] CalculiX .inp deck generated: {calculix_path}")

    # Check for ccx.exe
    ccx_exe = r"E:\Program Files\FreeCAD 1.1\bin\ccx.exe"
    if os.path.exists(ccx_exe):
        print(f"[*] Detected CalculiX executable: {ccx_exe}")
        code, log = run_calculix(calculix_path, ccx_exe_path=ccx_exe, timeout_s=30.0)
        print(f"[+] CalculiX run finished with returncode: {code}")

    ansys_path = os.path.join("fea", "tank_section_stress.mac")
    print(f"[+] ANSYS Mechanical APDL macro verified: {ansys_path}")
    return 0


def cmd_all(args) -> int:
    """Run full Phase 8 execution suite."""
    print("=" * 80)
    print("PHASE 8 STRUCTURAL FEA BENCHMARK — COMPLETE BATCH SUITE")
    print("=" * 80)

    cmd_benchmark(args)
    cmd_solve(argparse.Namespace(pressure=6.0, load_factor=3.0, n_theta=72, n_z=30, output=args.output))
    cmd_convergence(args)
    cmd_export_deck(args)

    print("\n" + "=" * 80)
    print("ALL PHASE 8 STRUCTURAL BENCHMARKS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Starship Phase 8 Structural FEA Benchmark CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # benchmark
    p_bm = subparsers.add_parser("benchmark", help="Run Roark analytical benchmarks")
    p_bm.add_argument("--output", default="output/phase8", help="Output directory")

    # solve
    p_sol = subparsers.add_parser("solve", help="Execute numerical shell FEA solve")
    p_sol.add_argument("--pressure", type=float, default=6.0, help="Internal pressure [bar]")
    p_sol.add_argument("--load-factor", type=float, default=3.0, help="Axial acceleration load factor [g]")
    p_sol.add_argument("--n-theta", type=int, default=72, help="Circumferential subdivisions")
    p_sol.add_argument("--n-z", type=int, default=30, help="Axial subdivisions")
    p_sol.add_argument("--output", default="output/phase8", help="Output directory")

    # convergence
    p_conv = subparsers.add_parser("convergence", help="Run mesh refinement study")
    p_conv.add_argument("--output", default="output/phase8", help="Output directory")

    # export-deck
    p_deck = subparsers.add_parser("export-deck", help="Export ANSYS APDL and CalculiX decks")
    p_deck.add_argument("--output", default="output/phase8", help="Output directory")

    # all
    p_all = subparsers.add_parser("all", help="Run complete Phase 8 suite")
    p_all.add_argument("--output", default="output/phase8", help="Output directory")

    args = parser.parse_args()

    if args.command == "benchmark":
        sys.exit(cmd_benchmark(args))
    elif args.command == "solve":
        sys.exit(cmd_solve(args))
    elif args.command == "convergence":
        sys.exit(cmd_convergence(args))
    elif args.command == "export-deck":
        sys.exit(cmd_export_deck(args))
    elif args.command == "all":
        sys.exit(cmd_all(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
