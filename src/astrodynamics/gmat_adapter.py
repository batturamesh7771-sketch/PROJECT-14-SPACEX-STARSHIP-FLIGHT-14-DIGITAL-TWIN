"""
NASA GMAT R2026a Script Generator, Execution Wrapper & Verification Adapter
==========================================================================
Enables independent cross-verification of Python orbital propagation
against NASA's General Mission Analysis Tool (GMAT R2026a).
Generates strictly ASCII GMAT scripts, executes GmatConsole.exe,
parses ephemeris reports, and evaluates residual differences.
"""

import os
import subprocess
import math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .constants import R_EARTH_EQUATORIAL
from .state import OrbitalState
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
    Generates a valid, strictly ASCII NASA GMAT R2026a mission script.
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
    report_fname_clean = output_report_path.replace("\\", "/")

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
        "GMAT OrbitalReport.Add = {StarshipP5.UTCGregorian, StarshipP5.Earth.SMA, StarshipP5.Earth.ECC, StarshipP5.Earth.Altitude, StarshipP5.Earth.RadPer, StarshipP5.Earth.RadApo};",
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
    Tokens 4..: SMA, ECC, Altitude, RadPer, RadApo
    """
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"GMAT report file does not exist: {report_path}")

    records = []
    with open(report_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        return []

    # First row is header, subsequent rows are data
    for line in lines[1:]:
        tokens = line.split()
        if len(tokens) < 9:
            continue
        utc_str = f"{tokens[0]} {tokens[1]} {tokens[2]} {tokens[3]}"
        sma = float(tokens[4])
        ecc = float(tokens[5])
        alt = float(tokens[6])
        rad_per = float(tokens[7])
        rad_apo = float(tokens[8])

        records.append({
            "utc_epoch": utc_str,
            "sma_km": sma,
            "eccentricity": ecc,
            "altitude_km": alt,
            "periapsis_radius_km": rad_per,
            "apoapsis_radius_km": rad_apo
        })

    return records


def compare_python_with_gmat(
    python_final_elements: Dict[str, float],
    gmat_final_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compares final orbital elements between Python propagator and NASA GMAT.
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

    return {
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
