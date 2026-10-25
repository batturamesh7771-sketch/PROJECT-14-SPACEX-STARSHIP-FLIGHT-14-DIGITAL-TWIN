"""
CalculiX / Abaqus .inp input deck generator and solver runner interface.
Executes FEA solve via CalculiX CCX (v2.22).
"""

import os
import subprocess
import math
from typing import Dict, Any, Optional, Tuple
from src.fea.mesh import CylindricalMesh, generate_cylindrical_shell_mesh


def export_calculix_deck(mesh: CylindricalMesh,
                         output_path: str,
                         pressure_pa: float = 6.0e5,
                         axial_force_N: float = 3.53e6,
                         youngs_modulus_pa: float = 1.93e11,
                         poissons_ratio: float = 0.29,
                         density_kg_m3: float = 7900.0) -> str:
    """
    Generate an Abaqus/CalculiX .inp file for the cylindrical tank section.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w") as f:
        f.write("*HEADING\n")
        f.write("Starship Flight 14 Digital Lab - Phase 8 Tank Section FEA\n")
        f.write("** Units: SI (m, N, kg, Pa)\n\n")

        # 1. Nodal Coordinates
        f.write("*NODE\n")
        for node in mesh.nodes:
            f.write(f"{node.node_id}, {node.x:.6e}, {node.y:.6e}, {node.z:.6e}\n")

        # 2. Element Topology
        f.write("*ELEMENT, TYPE=S4R, ELSET=EALL\n")
        for elem in mesh.elements:
            n1, n2, n3, n4 = elem.node_ids
            f.write(f"{elem.elem_id}, {n1}, {n2}, {n3}, {n4}\n")

        # 3. Node Sets for Boundary Conditions
        # Bottom edge: z = 0 (nodes with j = 0)
        bottom_node_ids = [n.node_id for n in mesh.nodes if abs(n.z) < 1e-5]
        top_node_ids = [n.node_id for n in mesh.nodes if abs(n.z - mesh.length_m) < 1e-5]

        f.write("*NSET, NSET=NBOTTOM\n")
        for idx, nid in enumerate(bottom_node_ids):
            f.write(f"{nid}")
            if (idx + 1) % 10 == 0 or idx == len(bottom_node_ids) - 1:
                f.write("\n")
            else:
                f.write(", ")

        f.write("*NSET, NSET=NTOP\n")
        for idx, nid in enumerate(top_node_ids):
            f.write(f"{nid}")
            if (idx + 1) % 10 == 0 or idx == len(top_node_ids) - 1:
                f.write("\n")
            else:
                f.write(", ")

        # 4. Section and Material Properties
        f.write(f"*SHELL SECTION, ELSET=EALL, MATERIAL=STEEL_304L\n")
        f.write(f"{mesh.thickness_m:.6e}, 5\n")  # 4 mm thickness, 5 integration points

        f.write("*MATERIAL, NAME=STEEL_304L\n")
        f.write("*ELASTIC\n")
        f.write(f"{youngs_modulus_pa:.6e}, {poissons_ratio:.4f}\n")
        f.write("*DENSITY\n")
        f.write(f"{density_kg_m3:.2f}\n\n")

        # 5. Boundary Conditions (Base Fixity)
        f.write("*BOUNDARY\n")
        f.write("NBOTTOM, 3, 3, 0.0\n")  # Constrain axial motion at base ring (Z=0)
        # Pin one node to prevent rigid body translation in X and Y
        f.write(f"{bottom_node_ids[0]}, 1, 2, 0.0\n")
        # Pin orthogonal node to prevent rigid body rotation about Z
        quarter_idx = len(bottom_node_ids) // 4
        f.write(f"{bottom_node_ids[quarter_idx]}, 1, 1, 0.0\n\n")

        # 6. Step Definition
        f.write("*STEP\n")
        f.write("*STATIC\n")

        # Internal Ullage Pressure
        if abs(pressure_pa) > 0.0:
            f.write("*DLOAD\n")
            # In CalculiX, P applies positive pressure normal to the shell surface
            f.write(f"EALL, P, {pressure_pa:.6e}\n")

        # Top Compressive Axial Load
        if abs(axial_force_N) > 0.0:
            f.write("*CLOAD\n")
            axial_per_node = -axial_force_N / len(top_node_ids)  # Compressive force pointing -Z
            for nid in top_node_ids:
                f.write(f"{nid}, 3, {axial_per_node:.6e}\n")

        # 7. Output Requests
        f.write("*NODE PRINT, NSET=NTOP\n")
        f.write("U\n")
        f.write("*EL PRINT, ELSET=EALL\n")
        f.write("S\n")
        f.write("*NODE FILE\n")
        f.write("U\n")
        f.write("*EL FILE\n")
        f.write("S\n")
        f.write("*END STEP\n")

    return output_path


def run_calculix(inp_file_path: str,
                 ccx_exe_path: str = r"E:\Program Files\FreeCAD 1.1\bin\ccx.exe",
                 timeout_s: float = 60.0) -> Tuple[int, str]:
    """
    Execute CalculiX solver on the generated .inp file.
    Returns: (exit_code, log_output)
    """
    if not os.path.exists(ccx_exe_path):
        return -1, f"CalculiX executable not found at {ccx_exe_path}"

    job_dir = os.path.dirname(os.path.abspath(inp_file_path))
    job_name = os.path.splitext(os.path.basename(inp_file_path))[0]

    try:
        res = subprocess.run(
            [ccx_exe_path, job_name],
            cwd=job_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s
        )
        return res.returncode, res.stdout + "\n" + res.stderr
    except subprocess.TimeoutExpired:
        return -2, "CalculiX execution timed out."
    except Exception as e:
        return -3, str(e)
