"""
Parametric thin-walled cylindrical shell mesh generator for structural FEA.
Supports Abaqus / CalculiX S4/S4R quadrilateral shell formulations.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
import math


@dataclass
class ShellNode:
    """Nodal coordinate point."""
    node_id: int
    x: float
    y: float
    z: float
    theta_rad: float


@dataclass
class ShellElement:
    """4-node quadrilateral shell element."""
    elem_id: int
    node_ids: Tuple[int, int, int, int]  # CCW ordering (n1, n2, n3, n4)
    centroid: Tuple[float, float, float]
    area_m2: float


@dataclass
class CylindricalMesh:
    """Full discrete cylindrical shell mesh structure."""
    radius_m: float
    thickness_m: float
    length_m: float
    n_theta: int
    n_z: int
    nodes: List[ShellNode]
    elements: List[ShellElement]

    @property
    def total_nodes(self) -> int:
        return len(self.nodes)

    @property
    def total_elements(self) -> int:
        return len(self.elements)

    @property
    def nominal_element_size_m(self) -> float:
        circumference = 2.0 * math.pi * self.radius_m
        ds_theta = circumference / self.n_theta
        dz = self.length_m / max(self.n_z - 1, 1)
        return (ds_theta + dz) / 2.0

    def get_bottom_boundary_nodes(self) -> List[int]:
        """Return list of node IDs at the bottom edge (z = 0)."""
        return [node.node_id for node in self.nodes if abs(node.z) < 1e-5]

    def get_top_boundary_nodes(self) -> List[int]:
        """Return list of node IDs at the top edge (z = length_m)."""
        return [node.node_id for node in self.nodes if abs(node.z - self.length_m) < 1e-5]



def generate_cylindrical_shell_mesh(radius_m: float = 4.5,
                                    thickness_m: float = 0.004,
                                    length_m: float = 10.0,
                                    n_theta: int = 72,
                                    n_z: int = 30) -> CylindricalMesh:
    """
    Generate structured quad mesh for cylindrical propellant tank shell.
    n_theta: Number of circumferential subdivisions (e.g. 72 for 5-degree increments).
    n_z: Number of axial subdivisions along length.
    """
    nodes: List[ShellNode] = []
    node_id_map: Dict[Tuple[int, int], int] = {}

    cur_node_id = 1
    dz = length_m / max(n_z - 1, 1)
    dtheta = (2.0 * math.pi) / n_theta

    # Generate nodes
    for j in range(n_z):
        z_val = j * dz
        for i in range(n_theta):
            theta_val = i * dtheta
            x_val = radius_m * math.cos(theta_val)
            y_val = radius_m * math.sin(theta_val)

            node = ShellNode(
                node_id=cur_node_id,
                x=x_val,
                y=y_val,
                z=z_val,
                theta_rad=theta_val
            )
            nodes.append(node)
            node_id_map[(i, j)] = cur_node_id
            cur_node_id += 1

    # Generate quad elements
    elements: List[ShellElement] = []
    elem_id = 1
    ds_theta = radius_m * dtheta
    quad_area = ds_theta * dz

    for j in range(n_z - 1):
        for i in range(n_theta):
            i_next = (i + 1) % n_theta  # Wrap around circumference

            n1 = node_id_map[(i, j)]
            n2 = node_id_map[(i_next, j)]
            n3 = node_id_map[(i_next, j + 1)]
            n4 = node_id_map[(i, j + 1)]

            mid_theta = (i + 0.5) * dtheta
            mid_z = (j + 0.5) * dz
            centroid = (radius_m * math.cos(mid_theta), radius_m * math.sin(mid_theta), mid_z)

            elem = ShellElement(
                elem_id=elem_id,
                node_ids=(n1, n2, n3, n4),
                centroid=centroid,
                area_m2=quad_area
            )
            elements.append(elem)
            elem_id += 1

    return CylindricalMesh(
        radius_m=radius_m,
        thickness_m=thickness_m,
        length_m=length_m,
        n_theta=n_theta,
        n_z=n_z,
        nodes=nodes,
        elements=elements
    )
