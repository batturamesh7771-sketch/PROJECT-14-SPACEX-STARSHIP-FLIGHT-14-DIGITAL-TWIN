"""
High-fidelity 1D transient finite-difference thermal conduction solver for composite TPS stacks.
Solves non-linear 1D heat equation with temperature-dependent properties k(T), cp(T),
surface radiative equilibrium, multi-layer interfaces (Tile, SIP/RTV, Steel substrate),
and Thomas algorithm (TDMA) implicit time-stepping.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import math
import numpy as np

from src.thermal.material_properties import (
    MaterialProperties,
    get_silica_tile_properties,
    get_sip_felt_properties,
    get_stainless_steel_properties,
    STEFAN_BOLTZMANN,
    RTV_BONDLINE_LIMIT_K,
)


@dataclass
class ThermalStackLayer:
    """A discrete physical layer in the 1D thermal protection stack."""
    name: str
    material: MaterialProperties
    thickness_m: float
    num_nodes: int


@dataclass
class ThermalStackMesh:
    """Discretized 1D spatial mesh across composite layers."""
    layers: List[ThermalStackLayer]
    total_thickness_m: float
    total_nodes: int
    node_x: List[float]                  # Spatial coordinate of each node [m]
    node_dx: List[float]                 # Tributary thickness around each node [m]
    node_layer_idx: List[int]            # Layer index for each node
    bondline_node_idx: int               # Index of node corresponding to RTV bondline
    steel_backface_node_idx: int         # Index of innermost steel backface node


def generate_thermal_stack_mesh(tile_thickness_m: float = 0.028,
                                sip_thickness_m: float = 0.0025,
                                steel_thickness_m: float = 0.0040,
                                n_tile: int = 35,
                                n_sip: int = 10,
                                n_steel: int = 10) -> ThermalStackMesh:
    """
    Generate discretized spatial mesh across the 3 layers:
      1. Ceramic Silica Tile (0 to L_tile)
      2. Strain Isolation Pad (SIP) / RTV Adhesive (L_tile to L_tile + L_sip)
      3. 304L Stainless Steel Tank Skin (to L_total)
    """
    tile_mat = get_silica_tile_properties()
    sip_mat = get_sip_felt_properties()
    steel_mat = get_stainless_steel_properties()

    layers = [
        ThermalStackLayer("Ceramic_Tile", tile_mat, tile_thickness_m, n_tile),
        ThermalStackLayer("SIP_RTV_Bond", sip_mat, sip_thickness_m, n_sip),
        ThermalStackLayer("304L_Steel_Skin", steel_mat, steel_thickness_m, n_steel),
    ]

    node_x: List[float] = []
    node_dx: List[float] = []
    node_layer_idx: List[int] = []

    cur_x = 0.0

    # Layer 0: Tile
    dx_tile = tile_thickness_m / (n_tile - 1)
    for i in range(n_tile):
        x = i * dx_tile
        node_x.append(x)
        node_dx.append(dx_tile)
        node_layer_idx.append(0)
    cur_x = tile_thickness_m

    # Layer 1: SIP (starts after tile)
    bondline_idx = len(node_x) - 1  # Interface between tile and SIP is the bondline
    dx_sip = sip_thickness_m / n_sip
    for i in range(1, n_sip + 1):
        x = cur_x + i * dx_sip
        node_x.append(x)
        node_dx.append(dx_sip)
        node_layer_idx.append(1)
    cur_x += sip_thickness_m

    # Layer 2: Steel skin
    dx_steel = steel_thickness_m / n_steel
    for i in range(1, n_steel + 1):
        x = cur_x + i * dx_steel
        node_x.append(x)
        node_dx.append(dx_steel)
        node_layer_idx.append(2)
    cur_x += steel_thickness_m

    tot_nodes = len(node_x)
    backface_idx = tot_nodes - 1

    return ThermalStackMesh(
        layers=layers,
        total_thickness_m=cur_x,
        total_nodes=tot_nodes,
        node_x=node_x,
        node_dx=node_dx,
        node_layer_idx=node_layer_idx,
        bondline_node_idx=bondline_idx,
        steel_backface_node_idx=backface_idx
    )


@dataclass
class ThermalSolution1D:
    """Complete 1D transient thermal profile history across trajectory."""
    time_history_s: List[float]
    surface_temp_history_k: List[float]
    bondline_temp_history_k: List[float]
    backface_temp_history_k: List[float]
    peak_surface_temp_k: float
    time_of_peak_surface_s: float
    peak_bondline_temp_k: float
    time_of_peak_bondline_s: float
    peak_backface_temp_k: float
    bondline_thermal_margin_k: float   # RTV_BONDLINE_LIMIT_K - peak_bondline_temp_k
    heat_soak_lag_s: float             # time_of_peak_bondline - time_of_peak_surface
    temperature_profiles_by_time: Dict[float, List[float]]  # Snapshots of T(x) at specific times
    mesh: ThermalStackMesh

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_simulation_time_s": round(self.time_history_s[-1], 1),
            "peak_surface_temp_K": round(self.peak_surface_temp_k, 2),
            "peak_surface_temp_degC": round(self.peak_surface_temp_k - 273.15, 2),
            "time_of_peak_surface_s": round(self.time_of_peak_surface_s, 1),
            "peak_bondline_temp_K": round(self.peak_bondline_temp_k, 2),
            "peak_bondline_temp_degC": round(self.peak_bondline_temp_k - 273.15, 2),
            "time_of_peak_bondline_s": round(self.time_of_peak_bondline_s, 1),
            "rtv_bondline_limit_K": round(RTV_BONDLINE_LIMIT_K, 2),
            "bondline_thermal_margin_K": round(self.bondline_thermal_margin_k, 2),
            "heat_soak_lag_seconds": round(self.heat_soak_lag_s, 1),
            "peak_backface_temp_K": round(self.peak_backface_temp_k, 2),
            "peak_backface_temp_degC": round(self.peak_backface_temp_k - 273.15, 2),
            "tile_thickness_mm": round(self.mesh.layers[0].thickness_m * 1000.0, 1),
            "total_stack_thickness_mm": round(self.mesh.total_thickness_m * 1000.0, 1),
        }


class TransientThermalSolver1D:
    """1D implicit non-linear thermal conduction solver with surface radiation."""

    def __init__(self, mesh: ThermalStackMesh, initial_temp_k: float = 293.15):
        self.mesh = mesh
        self.initial_temp_k = initial_temp_k

    def solve_trajectory(self,
                         times_s: List[float],
                         heat_flux_w_m2: List[float],
                         ambient_temp_k: float = 220.0,
                         backface_adiabatic: bool = True,
                         backface_htc: float = 10.0,
                         internal_fluid_temp_k: float = 290.0) -> ThermalSolution1D:
        """
        Integrate 1D thermal conduction forward in time along entry trajectory.
        times_s: Sequence of trajectory timestamps [s]
        heat_flux_w_m2: Aero heat flux incident on outer tile surface [W/m^2]
        """
        n_nodes = self.mesh.total_nodes
        # Initialize temperature vector
        T = np.full(n_nodes, self.initial_temp_k, dtype=np.float64)

        surface_history: List[float] = []
        bondline_history: List[float] = []
        backface_history: List[float] = []

        # Store snapshots at key times (e.g. 0s, 25%, 50%, 75%, 100% of flight)
        n_steps = len(times_s)
        snapshot_indices = [
            0,
            n_steps // 4,
            n_steps // 2,
            (3 * n_steps) // 4,
            n_steps - 1
        ]
        snapshots: Dict[float, List[float]] = {}

        # Node layer properties lookup
        layer_materials = [layer.material for layer in self.mesh.layers]
        emissivity = self.mesh.layers[0].material.emissivity
        rad_coeff = emissivity * STEFAN_BOLTZMANN

        for step_idx in range(n_steps):
            t_curr = times_s[step_idx]
            q_aero = heat_flux_w_m2[step_idx]

            if step_idx == 0:
                dt = times_s[1] - times_s[0] if n_steps > 1 else 1.0
            else:
                dt = times_s[step_idx] - times_s[step_idx - 1]
            dt = max(dt, 0.01)

            # Assemble Tridiagonal Matrix: A * T^{n+1} = B
            # a_i * T_{i-1}^{n+1} + b_i * T_i^{n+1} + c_i * T_{i+1}^{n+1} = d_i
            a = np.zeros(n_nodes, dtype=np.float64)
            b = np.zeros(n_nodes, dtype=np.float64)
            c = np.zeros(n_nodes, dtype=np.float64)
            d = np.zeros(n_nodes, dtype=np.float64)

            # Compute local properties k_i and (rho*cp)_i
            k_nodes = np.zeros(n_nodes, dtype=np.float64)
            cp_nodes = np.zeros(n_nodes, dtype=np.float64)
            rho_nodes = np.zeros(n_nodes, dtype=np.float64)

            for i in range(n_nodes):
                mat = layer_materials[self.mesh.node_layer_idx[i]]
                k_nodes[i] = mat.get_conductivity(T[i])
                cp_nodes[i] = mat.get_specific_heat(T[i])
                rho_nodes[i] = mat.density_kg_m3

            # Interior nodes (i = 1 to n_nodes - 2)
            for i in range(1, n_nodes - 1):
                dx_left = self.mesh.node_x[i] - self.mesh.node_x[i - 1]
                dx_right = self.mesh.node_x[i + 1] - self.mesh.node_x[i]
                dx_avg = 0.5 * (dx_left + dx_right)

                k_left = 2.0 * k_nodes[i - 1] * k_nodes[i] / (k_nodes[i - 1] + k_nodes[i] + 1e-12)
                k_right = 2.0 * k_nodes[i] * k_nodes[i + 1] / (k_nodes[i] + k_nodes[i + 1] + 1e-12)

                thermal_capacitance = rho_nodes[i] * cp_nodes[i] * dx_avg / dt

                conductance_left = k_left / dx_left
                conductance_right = k_right / dx_right

                a[i] = -conductance_left
                b[i] = thermal_capacitance + conductance_left + conductance_right
                c[i] = -conductance_right
                d[i] = thermal_capacitance * T[i]

            # Node 0: Outer Tile Surface (x = 0)
            # Energy balance: rho*cp*(dx/2)/dt * (T_0^{n+1} - T_0^n) = q_aero - q_rad - q_cond_into_tile
            # Linearize radiation: T_0^4 ~ 4*(T_0^n)^3 * T_0^{n+1} - 3*(T_0^n)^4
            dx_0 = self.mesh.node_x[1] - self.mesh.node_x[0]
            k_half = 2.0 * k_nodes[0] * k_nodes[1] / (k_nodes[0] + k_nodes[1] + 1e-12)
            cap_0 = rho_nodes[0] * cp_nodes[0] * (0.5 * dx_0) / dt
            cond_0 = k_half / dx_0

            t_old_0 = T[0]
            h_rad_lin = 4.0 * rad_coeff * (t_old_0 ** 3)
            q_rad_const = 3.0 * rad_coeff * (t_old_0 ** 4) + rad_coeff * (ambient_temp_k ** 4)

            b[0] = cap_0 + cond_0 + h_rad_lin
            c[0] = -cond_0
            d[0] = cap_0 * t_old_0 + q_aero + q_rad_const

            # Node n_nodes - 1: Inner Backface (x = L_total)
            dx_end = self.mesh.node_x[-1] - self.mesh.node_x[-2]
            k_end_half = 2.0 * k_nodes[-2] * k_nodes[-1] / (k_nodes[-2] + k_nodes[-1] + 1e-12)
            cap_end = rho_nodes[-1] * cp_nodes[-1] * (0.5 * dx_end) / dt
            cond_end = k_end_half / dx_end

            if backface_adiabatic:
                # Insulated: dT/dx = 0
                a[-1] = -cond_end
                b[-1] = cap_end + cond_end
                d[-1] = cap_end * T[-1]
            else:
                # Convective backface loss
                a[-1] = -cond_end
                b[-1] = cap_end + cond_end + backface_htc
                d[-1] = cap_end * T[-1] + backface_htc * internal_fluid_temp_k

            # Solve Tridiagonal System using Thomas Algorithm
            T = self._solve_tridiagonal(a, b, c, d)

            # Record history
            surface_history.append(float(T[0]))
            bondline_history.append(float(T[self.mesh.bondline_node_idx]))
            backface_history.append(float(T[self.mesh.steel_backface_node_idx]))

            if step_idx in snapshot_indices:
                snapshots[round(t_curr, 1)] = T.tolist()

        # Compute key metrics
        peak_surf = max(surface_history)
        t_peak_surf = times_s[surface_history.index(peak_surf)]

        peak_bond = max(bondline_history)
        t_peak_bond = times_s[bondline_history.index(peak_bond)]

        peak_back = max(backface_history)
        bond_margin = RTV_BONDLINE_LIMIT_K - peak_bond
        heat_lag = t_peak_bond - t_peak_surf

        return ThermalSolution1D(
            time_history_s=times_s,
            surface_temp_history_k=surface_history,
            bondline_temp_history_k=bondline_history,
            backface_temp_history_k=backface_history,
            peak_surface_temp_k=peak_surf,
            time_of_peak_surface_s=t_peak_surf,
            peak_bondline_temp_k=peak_bond,
            time_of_peak_bondline_s=t_peak_bond,
            peak_backface_temp_k=peak_back,
            bondline_thermal_margin_k=bond_margin,
            heat_soak_lag_s=heat_lag,
            temperature_profiles_by_time=snapshots,
            mesh=self.mesh
        )

    @staticmethod
    def _solve_tridiagonal(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
        """Thomas algorithm (TDMA) for solving tridiagonal linear systems in O(N)."""
        n = len(d)
        c_prime = np.zeros(n - 1, dtype=np.float64)
        d_prime = np.zeros(n, dtype=np.float64)

        c_prime[0] = c[0] / b[0]
        d_prime[0] = d[0] / b[0]

        for i in range(1, n - 1):
            denom = b[i] - a[i] * c_prime[i - 1]
            c_prime[i] = c[i] / denom
            d_prime[i] = (d[i] - a[i] * d_prime[i - 1]) / denom

        denom = b[-1] - a[-1] * c_prime[-1]
        d_prime[-1] = (d[-1] - a[-1] * d_prime[-2]) / denom

        # Back-substitution
        x = np.zeros(n, dtype=np.float64)
        x[-1] = d_prime[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_prime[i] - c_prime[i] * x[i + 1]

        return x
