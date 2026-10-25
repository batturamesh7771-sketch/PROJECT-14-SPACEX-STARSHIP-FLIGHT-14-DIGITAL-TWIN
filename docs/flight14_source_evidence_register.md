# Starship Flight 14 — Source Evidence & Provenance Register

**Version:** 1.0.0  
**Effective Date:** October 26, 2026  
**Standard Compliance:** NASA-STD-7009B / NASA-HDBK-7009  
**Status:** Canonical Project Artifact  

---

## 1. Master Source Registry

| Source ID | Source Organization / Publication | Document Title / URL | Publication Date | Access Date | Provenance & Usage |
|:---|:---|:---|:---:|:---:|:---|
| `SRC-01` | SpaceX | [Starship Flight 14 Official Release](https://www.spacex.com/launches/starship-flight-14) | 2026-09-28 | 2026-10-25 | Primary authority for Flight 14: liftoff, 33 Raptor 3 engines, ascent engine issue, hot-staging, booster boostback (LOX test), 26 Starlinks deployed via PEZ slot, deorbit, and splashdowns. |
| `SRC-02` | SpaceX | [Starship to Orbit / Reusability Update](https://www.spacex.com/updates/reusability) | 2026-09-15 | 2026-10-25 | Preflight planned mission baseline: 275 km target orbit, ~6 orbits (~10 h duration), 26 Starlink V3 payload manifest. |
| `SRC-03` | SpaceX | [Mission Media & Flight Profile Schematic](https://www.spacex.com/media/9091/download) | 2026-09-28 | 2026-10-25 | Official side-elevation mission trajectory topology: branching hot-staging, booster Gulf return arc, Starship orbital arc, PEZ deploy, Pacific splashdown. |
| `SRC-04` | Reuters | [SpaceX Starship launches 14th flight, first headed to orbit](https://www.reuters.com/business/media-telecom/spacexs-starship-launches-14th-flight-first-headed-orbit-2026-09-28/) | 2026-09-28 | 2026-10-25 | Independent corroboration of mission duration: shortened ~3-hour mission out of caution after ascent engine anomaly; successful orbital insertion and payload release. |
| `SRC-05` | Space.com | [Starship Flight 14 Live Mission Coverage](https://www.space.com/news/live/spacex-starship-flight-14-live-updates-sept-28-2026-starship-first-orbital-launch-attempt) | 2026-09-28 | 2026-10-25 | Independent timeline cross-check: booster splashdown in Gulf, Starship splashdown in Northern Pacific. |
| `SRC-06` | NASA | [NASA-STD-7009B: Standard for Models and Simulations](https://standards.nasa.gov/node/263) | 2021-08-01 | 2026-10-25 | Credibility assessment guidelines: explicit assumptions, uncertainty boundaries, default deny on unverified telemetry, verification matrices. |
| `SRC-07` | NOAA / NASA / USAF | [U.S. Standard Atmosphere 1976 (NOAA-S/T 76-1562)](https://www.ngdc.noaa.gov/stp/space-weather/online-publications/miscellaneous/us-standard-atmosphere-1976/us-standard-atmosphere_st76-1562_noaa.pdf) | 1976-10-01 | 2026-10-25 | Atmospheric density $\rho(h)$, temperature $T(h)$, pressure $p(h)$, speed of sound $a(h)$, dynamic pressure $q = \frac{1}{2}\rho v_{rel}^2$. |
| `SRC-08` | NASA | [Sutton-Graves Convective Heat Flux Correlation (AIAA 2022 Paper 6)](https://ntrs.nasa.gov/api/citations/20220018610/downloads/AIAA_Aviation_2022_Paper-6.pdf) | 2022-06-01 | 2026-10-25 | Sutton-Graves stagnation heat flux formulation: $\dot{q}_s = k_{SG} \sqrt{\rho / R_n} v^3$ ($k_{SG} = 1.7415 \times 10^{-4}\text{ kg}^{1/2}\text{m}^{-1}$). |
| `SRC-09` | NASA GMAT | [General Mission Analysis Tool (GSC-19640-1)](https://software.nasa.gov/software/GSC-19640-1) | 2022-01-01 | 2026-10-25 | Orbital mechanics reference equations: J2 zonal perturbation, Runge-Kutta 8(9) Prince-Dormand integrator verification. |
| `SRC-10` | Three.js Authors | [Three.js WebGL2 3D Scene Engine (r128)](https://threejs.org/docs/) | 2024-01-01 | 2026-10-25 | WebGL2 scene graph, PBR shaders, procedural geometry, Euler/quaternion kinematics, particle systems. |

---

## 2. Claim-Level Evidence Ledger

| Claim ID | Flight Milestone / Technical Fact | Sourced Value / Description | Source ID | Quality Status | Model Representation in Digital Lab |
|:---|:---|:---|:---:|:---:|:---|
| `CLM-01` | Launch Date & Epoch | September 28, 2026 at 07:48 CT (12:48:59 UTC) | `SRC-01`, `SRC-04` | `VERIFIED` | Sets master timeline clock epoch and UTC synchronizer. |
| `CLM-02` | Liftoff Propulsion | Super Heavy 33 Raptor 3 engines ignited | `SRC-01` | `VERIFIED` | 33 engine matrix rendered with initial active state. |
| `CLM-03` | Booster Ascent Anomaly | Single Raptor engine shut down during climb to space | `SRC-01` | `VERIFIED` | Engine #13 marked shutdown at $T+45\text{s}$; load compensated. |
| `CLM-04` | Hot-Staging Separation | Hot-staging maneuver; Starship 6 Raptors ignited | `SRC-01` | `VERIFIED` | Dynamic separation at $T+162\text{s}$; Super Heavy and Starship diverge. |
| `CLM-05` | Booster Boostback Burn | Super Heavy flipped and relit 31 engines (LOX burn-through test) | `SRC-01` | `VERIFIED` | Booster executes $180^\circ$ pitch flip; boostback trajectory to Gulf. |
| `CLM-06` | Booster Landing & Splashdown | Landing burn (11 $\rightarrow$ 5 $\rightarrow$ 3 engines); Gulf splashdown; FTS triggered | `SRC-01` | `VERIFIED` | Splashdown in Gulf of America at $T+425\text{s}$; FTS safety test demo. |
| `CLM-07` | Starship Ascent Anomaly | Single Raptor vacuum engine early shutdown; compensated by 5 engines | `SRC-01` | `VERIFIED` | Single vacuum engine early cutoff; 5 engines burn extended. |
| `CLM-08` | Orbital Insertion | Reached orbit around Earth for the first time | `SRC-01` | `VERIFIED` | Orbit insertion at $T+522.35\text{s}$; circularization burn at $T+900\text{s}$. |
| `CLM-09` | Payload Deployment | All 26 Starlink V3 satellites deployed from mouth PEZ dispenser slot | `SRC-01`, `SRC-03` | `VERIFIED` | Forward PEZ slot opens at $T+1320\text{s}$; 26 flat-pack satellites deploy sequentially into constellation train. |
| `CLM-10` | Mission Shortening Decision | Flight control limited duration to ~3 hours out of abundance of caution | `SRC-01`, `SRC-04` | `VERIFIED` | Observed duration constrained to 11,732 s (~3.15 h), rather than ~10 h. |
| `CLM-11` | Deorbit Burn | Single Raptor sea-level engine deorbit burn | `SRC-01` | `VERIFIED` | Retrograde deorbit burn executed at $T+9900\text{s}$ ($\Delta v = 120\text{ m/s}$). |
| `CLM-12` | Reentry & Pacific Splashdown | Atmospheric reentry at $70^\circ$ AoA; 3 Raptor landing flip; Pacific splashdown | `SRC-01`, `SRC-04` | `VERIFIED` | Reentry heating peak (1330 K); landing flip; northern Pacific splashdown. |

---

## 3. Epistemic Separation Policy

1. **Measured vs. Reconstructed:** Continuous internal engine pressures, structural strain gauge readings, and millimeter-level flap telemetry are proprietary SpaceX flight-computer records and are NOT publicly available. All continuous telemetry channels are explicitly tagged `RECONSTRUCTED_NUMERICAL_SOLVER`.
2. **Planned vs. Observed:** The preflight 6-orbit baseline (`flight14_planned`) and the factual ~3-hour reconstructed flight (`flight14_observed_reconstruction`) are kept strictly isolated.
3. **Synthetic Engineering Test:** The Phase 7 terminal flip and catch lab (`synthetic_engineering_test`) is permanently stamped with a prominent warning banner and cannot be confused with historical Flight 14.
