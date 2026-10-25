"""
Visualization, plot generation, and reporting for Phase 7 terminal landing dynamics.
"""

from typing import List, Dict, Any, Optional
import os
import json
from src.landing.state import LandingState
from src.landing.touchdown import TouchdownReport


def generate_plots(history: List[LandingState],
                   report: TouchdownReport,
                   output_path: str,
                   title_prefix: str = "Synthetic Reusable Landing Demo") -> Optional[str]:
    """
    Generate publication-grade 6-panel trajectory figures if matplotlib is installed.
    Gracefully skips if matplotlib is not available in the current Python environment.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[WARNING] Matplotlib not found in current Python interpreter; skipping plot rendering.")
        return None

    times = [s.time_s for s in history]
    alts = [s.z for s in history]
    vzs = [s.vz for s in history]
    vxs = [s.vx for s in history]
    pitches = [s.pitch_deg for s in history]
    thrusts = [s.thrust_N / 1e6 for s in history]  # MN
    masses = [s.mass_kg / 1e3 for s in history]    # tonnes
    gs = [s.apparent_g for s in history]
    xs = [s.x for s in history]

    fig, axs = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle(f"{title_prefix} — Terminal Dynamics\nOutcome: {report.outcome_classification}", fontsize=14, fontweight="bold")

    # 1. Altitude vs Time
    axs[0, 0].plot(times, alts, "b-", linewidth=2, label="Altitude (m)")
    axs[0, 0].axhline(0, color="k", linestyle="--", alpha=0.7, label="Pad Datum (0 m)")
    axs[0, 0].set_ylabel("Altitude [m]")
    axs[0, 0].set_xlabel("Time [s]")
    axs[0, 0].grid(True, alpha=0.3)
    axs[0, 0].legend()
    axs[0, 0].set_title("Altitude Profile")

    # 2. Vertical Velocity vs Time
    axs[0, 1].plot(times, vzs, "r-", linewidth=2, label="Vertical Speed vz (m/s)")
    axs[0, 1].axhline(0, color="k", linestyle="--", alpha=0.5)
    axs[0, 1].axhline(-report.terminal_vertical_speed_mps, color="g", linestyle=":", label=f"Terminal vz: {report.terminal_vertical_speed_mps:.2f} m/s")
    axs[0, 1].set_ylabel("Vertical Velocity vz [m/s]")
    axs[0, 1].set_xlabel("Time [s]")
    axs[0, 1].grid(True, alpha=0.3)
    axs[0, 1].legend()
    axs[0, 1].set_title("Vertical Velocity Profile")

    # 3. Attitude (Pitch) vs Time
    axs[1, 0].plot(times, pitches, "m-", linewidth=2, label="Pitch Angle (deg)")
    axs[1, 0].axhline(0, color="k", linestyle="--", alpha=0.7, label="Upright (0 deg)")
    axs[1, 0].axhline(-90, color="gray", linestyle=":", label="Belly-Flop (-90 deg)")
    axs[1, 0].set_ylabel("Pitch Angle [deg]")
    axs[1, 0].set_xlabel("Time [s]")
    axs[1, 0].grid(True, alpha=0.3)
    axs[1, 0].legend()
    axs[1, 0].set_title("Attitude Flip Maneuver")

    # 4. Thrust and Vehicle Mass
    ax4_twin = axs[1, 1].twinx()
    l1 = axs[1, 1].plot(times, thrusts, "tab:orange", linewidth=2, label="Thrust (MN)")
    l2 = ax4_twin.plot(times, masses, "tab:brown", linestyle="--", linewidth=2, label="Vehicle Mass (t)")
    axs[1, 1].set_ylabel("Thrust [MN]", color="tab:orange")
    ax4_twin.set_ylabel("Mass [t]", color="tab:brown")
    axs[1, 1].set_xlabel("Time [s]")
    axs[1, 1].grid(True, alpha=0.3)
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    axs[1, 1].legend(lines, labels, loc="upper right")
    axs[1, 1].set_title("Propulsion & Mass Depletion")

    # 5. Trajectory in Flight Plane (Z vs X)
    axs[2, 0].plot(xs, alts, "g-", linewidth=2, label="Trajectory")
    axs[2, 0].scatter([0], [0], color="red", marker="x", s=100, label="Target Pad (0,0)")
    axs[2, 0].set_xlabel("Downrange Distance [m]")
    axs[2, 0].set_ylabel("Altitude [m]")
    axs[2, 0].grid(True, alpha=0.3)
    axs[2, 0].legend()
    axs[2, 0].set_title(f"Flight Plane Path (Miss: {report.miss_distance_m:.1f} m)")

    # 6. Apparent Deceleration Load
    axs[2, 1].plot(times, gs, "k-", linewidth=2, label="Apparent Load (g)")
    axs[2, 1].axhline(1.0, color="gray", linestyle=":", label="1g Reference")
    axs[2, 1].set_ylabel("Apparent Deceleration [g]")
    axs[2, 1].set_xlabel("Time [s]")
    axs[2, 1].grid(True, alpha=0.3)
    axs[2, 1].legend()
    axs[2, 1].set_title(f"G-Load History (Peak: {report.peak_apparent_g:.2f} g)")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path
