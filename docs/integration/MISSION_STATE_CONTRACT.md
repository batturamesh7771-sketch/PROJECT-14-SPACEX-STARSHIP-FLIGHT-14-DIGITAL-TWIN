# Starship Flight 14 Digital Engineering Lab — Mission State Contract Specification

**Document ID:** `DOC-INT-STATE-CONTRACT-001`  
**Classification:** Cross-Phase System Architecture Contract  
**Lead:** Systems Engineering & Software Architecture Lead  

---

## 1. Objective and Scope

This contract establishes the mandatory, versioned data structure, physical units, coordinate frame definitions, and validation rules governing every state handoff between phases of the Starship Flight 14 simulation pipeline.

No phase may consume or produce a state vector that violates this contract.

---

## 2. Universal State Schema Specification

Every discrete state handoff between mission phases must conform to the following schema:

```json
{
  "schema_version": "1.0.0",
  "mission_id": "Starship_Flight14",
  "scenario_id": "FLIGHT14_NOMINAL_DISPOSAL",
  "stage_id": "STARSHIP_STAGE2",
  "event_id": "ENTRY_INTERFACE_CROSSING",
  "time_epoch_utc": "2026-09-28T15:48:47.315Z",
  "elapsed_mission_time_s": 6527.315,
  "elapsed_stage_time_s": 6004.965,
  "coordinate_frame": "ECI_J2000",
  "position_m": [5528938.10, -3319172.12, 798881.33],
  "velocity_m_s": [3895.7417, 5894.2764, -3257.6110],
  "mass_kg": 177272.71,
  "mass_breakdown": {
    "dry_mass_kg": 99975.0,
    "payload_mass_kg": 0.0,
    "propellant_mass_kg": 77297.71
  },
  "geodetic": {
    "latitude_deg": 7.1084,
    "longitude_deg": -58.3341,
    "altitude_m": 120000.0
  },
  "atmosphere_relative": {
    "speed_m_s": 7356.24,
    "mach": 17.80,
    "flight_path_angle_deg": -0.7519,
    "dynamic_pressure_pa": 0.66
  },
  "attitude_trim": {
    "angle_of_attack_deg": 70.0,
    "bank_angle_deg": 0.0,
    "attitude_representation": "TRIMMED_3DOF"
  },
  "provenance_tag": "SIMULATION_OUTPUT",
  "validity_status": "VALID_DISPOSAL_ENTRY"
}
```

---

## 3. Strict Coordinate Frame Conventions

1. **Inertial Frame (`ECI_J2000`):**
   - Origin: Earth Center of Mass.
   - Fundamental Plane: Mean Equator at J2000.0.
   - X-axis: Mean Vernal Equinox at J2000.0.
   - Z-axis: Earth Mean Rotation Axis at J2000.0 (pointing North).
   - Y-axis: Completes right-handed orthogonal system ($\hat{\mathbf{Y}} = \hat{\mathbf{Z}} \times \hat{\mathbf{X}}$).
2. **Rotating Earth-Fixed Frame (`ECEF_WGS84`):**
   - Origin: Earth Center of Mass.
   - X-axis: Intersection of Prime Meridian (Greenwich) and Equator.
   - Z-axis: International Reference Pole (IRP).
   - Transformation: $\mathbf{r}_{\text{ECEF}} = \mathbf{R}_z(\theta_{\text{GST}})\,\mathbf{r}_{\text{ECI}}$, where $\theta_{\text{GST}} = \theta_{\text{GST},0} + \omega_E t$.
   - Velocity Transformation: $\mathbf{v}_{\text{rel}} = \mathbf{v}_{\text{ECI}} - \boldsymbol{\omega}_E \times \mathbf{r}_{\text{ECI}}$.
3. **Trajectory Frame (Aerodynamic Lift/Drag Basis):**
   - Drag unit vector: $\hat{\mathbf{u}}_{\text{drag}} = - \frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|}$.
   - Orbit/Trajectory normal: $\hat{\mathbf{w}} = \frac{\hat{\mathbf{r}} \times \hat{\mathbf{v}}_{\text{rel}}}{\|\hat{\mathbf{r}} \times \hat{\mathbf{v}}_{\text{rel}}\|}$.
   - Upward lift unit vector: $\hat{\mathbf{u}}_{\text{up}} = \frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|} \times \hat{\mathbf{w}}$.
   - Bank-rotated lift vector: $\hat{\mathbf{l}} = \cos(\sigma)\,\hat{\mathbf{u}}_{\text{up}} + \sin(\sigma)\,\hat{\mathbf{w}}$.

---

## 4. Time Conventions and Standards

- **Internal Simulation Clock:** Monotonically increasing floating-point seconds ($t_{\text{elapsed}}$) relative to liftoff epoch ($T_0 = 0.0\,\text{s}$).
- **Mission Reference UTC Epoch:** `2026-09-28T14:00:00.000Z` (Liftoff).
- **Time Conversion Equation:**
  $$\text{UTC Epoch} = \text{Reference Epoch} + t_{\text{elapsed}}\,\text{seconds}$$
- **Discontinuities:** Discontinuous time resets are strictly forbidden. Staging and discrete burns must record elapsed mission time without zeroing the mission clock.
