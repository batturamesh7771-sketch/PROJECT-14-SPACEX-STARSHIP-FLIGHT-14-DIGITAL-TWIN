"""
Phase 4 Telemetry Plotter — Hot-Staging Dynamics & Dual-Vehicle Trajectory
===========================================================================
Generates publication-quality 6-panel engineering plots for:
1. Relative Center-of-Mass Range and Displacement vs Elapsed Time
2. Relative Velocity & Relative Acceleration (g-load) vs Time
3. Hot-Staging Thrust Schedule & Interstage Plume Impingement Force
4. Dual-Vehicle Altitude Profiles (Booster Return vs Starship Ascent)
5. Vehicle Mass Depletion & Propellant Consumption
6. Downrange vs Altitude Dual-Vehicle Flight Paths
"""

import os
import sys
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "output")

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = {k: [] for k in reader.fieldnames}
        for row in reader:
            for k, v in row.items():
                try:
                    data[k].append(float(v))
                except (ValueError, TypeError):
                    data[k].append(v)
        return {k: np.array(v) if all(isinstance(x, (int, float)) for x in v) else v for k, v in data.items()}

def plot_phase4_telemetry():
    staging_csv = os.path.join(OUT_DIR, "flight14_staging_relative_motion.csv")
    booster_csv = os.path.join(OUT_DIR, "flight14_booster_return.csv")
    ship_csv = os.path.join(OUT_DIR, "flight14_starship_upper_ascent.csv")

    if not os.path.exists(staging_csv):
        print(f"Error: {staging_csv} not found.")
        return

    stg = load_csv(staging_csv)
    bst = load_csv(booster_csv)
    shp = load_csv(ship_csv)

    fig, axs = plt.subplots(3, 2, figsize=(16, 14), dpi=150)
    fig.patch.set_facecolor("#0F141C")

    colors = {
        "ship": "#00D4FF",
        "booster": "#FF6B00",
        "relative": "#00FF88",
        "plume": "#FF0055",
        "text": "#E0E6ED",
        "grid": "#222C38",
        "bg": "#151C26"
    }

    for ax in axs.flat:
        ax.set_facecolor(colors["bg"])
        ax.grid(True, linestyle="--", alpha=0.4, color=colors["grid"])
        ax.tick_params(colors=colors["text"], labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(colors["grid"])

    # -------------------------------------------------------------
    # Plot 1: Center Range & Displacement Increment
    # -------------------------------------------------------------
    ax1 = axs[0, 0]
    t_stg = stg["time_s"]
    ax1.plot(t_stg, stg["center_range_m"], color=colors["relative"], linewidth=2.0, label="Center-of-Mass Range (m)")
    ax1.axvline(142.0, color="#FFCC00", linestyle=":", label="Staging Trigger (T+142.0s)")
    ax1.scatter([143.0, 145.0], [5.50, 48.06], color="#FF0055", zorder=5)
    ax1.annotate("1s post: 5.50 m", (143.0, 5.50), textcoords="offset points", xytext=(15, 5),
                 color=colors["text"], fontsize=8, arrowprops=dict(arrowstyle="->", color=colors["text"]))
    ax1.annotate("3s post: 48.06 m", (145.0, 48.06), textcoords="offset points", xytext=(-60, 15),
                 color=colors["text"], fontsize=8, arrowprops=dict(arrowstyle="->", color=colors["text"]))
    ax1.set_title("Dual-Vehicle Center-of-Mass Separation Distance (L1 3-DOF)", color=colors["text"], fontsize=11, fontweight="bold")
    ax1.set_xlabel("Elapsed Time (s)", color=colors["text"], fontsize=9)
    ax1.set_ylabel("Relative Range (m)", color=colors["text"], fontsize=9)
    ax1.legend(loc="upper left", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    # -------------------------------------------------------------
    # Plot 2: Relative Velocity & Relative Acceleration
    # -------------------------------------------------------------
    ax2 = axs[0, 1]
    ax2_acc = ax2.twinx()
    ax2_acc.set_facecolor("none")
    ax2_acc.grid(False)
    ax2_acc.tick_params(colors=colors["text"], labelsize=9)
    for spine in ax2_acc.spines.values():
        spine.set_color(colors["grid"])

    l1 = ax2.plot(t_stg, stg["relative_velocity_ms"], color=colors["ship"], linewidth=2.0, label="Relative Velocity (m/s)")
    l2 = ax2_acc.plot(t_stg, stg["relative_acceleration_g"], color="#FFCC00", linewidth=1.5, linestyle="--", label="Relative Acceleration (g)")
    ax2.set_title("Relative Velocity & Differential Acceleration", color=colors["text"], fontsize=11, fontweight="bold")
    ax2.set_xlabel("Elapsed Time (s)", color=colors["text"], fontsize=9)
    ax2.set_ylabel("Relative Velocity (m/s)", color=colors["ship"], fontsize=9)
    ax2_acc.set_ylabel("Relative Accel (g)", color="#FFCC00", fontsize=9)
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper left", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    # -------------------------------------------------------------
    # Plot 3: Hot-Staging Thrust & Plume Force
    # -------------------------------------------------------------
    ax3 = axs[1, 0]
    ax3_plume = ax3.twinx()
    ax3_plume.set_facecolor("none")
    ax3_plume.grid(False)
    ax3_plume.tick_params(colors=colors["text"], labelsize=9)
    for spine in ax3_plume.spines.values():
        spine.set_color(colors["grid"])

    l3a = ax3.plot(t_stg, stg["ship_thrust_mn"], color=colors["ship"], linewidth=2.0, label="Ship Thrust (MN)")
    l3b = ax3.plot(t_stg, stg["booster_thrust_mn"], color=colors["booster"], linewidth=2.0, label="Booster Staging Thrust (MN)")
    l3c = ax3_plume.plot(t_stg, stg["plume_force_kn"], color=colors["plume"], linewidth=1.5, linestyle="-.", label="Plume Pushback (kN)")
    ax3.set_title("Hot-Staging Thrust Schedule & Plume Backpressure", color=colors["text"], fontsize=11, fontweight="bold")
    ax3.set_xlabel("Elapsed Time (s)", color=colors["text"], fontsize=9)
    ax3.set_ylabel("Propulsion Thrust (MN)", color=colors["text"], fontsize=9)
    ax3_plume.set_ylabel("Plume Force on Dome (kN)", color=colors["plume"], fontsize=9)
    lines3 = l3a + l3b + l3c
    labels3 = [l.get_label() for l in lines3]
    ax3.legend(lines3, labels3, loc="upper right", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    # -------------------------------------------------------------
    # Plot 4: Dual-Vehicle Altitude Trajectories
    # -------------------------------------------------------------
    ax4 = axs[1, 1]
    ax4.plot(shp["time_s"], shp["altitude_km"], color=colors["ship"], linewidth=2.0, label="Starship Upper Stage")
    ax4.plot(bst["time_s"], bst["altitude_km"], color=colors["booster"], linewidth=2.0, label="Super Heavy Booster Return")
    ax4.axhline(100.0, color="#888888", linestyle=":", alpha=0.7, label="Kármán Line (100 km)")
    ax4.scatter([bst["time_s"][np.argmax(bst["altitude_km"])]], [np.max(bst["altitude_km"])], color=colors["booster"], zorder=5)
    ax4.annotate(f"Booster Apogee: {np.max(bst['altitude_km']):.1f} km",
                 (bst["time_s"][np.argmax(bst["altitude_km"])], np.max(bst["altitude_km"])),
                 textcoords="offset points", xytext=(-40, 10), color=colors["text"], fontsize=8)
    ax4.scatter([shp["time_s"][-1]], [shp["altitude_km"][-1]], color=colors["ship"], zorder=5)
    ax4.annotate(f"SECO Insertion: {shp['altitude_km'][-1]:.1f} km",
                 (shp["time_s"][-1], shp["altitude_km"][-1]),
                 textcoords="offset points", xytext=(-60, -15), color=colors["text"], fontsize=8)
    ax4.set_title("Altitude Profiles Post-Separation", color=colors["text"], fontsize=11, fontweight="bold")
    ax4.set_xlabel("Elapsed Time (s)", color=colors["text"], fontsize=9)
    ax4.set_ylabel("Geodetic Altitude (km)", color=colors["text"], fontsize=9)
    ax4.legend(loc="center right", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    # -------------------------------------------------------------
    # Plot 5: Vehicle Mass Depletion
    # -------------------------------------------------------------
    ax5 = axs[2, 0]
    ax5.plot(shp["time_s"], shp["mass_tonnes"], color=colors["ship"], linewidth=2.0, label="Starship Mass (t)")
    ax5.plot(bst["time_s"], bst["mass_tonnes"], color=colors["booster"], linewidth=2.0, label="Booster Mass (t)")
    ax5.set_title("Independent Mass Depletion (Propellant Consumption)", color=colors["text"], fontsize=11, fontweight="bold")
    ax5.set_xlabel("Elapsed Time (s)", color=colors["text"], fontsize=9)
    ax5.set_ylabel("Total Mass (tonnes)", color=colors["text"], fontsize=9)
    ax5.legend(loc="upper right", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    # -------------------------------------------------------------
    # Plot 6: Downrange vs Altitude Dual Flight Paths
    # -------------------------------------------------------------
    ax6 = axs[2, 1]
    ax6.plot(shp["downrange_km"], shp["altitude_km"], color=colors["ship"], linewidth=2.0, label="Starship to Orbit")
    ax6.plot(bst["downrange_km"], bst["altitude_km"], color=colors["booster"], linewidth=2.0, label="Booster Boostback to Gulf")
    ax6.set_title("Downrange vs Altitude Profiles", color=colors["text"], fontsize=11, fontweight="bold")
    ax6.set_xlabel("Downrange Distance (km)", color=colors["text"], fontsize=9)
    ax6.set_ylabel("Altitude (km)", color=colors["text"], fontsize=9)
    ax6.legend(loc="upper left", facecolor=colors["bg"], edgecolor=colors["grid"], labelcolor=colors["text"], fontsize=8)

    plt.suptitle("STARSHIP FLIGHT 14 — PHASE 4: STAGING SEPARATION & DUAL-VEHICLE DYNAMICS",
                 color=colors["text"], fontsize=14, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])

    plot_path = os.path.join(OUT_DIR, "flight14_phase4_staging_plots.png")
    plt.savefig(plot_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Phase 4 plots generated successfully: {plot_path} ({os.path.getsize(plot_path):,} bytes)")

if __name__ == "__main__":
    plot_phase4_telemetry()
