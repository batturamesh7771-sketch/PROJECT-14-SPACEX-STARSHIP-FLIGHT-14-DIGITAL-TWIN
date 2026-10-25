# Starship Flight 14 — Canonical Data Contract & Telemetry Schema

**Schema Version:** 1.0.0  
**Effective Date:** October 26, 2026  
**Document ID:** `SPEC-DATA-CONTRACT-01`  

---

## 1. Principles of State Invariance

1. **Singular State Authority:** All application views (3D WebGL scene, HUD telemetry cards, multi-channel 2D charts, mission event table, satellite manifest, and data inspector) MUST derive from one unified state object evaluated at the active simulation time $t$:
   $$\mathcal{S}(t) = \text{EvaluateState}(\text{activeProfile}, t)$$
2. **Strict SI Units Internally:** All internal calculations, APIs, and data models store physical quantities in base SI units:
   - Position: meters ($\text{m}$)
   - Velocity: meters per second ($\text{m/s}$)
   - Force / Thrust: Newtons ($\text{N}$)
   - Pressure: Pascals ($\text{Pa}$)
   - Heat Flux: Watts per square meter ($\text{W/m}^2$)
   - Mass: kilograms ($\text{kg}$)
   - Angle: radians ($\text{rad}$)
3. **Explicit Quality Tagging & "Missing is Not Zero":**
   When telemetry or an engineering state channel is not available or not modeled for a specific mission phase, the value MUST remain `null` or `undefined` with a documented `quality_status` of `"unavailable"` or `"unmodeled"`. It is strictly forbidden to replace missing telemetry with `0.0`.

---

## 2. Canonical Vehicle State Schema (JSON)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StarshipFlight14VehicleStateRecord",
  "type": "object",
  "required": [
    "schema_version",
    "scenario_id",
    "vehicle_id",
    "time_s",
    "position_m",
    "velocity_m_s",
    "attitude",
    "quality_status"
  ],
  "properties": {
    "schema_version": { "type": "string", "enum": ["1.0.0"] },
    "scenario_id": { 
      "type": "string", 
      "enum": ["flight14_planned", "flight14_observed_reconstruction", "synthetic_engineering_test"] 
    },
    "run_id": { "type": "string" },
    "vehicle_id": { 
      "type": "string", 
      "enum": ["stack", "starship", "super_heavy", "starlink_v3"] 
    },
    "time_s": { "type": "number", "minimum": 0.0 },
    "utc": { "type": ["string", "null"] },
    "time_quality": { 
      "type": "string", 
      "enum": ["source-timed", "estimated", "solver-time", "reconstructed"] 
    },
    "position_m": {
      "type": "object",
      "required": ["frame", "x", "y", "z"],
      "properties": {
        "frame": { "type": "string", "enum": ["ECI_J2000", "ECEF_WGS84", "LOCAL_NED"] },
        "x": { "type": "number" },
        "y": { "type": "number" },
        "z": { "type": "number" }
      }
    },
    "velocity_m_s": {
      "type": "object",
      "required": ["frame", "vx", "vy", "vz"],
      "properties": {
        "frame": { "type": "string", "enum": ["ECI_J2000", "ECEF_WGS84", "LOCAL_NED"] },
        "vx": { "type": "number" },
        "vy": { "type": "number" },
        "vz": { "type": "number" }
      }
    },
    "attitude": {
      "type": "object",
      "required": ["type", "convention", "qx", "qy", "qz", "qw"],
      "properties": {
        "type": { "type": "string", "enum": ["quaternion"] },
        "convention": { "type": "string", "enum": ["scalar_last_xyzw"] },
        "qx": { "type": "number" },
        "qy": { "type": "number" },
        "qz": { "type": "number" },
        "qw": { "type": "number" }
      }
    },
    "mass_kg": { "type": ["number", "null"], "minimum": 0.0 },
    "engine_mode": { "type": "string" },
    "engine_count_active": { "type": ["integer", "null"], "minimum": 0, "maximum": 33 },
    "thrust_N": { "type": ["number", "null"], "minimum": 0.0 },
    "altitude_m": { "type": ["number", "null"] },
    "speed_m_s": { "type": ["number", "null"], "minimum": 0.0 },
    "mach": { "type": ["number", "null"], "minimum": 0.0 },
    "dynamic_pressure_Pa": { "type": ["number", "null"], "minimum": 0.0 },
    "heat_flux_W_m2": { "type": ["number", "null"], "minimum": 0.0 },
    "tps_surface_temp_K": { "type": ["number", "null"], "minimum": 0.0 },
    "bondline_temp_K": { "type": ["number", "null"], "minimum": 0.0 },
    "tank_hoop_stress_MPa": { "type": ["number", "null"] },
    "flap_angles_deg": {
      "type": ["object", "null"],
      "properties": {
        "forward_left": { "type": "number" },
        "forward_right": { "type": "number" },
        "aft_left": { "type": "number" },
        "aft_right": { "type": "number" }
      }
    },
    "source_ids": { "type": "array", "items": { "type": "string" } },
    "quality_status": { 
      "type": "string", 
      "enum": ["valid", "estimated", "reconstructed", "unavailable"] 
    }
  }
}
```

---

## 3. Satellite Payload Deployment Contract

```json
{
  "satellite_number": 1,
  "id": "STARLINK-V3-001",
  "deploy_time_s": 1320.0,
  "dispenser_slot": "FORWARD_PEZ_SLOT_01",
  "dispersion_delta_v_m_s": 0.75,
  "mass_kg": 1500.0,
  "solar_array_deployed": true,
  "beacon_status": "ACTIVE_LASER_LINK",
  "orbital_plane": "PLANE_28_5_DEG",
  "provenance": "SpaceX Flight 14 Official Manifest (SRC-01)"
}
```
