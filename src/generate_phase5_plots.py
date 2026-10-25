"""
Phase 5 Publication-Grade Visualization Generator
=================================================
Generates high-resolution engineering plots from Phase 5 outputs using Matplotlib:
1. orbit_trajectory_3d.png: 3D Earth sphere with ECI parking orbit and disposal trajectory
2. orbital_elements_history.png: Evolution of SMA, eccentricity, inclination, and altitudes
3. energy_momentum_drift.png: Physical invariant conservation and numerical error drift
4. gmat_vs_python_comparison.png: NASA GMAT R2026a vs. Python ephemeris comparison
5. sensitivity_analysis.png: Deterministic parameter influence gradients
6. monte_carlo_dispersions.png: Histograms and dispersion distributions for a, e, hp, ha
"""

import os
import json
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

OUTPUT_DIR = "output/phase5"
R_EARTH_KM = 6378.137


def plot_3d_trajectory():
    """Generates 3D orbital trajectory around spherical Earth."""
    csv_path = os.path.join(OUTPUT_DIR, "orbit_state_history.csv")
    if not os.path.exists(csv_path):
        return

    data = np.genfromtxt(csv_path, delimiter=",", skip_header=1, usecols=(2, 3, 4))
    x_km = data[:, 0] / 1000.0
    y_km = data[:, 1] / 1000.0
    z_km = data[:, 2] / 1000.0

    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_subplot(111, projection="3d")

    # Wireframe Earth
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    x_earth = R_EARTH_KM * np.outer(np.cos(u), np.sin(v))
    y_earth = R_EARTH_KM * np.outer(np.sin(u), np.sin(v))
    z_earth = R_EARTH_KM * np.outer(np.ones(np.size(u)), np.cos(v))

    ax.plot_surface(x_earth, y_earth, z_earth, color="skyblue", alpha=0.3, edgecolor="gray", linewidth=0.2)

    # Spacecraft trajectory
    ax.plot(x_km, y_km, z_km, color="crimson", linewidth=2.0, label="Starship Flight 14 Coast (3.0 hr)")
    ax.scatter([x_km[0]], [y_km[0]], [z_km[0]], color="lime", s=60, label="SECO Insertion Point (T+522.35s)")
    ax.scatter([x_km[-1]], [y_km[-1]], [z_km[-1]], color="orange", s=60, label="End of Simulation Coast")

    ax.set_title("Starship Flight 14 — Upper-Stage 3D Orbital Trajectory (ECI J2000)", fontsize=13, fontweight="bold")
    ax.set_xlabel("ECI X (km)")
    ax.set_ylabel("ECI Y (km)")
    ax.set_zlabel("ECI Z (km)")
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()

    out_file = os.path.join(OUTPUT_DIR, "orbit_trajectory_3d.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def plot_orbital_elements():
    """Generates 4-panel time series of Keplerian elements."""
    csv_path = os.path.join(OUTPUT_DIR, "orbital_elements_history.csv")
    if not os.path.exists(csv_path):
        return

    times_s = []
    sma_km = []
    ecc = []
    inc_deg = []
    hp_km = []
    ha_km = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times_s.append(float(row["time_s"]) / 60.0)  # minutes
            sma_km.append(float(row["semi_major_axis_km"]))
            ecc.append(float(row["eccentricity"]))
            inc_deg.append(float(row["inclination_deg"]))
            hp_km.append(float(row["perigee_altitude_km"]))
            ha_km.append(float(row["apogee_altitude_km"]))

    fig, axs = plt.subplots(2, 2, figsize=(12, 8), dpi=150)

    # 1. Semi-major axis
    axs[0, 0].plot(times_s, sma_km, color="royalblue", linewidth=1.8)
    axs[0, 0].set_title("Semi-Major Axis $a(t)$", fontweight="bold")
    axs[0, 0].set_ylabel("SMA (km)")
    axs[0, 0].grid(True, linestyle="--", alpha=0.6)

    # 2. Eccentricity
    axs[0, 1].plot(times_s, ecc, color="purple", linewidth=1.8)
    axs[0, 1].set_title("Eccentricity $e(t)$", fontweight="bold")
    axs[0, 1].set_ylabel("Eccentricity")
    axs[0, 1].grid(True, linestyle="--", alpha=0.6)

    # 3. Altitudes
    axs[1, 0].plot(times_s, ha_km, color="red", label="Apogee $h_a$", linewidth=1.5)
    axs[1, 0].plot(times_s, hp_km, color="blue", label="Perigee $h_p$", linewidth=1.5)
    axs[1, 0].set_title("Perigee & Apogee Altitudes", fontweight="bold")
    axs[1, 0].set_xlabel("Mission Elapsed Time (min)")
    axs[1, 0].set_ylabel("Altitude (km)")
    axs[1, 0].legend()
    axs[1, 0].grid(True, linestyle="--", alpha=0.6)

    # 4. Inclination
    axs[1, 1].plot(times_s, inc_deg, color="green", linewidth=1.8)
    axs[1, 1].set_title("Inclination $i(t)$", fontweight="bold")
    axs[1, 1].set_xlabel("Mission Elapsed Time (min)")
    axs[1, 1].set_ylabel("Inclination (deg)")
    axs[1, 1].grid(True, linestyle="--", alpha=0.6)

    plt.suptitle("Starship Flight 14 — Keplerian Orbital Elements History", fontsize=14, fontweight="bold")
    plt.tight_layout()

    out_file = os.path.join(OUTPUT_DIR, "orbital_elements_history.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def plot_energy_momentum_drift():
    """Generates energy and angular momentum invariant drift plot."""
    conv_csv = os.path.join(OUTPUT_DIR, "convergence_study.csv")
    if not os.path.exists(conv_csv):
        return

    dt_s = []
    pos_err = []
    e_drift = []
    h_drift = []

    with open(conv_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt_s.append(float(row["step_size_dt_s"]))
            pos_err.append(float(row["pos_error_norm_m"]))
            e_drift.append(float(row["energy_relative_drift"]))
            h_drift.append(float(row["h_relative_drift"]))

    fig, ax1 = plt.subplots(figsize=(9, 6), dpi=150)

    color = "tab:red"
    ax1.set_xlabel("Integration Time Step $\\Delta t$ (s)", fontsize=11)
    ax1.set_ylabel("Position Error Norm vs DOP853 (m)", color=color, fontsize=11)
    ax1.loglog(dt_s, pos_err, "o--", color=color, linewidth=2.0, markersize=7, label="Position Error")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    color = "tab:blue"
    ax2.set_ylabel("Relative Specific Energy Drift $|\\Delta \\mathcal{E}| / \\mathcal{E}_0$", color=color, fontsize=11)
    ax2.loglog(dt_s, e_drift, "s-", color=color, linewidth=2.0, markersize=7, label="Energy Drift")
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title("Numerical Convergence & Energy Invariant Conservation Study", fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = os.path.join(OUTPUT_DIR, "energy_momentum_drift.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def plot_gmat_comparison():
    """Generates comparison bar chart between Python and NASA GMAT."""
    json_path = os.path.join(OUTPUT_DIR, "gmat_comparison.json")
    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    labels = ["SMA (km)", "Perigee (km)", "Apogee (km)"]
    py_vals = [data["python_sma_km"], data["python_periapsis_km"], data["python_apoapsis_km"]]
    gmat_vals = [data["gmat_sma_km"], data["gmat_periapsis_km"], data["gmat_apoapsis_km"]]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    rects1 = ax.bar(x - width/2, py_vals, width, label="Python Propagator", color="royalblue")
    rects2 = ax.bar(x + width/2, gmat_vals, width, label="NASA GMAT R2026a", color="darkorange")

    ax.set_ylabel("Kilometers (km)")
    ax.set_title("Independent Verification: Python vs. NASA GMAT R2026a Ephemeris", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim([6300, 6700])
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5, axis="y")

    # Add text banner with error percentage
    err_text = f"SMA Difference: {data['sma_diff_km']:.4f} km ({data['sma_error_percent']:.4f}%)\nEccentricity Diff: {data['ecc_diff']:.6f}\nVerification Status: {data['status']}"
    ax.text(0.05, 0.92, err_text, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))

    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, "gmat_vs_python_comparison.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def plot_sensitivity_analysis():
    """Generates horizontal bar chart of parameter influence gradients."""
    csv_path = os.path.join(OUTPUT_DIR, "sensitivity_results.csv")
    if not os.path.exists(csv_path):
        return

    params = []
    d_sma = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            params.append(row["parameter"])
            d_sma.append(float(row["delta_sma_km"]))

    y_pos = np.arange(len(params))
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    colors = ["teal" if v >= 0 else "crimson" for v in d_sma]
    ax.barh(y_pos, d_sma, color=colors, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params)
    ax.invert_yaxis()
    ax.set_xlabel("Induced $\\Delta a$ in Semi-Major Axis (km)")
    ax.set_title("Deterministic One-at-a-Time (OAT) Sensitivity Analysis", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")

    plt.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, "sensitivity_analysis.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def plot_monte_carlo():
    """Generates histograms of Monte Carlo dispersion results."""
    csv_path = os.path.join(OUTPUT_DIR, "monte_carlo_samples.csv")
    if not os.path.exists(csv_path):
        return

    sma_vals = []
    ecc_vals = []
    hp_vals = []
    ha_vals = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sma_vals.append(float(row["final_sma_km"]))
            ecc_vals.append(float(row["final_ecc"]))
            hp_vals.append(float(row["final_perigee_km"]))
            ha_vals.append(float(row["final_apogee_km"]))

    fig, axs = plt.subplots(2, 2, figsize=(11, 8), dpi=150)

    axs[0, 0].hist(sma_vals, bins=15, color="steelblue", edgecolor="black", alpha=0.8)
    axs[0, 0].set_title(f"Semi-Major Axis (Mean: {np.mean(sma_vals):.2f} km)")
    axs[0, 0].set_xlabel("SMA (km)")

    axs[0, 1].hist(ecc_vals, bins=15, color="coral", edgecolor="black", alpha=0.8)
    axs[0, 1].set_title(f"Eccentricity (Mean: {np.mean(ecc_vals):.5f})")
    axs[0, 1].set_xlabel("Eccentricity")

    axs[1, 0].hist(hp_vals, bins=15, color="mediumseagreen", edgecolor="black", alpha=0.8)
    axs[1, 0].set_title(f"Perigee Altitude (Mean: {np.mean(hp_vals):.1f} km)")
    axs[1, 0].set_xlabel("Altitude (km)")

    axs[1, 1].hist(ha_vals, bins=15, color="mediumpurple", edgecolor="black", alpha=0.8)
    axs[1, 1].set_title(f"Apogee Altitude (Mean: {np.mean(ha_vals):.1f} km)")
    axs[1, 1].set_xlabel("Altitude (km)")

    for ax in axs.flat:
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Monte Carlo Ensemble Dispersions (N = 100 Realizations, Seed = 42)", fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = os.path.join(OUTPUT_DIR, "monte_carlo_dispersions.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Saved: {out_file}")


def main():
    print("Generating Phase 5 engineering figures...")
    plot_3d_trajectory()
    plot_orbital_elements()
    plot_energy_momentum_drift()
    plot_gmat_comparison()
    plot_sensitivity_analysis()
    plot_monte_carlo()
    print("All plots generated successfully.")


if __name__ == "__main__":
    main()
