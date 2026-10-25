# STARSHIP FLIGHT 14 DIGITAL ENGINEERING LAB
## PHASE 7 — PARAMETER PROVENANCE & ASSUMPTIONS REGISTER

**Document ID:** `DOC-P7-PROV-001`  
**Revision:** 1.0.0  
**Date:** 2026-10-25  
**Classification:** Engineering Specification Document  
**Authoritative Reference:** `data/phase7/parameter_provenance.csv`  

---

### 1. Purpose and Methodology

This document establishes the formal pedigree, uncertainty bounds, and domain of applicability for every numerical parameter utilized in Phase 7 (Terminal Landing Dynamics).

In strict adherence to the project guidelines:
1. Parameters derived from audited upstream mission states or verified public facts are classified as `derived` or `public_fact`.
2. Parameters representing internal SpaceX vehicle dynamics, turbopump relight transients, or control allocations that are not publicly available are classified as `assumption` or `synthetic_scenario`.
3. Under no circumstances are assumed parameters presented as proprietary SpaceX flight software or operational telemetry.

---

### 2. Vehicle Structural and Mass Parameters

| Parameter | Value | Units | Classification | Source | Uncertainty / Rationale |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `dry_mass_kg` | $99,980.0$ | $\text{kg}$ | `derived` | Phase 2/3 Audited Baseline | Audited dry mass of Starship Upper Stage ($\pm 5,000\,\text{kg}$). |
| `usable_propellant_kg` | $25,000.0$ | $\text{kg}$ | `assumption` | Starship Header Tank Architecture | Header tank propellant reserved for flip and landing burn ($\pm 3,000\,\text{kg}$). |
| `reserve_propellant_kg` | $1,500.0$ | $\text{kg}$ | `assumption` | Standard Reserve Policy | Unusable residual propellant margin ($\pm 500\,\text{kg}$). |
| `reference_area_m2` | $63.62$ | $\text{m}^2$ | `derived` | Vehicle Geometry | Axial circular cross-section ($\pi \times 4.5^2$). |
| `broadside_area_m2` | $450.0$ | $\text{m}^2$ | `derived` | Vehicle Dimensions | Projected area in horizontal belly-down attitude ($50.3\,\text{m} \times 9.0\,\text{m}$, $\pm 20\,\text{m}^2$). |
| `pitch_inertia_nom_kg_m2` | $2.5\times 10^7$ | $\text{kg}\cdot\text{m}^2$ | `derived` | Analytical Thin-Shell Model | $I_{yy} \approx \frac{1}{12} m (L^2 + 3R^2)$, scaled dynamically with mass ($\pm 0.5\times 10^7\,\text{kg}\cdot\text{m}^2$). |
| `gimbal_arm_m` | $20.0$ | $\text{m}$ | `derived` | Internal Tank Layout | Distance from vehicle center of mass to engine gimbal pivot ($\pm 2.0\,\text{m}$). |

---

### 3. Propulsion & Relight Parameters

| Parameter | Value | Units | Classification | Source | Uncertainty / Rationale |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `raptor_count_landing` | $3$ | count | `public_fact` | Flight Test Webcasts | 3 Center gimbaling Raptor engines relight for flip maneuver. |
| `thrust_nominal_N` | $2.25\times 10^6$ | $\text{N}$ | `public_fact` | Public Raptor 2/3 Data | Rated sea-level thrust per engine ($2.25\,\text{MN}$, $\pm 100\,\text{kN}$). |
| `specific_impulse_s` | $327.0$ | $\text{s}$ | `public_fact` | NASA GRC Rocket Thrust | Nominal sea-level effective specific impulse ($\pm 5\,\text{s}$). |
| `minimum_throttle` | $0.40$ | ratio | `assumption` | Deep-Throttle Requirement | Assumed minimum throttle floor for Raptor ($40\%$, $\pm 5\%$). |
| `maximum_throttle` | $1.00$ | ratio | `assumption` | Standard Operating Rating | $100\%$ rated sea-level thrust. |
| `ignition_delay_s` | $1.0$ | $\text{s}$ | `assumption` | NASA Morpheus VTVL | Turbopump chill and spin-up delay prior to ramp ($0.6\text{--}1.6\,\text{s}$). |
| `thrust_ramp_duration_s` | $0.8$ | $\text{s}$ | `assumption` | Continuous S-Curve Model | Duration of continuous thrust rise to commanded throttle ($\pm 0.2\,\text{s}$). |
| `gimbal_limit_deg` | $15.0$ | $\text{deg}$ | `assumption` | NASA Morpheus TVC Architecture | Maximum TVC nozzle deflection angle ($\pm 2.0^\circ$). |
| `gimbal_slew_rate_deg_s` | $20.0$ | $\text{deg/s}$ | `assumption` | Hydraulic/Electric Actuators | Maximum TVC actuator slew rate ($\pm 5.0^\circ/\text{s}$). |

---

### 4. Aerodynamic & Guidance Parameters

| Parameter | Value | Units | Classification | Source | Uncertainty / Rationale |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `axial_drag_coeff` | $0.30$ | dimensionless | `assumption` | Subsonic Blunt Cylinder | Cylinder nose-first / tail-first axial drag coefficient ($\pm 0.05$). |
| `crossflow_drag_coeff` | $1.15$ | dimensionless | `assumption` | Subsonic Cross-Flow Cylinder | Broadside belly-flop drag coefficient ($\pm 0.15$). |
| `lift_coeff_max` | $0.25$ | dimensionless | `assumption` | Body-Flap Lift Polar | Maximum aerodynamic lift coefficient at $\alpha \approx 45^\circ$ ($\pm 0.05$). |
| `flip_trigger_alt_m` | $800.0$ | $\text{m}$ | `assumption` | SN8–SN15 Observations | Altitude to command flip-to-vertical maneuver ($\pm 150\,\text{m}$). |
| `flip_duration_s` | $4.0$ | $\text{s}$ | `assumption` | Smoothstep Kinematics | Nominal duration of smooth aerodynamic pitch rotation ($\pm 1.0\,\text{s}$). |
| `target_decel_mps2` | $12.0$ | $\text{m/s}^2$ | `assumption` | Parabolic Guidance Law | Nominal deceleration profile for vertical landing ($1.22\,\text{g}$). |
| `touchdown_vel_mps` | $1.5$ | $\text{m/s}$ | `assumption` | Aerospace Landing Gear | Soft touchdown contact descent rate target ($1.5\,\text{m/s}$). |
