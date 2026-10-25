# Phase 4 Parameter Provenance & Uncertainty Ledger

**Document ID:** `DOC-P4-PROV-001`  
**Classification:** Engineering Parameter Traceability Ledger  
**Revision:** 1.0  
**Lead:** Systems Engineering & Verification Lead  

---

## 1. Classification Definitions

Every numerical quantity used in Phase 4 is tagged with one of the following authoritative classifications:
1. `public_fact`: Officially documented by SpaceX, NASA, FAA, or FCC regulatory filings.
2. `observed_event`: Derived from broadcast flight telemetry callouts, mission video, or contemporaneous news reporting.
3. `derived`: Computed via exact physical law, geometry, coordinate transforms, or mathematical integration.
4. `assumption`: Professional engineering estimate where proprietary manufacturer data is unavailable.
5. `unknown`: Parameters that cannot be defended with existing public evidence and are therefore excluded.

---

## 2. Parameter Provenance Matrix

| Parameter Description | Symbol | Value | Units | Classification | Source ID | Source Citation Locator | Uncertainty Bounds |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Booster MECO Time** | $T_{\text{MECO}}$ | 140.0 | $\text{s}$ | `observed_event` | F4-05, SPX-F14-001 | Mission broadcast audio callout | $\pm 0.5\,\text{s}$ |
| **Staging Ignition Epoch** | $T_{\text{stage}}$ | 142.0 | $\text{s}$ | `observed_event` | F4-05, SPX-F14-001 | Visual upper stage plume eruption | $\pm 0.5\,\text{s}$ |
| **Booster Staging Throttle** | $\delta_{\text{stage,b}}$| 0.40 | — | `assumption` | F4-02, NASA-HECC-001| NASA HECC Starship hot-stage profile | $\pm 0.05$ |
| **Booster Center Engines at Staging**| $N_{\text{stage,b}}$| 3 | count | `public_fact` | SPX-UPD-001 | SpaceX hot-stage architecture | Exact ($3\times\text{SL}$) |
| **Ship Engines at Staging** | $N_{\text{stage,s}}$| 6 | count | `public_fact` | SPX-F14-001 | $3\times\text{SL} + 3\times\text{Vac}$ ignition | Exact |
| **Hot-Stage Peak Plume Force** | $F_{\text{plume}}$ | 1.90 | $\text{MN}$ | `assumption` | F4-02, NASA-HECC-002| Pressure integral over forward dome | $\pm 35\%$ |
| **Hot-Stage Plume Decay Tau** | $\tau_{\text{plume}}$ | 1.50 | $\text{s}$ | `assumption` | F4-02 | Ring venting transient decay | $\pm 0.3\,\text{s}$ |
| **Mechanical Separation Impulse** | $J_{\text{mech}}$ | 0.0 | $\text{N}\cdot\text{s}$ | `assumption` | F4-04 | Free aerodynamic pneumatic release | $\pm 5\times 10^4\,\text{N}\cdot\text{s}$ |
| **Booster Boostback Ignition Time** | $T_{\text{boostback}}$| 155.0 | $\text{s}$ | `observed_event` | F4-05, SPX-F14-001 | Telemetry acceleration reversal | $\pm 1.0\,\text{s}$ |
| **Booster Boostback Burn Duration** | $\Delta t_{\text{bb}}$| 58.0 | $\text{s}$ | `observed_event` | F4-05 | Center 13 engine burn | $\pm 2.0\,\text{s}$ |
| **Booster Boostback Pitch Angle** | $\theta_{\text{bb}}$ | -2.8 | $\text{deg}$ | `derived` | Calibrated | Locks apogee to $107.6\,\text{km}$ | $\pm 0.5^\circ$ |
| **Booster Splashdown Time** | $T_{\text{splash,b}}$| 413.35 | $\text{s}$ | `observed_event` | F4-05, REU-F14-001 | Gulf of Mexico landing telemetry | $\pm 3.0\,\text{s}$ |
| **Booster Splashdown Speed** | $v_{\text{splash,b}}$| 6.0 | $\text{m/s}$ | `derived` | Landing Burn Solver| Controlled soft touchdown | $\pm 1.5\,\text{m/s}$ |
| **Ship SECO Insertion Time** | $T_{\text{SECO}}$ | 522.35 | $\text{s}$ | `observed_event` | F4-05, REU-F14-001 | Orbital insertion announcement | $\pm 1.0\,\text{s}$ |
| **Ship Insertion Perigee Altitude** | $h_p$ | 148.6 | $\text{km}$ | `derived` | Keplerian Solver | Confirmed via GMAT ($148.56\,\text{km}$) | $\pm 2.0\,\text{km}$ |
| **Ship Insertion Apogee Altitude** | $h_a$ | 229.7 | $\text{km}$ | `derived` | Keplerian Solver | Confirmed via GMAT ($229.74\,\text{km}$) | $\pm 3.0\,\text{km}$ |
| **Ship Insertion Speed (Inertial)** | $v_{\text{SECO}}$| 7,838.9 | $\text{m/s}$ | `derived` | Vis-viva Identity | Confirmed via GMAT ($7,838.92\,\text{m/s}$) | $\pm 5.0\,\text{m/s}$ |
| **Ship Reserve Propellant at SECO**| $m_{\text{res,s}}$| 81.88 | $\text{t}$ | `derived` | Integrated mass | For deorbit & landing burns | $\pm 10.0\,\text{t}$ |
| **Payload Manifest Count** | $N_{\text{payload}}$| 26 | count | `public_fact` | F4-05, FCC-SAT-001 | Starlink V3 operational batch | Exact |
| **Total Payload Mass** | $m_{\text{payload}}$| 39,000.0 | $\text{kg}$ | `public_fact` | FCC-SAT-001 | 26 satellites @ 1,500 kg each | $\pm 5\%$ |
| **Upper Stage Early Anomaly Window**| $T_{\text{anomaly}}$| 2.5 to 3.0| $\text{hours}$ | `observed_event` | F4-05, REU-F14-001 | On-orbit engine restart issue | $\pm 0.3\,\text{h}$ |
