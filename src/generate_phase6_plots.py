"""
Phase 6 Publication Visualization Generator
===========================================
Generates 10 high-resolution publication figures for the Starship Flight 14
atmospheric reentry, aerothermodynamic heating, guidance, and splashdown simulation.

Outputs:
  - fig01_3d_trajectory_and_ground_track.png
  - fig02_altitude_vs_time.png
  - fig03_speed_and_mach_vs_time.png
  - fig04_dynamic_pressure_profiles.png
  - fig05_deceleration_and_g_loads.png
  - fig06_aerothermal_heating_and_heat_load.png
  - fig07_guidance_crossrange_and_bank.png
  - fig08_terminal_splashdown_assessment.png
  - fig09_monte_carlo_uncertainty_distributions.png
  - fig10_step_size_convergence.png
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Ensure project root in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.astrodynamics.constants import R_EARTH_EQUATORIAL
from src.astrodynamics.state import OrbitalState
from src.reentry import (
    ReentryVehicleConfig,
    USStandardAtmosphere1976,
    CrossrangeBankGuidanceController,
    propagate_reentry,
    run_reentry_monte_carlo,
    great_circle_distance_m
)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def get_default_entry_state() -> OrbitalState:
    r_vec = np.array([5528938.10, -3319172.12, 798881.33], dtype=np.float64)
    v_vec = np.array([3895.7417, 5894.2764, -3257.6110], dtype=np.float64)
    return OrbitalState(r=r_vec, v=v_vec, epoch=6527.315, mass_kg=177272.71)


def generate_all_plots(output_dir: str = "output/phase6/figures"):
    ensure_dir(output_dir)
    print(f"Generating Phase 6 publication figures in: {output_dir}")

    # Set publication plot style
    plt.style.use('default')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 13,
        'lines.linewidth': 1.8,
        'grid.alpha': 0.35,
        'grid.linestyle': '--'
    })

    entry_state = get_default_entry_state()
    veh = ReentryVehicleConfig()
    atm = USStandardAtmosphere1976()

    # 1. Run Baseline Uncontrolled
    print("Propagating baseline uncontrolled trajectory...")
    res_base = propagate_reentry(
        initial_state=entry_state,
        vehicle_config=veh,
        atmosphere=atm,
        guidance=None,
        eval_step_s=1.0,
        scenario_id="SYNTHETIC_REENTRY_BASELINE"
    )

    # 2. Run Guided Closed-Loop
    print("Propagating guided closed-loop trajectory...")
    guidance = CrossrangeBankGuidanceController(
        target_lat_deg=26.50,
        target_lon_deg=-162.00,
        entry_lat_deg=7.1084,
        entry_lon_deg=-58.3341
    )
    res_guided = propagate_reentry(
        initial_state=entry_state,
        vehicle_config=veh,
        atmosphere=atm,
        guidance=guidance,
        eval_step_s=1.0,
        scenario_id="SYNTHETIC_REENTRY_GUIDED"
    )

    t_b = res_base.times_s
    alt_b = res_base.altitudes_km
    v_b = res_base.speeds_km_s
    mach_b = res_base.mach_history
    q_b = res_base.q_dyn_kpa
    g_b = res_base.g_loads
    qdot_b = res_base.heat_fluxes_mw_m2
    qload_b = res_base.heat_loads_mj_m2

    # -------------------------------------------------------------
    # FIGURE 1: 3D Reentry Trajectory & Earth Ground Track
    # -------------------------------------------------------------
    print("Plotting Figure 1: 3D Trajectory & Ground Track...")
    fig = plt.figure(figsize=(14, 6))

    # Subplot 1: 3D ECI Trajectory
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    r_base_km = np.array([s.r_eci for s in res_base.steps]) / 1000.0
    r_guid_km = np.array([s.r_eci for s in res_guided.steps]) / 1000.0

    # Draw Earth wireframe
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 20)
    r_e_km = R_EARTH_EQUATORIAL / 1000.0
    xe = r_e_km * np.outer(np.cos(u), np.sin(v))
    ye = r_e_km * np.outer(np.sin(u), np.sin(v))
    ze = r_e_km * np.outer(np.ones(np.size(u)), np.cos(v))
    ax1.plot_wireframe(xe, ye, ze, color='lightblue', alpha=0.15, linewidth=0.5)

    ax1.plot(r_base_km[:, 0], r_base_km[:, 1], r_base_km[:, 2], 'crimson', label='Uncontrolled Trajectory')
    ax1.plot(r_guid_km[:, 0], r_guid_km[:, 1], r_guid_km[:, 2], 'royalblue', linestyle='--', label='Guided Trajectory')
    ax1.scatter([r_base_km[0, 0]], [r_base_km[0, 1]], [r_base_km[0, 2]], color='green', s=40, label='Entry Interface (120 km)')
    ax1.scatter([r_base_km[-1, 0]], [r_base_km[-1, 1]], [r_base_km[-1, 2]], color='black', marker='x', s=50, label='Splashdown')

    ax1.set_xlabel('X_ECI (km)')
    ax1.set_ylabel('Y_ECI (km)')
    ax1.set_zlabel('Z_ECI (km)')
    ax1.set_title('(a) 3D Inertial Trajectory Arc')
    ax1.legend(loc='upper right', fontsize=8)

    # Subplot 2: Geodetic Ground Track
    ax2 = fig.add_subplot(1, 2, 2)
    lats_b = [s.geodetic_lat_deg for s in res_base.steps]
    lons_b = [s.geodetic_lon_deg for s in res_base.steps]
    lats_g = [s.geodetic_lat_deg for s in res_guided.steps]
    lons_g = [s.geodetic_lon_deg for s in res_guided.steps]

    ax2.plot(lons_b, lats_b, 'crimson', label='Uncontrolled Ground Track')
    ax2.plot(lons_g, lats_g, 'royalblue', linestyle='--', label='Guided Ground Track')
    ax2.scatter(lons_b[0], lats_b[0], color='green', s=50, zorder=5, label=f'Entry (lat {lats_b[0]:.2f}°, lon {lons_b[0]:.2f}°)')
    ax2.scatter(lons_b[-1], lats_b[-1], color='darkred', marker='x', s=70, zorder=5, label=f'Uncontrolled Impact ({lats_b[-1]:.2f}°, {lons_b[-1]:.2f}°)')
    ax2.scatter(lons_g[-1], lats_g[-1], color='navy', marker='o', s=60, zorder=5, label=f'Guided Impact ({lats_g[-1]:.2f}°, {lons_g[-1]:.2f}°)')
    ax2.scatter(-162.0, 26.5, color='orange', marker='*', s=120, zorder=6, label='Modeled Target Corridor (26.5°N, 162.0°W)')

    ax2.set_xlabel('Geodetic Longitude (°E)')
    ax2.set_ylabel('Geodetic Latitude (°N)')
    ax2.set_title('(b) Earth Geodetic Ground Track')
    ax2.grid(True)
    ax2.legend(loc='lower left', fontsize=8)

    fig.suptitle('Starship Flight 14 Reentry: 3D Trajectory Arc & Ground Track', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig01_3d_trajectory_and_ground_track.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 2: Altitude vs. Time
    # -------------------------------------------------------------
    print("Plotting Figure 2: Altitude vs Time...")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(t_b, alt_b, 'royalblue', label='Altitude h(t)')

    # Critical regime annotations
    idx_peak_heat = int(np.argmax(qdot_b))
    idx_peak_q = int(np.argmax(q_b))
    idx_peak_g = int(np.argmax(g_b))
    idx_subsonic = int(np.where(mach_b <= 1.0)[0][0]) if np.any(mach_b <= 1.0) else -1

    ax.scatter([t_b[idx_peak_heat]], [alt_b[idx_peak_heat]], color='crimson', s=60, zorder=5,
               label=f'Peak Heating: {alt_b[idx_peak_heat]:.1f} km (t={t_b[idx_peak_heat]:.0f} s)')
    ax.scatter([t_b[idx_peak_q]], [alt_b[idx_peak_q]], color='darkorange', s=60, zorder=5,
               label=f'Peak Dynamic Pressure: {alt_b[idx_peak_q]:.1f} km (t={t_b[idx_peak_q]:.0f} s)')
    ax.scatter([t_b[idx_peak_g]], [alt_b[idx_peak_g]], color='purple', s=60, zorder=5,
               label=f'Peak Deceleration: {alt_b[idx_peak_g]:.1f} km (t={t_b[idx_peak_g]:.0f} s)')
    if idx_subsonic >= 0:
        ax.scatter([t_b[idx_subsonic]], [alt_b[idx_subsonic]], color='darkgreen', marker='s', s=50, zorder=5,
                   label=f'Subsonic Transition (M=1.0): {alt_b[idx_subsonic]:.1f} km (t={t_b[idx_subsonic]:.0f} s)')

    ax.axhline(120.0, color='gray', linestyle=':', label='Entry Interface (120 km)')
    ax.axhline(0.0, color='black', linestyle='-', linewidth=1.2, label='Ocean Surface Datum (0 km)')

    ax.set_xlabel('Entry Elapsed Time (s)')
    ax.set_ylabel('Geodetic Altitude (km)')
    ax.set_title('Reentry Altitude Profile & Critical Flight Events', fontweight='bold')
    ax.set_xlim(0, max(t_b) * 1.05)
    ax.set_ylim(-2, 130)
    ax.grid(True)
    ax.legend(loc='upper right', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig02_altitude_vs_time.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 3: Speed & Mach vs. Time
    # -------------------------------------------------------------
    print("Plotting Figure 3: Speed & Mach vs Time...")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    p1 = ax1.plot(t_b, v_b * 1000.0, 'navy', label='Atmospheric-Relative Speed (m/s)')
    p2 = ax2.plot(t_b, mach_b, 'crimson', linestyle='--', label='Mach Number')

    ax1.set_xlabel('Entry Elapsed Time (s)')
    ax1.set_ylabel('Atmospheric-Relative Speed (m/s)', color='navy')
    ax2.set_ylabel('Mach Number', color='crimson')
    ax1.tick_params(axis='y', labelcolor='navy')
    ax2.tick_params(axis='y', labelcolor='crimson')

    # Hypersonic / Supersonic threshold lines
    ax2.axhline(5.0, color='orange', linestyle=':', label='Hypersonic Boundary (M=5)')
    ax2.axhline(1.0, color='green', linestyle=':', label='Sonic Boundary (M=1)')

    lines = p1 + p2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', framealpha=0.9)
    ax1.grid(True)
    plt.title('Hypersonic Deceleration: Speed & Mach History', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig03_speed_and_mach_vs_time.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 4: Dynamic Pressure Profiles
    # -------------------------------------------------------------
    print("Plotting Figure 4: Dynamic Pressure Profiles...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(t_b, q_b, 'darkorange', label='q_dyn(t)')
    ax1.scatter([t_b[idx_peak_q]], [q_b[idx_peak_q]], color='red', s=60, zorder=5,
                label=f'Peak q = {q_b[idx_peak_q]:.1f} kPa\n(t = {t_b[idx_peak_q]:.0f} s)')
    ax1.set_xlabel('Entry Elapsed Time (s)')
    ax1.set_ylabel('Dynamic Pressure (kPa)')
    ax1.set_title('(a) Dynamic Pressure vs. Time')
    ax1.grid(True)
    ax1.legend(loc='upper right')

    ax2.plot(q_b, alt_b, 'darkorange', label='Altitude vs q_dyn')
    ax2.scatter([q_b[idx_peak_q]], [alt_b[idx_peak_q]], color='red', s=60, zorder=5,
                label=f'Peak q at alt = {alt_b[idx_peak_q]:.1f} km')
    ax2.set_xlabel('Dynamic Pressure (kPa)')
    ax2.set_ylabel('Geodetic Altitude (km)')
    ax2.set_title('(b) Dynamic Pressure vs. Altitude')
    ax2.grid(True)
    ax2.legend(loc='upper right')

    fig.suptitle('Aerodynamic Pressure Regimes', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig04_dynamic_pressure_profiles.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 5: Deceleration & Structural g-Loads
    # -------------------------------------------------------------
    print("Plotting Figure 5: Deceleration & g-Loads...")
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(t_b, g_b, 'purple', label='Apparent Structural Deceleration (g)')
    ax.scatter([t_b[idx_peak_g]], [g_b[idx_peak_g]], color='crimson', s=70, zorder=5,
               label=f'Peak Deceleration: {g_b[idx_peak_g]:.2f} g (t={t_b[idx_peak_g]:.0f} s, alt={alt_b[idx_peak_g]:.1f} km)')

    ax.axhline(5.0, color='darkred', linestyle='--', label='Structural Design Limit (5.0 g)')
    ax.axhline(3.0, color='darkorange', linestyle=':', label='Human Tolerance Reference (3.0 g)')

    ax.set_xlabel('Entry Elapsed Time (s)')
    ax.set_ylabel('Total Aerodynamic Deceleration (Earth g)')
    ax.set_title('Apparent Deceleration & Structural G-Load Profile', fontweight='bold')
    ax.set_ylim(0, max(5.5, max(g_b) * 1.2))
    ax.grid(True)
    ax.legend(loc='upper right', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig05_deceleration_and_g_loads.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 6: Aerothermal Heating & Cumulative Heat Load
    # -------------------------------------------------------------
    print("Plotting Figure 6: Aerothermal Heating & Heat Load...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    p1 = ax1.plot(t_b, qdot_b, 'crimson', label='Stagnation Heat Flux (MW/m²)')
    ax1_twin = ax1.twinx()
    p2 = ax1_twin.plot(t_b, qload_b, 'darkblue', linestyle='--', label='Cumulative Heat Load (MJ/m²)')

    ax1.set_xlabel('Entry Elapsed Time (s)')
    ax1.set_ylabel('Stagnation Heat Flux (MW/m²)', color='crimson')
    ax1_twin.set_ylabel('Integrated Heat Load (MJ/m²)', color='darkblue')
    ax1.tick_params(axis='y', labelcolor='crimson')
    ax1_twin.tick_params(axis='y', labelcolor='darkblue')

    ax1.scatter([t_b[idx_peak_heat]], [qdot_b[idx_peak_heat]], color='black', s=50, zorder=5,
                label=f'Peak Flux: {qdot_b[idx_peak_heat]:.3f} MW/m²\n({qdot_b[idx_peak_heat]*100.0:.1f} W/cm²)')
    lines = p1 + p2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', framealpha=0.9)
    ax1.set_title('(a) Heat Flux & Cumulative Load vs. Time')
    ax1.grid(True)

    # Flux vs altitude
    ax2.plot(qdot_b, alt_b, 'crimson', label='q_dot_stag vs Altitude')
    ax2.scatter([qdot_b[idx_peak_heat]], [alt_b[idx_peak_heat]], color='black', s=50, zorder=5,
                label=f'Peak at alt = {alt_b[idx_peak_heat]:.1f} km')
    ax2.set_xlabel('Stagnation Heat Flux (MW/m²)')
    ax2.set_ylabel('Geodetic Altitude (km)')
    ax2.set_title('(b) Heat Flux vs. Altitude')
    ax2.grid(True)
    ax2.legend(loc='upper right')

    fig.suptitle('Sutton-Graves Convective Aerothermal Heating Environment', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig06_aerothermal_heating_and_heat_load.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 7: Guidance Crossrange & Bank Command
    # -------------------------------------------------------------
    print("Plotting Figure 7: Guidance & Crossrange Error...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    cross_b = [s.crossrange_error_km for s in res_base.steps]
    cross_g = [s.crossrange_error_km for s in res_guided.steps]
    bank_g = res_guided.bank_angles_deg

    ax1.plot(res_base.times_s, cross_b, 'crimson', label='Uncontrolled Crossrange Error')
    ax1.plot(res_guided.times_s, cross_g, 'royalblue', label='Guided Crossrange Error')
    ax1.axhline(0.0, color='black', linestyle=':', label='Null Crossrange Target Track')
    ax1.set_ylabel('Crossrange Error (km)')
    ax1.set_title('(a) Cross-Track Trajectory Error vs. Target Track')
    ax1.grid(True)
    ax1.legend(loc='upper right')

    ax2.plot(res_guided.times_s, bank_g, 'seagreen', label='Commanded Bank Angle σ(t)')
    ax2.axhline(45.0, color='red', linestyle='--', label='Bank Saturation Bound (±45°)')
    ax2.axhline(-45.0, color='red', linestyle='--')
    ax2.set_xlabel('Entry Elapsed Time (s)')
    ax2.set_ylabel('Bank Angle (°)')
    ax2.set_title('(b) Closed-Loop Guidance Bank Command History')
    ax2.grid(True)
    ax2.legend(loc='upper right')

    fig.suptitle('Closed-Loop Bank Angle Modulation & Crossrange Nulling', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig07_guidance_crossrange_and_bank.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 8: Terminal Splashdown Assessment
    # -------------------------------------------------------------
    print("Plotting Figure 8: Terminal Splashdown Assessment...")
    fig, ax = plt.subplots(figsize=(8, 8))

    # Target circle (radius 50 km)
    theta_circ = np.linspace(0, 2 * np.pi, 200)
    r_target_km = 50.0
    x_circ = r_target_km * np.cos(theta_circ)
    y_circ = r_target_km * np.sin(theta_circ)

    ax.plot(x_circ, y_circ, 'darkorange', linewidth=2.0, label='Modeled Target Corridor (R = 50 km)')
    ax.fill(x_circ, y_circ, 'moccasin', alpha=0.3)

    # Secondary buffer 100 km
    ax.plot(100.0 * np.cos(theta_circ), 100.0 * np.sin(theta_circ), 'gray', linestyle=':', label='Contingency Corridor (R = 100 km)')

    # Target center at (0, 0)
    ax.scatter(0.0, 0.0, color='red', marker='+', s=150, linewidth=2.0, label='Target Center (26.5°N, 162.0°W)')

    # Guided and uncontrolled terminal relative offsets
    term_b = res_base.terminal_assessment
    term_g = res_guided.terminal_assessment

    ax.scatter(term_b.crossrange_error_km, term_b.downrange_error_km, color='crimson', marker='x', s=100, linewidth=2.0,
               label=f'Uncontrolled Impact (Miss: {term_b.miss_distance_km:.1f} km)')
    ax.scatter(term_g.crossrange_error_km, term_g.downrange_error_km, color='navy', marker='o', s=90,
               label=f'Guided Impact (Miss: {term_g.miss_distance_km:.1f} km)')

    # Draw miss vectors
    ax.annotate('', xy=(term_b.crossrange_error_km, term_b.downrange_error_km), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="crimson", lw=1.2))
    ax.annotate('', xy=(term_g.crossrange_error_km, term_g.downrange_error_km), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="navy", lw=1.2))

    ax.set_xlabel('Crossrange Relative Offset (km)')
    ax.set_ylabel('Downrange Relative Offset (km)')
    ax.set_title('Terminal Ocean Splashdown Target Assessment', fontweight='bold')
    ax.grid(True)
    ax.axis('equal')
    ax.legend(loc='lower left', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig08_terminal_splashdown_assessment.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 9: Monte Carlo Uncertainty Distributions
    # -------------------------------------------------------------
    print("Plotting Figure 9: Monte Carlo Uncertainty Distributions...")
    print("Running 30-sample Monte Carlo ensemble for visualization...")
    mc_summary = run_reentry_monte_carlo(
        baseline_state=entry_state,
        vehicle_config=veh,
        atmosphere=atm,
        guidance=guidance,
        sample_count=30,
        seed=42
    )

    valid_samples = [s for s in mc_summary.samples if s["status"] == "COMPLETED"]
    q_vals = [s["peak_q_kpa"] for s in valid_samples]
    g_vals = [s["peak_g"] for s in valid_samples]
    heat_vals = [s["peak_heat_mw_m2"] for s in valid_samples]
    load_vals = [s["total_heat_load_mj_m2"] for s in valid_samples]
    time_vals = [s["impact_time_s"] for s in valid_samples]
    miss_vals = [s["miss_distance_km"] for s in valid_samples]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    axes[0].hist(q_vals, bins=8, color='orange', edgecolor='black', alpha=0.7)
    axes[0].set_title(f'Peak Dynamic Pressure (kPa)\nMean: {np.mean(q_vals):.1f} ± {np.std(q_vals):.1f}')
    axes[0].set_xlabel('q_max (kPa)')
    axes[0].grid(True)

    axes[1].hist(g_vals, bins=8, color='purple', edgecolor='black', alpha=0.7)
    axes[1].set_title(f'Peak Deceleration (g)\nMean: {np.mean(g_vals):.2f} ± {np.std(g_vals):.2f}')
    axes[1].set_xlabel('Deceleration (g)')
    axes[1].grid(True)

    axes[2].hist(heat_vals, bins=8, color='crimson', edgecolor='black', alpha=0.7)
    axes[2].set_title(f'Peak Heat Flux (MW/m²)\nMean: {np.mean(heat_vals):.3f} ± {np.std(heat_vals):.3f}')
    axes[2].set_xlabel('Flux (MW/m²)')
    axes[2].grid(True)

    axes[3].hist(load_vals, bins=8, color='darkblue', edgecolor='black', alpha=0.7)
    axes[3].set_title(f'Total Heat Load (MJ/m²)\nMean: {np.mean(load_vals):.1f} ± {np.std(load_vals):.1f}')
    axes[3].set_xlabel('Heat Load (MJ/m²)')
    axes[3].grid(True)

    axes[4].hist(time_vals, bins=8, color='teal', edgecolor='black', alpha=0.7)
    axes[4].set_title(f'Entry Duration (s)\nMean: {np.mean(time_vals):.1f} ± {np.std(time_vals):.1f}')
    axes[4].set_xlabel('Duration (s)')
    axes[4].grid(True)

    axes[5].hist(miss_vals, bins=8, color='brown', edgecolor='black', alpha=0.7)
    axes[5].set_title(f'Target Miss Distance (km)\nMean: {np.mean(miss_vals):.1f} ± {np.std(miss_vals):.1f}')
    axes[5].set_xlabel('Miss Distance (km)')
    axes[5].grid(True)

    fig.suptitle('Monte Carlo Stochastic Trajectory Dispersion (N=30, Seed=42)', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig09_monte_carlo_uncertainty_distributions.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 10: Step-Size Convergence Analysis
    # -------------------------------------------------------------
    print("Plotting Figure 10: Step-Size Convergence Analysis...")
    step_sizes = [0.25, 0.50, 1.0, 2.0, 5.0]
    impact_times = []
    peak_qs = []
    peak_gs = []
    final_pos_diffs = []

    # Reference run with fine step
    ref_sol = propagate_reentry(entry_state, veh, atm, guidance=None, eval_step_s=0.25)
    ref_pos = ref_sol.steps[-1].r_eci

    for dt in step_sizes:
        sol = propagate_reentry(entry_state, veh, atm, guidance=None, eval_step_s=dt)
        impact_times.append(sol.impact_time_s)
        peak_qs.append(sol.peak_dynamic_pressure_pa / 1000.0)
        peak_gs.append(sol.peak_apparent_g_load)
        final_pos_diffs.append(np.linalg.norm(sol.steps[-1].r_eci - ref_pos))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(step_sizes, final_pos_diffs, 'bo-', linewidth=1.5, markersize=6)
    ax1.set_xlabel('Evaluation Time Step Δt (s)')
    ax1.set_ylabel('Terminal Position Difference vs. Ref (m)')
    ax1.set_title('(a) Terminal State Numerical Convergence')
    ax1.grid(True)

    ax2.plot(step_sizes, peak_qs, 'rs-', label='Peak Dynamic Pressure (kPa)')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(step_sizes, peak_gs, 'g^-', label='Peak Deceleration (g)')
    ax2.set_xlabel('Evaluation Time Step Δt (s)')
    ax2.set_ylabel('Peak q (kPa)', color='red')
    ax2_twin.set_ylabel('Peak g-load', color='green')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2_twin.tick_params(axis='y', labelcolor='green')
    ax2.set_title('(b) Peak Metric Invariance with Step Size')
    ax2.grid(True)

    fig.suptitle('Numerical Integration Step-Size Convergence (DOP853 / RK4)', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig10_step_size_convergence.png"), dpi=300)
    plt.close()

    print(f"All 10 Phase 6 publication figures successfully generated in {output_dir}")


if __name__ == '__main__':
    generate_all_plots()
