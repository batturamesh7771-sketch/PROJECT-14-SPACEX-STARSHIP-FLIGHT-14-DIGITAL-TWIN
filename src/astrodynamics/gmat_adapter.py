"""
NASA GMAT R2026a Script Generator, Execution Wrapper & Verification Adapter
==========================================================================
Enables independent cross-verification of Python orbital propagation
against NASA's General Mission Analysis Tool (GMAT R2026a).
Generates strictly ASCII GMAT scripts, executes GmatConsole.exe,
parses full ephemeris reports, and evaluates position/velocity residual time series.
"""

import os
import subprocess
import csv
import math
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .constants import R_EARTH_EQUATORIAL
from .state import OrbitalState
from .orbit_elements import compute_keplerian_elements
from .time_systems import format_gmat_epoch


GMAT_DEFAULT_BIN = r"E:\NASA\GMAT-R2026a\bin\GmatConsole.exe"


def generate_gmat_script(
    initial_state: OrbitalState,
    duration_s: float,
    output_report_path: str,
    target_script_path: str,
    gravity_degree: int = 2,
    gravity_order: int = 0,
    enable_drag: bool = False
) -> str:
    """
    Generates a valid, strictly ASCII NASA GMAT R2026a mission script
    subscribing to both Cartesian coordinates and Keplerian orbital elements.
    Note: Coordinates in GMAT are in kilometers and km/s.
    """
    epoch_gmat = format_gmat_epoch(initial_state.epoch)

    # Position in km, velocity in km/s
    x_km = initial_state.r[0] / 1000.0
    y_km = initial_state.r[1] / 1000.0
    z_km = initial_state.r[2] / 1000.0
    vx_km_s = initial_state.v[0] / 1000.0
    vy_km_s = initial_state.v[1] / 1000.0
    vz_km_s = initial_state.v[2] / 1000.0

    mass_kg = initial_state.mass_kg
    area_m2 = initial_state.area_m2
    cd = initial_state.cd

    # Normalize output report path for GMAT
    report_fname_clean = os.path.abspath(output_report_path).replace("\\", "/")

    script_lines = [
        "% NASA General Mission Analysis Tool (GMAT) Script",
        "% Starship Flight 14 - Independent Orbital Verification",
        f"% Epoch: {epoch_gmat}",
        "",
        "%----------------------------------------",
        "%---------- Spacecraft",
        "%----------------------------------------",
        "",
        "Create Spacecraft StarshipP5;",
        "GMAT StarshipP5.DateFormat = UTCGregorian;",
        f"GMAT StarshipP5.Epoch = '{epoch_gmat}';",
        "GMAT StarshipP5.CoordinateSystem = EarthMJ2000Eq;",
        "GMAT StarshipP5.DisplayStateType = Cartesian;",
        f"GMAT StarshipP5.X = {x_km:.6f};",
        f"GMAT StarshipP5.Y = {y_km:.6f};",
        f"GMAT StarshipP5.Z = {z_km:.6f};",
        f"GMAT StarshipP5.VX = {vx_km_s:.6f};",
        f"GMAT StarshipP5.VY = {vy_km_s:.6f};",
        f"GMAT StarshipP5.VZ = {vz_km_s:.6f};",
        f"GMAT StarshipP5.DryMass = {mass_kg:.1f};",
        f"GMAT StarshipP5.Cd = {cd:.2f};",
        "GMAT StarshipP5.Cr = 1.8;",
        f"GMAT StarshipP5.DragArea = {area_m2:.2f};",
        f"GMAT StarshipP5.SRPArea = {area_m2:.2f};",
        "",
        "%----------------------------------------",
        "%---------- Force Model & Propagator",
        "%----------------------------------------",
        "",
        "Create ForceModel Flight14_ForceModel;",
        "GMAT Flight14_ForceModel.CentralBody = Earth;",
        "GMAT Flight14_ForceModel.PrimaryBodies = {Earth};",
        "GMAT Flight14_ForceModel.PointMasses = {};",
        "GMAT Flight14_ForceModel.SRP = Off;",
        f"GMAT Flight14_ForceModel.GravityField.Earth.Degree = {gravity_degree};",
        f"GMAT Flight14_ForceModel.GravityField.Earth.Order = {gravity_order};",
        "GMAT Flight14_ForceModel.GravityField.Earth.PotentialFile = 'JGM2.cof';",
        "",
        "Create Propagator Flight14_Prop;",
        "GMAT Flight14_Prop.FM = Flight14_ForceModel;",
        "GMAT Flight14_Prop.Type = RungeKutta89;",
        "GMAT Flight14_Prop.InitialStepSize = 10;",
        "GMAT Flight14_Prop.Accuracy = 1e-11;",
        "GMAT Flight14_Prop.MinStep = 0.001;",
        "GMAT Flight14_Prop.MaxStep = 60;",
        "",
        "%----------------------------------------",
        "%---------- Subscribers & Reports",
        "%----------------------------------------",
        "",
        "Create ReportFile OrbitalReport;",
        f"GMAT OrbitalReport.Filename = '{report_fname_clean}';",
        "GMAT OrbitalReport.Add = {StarshipP5.UTCGregorian, StarshipP5.EarthMJ2000Eq.X, StarshipP5.EarthMJ2000Eq.Y, StarshipP5.EarthMJ2000Eq.Z, StarshipP5.EarthMJ2000Eq.VX, StarshipP5.EarthMJ2000Eq.VY, StarshipP5.EarthMJ2000Eq.VZ, StarshipP5.Earth.SMA, StarshipP5.Earth.ECC, StarshipP5.Earth.Altitude, StarshipP5.Earth.RadPer, StarshipP5.Earth.RadApo};",
        "",
        "%----------------------------------------",
        "%---------- Mission Sequence",
        "%----------------------------------------",
        "",
        "BeginMissionSequence;",
        f"Propagate Flight14_Prop(StarshipP5) {{StarshipP5.ElapsedSecs = {duration_s:.1f}}};",
        ""
    ]

    script_text = "\n".join(script_lines)

    # Ensure target script directory exists
    os.makedirs(os.path.dirname(os.path.abspath(target_script_path)), exist_ok=True)

    with open(target_script_path, "w", encoding="ascii") as f:
        f.write(script_text)

    return script_text


def execute_gmat_script(
    script_path: str,
    gmat_bin_path: str = GMAT_DEFAULT_BIN,
    timeout_s: float = 60.0
) -> Tuple[int, str, str]:
    """
    Executes GMAT Console with the specified script.
    """
    if not os.path.exists(gmat_bin_path):
        raise FileNotFoundError(f"NASA GMAT executable not found at: {gmat_bin_path}")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"GMAT script not found at: {script_path}")

    cmd = [gmat_bin_path, "--run", os.path.abspath(script_path)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False
    )
    return result.returncode, result.stdout, result.stderr


def parse_gmat_report(report_path: str) -> List[Dict[str, Any]]:
    """
    Parses a standard GMAT space-delimited report file.
    Tokens 0..3: UTCGregorian date/time ('28 Sep 2026 14:08:42.350')
    Tokens 4..6: X, Y, Z (km)
    Tokens 7..9: VX, VY, VZ (km/s)
    Tokens 10..: SMA, ECC, Altitude, RadPer, RadApo
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"GMAT report file does not exist: {report_path}")

    records = []
    with open(report_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        return []

    t0_dt = None

    for line in lines[1:]:
        tokens = line.split()
        if len(tokens) < 10:
            continue
        utc_str = f"{tokens[0]} {tokens[1]} {tokens[2]} {tokens[3]}"
        try:
            curr_dt = datetime.strptime(utc_str, "%d %b %Y %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        except Exception:
            curr_dt = None

        if t0_dt is None and curr_dt is not None:
            t0_dt = curr_dt

        elapsed_s = (curr_dt - t0_dt).total_seconds() if (t0_dt and curr_dt) else 0.0

        # Check if Cartesian tokens are present (12+ tokens)
        if len(tokens) >= 15:
            x_m = float(tokens[4]) * 1000.0
            y_m = float(tokens[5]) * 1000.0
            z_m = float(tokens[6]) * 1000.0
            vx_ms = float(tokens[7]) * 1000.0
            vy_ms = float(tokens[8]) * 1000.0
            vz_ms = float(tokens[9]) * 1000.0
            sma_km = float(tokens[10])
            ecc = float(tokens[11])
            alt_km = float(tokens[12])
            rad_per_km = float(tokens[13])
            rad_apo_km = float(tokens[14])
        else:
            # Fallback for element-only reports
            x_m = y_m = z_m = vx_ms = vy_ms = vz_ms = 0.0
            sma_km = float(tokens[4])
            ecc = float(tokens[5])
            alt_km = float(tokens[6])
            rad_per_km = float(tokens[7])
            rad_apo_km = float(tokens[8])

        records.append({
            "utc_epoch": utc_str,
            "elapsed_s": elapsed_s,
            "r_m": np.array([x_m, y_m, z_m], dtype=np.float64),
            "v_ms": np.array([vx_ms, vy_ms, vz_ms], dtype=np.float64),
            "sma_km": sma_km,
            "eccentricity": ecc,
            "altitude_km": alt_km,
            "periapsis_radius_km": rad_per_km,
            "apoapsis_radius_km": rad_apo_km
        })

    return records


def compute_ephemeris_residuals(
    py_result: Any,
    gmat_records: List[Dict[str, Any]],
    output_csv_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes exact common-epoch position and velocity residual vectors
    between Python propagator and NASA GMAT ephemeris.
    """
    pos_errs = []
    vel_errs = []
    sma_errs = []
    ecc_errs = []
    csv_rows = []

    times = py_result.times_s
    r_arr = py_result.states_r
    v_arr = py_result.states_v

    for rec in gmat_records:
        t_sec = rec["elapsed_s"]
        r_gm = rec["r_m"]
        v_gm = rec["v_ms"]

        # High-order cubic Hermite interpolation between bracketing Python time steps
        idx = int(np.searchsorted(times, t_sec))
        if idx == 0:
            r_py = r_arr[0]
            v_py = v_arr[0]
        elif idx >= len(times):
            r_py = r_arr[-1]
            v_py = v_arr[-1]
        else:
            t0, t1 = times[idx - 1], times[idx]
            dt = t1 - t0
            if dt > 1e-9:
                s = (t_sec - t0) / dt
                r0_pt, r1_pt = r_arr[idx - 1], r_arr[idx]
                v0_pt, v1_pt = v_arr[idx - 1], v_arr[idx]

                # Cubic Hermite basis functions for position
                h00 = 2.0 * s**3 - 3.0 * s**2 + 1.0
                h10 = s**3 - 2.0 * s**2 + s
                h01 = -2.0 * s**3 + 3.0 * s**2
                h11 = s**3 - s**2
                r_py = h00 * r0_pt + h10 * dt * v0_pt + h01 * r1_pt + h11 * dt * v1_pt

                # Analytical time derivative for velocity
                dh00 = (6.0 * s**2 - 6.0 * s) / dt
                dh10 = 3.0 * s**2 - 4.0 * s + 1.0
                dh01 = (-6.0 * s**2 + 6.0 * s) / dt
                dh11 = 3.0 * s**2 - 2.0 * s
                v_py = dh00 * r0_pt + dh10 * v0_pt + dh01 * r1_pt + dh11 * v1_pt
            else:
                r_py = r_arr[idx]
                v_py = v_arr[idx]

        dr_vec = r_py - r_gm
        dv_vec = v_py - v_gm
        pos_err = float(np.linalg.norm(dr_vec))
        vel_err = float(np.linalg.norm(dv_vec))

        pos_errs.append(pos_err)
        vel_errs.append(vel_err)

        try:
            elem_py = compute_keplerian_elements(r_py, v_py)
            py_sma_km = elem_py.get("semi_major_axis_m", 0.0) / 1000.0
            py_ecc = elem_py.get("eccentricity", 0.0)
        except Exception:
            py_sma_km = 0.0
            py_ecc = 0.0

        d_sma = abs(py_sma_km - rec["sma_km"])
        d_ecc = abs(py_ecc - rec["eccentricity"])

        sma_errs.append(d_sma)
        ecc_errs.append(d_ecc)

        csv_rows.append([
            f"{t_sec:.2f}", rec["utc_epoch"],
            f"{r_gm[0]:.2f}", f"{r_gm[1]:.2f}", f"{r_gm[2]:.2f}",
            f"{r_py[0]:.2f}", f"{r_py[1]:.2f}", f"{r_py[2]:.2f}",
            f"{pos_err:.2f}",
            f"{v_gm[0]:.4f}", f"{v_gm[1]:.4f}", f"{v_gm[2]:.4f}",
            f"{v_py[0]:.4f}", f"{v_py[1]:.4f}", f"{v_py[2]:.4f}",
            f"{vel_err:.4f}",
            f"{rec['sma_km']:.4f}", f"{py_sma_km:.4f}", f"{d_sma:.4f}",
            f"{rec['eccentricity']:.6f}", f"{py_ecc:.6f}", f"{d_ecc:.6f}"
        ])

    if output_csv_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
        with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "time_s", "epoch_utc",
                "gmat_x_m", "gmat_y_m", "gmat_z_m",
                "python_x_m", "python_y_m", "python_z_m",
                "pos_residual_norm_m",
                "gmat_vx_ms", "gmat_vy_ms", "gmat_vz_ms",
                "python_vx_ms", "python_vy_ms", "python_vz_ms",
                "vel_residual_norm_ms",
                "gmat_sma_km", "python_sma_km", "delta_sma_km",
                "gmat_ecc", "python_ecc", "delta_ecc"
            ])
            writer.writerows(csv_rows)

    return {
        "step_count": len(pos_errs),
        "max_pos_residual_m": float(np.max(pos_errs)) if pos_errs else 0.0,
        "mean_pos_residual_m": float(np.mean(pos_errs)) if pos_errs else 0.0,
        "final_pos_residual_m": float(pos_errs[-1]) if pos_errs else 0.0,
        "max_vel_residual_ms": float(np.max(vel_errs)) if vel_errs else 0.0,
        "mean_vel_residual_ms": float(np.mean(vel_errs)) if vel_errs else 0.0,
        "final_vel_residual_ms": float(vel_errs[-1]) if vel_errs else 0.0,
        "max_sma_residual_m": float(np.max(sma_errs) * 1000.0) if sma_errs else 0.0,
        "final_sma_residual_m": float(sma_errs[-1] * 1000.0) if sma_errs else 0.0,
        "final_ecc_residual": float(ecc_errs[-1]) if ecc_errs else 0.0
    }


def compare_python_with_gmat(
    python_final_elements: Dict[str, float],
    gmat_final_record: Dict[str, Any],
    residuals_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compares final orbital elements and state residuals between Python propagator and NASA GMAT.
    Computes absolute and percentage discrepancies.
    """
    py_sma_km = python_final_elements.get("semi_major_axis_m", 0.0) / 1000.0
    gmat_sma_km = gmat_final_record.get("sma_km", 0.0)
    sma_diff_km = abs(py_sma_km - gmat_sma_km)
    sma_err_pct = (sma_diff_km / max(abs(gmat_sma_km), 1e-6)) * 100.0

    py_ecc = python_final_elements.get("eccentricity", 0.0)
    gmat_ecc = gmat_final_record.get("eccentricity", 0.0)
    ecc_diff = abs(py_ecc - gmat_ecc)

    py_alt_km = python_final_elements.get("altitude_spherical_km", 0.0)
    gmat_alt_km = gmat_final_record.get("altitude_km", 0.0)
    alt_diff_km = abs(py_alt_km - gmat_alt_km)

    py_rp_km = python_final_elements.get("periapsis_radius_m", 0.0) / 1000.0
    gmat_rp_km = gmat_final_record.get("periapsis_radius_km", 0.0)
    rp_diff_km = abs(py_rp_km - gmat_rp_km)

    py_ra_km = python_final_elements.get("apoapsis_radius_m", 0.0) / 1000.0
    gmat_ra_km = gmat_final_record.get("apoapsis_radius_km", 0.0)
    ra_diff_km = abs(py_ra_km - gmat_ra_km)

    # Acceptance criteria: SMA diff < 0.1%, Ecc diff < 0.001
    passed = (sma_err_pct < 0.1) and (ecc_diff < 0.001)

    result = {
        "status": "PASS" if passed else "FAIL",
        "python_sma_km": py_sma_km,
        "gmat_sma_km": gmat_sma_km,
        "sma_diff_km": sma_diff_km,
        "sma_error_percent": sma_err_pct,
        "python_ecc": py_ecc,
        "gmat_ecc": gmat_ecc,
        "ecc_diff": ecc_diff,
        "python_periapsis_km": py_rp_km,
        "gmat_periapsis_km": gmat_rp_km,
        "periapsis_diff_km": rp_diff_km,
        "python_apoapsis_km": py_ra_km,
        "gmat_apoapsis_km": gmat_ra_km,
        "apoapsis_diff_km": ra_diff_km
    }

    if residuals_summary:
        result.update(residuals_summary)

    return result
