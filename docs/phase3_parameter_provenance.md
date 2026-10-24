# Starship Flight 14 Digital Engineering Laboratory
## Phase 3 — Parameter Provenance & Uncertainty Register

**Document ID:** `DOC-P3-PROV-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-25`  
**Author:** Senior Systems Engineer & Research Data Lead  

---

### 1. Master Parameter Provenance Table

Every physical, aerodynamic, propulsion, and mission parameter in Phase 3 is linked to authoritative sources:

| Parameter Name | Value in Simulation | Units | Provenance Tier | Citation / Source ID | Uncertainty / Boundary | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Launch Latitude** | `25.9960` | deg N | PUBLIC_FACT | FAA-ENV-001 (Boca Chica EIS) | $\pm 0.0001^\circ$ | Starbase OLM-1 geographic surveyed coordinate. |
| **Launch Longitude** | `-97.1550` | deg W | PUBLIC_FACT | FAA-ENV-001 (Boca Chica EIS) | $\pm 0.0001^\circ$ | Starbase OLM-1 geographic surveyed coordinate. |
| **Launch Elevation** | `3.0` | m MSL | OBSERVED | USGS National Map | $\pm 0.5\,\text{m}$ | Coastal pad elevation above mean sea level. |
| **Liftoff Total Mass** | `4939.80` | tonnes | DERIVED | Phase 2 CAD BOM & SPX-F14-001 | $\pm 3.0\%$ | Booster ($200.8\,\text{t}$ dry $+ 3,400\,\text{t}$ prop) + Ship ($139.0\,\text{t}$ dry/payload $+ 1,200\,\text{t}$ prop). |
| **Raptor 3 SL Thrust** | `2.75` | MN | PUBLIC_FACT | SPX-ENG-001 (Raptor 3 Announcement) | $\pm 2.0\%$ | Official SpaceX announcement: $280\,\text{tf}$ sea-level thrust. |
| **Raptor 3 Vac Thrust** | `2.90` | MN | PUBLIC_FACT | SPX-ENG-001 | $\pm 2.0\%$ | $295\,\text{tf}$ vacuum rated thrust. |
| **Raptor 3 SL Isp** | `330.0` (SL) / `350.0` (Vac) | s | PUBLIC_FACT | SPX-ENG-001 & NASA Spaceflight | $\pm 1.5\%$ | Standard sea-level expansion nozzle performance. |
| **Raptor 3 Vac Isp** | `380.0` | s | PUBLIC_FACT | SPX-ENG-001 | $\pm 1.5\%$ | High expansion ratio vacuum nozzle. |
| **Booster Engine Count** | `33` | engines | PUBLIC_FACT | SPX-F14-001 Webcast Telemetry | Exact (0%) | 1 center, 2 inner, 10 middle, 20 outer ring. |
| **Starship Engine Count**| `6` | engines | PUBLIC_FACT | SPX-F14-001 | Exact (0%) | 3 Sea-Level + 3 Vacuum Raptors. |
| **Transonic Drag Rise** | $C_{D,\text{peak}} = 0.63$ | dimensionless | DERIVED | NASA SP-8000 launch vehicle aerodata | $\pm 10.0\%$ | Peaking at Mach 1.05 for blunt cone-cylinder geometry. |
| **Booster Anomaly Time**| $T+35.0$ / $T+76.0$ | s | OBSERVED | SPX-F14-001 / REU-F14-001 | Exact timestamp | Outer engine 17 / 21 shut down during first-stage powered ascent. |
| **MECO Timestamp** | $T+140.0$ | s | MEASURED | SPX-F14-001 Webcast Telemetry | $\pm 0.5\,\text{s}$ | Outer engine cutoff prior to hot-staging separation. |
| **Staging Latch Time** | $T+142.0$ | s | MEASURED | SPX-F14-001 | $\pm 0.5\,\text{s}$ | Physical latch separation and Stage 2 full ignition. |

---

### 2. Distinction Between Data Integrity & Physical Truth

- **Data Integrity Tests** confirm that data files are syntactically valid, non-empty, and adhere to declared schema columns.
- **Physical Validation** requires cross-checking numerical outcomes (e.g. Max-Q altitude, velocity at MECO, orbital perigee) against empirical flight observations and independent high-precision reference propagators.
