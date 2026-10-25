# Phase 3 Corrected Parameter Registry

**Document ID:** `DOC-P3-REG-002`  
**Classification:** Corrected Engineering Baseline  
**Revision:** 2.0 (Post-Audit Reconciled)  
**Lead:** Propulsion Modeling Engineer & Mass Properties Lead  

---

## 1. Overview & Change Log

This document updates and replaces the preliminary parameter tables with reconciled numbers reflecting the findings of `docs/engineering_claims_audit.md`. All quantities are tagged with strict provenance classifications:
- `public_fact`: Officially documented by SpaceX, NASA, FAA, or FCC.
- `observed_event`: Derived directly from broadcast telemetry or contemporaneous photo/video evidence.
- `derived`: Calculated mathematically from physical laws, geometry, or gas dynamics.
- `assumption`: Standard aerospace engineering estimate when proprietary values are unavailable.

---

## 2. Reconciled Vehicle Mass Properties

| Parameter | Symbol | Reconciled Value | SI Units | Status | Primary Provenance | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gross Liftoff Mass** | $m_0$ | **4,939,800.0** | $\text{kg}$ | `derived` | Mass Sum Identity | Reconciled liftoff mass (4,939.8 t) |
| **Stage 1 (Booster) Wet Mass** | $m_{\text{b,wet}}$ | **3,600,825.0** | $\text{kg}$ | `derived` | Booster Sum | $200.825\,\text{t} + 3400.0\,\text{t}$ |
| **Stage 1 Dry Mass** | $m_{\text{b,dry}}$ | **200,825.0** | $\text{kg}$ | `derived` | CAD & Engineering | Tanks, stringers, 33 Raptor 3, ring, fins |
| **Stage 1 Propellant Mass** | $m_{\text{b,prop}}$ | **3,400,000.0** | $\text{kg}$ | `public_fact` | SpaceX Updates | $2,652\,\text{t}\,\text{LOX} + 748\,\text{t}\,\text{LCH}_4$ |
| **Stage 1 LOX/LCH4 Ratio** | $r_{\text{O/F,b}}$ | **3.55** | — | `assumption` | Standard Raptor | Cryogenic densified mixture ratio |
| **Stage 2 (Ship) Gross Wet Mass** | $m_{\text{s,wet}}$ | **1,338,975.0** | $\text{kg}$ | `derived` | Ship Sum | Burnout + tanked propellant |
| **Stage 2 Burnout / Insertion Mass**| $m_{\text{s,burnout}}$| **138,975.0** | $\text{kg}$ | `derived` | Hardware + Payload | $99.975\,\text{t} + 39.0\,\text{t}$ |
| **Stage 2 Dry Structure Mass** | $m_{\text{s,dry}}$ | **99,975.0** | $\text{kg}$ | `derived` | CAD & Engineering | Fuselage, flaps, 6 engines, TPS tiles |
| **Payload Mass (26 Starlinks)**| $m_{\text{payload}}$ | **39,000.0** | $\text{kg}$ | `public_fact` | FCC-SAT-001 | 26 Starlink V3 satellites @ 1,500 kg |
| **Stage 2 Propellant Mass** | $m_{\text{s,prop}}$ | **1,200,000.0** | $\text{kg}$ | `public_fact` | SpaceX Updates | $936\,\text{t}\,\text{LOX} + 264\,\text{t}\,\text{LCH}_4$ |
| **Stage 2 LOX/LCH4 Ratio** | $r_{\text{O/F,s}}$ | **3.60** | — | `assumption` | Vacuum Raptor | Optimized vacuum expansion ratio |

---

## 3. Reconciled Propulsion & Raptor 3 Specifications

| Parameter | Symbol | Stage 1 (Raptor 3 SL) | Stage 2 SL / Vac | SI Units | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Engine Quantity** | $N_{\text{eng}}$ | 33 | 3 SL + 3 Vac | count | `public_fact` | Flown vehicle configuration |
| **Vacuum Thrust per Engine** | $F_{\text{vac}}$ | 2.900 | 2.900 / 3.050 | $\text{MN}$ | `public_fact` | Official SpaceX Raptor 3 rating |
| **Sea-Level Thrust per Engine** | $F_{\text{SL}}$ | 2.766 | 2.766 / — | $\text{MN}$ | `derived` | $F_{\text{vac}} - p_{\text{SL}} A_e$ |
| **Vacuum Specific Impulse** | $I_{\text{sp,vac}}$| 350.0 | 350.0 / 380.0 | $\text{s}$ | `public_fact` | Full flow staged combustion cycle |
| **Sea-Level Specific Impulse** | $I_{\text{sp,SL}}$ | 327.0 | 327.0 / — | $\text{s}$ | `derived` | Expansion ratio pressure derate |
| **Nozzle Exit Diameter** | $D_e$ | 1.300 | 1.300 / 2.300 | $\text{m}$ | `public_fact` | Physical bell dimensions |
| **Nozzle Exit Area** | $A_e$ | 1.3273 | 1.3273 / 4.1548 | $\text{m}^2$ | `derived` | $\pi D_e^2 / 4$ |
| **Nominal Chamber Pressure** | $P_c$ | 35.0 | 35.0 | $\text{MPa}$ | `public_fact` | Raptor 3 rated design point |
| **Full Throttle Liftoff Thrust** | $F_{\text{stack,0}}$| **81.69 to 91.26** | — | $\text{MN}$ | `derived` | 90% ramp ($81.69\,\text{MN}$) $\to$ 100% ($91.26\,\text{MN}$) |
| **Full Throttle Vacuum Thrust**| $F_{\text{stack,vac}}$| **95.70** | **17.85** | $\text{MN}$ | `derived` | $33 \times 2.90\,\text{MN}$ / $(3\times 2.90 + 3\times 3.05)\,\text{MN}$ |

---

## 4. Reconciled Aerodynamic Reference Properties

| Parameter | Symbol | Super Heavy + Starship | Starship Stage 2 | SI Units | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Vehicle Outer Diameter** | $D_{\text{ref}}$ | 9.00 | 9.00 | $\text{m}$ | `public_fact` | Barrel diameter |
| **Aerodynamic Reference Area** | $S_{\text{ref}}$ | 63.617 | 63.617 | $\text{m}^2$ | `derived` | Cross-sectional area ($\frac{\pi}{4} D^2$) |
| **Total Stack Length** | $L_{\text{stack}}$ | 121.30 | 50.30 | $\text{m}$ | `public_fact` | Master skeleton geometry |
| **Subsonic Zero-Lift Drag Coeff** | $C_{D0,\text{sub}}$ | 0.28 | 0.32 | — | `assumption` | Slender cylinder with blunt nose |
| **Transonic Peak Drag Coeff** | $C_{D0,\text{trans}}$| 0.48 | 0.52 | — | `assumption` | Mach 1.0 to 1.3 wave drag rise |
| **Hypersonic Drag Coeff** | $C_{D0,\text{hyper}}$| 0.22 | 0.24 | — | `assumption` | Mach > 5 modified Newtonian |
