"""
Visualization Module — Starship Flight 14 Ascent Telemetry Plotter
===================================================================
Generates publication-quality aerospace engineering plots for:
1. Altitude vs Elapsed Time
2. Relative & Inertial Velocity vs Time (Mach scale)
3. Dynamic Pressure (Max-Q zone) vs Time
4. Total Propulsion Thrust & Active Engines vs Time
5. Vehicle Mass Depletion & Propellant vs Time
6. Net Non-Gravitational Acceleration (g-load) vs Time
"""

import os
import sys
import csv
import matplotlib
matplotlib.use("Agg") # Non-interactive headless rendering
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "output")

def plot_ascent_telemetry():
    nom_csv = os.path.join(OUT_DIR, "flight14_ascent_nominal.csv")
    anom_csv = os.path.join(OUT_DIR, "flight14_ascent_anomaly.csv")

    if not os.path.exists(nom_csv):
        print(f"Error: {nom_csv} not found.")
        return

    # Load telemetry
    def load_data(path):
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = {k: [] for k in reader.fieldnames}
            for row in reader:
                for k, v in row.items():
                    data[k].append(float(v))
            return {k: np.array(v) for k, v in data.items()}

    nom = load_data(nom_csv)
    has_anom = os.path.exists(anom_csv)
    anom = load_data(anom_csv) if has_anom else None

    # Style configuration
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axs = plt.subplots(3, 2, figsize=(16, 12), dpi=150)
    fig.suptitle("SpaceX Starship Flight 14 — Powered Ascent Dynamics (Starbase to MECO)", fontsize=16, fontweight="bold")

    t = nom["time_s"]

    # 1. Altitude vs Time
    ax = axs[0, 0]
    ax.plot(t, nom["altitude_km"], label="Nominal (33 Engines)", color="#0055ff", lw=2)
    if has_anom:
        ax.plot(t, anom["altitude_km"], label="Anomaly (Engine 17 Out)", color="#ff3300", lw=1.5, ls="--")
    ax.axvline(140.0, color="gray", ls=":", label="MECO (T+140s)")
    ax.set_ylabel("Geodetic Altitude (km)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("Altitude Profile (WGS-84 Ellipsoid)", fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # 2. Velocity & Mach Number
    ax = axs[0, 1]
    ax.plot(t, nom["v_rel_ms"], label="Atmospheric Relative Speed (m/s)", color="#008844", lw=2)
    ax.plot(t, nom["v_inertial_ms"], label="Inertial Speed (m/s)", color="#6600cc", lw=1.5, ls="-.")
    ax.set_ylabel("Velocity (m/s)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("Velocity Evolution (Mach & Inertial)", fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # 3. Dynamic Pressure (Max-Q)
    ax = axs[1, 0]
    ax.plot(t, nom["dynamic_pressure_kpa"], color="#dd6600", lw=2, label="Dynamic Pressure q (kPa)")
    max_q_idx = np.argmax(nom["dynamic_pressure_kpa"])
    t_max_q = t[max_q_idx]
    q_val = nom["dynamic_pressure_kpa"][max_q_idx]
    ax.scatter([t_max_q], [q_val], color="red", zorder=5)
    ax.annotate(f"Max-Q: {q_val:.1f} kPa\nat T+{t_max_q:.1f}s", xy=(t_max_q, q_val),
                xytext=(t_max_q + 10, q_val + 2),
                arrowprops=dict(arrowstyle="->", color="black"), fontweight="bold")
    ax.set_ylabel("Dynamic Pressure (kPa)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("Aerodynamic Load (Max-Q Bucket ~39 kPa)", fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 4. Total Thrust
    ax = axs[1, 1]
    ax.plot(t, nom["thrust_mn"], label="Nominal Thrust (MN)", color="#cc0000", lw=2)
    if has_anom:
        ax.plot(t, anom["thrust_mn"], label="Anomaly Thrust (MN)", color="#ff8800", lw=1.5, ls="--")
    ax.set_ylabel("Cluster Thrust (MN)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("33-Raptor 3 Cluster Thrust & Throttle Program", fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 5. Vehicle Mass Depletion
    ax = axs[2, 0]
    ax.plot(t, nom["mass_tonnes"], label="Total Vehicle Mass (t)", color="#333333", lw=2)
    ax.axhline(200.825 + 138.975, color="purple", ls=":", label="Dry + Payload Mass (~340 t)")
    ax.set_ylabel("Mass (Metric Tons)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("Mass Depletion (-2,841 t Propellant Consumed)", fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 6. Acceleration (g-load)
    ax = axs[2, 1]
    ax.plot(t, nom["accel_g"], label="Nominal Acceleration (g)", color="#0066aa", lw=2)
    if has_anom:
        ax.plot(t, anom["accel_g"], label="Anomaly Acceleration (g)", color="#ff5500", lw=1.5, ls="--")
    ax.set_ylabel("Acceleration (g)", fontweight="bold")
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_title("Structural g-Load Profile (< 2.0g Limit)", fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_plot_path = os.path.join(OUT_DIR, "flight14_phase3_ascent_plots.png")
    plt.savefig(out_plot_path, dpi=150)
    plt.close()
    print(f"  --> Ascent plots generated: {out_plot_path} ({os.path.getsize(out_plot_path):,} bytes)")

if __name__ == "__main__":
    plot_ascent_telemetry()
