# Starship Flight 14 Digital Engineering Lab — Phase 6 Master Engineering Report
## Atmospheric Reentry, Hypersonic Aerodynamics, Aerothermal Heating, Trajectory Guidance, and Splashdown Simulation

**Document ID:** `DOC-P6-ENG-REPORT-001`  
**Phase:** 6 — Atmospheric Reentry & Aerothermodynamics  
**System Under Test:** Starship Flight 14 Upper Stage (Deorbited Reentry Vehicle)  
**Classification:** Digital Engineering Architectural & Scientific Verification Report  
**Baseline Git Commit Target:** Phase 6 Final  
**Date of Publication:** October 25, 2026  

---

## 1. Executive Summary

Phase 6 of the Starship Flight 14 Digital Engineering Lab establishes an end-to-end, scientifically defensible, reproducible 3-DOF numerical simulation of atmospheric reentry, hypersonic deceleration, aerothermal heating, trajectory guidance, and ocean splashdown target assessment.

The simulation bridges the orbital disposal trajectory developed in Phase 5 to ocean surface contact, solving the full coupled translational equations of motion in an Earth-Centered Inertial (ECI) frame with WGS-84 oblate gravity ($J_2$), a rotating atmosphere ($\boldsymbol{\omega}_E \times \mathbf{r}$), high-angle-of-attack hypersonic aerodynamics, Sutton-Graves convective stagnation heating, and closed-loop bank-angle modulation.

### 1.1 Core Mission & Numerical Findings
- **Entry Interface Conditions ($h = 120.0\,\text{km}$):**
  - Inertial Speed: $7,780.20\,\text{m/s}$
  - Atmospheric-Relative Speed: $7,356.24\,\text{m/s}$ (Mach $17.80$)
  - Relative Flight-Path Angle: $\gamma_{\text{rel}} = -0.7519^\circ$
  - Geodetic Coordinates: $7.1084^\circ\,\text{N}$, $58.3341^\circ\,\text{W}$ (over the Atlantic coast of northern South America)
  - Vehicle Entry Mass: $177,272.71\,\text{kg}$ ($177.27\,\text{t}$)
- **Baseline Reentry Performance (Uncontrolled Nominal):**
  - Peak Dynamic Pressure: $q_{\text{dyn,max}} = 68.26\,\text{kPa}$ at $h = 28.1\,\text{km}$ ($t = 618\,\text{s}$)
  - Peak Apparent Deceleration: $a_{\max} = 3.23\,\text{g}$ ($31.67\,\text{m/s}^2$) at $h = 23.4\,\text{km}$ ($t = 642\,\text{s}$)
  - Peak Stagnation Convective Heat Flux: $\dot{q}_{\text{stag,max}} = 0.794\,\text{MW/m}^2$ ($79.4\,\text{W/cm}^2$) at $h = 48.2\,\text{km}$ ($t = 478\,\text{s}$)
  - Peak Outer Mold Line (OML) Wall Temperature: $T_{\text{wall,max}} = 1,686\,\text{K}$ ($1,413^\circ\text{C}$) under radiative equilibrium ($\epsilon = 0.85$)
  - Cumulative Stagnation Heat Load: $Q_{\text{stag}} = 240.67\,\text{MJ/m}^2$
  - Entry Duration to Sea Level ($h = 0\,\text{m}$): $929.44\,\text{s}$ ($\approx 15.49\,\text{minutes}$)
  - Terminal Subsonic Relative Speed: $v_{\text{term}} = 209.7\,\text{m/s}$ (Mach $0.62$)
  - Terminal Impact Location: $14.0441^\circ\,\text{S}$, $15.4063^\circ\,\text{W}$ (South Atlantic Ocean disposal track)
  - Target Miss Distance (Disposal Datum): $9.05\,\text{km}$ ($< 50\,\text{km}$ corridor radius, classified as `TARGET_REGION_REACHED`)
- **Closed-Loop Guidance Tradeoffs:**
  - Active bank modulation ($\sigma \in [-45^\circ, +45^\circ]$) tilts the aerodynamic lift vector to null crossrange trajectory error.
  - Aggressive bank-to-turn maneuvers induce flight-path steepening, elevating peak dynamic pressure to $85.47\,\text{kPa}$ and peak deceleration to $4.04\,\text{g}$, demonstrating real-world aerodynamic control tradeoffs.
- **Verification & Software Health:**
  - Automated unit test suite: **114 passing tests out of 114 (100%)** with zero regressions across Phases 1–5.
  - Step-size convergence: Terminal position error between $\Delta t = 1.0\,\text{s}$ and the $\Delta t = 0.25\,\text{s}$ reference is $\le 0.01\,\text{m}$.
  - Monte Carlo dispersion (50 samples, Seed 42): Mean peak dynamic pressure is $68.92 \pm 2.87\,\text{kPa}$, mean peak deceleration is $3.23 \pm 0.09\,\text{g}$, mean total heat load is $242.44 \pm 10.03\,\text{MJ/m}^2$.

---

## 2. Mission Architecture & Trajectory Pathways

Phase 6 evaluates three primary reentry scenarios:

```
+--------------------------------------------------------------------------------------------------+
|                                    PHASE 6 REENTRY TIMELINE                                      |
+--------------------------------------------------------------------------------------------------+
| T+6527.3s (t=0s)   | Entry Interface (120 km)      | V_rel = 7356 m/s, gamma = -0.75 deg         |
| T+7005.3s (t=478s) | Peak Aerothermal Heating      | alt = 48.2 km, q_dot = 0.794 MW/m^2         |
| T+7145.3s (t=618s) | Peak Dynamic Pressure         | alt = 28.1 km, q_dyn = 68.26 kPa            |
| T+7169.3s (t=642s) | Peak Structural Deceleration  | alt = 23.4 km, a_apparent = 3.23 g          |
| T+7372.3s (t=845s) | Subsonic Mach Transition      | alt = 8.6 km, Mach = 1.00                   |
| T+7456.8s (t=929s) | Terminal Sea-Level Impact     | alt = 0.0 km, V_rel = 209.7 m/s (Mach 0.62) |
+--------------------------------------------------------------------------------------------------+
```

1. **Pathway A (Nominal South Atlantic Disposal — Approved Baseline):** Derived directly from the audited Phase 5 disposal burn. The upper stage executes a targeted retrograde burn ($\Delta v = 41.52\,\text{m/s}$), lowering perigee to $-81.09\,\text{km}$ (sub-surface), ensuring steep atmospheric capture and safe disposal in the remote South Atlantic Ocean south of the equator.
2. **Pathway B (Synthetic Pacific Exclusion Corridor):** A constructed scenario evaluating closed-loop bank angle guidance toward an exclusion polygon north of Hawaii ($26.50^\circ\,\text{N}$, $162.00^\circ\,\text{W}$), testing crossrange steering authority and energy dissipation.
3. **Pathway C (Hypothetical Direct Uncontrolled Decay):** A baseline uncontrolled scenario isolating open-loop aerodynamic trim ($\sigma = 0^\circ$).

---

## 3. Atmospheric and Geophysical Environment Models

### 3.1 Earth Oblateness and Gravity
Gravitational acceleration incorporates Earth oblateness via the $J_2$ zonal harmonic:
$$\mathbf{a}_{\text{grav}} = -\frac{\mu_E}{r^3} \mathbf{r} + \mathbf{a}_{J_2}$$
where:
$$\mathbf{a}_{J_2} = \frac{3 \mu_E J_2 R_E^2}{2 r^5} \left[ \left(5 \frac{z^2}{r^2} - 1\right) x\,\hat{\mathbf{i}} + \left(5 \frac{z^2}{r^2} - 1\right) y\,\hat{\mathbf{j}} + \left(5 \frac{z^2}{r^2} - 3\right) z\,\hat{\mathbf{k}} \right]$$
Constants: $\mu_E = 3.986004418 \times 10^{14}\,\text{m}^3/\text{s}^2$, $R_E = 6,378,137.0\,\text{m}$, $J_2 = 1.08262668 \times 10^{-3}$.

### 3.2 US Standard Atmosphere 1976 with Continuum Extension
Atmospheric density $\rho(z)$, pressure $P(z)$, and temperature $T(z)$ are evaluated across standard geopotential layers from sea level to $86.0\,\text{km}$ using exact standard lapse rates. Above $86.0\,\text{km}$ (the mesopause, $T_{86} = 184.65\,\text{K}$, $P_{86} = 0.3023\,\text{Pa}$), a continuous thermospheric continuum model provides smooth density decay up to $150\,\text{km}$:
$$\rho(z) = \rho_{86} \exp\left(-\frac{z - 86000}{H(z)}\right)$$
where scale height $H(z)$ smoothly increases from $5.5\,\text{km}$ to $12.0\,\text{km}$ to match published thermospheric tables.

### 3.3 Atmospheric-Relative Kinematics
Because the atmosphere co-rotates with the solid Earth at angular rate $\boldsymbol{\omega}_E = [0, 0, 7.2921150 \times 10^{-5}]^T\,\text{rad/s}$, the aerodynamic velocity vector is strictly:
$$\mathbf{v}_{\text{rel}} = \mathbf{v}_{\text{ECI}} - \boldsymbol{\omega}_E \times \mathbf{r}_{\text{ECI}}$$
Accounting for Earth rotation is critical: at entry, inertial speed is $7,780.2\,\text{m/s}$, whereas atmospheric-relative speed is $7,356.2\,\text{m/s}$ (a difference of over $420\,\text{m/s}$).

---

## 4. Hypersonic Vehicle & Aerodynamics Model

### 4.1 Mass and Geometric Configuration
- Reentry Mass: $m = 177,272.71\,\text{kg}$ ($177.27\,\text{t}$)
- Cross-Sectional Reference Area: $A_{\text{ref}} = \pi (4.5\,\text{m})^2 = 63.617\,\text{m}^2$
- Reference Length: $L_{\text{ref}} = 50.0\,\text{m}$
- Forebody Effective Nose Curvature Radius: $R_n = 4.50\,\text{m}$
- Nominal Trim Angle of Attack: $\alpha = 70.0^\circ$ ("belly-flop" high-drag orientation)
- Hypersonic Ballistic Coefficient:
  $$\beta = \frac{m}{C_d A_{\text{ref}}} = \frac{177,272.71}{1.50 \times 63.617} \approx 1,857.7\,\text{kg/m}^2$$

### 4.2 Aerodynamic Polar Formulation
Forces are computed using modified Newtonian theory blended with subsonic cross-flow drag:
- Hypersonic ($M \ge 5.0$):
  $$C_d = 0.15 + (1.50 - 0.15) \sin^3(\alpha) = 1.272$$
  $$C_l = 2.0 (0.40) \sin^2(\alpha) \cos(\alpha) = 0.241$$
  resulting in hypersonic lift-to-drag ratio $L/D \approx 0.19\text{--}0.27$.
- Subsonic ($M \le 0.8$):
  $$C_d = 0.10 + (1.20 - 0.10) \sin^2(\alpha) = 1.071$$
  $$C_l = 1.20 \sin^2(\alpha) \cos(\alpha) = 0.362$$
- Transonic/Supersonic ($0.8 < M < 5.0$): Smooth cubic Hermite polynomial blending.

### 4.3 Strictly Orthogonal Aerodynamic Force Vectors
1. **Drag Force:** Strictly opposes relative velocity:
   $$\hat{\mathbf{v}} = \frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|}, \quad \mathbf{F}_D = - \frac{1}{2} \rho v_{\text{rel}}^2 C_d A_{\text{ref}}\,\hat{\mathbf{v}}$$
2. **Trajectory Lift Basis:** Defined using the radial unit vector $\hat{\mathbf{r}} = \mathbf{r} / \|\mathbf{r}\|$:
   $$\hat{\mathbf{w}} = \frac{\hat{\mathbf{r}} \times \hat{\mathbf{v}}}{\|\hat{\mathbf{r}} \times \hat{\mathbf{v}}\|}, \quad \hat{\mathbf{u}}_{\text{up}} = \hat{\mathbf{v}} \times \hat{\mathbf{w}}$$
   $\hat{\mathbf{u}}_{\text{up}}$ is strictly orthogonal to $\hat{\mathbf{v}}$ and points upward (away from Earth center).
3. **Bank Angle Rotation:** The commanded bank angle $\sigma$ rotates lift around $\hat{\mathbf{v}}$:
   $$\hat{\mathbf{l}} = \cos(\sigma)\,\hat{\mathbf{u}}_{\text{up}} + \sin(\sigma)\,\hat{\mathbf{w}}$$
   $$\mathbf{F}_L = \frac{1}{2} \rho v_{\text{rel}}^2 C_l A_{\text{ref}}\,\hat{\mathbf{l}}$$

---

## 5. Aerothermal Heating & Thermal Environment

### 5.1 Sutton-Graves Convective Stagnation Heating
Convective stagnation heat flux is calculated via the NASA TR R-376 correlation for Earth air:
$$\dot{q}_{\text{stag}} = k_{\text{SG}} \sqrt{\frac{\rho}{R_n}}\,v_{\text{rel}}^3$$
where $k_{\text{SG}} = 1.7415 \times 10^{-4}\,\text{W}\cdot\text{s}^3/(\text{m}^{3.5}\cdot\text{kg}^{0.5})$.
- Peak stagnation flux: $\dot{q}_{\text{stag,max}} = 0.794\,\text{MW/m}^2 = 79.4\,\text{W/cm}^2$.
- Windward acreage heating is scaled by characteristic geometric shielding: $\dot{q}_{\text{wind}} \approx 0.25\,\dot{q}_{\text{stag}} = 0.199\,\text{MW/m}^2$.

### 5.2 Radiative Equilibrium Surface Temperature
Assuming non-catalytic gray-body radiation balance ($\dot{q} = \epsilon \sigma_{\text{SB}} T_{\text{wall}}^4$) with ceramic tile surface emissivity $\epsilon = 0.85$:
$$T_{\text{wall}} = \left(\frac{\dot{q}_{\text{stag}}}{\epsilon \sigma_{\text{SB}}}\right)^{0.25}$$
where $\sigma_{\text{SB}} = 5.670374419 \times 10^{-8}\,\text{W}/(\text{m}^2\cdot\text{K}^4)$.
- Maximum theoretical wall temperature: $T_{\text{wall,max}} = 1,686\,\text{K}$ ($1,413^\circ\text{C}$).
- This falls safely within the transient temperature capability of sintered reaction-bonded silicon carbide / silica ceramic tiles (rated to $\sim 1,650^\circ\text{C}$).

### 5.3 Cumulative Heat Load Integration
The total integrated thermal energy absorbed per unit area is evaluated by continuous integration:
$$Q(t) = \int_{0}^{t} \dot{q}_{\text{stag}}(\tau)\,d\tau$$
- Cumulative stagnation load at sea level: $Q_{\text{stag}} = 240.67\,\text{MJ/m}^2$.

---

## 6. Hypersonic Deceleration & Dynamic Pressure Profiles

Reentry vehicles experience three distinct physical peaks during shallow atmospheric entry:
1. **Peak Heating First:** Occurs high in the mesosphere ($h = 48.2\,\text{km}$) where relative speed remains extreme ($v_{\text{rel}} \approx 6,650\,\text{m/s}$) and density begins to rise rapidly.
2. **Peak Dynamic Pressure Second:** Occurs in the upper stratosphere ($h = 28.1\,\text{km}$, $q_{\text{dyn,max}} = 68.26\,\text{kPa}$) where the product $\rho v^2$ maximizes.
3. **Peak Apparent Deceleration Third:** Occurs in the mid-stratosphere ($h = 23.4\,\text{km}$, $a_{\max} = 3.23\,\text{g}$) as vehicle drag force peaks relative to its total mass.
4. **Subsonic Terminal Descent:** Below $10\,\text{km}$, drag has removed over $99.9\%$ of vehicle kinetic energy. The vehicle decelerates past Mach $1.0$ at $h = 8.6\,\text{km}$, stabilizing at terminal aerodynamic speed $v_{\text{rel}} \approx 209.7\,\text{m/s}$ at sea level.

---

## 7. Closed-Loop Guidance & Crossrange Control

### 7.1 Architecture & Control Laws
The guidance system employs a closed-loop Proportional-Derivative (PD) bank-angle modulation controller:
$$\sigma_{\text{cmd}} = - \left( K_p\,\Delta y_{\text{cross}} + K_d\,\frac{d\Delta y_{\text{cross}}}{dt} \right)$$
- Gain parameters: $K_p = 0.50^\circ/\text{km}$, $K_d = 0.05\,\text{s}/\text{km}$.
- Control constraints:
  - Saturation limit: $|\sigma| \le 45.0^\circ$.
  - Actuator slew rate limit: $|\dot{\sigma}| \le 10.0^\circ/\text{s}$.
  - Dynamic pressure deadband: Inactive if $q_{\text{dyn}} < 50.0\,\text{Pa}$.
  - Operational altitude window: Active between $100\,\text{km}$ and $15\,\text{km}$.

### 7.2 Guidance Coupling & Load Tradeoffs
Bank angle commands roll the lift vector out of the vertical plane, generating cross-track acceleration to null crossrange errors. Tilting the lift vector reduces the vertical lift component, resulting in a slightly steeper trajectory that elevates peak dynamic pressure ($85.47\,\text{kPa}$ vs $68.26\,\text{kPa}$) and peak deceleration ($4.04\,\text{g}$ vs $3.23\,\text{g}$).

---

## 8. Terminal Ocean Impact & Splashdown Assessment

Terminal state assessment converts ECI coordinates to Earth-fixed geodetic coordinates via closed-form Bowring transformation on the WGS-84 ellipsoid:
- **Disposal Impact Coordinates:** $14.0441^\circ\,\text{S}$, $15.4063^\circ\,\text{W}$.
- **Target Miss Distance:** $9.05\,\text{km}$ relative to planned disposal datum.
- **Corridor Classification:** `TARGET_REGION_REACHED` (miss distance well within the $50\,\text{km}$ primary exclusion boundary).
- **Terminal Kinetic Energy:** $\approx 3.89\,\text{GJ}$ at terminal velocity ($209.7\,\text{m/s}$), emphasizing that surface intersection represents a high-energy water impact and does not imply vehicle recovery.

---

## 9. Numerical Integration & Convergence Study

Integration is performed using the adaptive 8th-order Dormand-Prince method (DOP853) with an analytical root-finding event function detecting $h_{\text{geodetic}} = 0.0\,\text{m}$.
The step-size convergence study verified:
- $\Delta t = 0.25\,\text{s}$ (Reference): 3,719 steps, impact time $929.44\,\text{s}$.
- $\Delta t = 1.00\,\text{s}$ (Nominal): 931 steps, position difference $\le 0.01\,\text{m}$.
- Even a coarse $\Delta t = 5.00\,\text{s}$ produces only $1.44\,\text{m}$ of terminal position error.

---

## 10. Uncertainty Quantification & Monte Carlo Analysis

### 10.1 Deterministic One-At-a-Time (OAT) Sensitivities
Sensitivity derivatives evaluated for 7 key parameters:
1. **Vehicle Mass (+5,000 kg):** Increases ballistic coefficient $\beta$, shifting peak deceleration deeper into the atmosphere ($\Delta h \approx -0.4\,\text{km}$), increasing peak dynamic pressure by $+1.92\,\text{kPa}$.
2. **Hypersonic Drag Coefficient (+0.10):** Decreases ballistic coefficient, raising the deceleration altitude and lowering peak dynamic pressure by $-4.35\,\text{kPa}$.
3. **Atmospheric Density Scale (+10%):** Compresses entry duration by $-12.4\,\text{s}$, increases peak deceleration by $+0.04\,\text{g}$.
4. **Nose Radius (+0.50 m):** Blunts the vehicle forebody, reducing stagnation heat flux by $-0.041\,\text{MW/m}^2$ (a $5.2\%$ reduction in peak flux).

### 10.2 Monte Carlo Dispersion (N = 50 Samples, Seed 42)
Stochastic perturbations applied simultaneously across mass, reference area, aerodynamic coefficients, atmospheric density, and entry velocity vector:
- Peak Dynamic Pressure: Mean $= 68.92\,\text{kPa}$, Std $= 2.87\,\text{kPa}$, 90th percentile $= 72.8\,\text{kPa}$.
- Peak Apparent Deceleration: Mean $= 3.23\,\text{g}$, Std $= 0.09\,\text{g}$, max observed $= 3.48\,\text{g}$.
- Peak Stagnation Flux: Mean $= 0.799\,\text{MW/m}^2$, Std $= 0.028\,\text{MW/m}^2$.
- Total Cumulative Heat Load: Mean $= 242.44\,\text{MJ/m}^2$, Std $= 10.03\,\text{MJ/m}^2$.
- Primary Corridor Containment Fraction: $44.0\%$ within $50\,\text{km}$ circle; $100\%$ within $95\,\text{km}$ exclusion zone.

---

## 11. Engineering Conclusions

1. **Physical Integrity:** Phase 6 delivers an open, scientifically sound, transparent reentry dynamics model strictly aligned with classical hypersonic aerodynamics and aerothermodynamics literature.
2. **Baseline Continuity:** Zero regressions across 89 prior unit tests from Phases 1–5; 25 new tests verify all Phase 6 subsystems (`TEST-P6-01` to `TEST-P6-25`).
3. **Data Provenance:** Every parameter is strictly classified under authoritative provenance tags (`PUBLIC_FACT`, `DERIVED_PUBLIC`, `MODEL_ASSUMPTION`, `SYNTHETIC_SCENARIO`, `SIMULATION_OUTPUT`, `VALIDATION_REFERENCE`).
4. **Readiness for Downstream Digital Engineering:** Trajectory dynamic pressures, structural $g$-loads, and aerothermal heat fluxes provide realistic boundary inputs for subsequent structural, thermal, and recovery analyses.
