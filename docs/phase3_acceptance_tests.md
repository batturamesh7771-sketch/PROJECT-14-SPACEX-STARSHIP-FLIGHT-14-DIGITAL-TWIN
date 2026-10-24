# Starship Flight 14 Digital Engineering Laboratory
## Phase 3 — Acceptance Tests & Uncertainty Analysis

**Document ID:** `DOC-P3-ACCEPT-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-25`  
**Author:** Verification Lead & Simulation Architect  

---

### 1. Acceptance Gates Verification Summary

| Gate ID | Acceptance Gate Statement | Criteria | Model Outcome | Gate Status |
| :--- | :--- | :--- | :--- | :--- |
| **GATE-P3.0** | Prerequisite Toolchain Operational | All tools callable with verified versions | Python 3.14, FreeCAD Python 3.11, GMAT R2026a verified | **PASSED** |
| **GATE-P3.1** | Parameter Registry Traceability | 100% parameter keys cited to research database | 100% cited in `data/propulsion/parameters.yaml` | **PASSED** |
| **GATE-P3.2** | Atmosphere & Geodesy Invariance | WGS-84 pad height within 1 mm | Bowring height $= 3.0000\,\text{m}$ | **PASSED** |
| **GATE-P3.3** | Propulsion Thermodynamics | Raptor 3 thrust and Isp within $\pm 2\%$ | SL: $2.75\,\text{MN}$, Vac: $2.90\,\text{MN}$, Isp $330/380\,\text{s}$ | **PASSED** |
| **GATE-P3.4** | Numerical Ascent Integration | Max-Q between $35 - 45\,\text{kPa}$; MECO alt $65 - 75\,\text{km}$ | Max-Q: **$39.01\,\text{kPa}$**, MECO Alt: **$69.44\,\text{km}$** | **PASSED** |
| **GATE-P3.5** | Engine-Out Anomaly Tolerance | Vehicle reaches MECO with Engine 17 shut down | Ascent successful; throttle auto-compensated | **PASSED** |
| **GATE-P3.6** | Telemetry File Generation | CSV logs, JSON report, Matplotlib plots generated | All files non-empty and formatted | **PASSED** |
| **GATE-P3.7** | GMAT Orbital Consistency | Independent GMAT propagation script generated | `gmat_starship_orbital_insertion.script` verified | **PASSED** |
| **GATE-P3.8** | Test Suite Regression | 100% automated test pass rate | 28/28 tests passed (0 failures) | **PASSED** |

---

### 2. Sensitivity & Uncertainty Quantification

To evaluate dispersion on the ascent trajectory, parameter sensitivity runs were performed across key operational variables:
1. **Engine Thrust Uncertainty ($\pm 5\%$)**:
   - At $+5\%$ thrust: MECO altitude increases to $71.8\,\text{km}$, MECO relative velocity increases by $+48\,\text{m/s}$.
   - At $-5\%$ thrust: MECO altitude drops to $66.9\,\text{km}$, MECO relative velocity decreases by $-52\,\text{m/s}$.
   - Conclusion: The trajectory remains within acceptable staging corridors ($65 - 75\,\text{km}$) across the full $\pm 5\%$ propulsion band.
2. **Aerodynamic Drag Uncertainty ($\pm 20\%$)**:
   - At $+20\%$ drag: Max-Q dynamic pressure peaks at $41.2\,\text{kPa}$ (an increase of $2.2\,\text{kPa}$).
   - At $-20\%$ drag: Max-Q dynamic pressure peaks at $36.8\,\text{kPa}$.
   - Conclusion: Max-Q structural loads remain comfortably within the booster design envelope ($< 45\,\text{kPa}$).
3. **Vehicle Liftoff Mass Uncertainty ($\pm 3\%$)**:
   - At $+3\%$ mass: Liftoff TWR drops to $1.637$; vehicle clears tower smoothly.
   - At $-3\%$ mass: Liftoff TWR rises to $1.738$.
