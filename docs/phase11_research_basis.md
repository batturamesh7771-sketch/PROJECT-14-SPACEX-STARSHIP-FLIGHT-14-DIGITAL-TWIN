# Phase 11: Research Basis & Methodological Standards
**Starship Flight 14 Digital Engineering Lab**  
**Standards Reference:** NASA-STD-7009B, NASA-HDBK-7009B, NIST TN 1297, JCGM 101:2008, NPR 7150.2D  
**Author:** Lead Independent Verification, Flight-Dynamics Validation & Software-Assurance Engineer

---

## 1. Methodological & Standards Hierarchy

To ensure scientific credibility without making false claims of official agency endorsement or certification, Phase 11 adopts the best-practice principles of leading aerospace and metrology standards:

| Document ID | Issuing Authority | Scope & Relevance to Flight 14 Digital Lab |
| :--- | :--- | :--- |
| **NASA-STD-7009B** | NASA Technical Standards Program | Standard for Models and Simulations: Defines model lifecycle credibility, empirical validation, input data pedigree, uncertainty characterization, robustness, and intended use. |
| **NASA-HDBK-7009B** | NASA Technical Standards System (2026-02-03) | Handbook for Models and Simulations: Practical implementation guidelines for model verification, empirical validation, error bounds, validation domain definition, and M&S risk assessment. |
| **NASA SP-2016-6105 Rev 2 (App. D)** | NASA Systems Engineering Handbook | Requirements Verification Matrix (RVM) standards: Mapping each shall-statement to a unique ID, definitive source, verification method, test case, expected result, and recorded evidence. |
| **NASA-STD-8739.8B** | NASA Software Assurance | Software Assurance and Software Safety: Principles of independent review, regression management, and verification integrity. |
| **NASA NPR 7150.2D (Ch. 4.5)** | NASA Procedural Requirements | Software Testing Requirements: Requirements-based testing, measured test execution, regression suites, and acceptance criteria. |
| **NIST TN 1297** | National Institute of Standards & Technology | Guidelines for Evaluating and Expressing the Uncertainty of Measurement Results: Type A and Type B evaluations, combined standard uncertainty, covariance-aware propagation, and expanded uncertainty. |
| **JCGM 101:2008** | BIPM / Joint Committee for Guides in Metrology | GUM Supplement 1: Propagation of probability distributions through mathematical models using Monte Carlo methods. |

> [!IMPORTANT]
> **Legal and Technical Disclaimer:**  
> This digital engineering laboratory is an **independent, public-data educational reconstruction**. It is not SpaceX internal flight software, not live proprietary telemetry, not NASA-certified software, and not an FAA flight-certified model. NASA and NIST documents are utilized strictly as **methodological engineering references**, not as an assertion of official compliance or certification.

---

## 2. Core Methodological Invariants

### 2.1 Verification vs. Validation
- **Software Verification:** Confirms that the code implements the chosen mathematical equations correctly ("Did we build the software right?"). Measured by unit tests, boundary tests, schema checks, and code coverage.
- **Numerical Verification:** Quantifies numerical error arising from discretization, integration step sizes, tolerances, and roundoff ("Is the numerical solver converging to the analytical solution?"). Measured by step refinement studies and conservation drift.
- **Validation:** Assesses whether the model matches physical reality within a specified intended domain ("Did we build the right model?"). Measured by comparing simulation predictions against independent benchmarks or physical evidence.

### 2.2 Calibration vs. Independent Validation
Tuning empirical coefficients (e.g., drag coefficient $C_D$, engine specific impulse $I_{sp}$, or convective heating constant $k_{SG}$) to force agreement with observed data is **calibration**. The calibrated model cannot then be compared against the same data to claim "independent validation." An independent validation must test the model against independent reference fixtures (such as NASA GMAT for astrodynamics or Roark's formulas for structural shell stress).

### 2.3 The Validation Domain Concept
A model is never universally valid. Its validity is strictly bounded by the parameter ranges, flight regimes, and assumptions under which it was verified:
- **Phase 3 Ascent:** Valid for 3-DOF point-mass ascent through 1976 US Standard Atmosphere up to orbital insertion. Invalid for 6-DOF aerodynamic cross-coupling or aeroelastic flutter.
- **Phase 5 Orbit:** Valid for unperturbed Keplerian two-body motion and secular $J_2$ Earth oblateness nodal precession. Invalid for non-spherical tesseral harmonics ($J_{2,2}$), atmospheric drag below $150\,\text{km}$, or solar radiation pressure over multi-week timescales.
- **Phase 6 Reentry:** Valid for hypersonic blunt-body aerothermodynamics ($M > 5$, $\alpha \approx 40^\circ$) and terminal subsonic deceleration. Invalid for complex supersonic shock-shock interactions or boundary layer transition turbulence.
- **Phase 8 FEA:** Valid for linear elastic thin-walled cylindrical pressure vessel membrane stress. Invalid for plastic post-buckling or cryogenic weld fatigue.
- **Phase 9 TPS:** Valid for 1D through-thickness transient thermal conduction under non-ablative conditions. Invalid for 3D aerothermal tile gap plasma flow or tile spallation.

---

## 3. Flight 14 Primary Public Reference Set

The public baseline is drawn strictly from contemporaneous primary sources and accredited reporting:

1. **SpaceX Flight 14 Preflight Mission Page:**  
   URL: `https://www.spacex.com/launches/starship-flight-14`  
   *Scope:* Planned nominal timeline, ~275 km circular parking orbit, ~10-hour duration, 6 orbits, 26 Starlink V3 payload satellites, Pacific deorbit disposal.
2. **SpaceX Official Mission Updates Archive:**  
   URL: `https://new.spacex.com/updates`  
   *Scope:* Corporate confirmation of upper-stage engine anomaly, satellite deployment success, and ocean splashdown.
3. **Space.com Contemporaneous Live Chronology (28 Sep 2026):**  
   URL: `https://www.space.com/news/live/spacex-starship-flight-14-live-updates-sept-28-2026-starship-first-orbital-launch-attempt`  
   *Scope:* Real-time live blog reporting liftoff at 8:49 a.m. EDT, hot-staging at ~2m 34s, engine shutdown anomaly on upper stage, Starlink deployment start at ~T+34m, deployment duration ~30m, decision for early return, Pacific splashdown at ~3h 09m.
4. **Associated Press (AP) Flight 14 Report:**  
   URL: `https://apnews.com/article/spacex-starship-orbit-262d3c58d56bf7a525b49115d6c5dfe8`  
   *Scope:* Corroborates 26 Starlink V3 deployments (3 equipped with cameras to inspect thermal tiles), shortened ~3h flight, Northern Pacific splashdown north of Hawaii, post-splashdown tip-over and fire.
5. **Reuters Flight 14 Wire Report:**  
   URL: `https://www.reuters.com/business/media-telecom/spacexs-starship-launches-14th-flight-first-headed-orbit-2026-09-28/`  
   *Scope:* Independent corroboration of orbital insertion, premature engine shutdown, early reentry command, and offshore water splashdown for both Super Heavy (Gulf of Mexico) and Starship (Northern Pacific).

---

## 4. Distinct Mission Profile Identifiers

To prevent data contamination, all data points, state vectors, and event records in the lab are tagged with one of four strictly segregated profile IDs:

1. `flight14_planned_public_reference`:  
   Preflight design baseline. 6 orbits, ~275 km circular orbit, ~10 hours, 26 Starlinks deployed, controlled deorbit west of Chile.
2. `flight14_observed_public_reconstruction`:  
   Postflight historical reconstruction. Liftoff, hot-staging, upper-stage engine anomaly, orbit insertion, 26 Starlinks deployed, early return command, reentry, and Northern Pacific splashdown at $T+3\,\text{h}\,09\,\text{m}$ (expended).
3. `synthetic_integrated_test`:  
   Full-stack numerical verification pipeline testing mathematical couplings and software interfaces across Phases 3–9.
4. `synthetic_phase7_reusable_landing`:  
   Isolated experimental simulation of terminal flip maneuver, 3-to-1 engine throttle, and vertical touchdown. Permanently isolated with synthetic warning banner.
