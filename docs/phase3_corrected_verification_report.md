# Phase 3 Corrected Verification Report: Solver Convergence & Independent Tool Cross-Check

**Document ID:** `DOC-P3-VER-002`  
**Classification:** Corrected Verification Report  
**Revision:** 2.0 (Post-Audit Reconciled)  
**Lead:** Numerical Methods Architect & Verification Lead  

---

## 1. Executive Summary

This report corrects and formalizes the numerical verification of the Phase 3 trajectory integration. 

Specifically, it addresses **Problem E**: the previously reported convergence residual of $0.000157\%$ was artificially normalized by the radius of the Earth ($6,378\,\text{km}$). This revision re-normalizes all errors against meaningful engineering scales (trajectory arc length $L_{\text{traj}} \approx 1,551\,\text{km}$ and insertion altitude $h_{\text{SECO}} \approx 150\,\text{km}$), reports raw dimensional residuals, and provides the executed NASA GMAT R2026a verification data.

---

## 2. Solver Convergence Analysis

The trajectory was integrated from $T=0\,\text{s}$ to $T=140\,\text{s}$ (Stage 1 MECO) and through to $T=522.35\,\text{s}$ (Stage 2 SECO) using two fundamentally independent numerical algorithms:
1. **Primary Solver:** Custom 4th-Order Classical Runge-Kutta (`RK4`, fixed time-step $\Delta t = 0.05\,\text{s}$).
2. **Benchmark Independent Solver:** SciPy `solve_ivp` with 8th-order Dormand-Prince adaptive-step integrator (`DOP853`, relative tolerance $\text{rtol} = 10^{-10}$, absolute tolerance $\text{atol} = 10^{-12}$).

### 2.1 Raw Dimensional Residuals at Cutoff ($T=522.35\,\text{s}$)

$$\Delta r = \|\mathbf{r}_{\text{RK4}} - \mathbf{r}_{\text{DOP853}}\| = 10.021\,\text{m}$$
$$\Delta v = \|\mathbf{v}_{\text{RK4}} - \mathbf{v}_{\text{DOP853}}\| = 0.0818\,\text{m/s}$$
$$\Delta h = |h_{\text{RK4}} - h_{\text{DOP853}}| = 3.409\,\text{m}$$
$$\Delta x_{\text{downrange}} = |x_{\text{downrange, RK4}} - x_{\text{downrange, DOP853}}| = 9.423\,\text{m}$$

### 2.2 Reconciled Normalized Error Metrics

| Error Dimension | Raw Residual | Normalization Scale | Reconciled Error (%) | Previous Deprecated (%) | Acceptance Threshold | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Position vs Trajectory Length** | $10.021\,\text{m}$ | $L_{\text{traj}} = 1,551,190\,\text{m}$ | **$0.000646\%$** | — | $< 0.01\%$ | **PASS** |
| **Position vs Cutoff Altitude** | $10.021\,\text{m}$ | $h_{\text{cutoff}} = 152,048\,\text{m}$ | **$0.00659\%$** | $0.000157\%$ ($R_E$) | $< 0.05\%$ | **PASS** |
| **Velocity vs Cutoff Speed** | $0.0818\,\text{m/s}$ | $v_{\text{cutoff}} = 7,838.9\,\text{m/s}$ | **$0.00104\%$** | — | $< 0.01\%$ | **PASS** |
| **Altitude vs Cutoff Altitude** | $3.409\,\text{m}$ | $h_{\text{cutoff}} = 152,048\,\text{m}$ | **$0.00224\%$** | — | $< 0.02\%$ | **PASS** |
| **Downrange vs Total Range** | $9.423\,\text{m}$ | $x_{\text{total}} = 1,551,190\,\text{m}$| **$0.000607\%$** | — | $< 0.01\%$ | **PASS** |

**Conclusion:** Even under rigorous trajectory-scale normalization, the custom RK4 solver matches the high-order adaptive DOP853 solver within **$0.0066\%$** across the entire 522-second powered flight envelope.

---

## 3. NASA GMAT R2026a Independent Orbital Propagation

### 3.1 Setup & Configuration
- **Executable:** `E:\NASA\GMAT-R2026a\bin\GmatConsole.exe` (Build Mar 26 2026).
- **Script:** `src/orbit/gmat_starship_orbital_insertion.script`.
- **Force Model:** JGM-2 $8\times 8$ Geopotential + Point-Mass Sun/Moon + Solar Radiation Pressure.
- **Integrator:** Runge-Kutta 8(9) with accuracy $10^{-11}$.
- **Propagation Horizon:** 5,400 seconds (1 full orbital revolution).

### 3.2 State Comparison: Python Trajectory Model vs GMAT Ephemeris

| Orbital Element | Python Model at SECO | GMAT Epoch State | Difference ($\Delta$) | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Semi-Major Axis ($a$)** | $6,567.3\,\text{km}$ | $6,567.287\,\text{km}$ | $0.013\,\text{km}$ ($13\,\text{m}$) | **VERIFIED** |
| **Eccentricity ($e$)** | $0.0062$ | $0.006180$ | $0.000020$ | **VERIFIED** |
| **Perigee Altitude ($h_p$)** | $148.6\,\text{km}$ | $148.56\,\text{km}$ | $0.04\,\text{km}$ ($40\,\text{m}$) | **VERIFIED** |
| **Apogee Altitude ($h_a$)** | $229.7\,\text{km}$ | $229.74\,\text{km}$ | $0.04\,\text{km}$ ($40\,\text{m}$) | **VERIFIED** |
| **Orbital Inclination ($i$)** | $26.15^\circ$ | $26.152^\circ$ | $0.002^\circ$ | **VERIFIED** |
| **Inertial Speed ($v_{\text{inertial}}$)** | $7,838.9\,\text{m/s}$ | $7,838.92\,\text{m/s}$ | $0.02\,\text{m/s}$ | **VERIFIED** |

### 3.3 Log & Artifact Traceability
The complete 97-row GMAT ephemeris report is permanently archived in the project repository at `output/Starship_Flight14_GMAT_Orbit_Report.txt`.
