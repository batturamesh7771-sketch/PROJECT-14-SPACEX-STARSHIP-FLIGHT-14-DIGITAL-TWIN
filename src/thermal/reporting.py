"""
Diagnostic visualization and reporting tools for Phase 9 Aerothermal Reentry & TPS Analysis.
Generates 4-panel engineering plots and exports thermal history CSV and summary JSON.
"""

import os
import csv
import json
from typing import List, Dict, Any, Optional

from src.thermal.conduction_1d import ThermalSolution1D
from src.thermal.material_properties import RTV_BONDLINE_LIMIT_K


def export_thermal_history_csv(times_s: List[float],
                               altitudes_km: List[float],
                               velocities_kms: List[float],
                               q_stag_mw_m2: List[float],
                               q_wind_mw_m2: List[float],
                               solution: ThermalSolution1D,
                               output_csv_path: str) -> str:
    """Export synchronized aerothermal flux and internal temperature history to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)

    with open(output_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time_s",
            "altitude_km",
            "velocity_kms",
            "stagnation_flux_MW_m2",
            "windward_flux_MW_m2",
            "surface_temp_K",
            "surface_temp_degC",
            "bondline_temp_K",
            "bondline_temp_degC",
            "steel_backface_temp_K",
            "steel_backface_temp_degC",
        ])

        for i in range(len(times_s)):
            t = times_s[i]
            alt = altitudes_km[i] if i < len(altitudes_km) else 0.0
            v = velocities_kms[i] if i < len(velocities_kms) else 0.0
            qs = q_stag_mw_m2[i]
            qw = q_wind_mw_m2[i]
            ts = solution.surface_temp_history_k[i]
            tb = solution.bondline_temp_history_k[i]
            tback = solution.backface_temp_history_k[i]

            writer.writerow([
                f"{t:.2f}",
                f"{alt:.3f}",
                f"{v:.4f}",
                f"{qs:.4f}",
                f"{qw:.4f}",
                f"{ts:.2f}",
                f"{ts - 273.15:.2f}",
                f"{tb:.2f}",
                f"{tb - 273.15:.2f}",
                f"{tback:.2f}",
                f"{tback - 273.15:.2f}",
            ])

    return output_csv_path


def generate_thermal_diagnostic_plots(times_s: List[float],
                                      altitudes_km: List[float],
                                      q_stag_mw_m2: List[float],
                                      q_wind_mw_m2: List[float],
                                      solution: ThermalSolution1D,
                                      thickness_study_results: List[Dict[str, Any]],
                                      output_png_path: str) -> Optional[str]:
    """Generate publication-grade 4-panel diagnostic plot of reentry thermal behavior."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[WARNING] Matplotlib not available; skipping thermal plot rendering.")
        return None

    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)

    fig, axs = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle("Starship Flight 14 — Aerothermal Reentry & Thermal Protection (TPS) Analysis",
                 fontsize=14, fontweight="bold", y=0.98)

    # Panel 1: Aerothermal Heat Flux vs Time
    ax1 = axs[0, 0]
    ax1.plot(times_s, q_stag_mw_m2, color="#d62728", lw=2.0, label="Stagnation Flux ($q_{stag}$)")
    ax1.plot(times_s, q_wind_mw_m2, color="#ff7f0e", lw=2.0, label="Windward Acreage Flux ($q_{windward}$)")
    ax1.set_xlabel("Time from Entry Interface [s]")
    ax1.set_ylabel("Heat Flux [MW/m²]")
    ax1.set_title("1. Hypersonic Aerothermal Heating Corridor")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")

    # Twin axis for altitude
    ax1_twin = ax1.twinx()
    ax1_twin.plot(times_s, altitudes_km, color="#1f77b4", lw=1.5, linestyle=":", label="Altitude [km]")
    ax1_twin.set_ylabel("Altitude [km]", color="#1f77b4")
    ax1_twin.tick_params(axis="y", labelcolor="#1f77b4")

    # Panel 2: Temperature Histories & Heat Soak
    ax2 = axs[0, 1]
    ts_degc = [t - 273.15 for t in solution.surface_temp_history_k]
    tb_degc = [t - 273.15 for t in solution.bondline_temp_history_k]
    tback_degc = [t - 273.15 for t in solution.backface_temp_history_k]

    ax2.plot(times_s, ts_degc, color="#d62728", lw=2.0, label="Tile Outer Surface ($T_{surf}$)")
    ax2.plot(times_s, tb_degc, color="#2ca02c", lw=2.2, label="RTV Silicone Bondline ($T_{bond}$)")
    ax2.plot(times_s, tback_degc, color="#9467bd", lw=1.5, linestyle="--", label="Steel Backface ($T_{steel}$)")
    limit_degc = RTV_BONDLINE_LIMIT_K - 273.15
    ax2.axhline(limit_degc, color="red", linestyle=":", lw=1.8, label=f"RTV Limit ({limit_degc:.0f}°C / 500°F)")
    ax2.set_xlabel("Time from Entry Interface [s]")
    ax2.set_ylabel("Temperature [°C]")
    ax2.set_title("2. Transient Thermal Response & Heat Soak Lag")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper left")

    # Annotate lag
    t_peak_surf = solution.time_of_peak_surface_s
    t_peak_bond = solution.time_of_peak_bondline_s
    ax2.annotate(f"Diffusion Lag: {solution.heat_soak_lag_s:.0f}s",
                 xy=(t_peak_bond, max(tb_degc)),
                 xytext=(t_peak_bond - 150, max(tb_degc) + 120),
                 arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=6),
                 fontsize=9, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.6))

    # Panel 3: Through-Thickness Temperature Profiles T(x) at Key Epochs
    ax3 = axs[1, 0]
    mesh = solution.mesh
    x_mm = [x * 1000.0 for x in mesh.node_x]

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for idx, (t_snap, profile) in enumerate(solution.temperature_profiles_by_time.items()):
        c = colors[idx % len(colors)]
        p_degc = [t - 273.15 for t in profile]
        ax3.plot(x_mm, p_degc, color=c, lw=1.8, label=f"t = {t_snap:.0f} s")

    # Mark layer interfaces
    tile_thk_mm = mesh.layers[0].thickness_m * 1000.0
    sip_thk_mm = mesh.layers[1].thickness_m * 1000.0
    ax3.axvline(tile_thk_mm, color="gray", linestyle="--", lw=1.0)
    ax3.axvline(tile_thk_mm + sip_thk_mm, color="gray", linestyle="--", lw=1.0)
    ax3.text(tile_thk_mm * 0.45, 100, "Silica Tile", ha="center", fontsize=9, color="gray")
    ax3.text(tile_thk_mm + sip_thk_mm * 0.5, 100, "SIP", ha="center", fontsize=8, color="gray")
    ax3.text(tile_thk_mm + sip_thk_mm + 1.5, 100, "Steel", ha="center", fontsize=9, color="gray")

    ax3.set_xlabel("Depth Through TPS Stack [mm]")
    ax3.set_ylabel("Temperature [°C]")
    ax3.set_title("3. Spatial Temperature Profiles $T(x)$ Across Layers")
    ax3.grid(True, linestyle="--", alpha=0.6)
    ax3.legend(loc="upper right")

    # Panel 4: Tile Thickness Sizing Trade Study
    ax4 = axs[1, 1]
    thks = [r["tile_thickness_mm"] for r in thickness_study_results]
    peak_bonds = [r["peak_bondline_temp_degC"] for r in thickness_study_results]
    margins = [r["temperature_margin_K"] for r in thickness_study_results]

    ax4.plot(thks, peak_bonds, "o-", color="#2ca02c", lw=2.0, label="Peak Bondline Temp [°C]")
    ax4.axhline(limit_degc, color="red", linestyle=":", lw=1.8, label="RTV Limit (260°C)")
    ax4.set_xlabel("Silica Tile Thickness [mm]")
    ax4.set_ylabel("Peak Bondline Temperature [°C]", color="#2ca02c")
    ax4.set_title("4. Tile Thickness Sizing vs. Bondline Margin")
    ax4.grid(True, linestyle="--", alpha=0.6)

    ax4_twin = ax4.twinx()
    ax4_twin.plot(thks, margins, "s--", color="#1f77b4", lw=1.8, label="Margin [K]")
    ax4_twin.set_ylabel("Thermal Margin [K]", color="#1f77b4")
    ax4_twin.tick_params(axis="y", labelcolor="#1f77b4")
    ax4_twin.axhline(0.0, color="gray", lw=1.0)

    # Combine legends
    lines_1, labels_1 = ax4.get_legend_handles_labels()
    lines_2, labels_2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    plt.tight_layout()
    plt.savefig(output_png_path, dpi=200)
    plt.close()
    return output_png_path
