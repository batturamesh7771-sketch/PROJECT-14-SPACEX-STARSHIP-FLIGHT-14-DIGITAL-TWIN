# Phase 10: Digital Engineering Spatial Dashboard — Data Contract & Schema Specification

## 1. Scope & Schema Architecture

The Phase 10 Spatial Dashboard consumes multi-phase simulation outputs and public mission reference data through a strictly versioned JSON data contract (`schema_version: "1.0.0"`).
All units are SI internally. Missing data must be explicitly represented as `null` with a documented quality status (`"N/A"`, `"Not modeled"`, `"Source unavailable"`, or `"No validated data"`).

---

## 2. Core JSON Schema Entities

### 2.1 Profile & Run Metadata
```json
{
  "scenario_id": "F14-OBS-20260928-001",
  "profile_type": "observed_reconstruction", // "planned" | "observed_reconstruction" | "synthetic_test"
  "run_id": "RUN-2026-10-25-P10",
  "schema_version": "1.0.0",
  "solver_name": "Starship Digital Engineering Lab",
  "solver_version": "1.0.0",
  "code_commit": "9bcc730",
  "created_utc": "2026-10-25T13:30:00Z",
  "source_ids": ["SRC-001", "SRC-002", "SRC-003", "NASA-STD-7009B"],
  "model_fidelity": {
    "dynamics": "3-DOF translational + 3-axis attitude kinematics",
    "gravity": "Earth J2 zonal harmonic + point mass",
    "atmosphere": "US Standard Atmosphere 1976",
    "aerodynamics": "Mach-dependent wave drag + windward pitch scaling",
    "thermal": "Sutton-Graves convective flux + 1D non-linear TDMA conduction",
    "structures": "Roark thin-shell membrane + CalculiX S4R FEA benchmark"
  }
}
```

### 2.2 Time-Series Sample Record
Each timestamp sample represents a synchronized multi-domain vehicle state:
```json
{
  "time_s": 318.0,
  "met_formatted": "00:05:18",
  "epoch_utc": "2026-09-28T15:54:05.315Z",
  "altitude_m": 64200.0,
  "velocity_inertial_ms": 7120.0,
  "velocity_relative_ms": 6820.0,
  "mach": 22.4,
  "dynamic_pressure_pa": 12450.0,
  "total_mass_kg": 181900.0,
  "propellant_remaining_kg": 81900.0,
  "thrust_n": 0.0,
  "apparent_g_load": 1.85,
  "position_eci_m": [5821000.0, -2910000.0, 1420000.0],
  "velocity_eci_ms": [2150.0, 6210.0, -2340.0],
  "quaternion": [0.9978, 0.0124, 0.0643, 0.0217],
  "euler_deg": {"roll": 0.2, "pitch": 0.5, "yaw": 1.1},
  "flap_deflections_deg": {
    "fwd_left": 12.5,
    "fwd_right": 12.5,
    "aft_left": 14.2,
    "aft_right": 14.2
  },
  "stagnation_heat_flux_mw_m2": 0.794,
  "windward_heat_flux_mw_m2": 0.157,
  "surface_temp_k": 1330.7,
  "rtv_bondline_temp_k": 377.1,
  "engines_active": 0,
  "active_phase": "reentry",
  "data_quality": "valid"
}
```

### 2.3 Event Ledger Record
```json
{
  "event_id": "EVT-04",
  "name": "Hot-Staging Separation",
  "planned_time_s": 162.0,
  "planned_formatted": "00:02:42",
  "planned_source": "SpaceX Flight 14 Launch Overview",
  "observed_time_s": 165.0,
  "observed_formatted": "00:02:45",
  "observed_source": "Flight Telemetry & Public Tracking",
  "delta_seconds": 3.0,
  "status": "completed",
  "evidence_level": "verified",
  "notes": "Hot-stage ring separation with 3 center Raptor ignition on Ship."
}
```

### 2.4 Satellite Manifest Record
```json
{
  "satellite_id": "STK-001",
  "payload_name": "Starlink V3-001",
  "deploy_time_s": 1320.0,
  "deploy_formatted": "00:22:00",
  "mass_kg": 1750.0,
  "dispenser_slot": 1,
  "target_orbit_km": "275 x 275",
  "status": "deployed"
}
```
