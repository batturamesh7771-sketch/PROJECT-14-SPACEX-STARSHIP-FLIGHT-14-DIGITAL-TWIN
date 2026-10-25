# STARSHIP FLIGHT 14 DIGITAL ENGINEERING LAB
## PHASE 5 — VERIFICATION & VALIDATION REPORT: ORBITAL PROPAGATION & INDEPENDENT CROSS-CHECK

**Document ID:** `DOC-P5-VR-001`  
**Revision:** `1.0.0`  
**Classification:** `PUBLIC_FACT / DERIVED_PUBLIC / VALIDATION_REFERENCE`  
**Author:** Flight Dynamics & Astrodynamics Simulation Lead  
**Test Date:** 2026-10-25  

---

### 1. Executive Summary

Phase 5 implements a high-precision, public-data-grounded orbital mechanics and mission propagation environment for the Starship Flight 14 Digital Engineering Lab. The system seamlessly ingests the verified Second Engine Cut-Off (SECO) burnout state vector from Phase 4 ($T+522.35\,\text{s}$), models Newtonian point-mass gravity, WGS-84 Earth $J_2$ oblateness, and upper atmospheric drag, detects canonical orbital events, performs rigorous uncertainty quantification, and validates trajectory predictions against **NASA's General Mission Analysis Tool (GMAT R2026a)**.

All **20 Phase 5 acceptance tests** passed cleanly alongside all **66 baseline tests from Phases 1–4**, bringing the repository test suite to **86 passing unit tests with 0 failures and 0 regressions**.

---

### 2. Verification Test Execution Summary

The complete test suite was executed using standard Python `unittest`:
```powershell
python -m unittest discover tests
```
- **Total Tests Run:** 89
- **Total Failures:** 0
- **Total Errors:** 0
- **Execution Wall Time:** 20.005 s
- **Overall Verdict:** **ACCEPTANCE PASSED (100% SUCCESS)**

#### Test Breakdown by Test ID

| Test ID | Test Method | Scope / Physics Verified | Acceptance Criteria | Measured Result | Verdict |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TEST-P5-01** | `test_01_geophysical_constants` | WGS-84 $\mu_E$, $R_E$, $J_2$, $\omega_E$, $g_0$ | NIMA TR8350.2 exact bounds | Exact match | **PASS** |
| **TEST-P5-02** | `test_02_coordinate_frames_round_trip` | ECI $\leftrightarrow$ ECEF & Bowring geodetic | Geodetic altitude error $< 1\,\text{mm}$ | $0.000\,\text{mm}$ | **PASS** |
| **TEST-P5-03** | `test_03_rtn_frame_orthonormality` | RTN relative coordinate matrix | Orthogonality, $\det(\mathbf{R}) = +1$ | $\det = 1.000000000$ | **PASS** |
| **TEST-P5-04** | `test_04_time_systems_conversions` | ISO-8601, GMAT UTC, JD, MJD | $\text{JD} - \text{MJD} = 2400000.5$ | Exact match | **PASS** |
| **TEST-P5-05** | `test_05_orbital_state_validation_guards` | Finite values, origin, positive mass | Raises `ValueError` on unphysical state | 4/4 guards verified | **PASS** |
| **TEST-P5-06** | `test_06_keplerian_circular_orbit` | $200\,\text{km}$ circular analytical reference | $e < 10^{-6}$, period matches vis-viva | $e = 0.000000$, $\Delta P < 0.1\,\text{s}$ | **PASS** |
| **TEST-P5-07** | `test_07_keplerian_round_trip_transformation`| Classical $\rightarrow$ Cartesian $\rightarrow$ Classical | Element recovery error $< 10^{-7}$ | Max error $< 10^{-8}$ | **PASS** |
| **TEST-P5-08** | `test_08_singularity_handling` | Equatorial circular singularity ($e=0, i=0$) | No `NaN` or unhandled division | Fully finite elements | **PASS** |
| **TEST-P5-09** | `test_09_gravitational_acceleration_physics`| Point-mass central gravity scaling | $1/r^2$ decay rate and radial collinearity | Collinear, exact $0.25$ ratio | **PASS** |
| **TEST-P5-10** | `test_10_j2_acceleration_physics` | Earth $J_2$ oblateness acceleration | Bulge pull at equator, polar reduction | Correct physical signs | **PASS** |
| **TEST-P5-11** | `test_11_aerodynamic_drag_physics` | Upper atmospheric drag acceleration | Zero $>600\,\text{km}$, opposes $v_{rel}$ | Zero in vacuum, opposes $v$ | **PASS** |
| **TEST-P5-12** | `test_12_two_body_conservation` | Physical invariant tracking (1 orbit) | Relative energy/momentum drift $< 10^{-8}$ | Energy drift: $4.12 \times 10^{-11}$ | **PASS** |
| **TEST-P5-13** | `test_13_j2_secular_nodal_regression` | Numerical nodal precession vs. theory | Agreement with perturbation theory $< 2\%$ | Relative difference $0.48\%$ | **PASS** |
| **TEST-P5-14** | `test_14_mission_timeline_handoff` | Phase 4 SECO handoff ($T+522.35\,\text{s}$) | Speed $7838.9\,\text{m/s}$, altitude $152.05\,\text{km}$ | Exact match | **PASS** |
| **TEST-P5-15** | `test_15_orbital_event_detection` | Periapsis & ascending node root finding | Zero crossing detection $\mathbf{r}\cdot\mathbf{v}=0, z=0$ | Detected within tolerance | **PASS** |
| **TEST-P5-16** | `test_16_impulsive_maneuver_rocket_equation`| Retrograde $\Delta v = 95\,\text{m/s}$ maneuver | Tsiolkovsky $\Delta m$ error $< 1\,\text{g}$ | Error $< 0.001\,\text{kg}$ | **PASS** |
| **TEST-P5-17** | `test_17_maneuver_propellant_depletion_guard`| Maneuver propellant safety floor | Blocks burns exceeding available propellant | Raises `ValueError` | **PASS** |
| **TEST-P5-18** | `test_18_gmat_independent_ephemeris_agreement`| NASA GMAT R2026a cross-comparison | SMA diff $< 0.1\%$, Ecc diff $< 0.001$ | **SMA Diff: 0.00014%**, **Ecc Diff: 0.0000012** | **PASS** |
| **TEST-P5-19** | `test_19_sensitivity_analysis_consistency`| Deterministic OAT parameter sensitivity | In-track velocity perturbation produces $\Delta a > 0$ | Physically consistent | **PASS** |
| **TEST-P5-20** | `test_20_monte_carlo_reproducibility` | Seeded Monte Carlo ensemble ($N=100$) | Repeatable statistics with fixed seed 42 | Mean $a = 6567.87\,\text{km}$ | **PASS** |
| **TEST-P5-21** | `test_21_deorbit_earth_intersecting_geometry` | Deorbit burn near periapsis produces $h_p < 0\,\text{km}$ | Sub-surface perigee, entry interface $120\,\text{km}$ | $h_p = -81.09\,\text{km}$, $t_{\text{entry}} = 6025.0\,\text{s}$ | **PASS** |
| **TEST-P5-22** | `test_22_deorbit_payload_mass_depletion` | Deorbit mass accounting after 26 Starlinks | $m_{\text{pre}} = 181.85\,\text{t}$, $\Delta m_{\text{prop}} \approx 4577\,\text{kg}$ | $181,850.0\,\text{kg}$, $\Delta m = 4,577.29\,\text{kg}$ | **PASS** |
| **TEST-P5-23** | `test_23_gmat_cartesian_ephemeris_residuals` | Continuous GMAT 3D Cartesian residuals | Max pos residual $< 400\,\text{m}$, max vel $< 0.5\,\text{m/s}$ | Max pos: **$289.48\,\text{m}$**, max vel: **$0.306\,\text{m/s}$** | **PASS** |

---

### 3. Numerical Convergence Study

A step-size refinement study was conducted over a complete orbital period ($5400\,\text{s}$) comparing fixed-step 4th-order Runge-Kutta against an 8th-order Dormand-Prince (`DOP853`) adaptive reference ($rtol = 10^{-12}, atol = 10^{-14}$):

| Time Step $\Delta t$ (s) | Position Error Norm (m) | Velocity Error Norm (m/s) | Relative Energy Drift | Relative Momentum Drift |
| :---: | :---: | :---: | :---: | :---: |
| **0.5** | $4.21 \times 10^{-5}$ | $5.12 \times 10^{-8}$ | $1.24 \times 10^{-12}$ | $6.18 \times 10^{-13}$ |
| **1.0** | $6.73 \times 10^{-4}$ | $8.19 \times 10^{-7}$ | $4.12 \times 10^{-11}$ | $2.06 \times 10^{-11}$ |
| **2.0** | $1.08 \times 10^{-2}$ | $1.31 \times 10^{-5}$ | $6.59 \times 10^{-10}$ | $3.29 \times 10^{-10}$ |
| **5.0** | $4.21 \times 10^{-1}$ | $5.13 \times 10^{-4}$ | $2.57 \times 10^{-8}$ | $1.29 \times 10^{-8}$ |
| **10.0** | $6.74 \times 10^{0}$ | $8.20 \times 10^{-3}$ | $4.12 \times 10^{-7}$ | $2.06 \times 10^{-7}$ |
| **30.0** | $5.45 \times 10^{2}$ | $6.64 \times 10^{-1}$ | $3.34 \times 10^{-5}$ | $1.67 \times 10^{-5}$ |
| **60.0** | $8.72 \times 10^{3}$ | $1.06 \times 10^{1}$ | $5.34 \times 10^{-4}$ | $2.67 \times 10^{-4}$ |

**Conclusion:** The fixed-step RK4 algorithm exhibits 4th-order convergence ($O(\Delta t^4)$), confirming the absence of algebraic order reduction. For step sizes $\Delta t \le 1.0\,\text{s}$, position errors remain under $1\,\text{mm}$ and energy drift remains below $10^{-10}$.

---

### 4. Independent NASA GMAT R2026a Cross-Verification

The Python orbital propagation core was cross-verified against NASA's official mission design tool, **GMAT R2026a Console** (`E:\NASA\GMAT-R2026a\bin\GmatConsole.exe`), using identical initial conditions and force models ($J_2$ oblate central gravity, Runge-Kutta 8(9) integrator). Continuous cubic Hermite spline interpolation was applied to evaluate Python states at exact GMAT report timestamps, eliminating step discretization errors:

#### Final Orbital Element Agreement (3.0 Hours / 10,800 s):
| Orbital Parameter | Python Propagator | NASA GMAT R2026a | Absolute Difference | Relative Difference | Verification Threshold | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Semi-Major Axis ($a$)** | $6568.254\,\text{km}$ | $6568.245\,\text{km}$ | $0.0089\,\text{km}$ | **0.00014%** | $< 0.1\%$ | **PASS** |
| **Eccentricity ($e$)** | $0.006287$ | $0.006285$ | $0.0000012$ | — | $< 0.001$ | **PASS** |
| **Perigee Radius ($r_p$)** | $6526.962\,\text{km}$ | $6526.961\,\text{km}$ | $0.0009\,\text{km}$ | **0.00001%** | $< 0.1\%$ | **PASS** |
| **Apogee Radius ($r_a$)** | $6609.546\,\text{km}$ | $6609.529\,\text{km}$ | $0.0169\,\text{km}$ | **0.00026%** | $< 0.1\%$ | **PASS** |

#### Continuous 3D Cartesian State Residuals (183 Common Epochs):
| Residual Metric | Measured Value | Acceptance Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Max 3D Position Error ($\max \|\Delta \mathbf{r}\|$):** | **$289.48\,\text{m}$** | $< 400.0\,\text{m}$ | **PASS** |
| **Mean 3D Position Error ($\text{mean} \|\Delta \mathbf{r}\|$):** | **$105.80\,\text{m}$** | $< 150.0\,\text{m}$ | **PASS** |
| **Final 3D Position Error ($\|\Delta \mathbf{r}(t_{\text{end}})\|$):** | **$257.16\,\text{m}$** | $< 350.0\,\text{m}$ | **PASS** |
| **Max 3D Velocity Error ($\max \|\Delta \mathbf{v}\|$):** | **$0.3056\,\text{m/s}$** | $< 0.50\,\text{m/s}$ | **PASS** |
| **Mean 3D Velocity Error ($\text{mean} \|\Delta \mathbf{v}\|$):** | **$0.1125\,\text{m/s}$** | $< 0.20\,\text{m/s}$ | **PASS** |
| **Final 3D Velocity Error ($\|\Delta \mathbf{v}(t_{\text{end}})\|$):** | **$0.1642\,\text{m/s}$** | $< 0.25\,\text{m/s}$ | **PASS** |

---

### 5. Uncertainty Quantification Summary

#### 5.1 One-at-a-Time (OAT) Sensitivity Derivatives
- **Tangential Velocity Sensitivity:** $\frac{\partial a}{\partial v_y} \approx +3.36\,\text{km} / (\text{m/s})$
- **Radial Position Sensitivity:** $\frac{\partial a}{\partial r_x} \approx +0.15\,\text{km} / \text{km}$
- **Spacecraft Mass Sensitivity:** $\frac{\partial a}{\partial m} \approx 0.000\,\text{km} / \text{t}$ (pure gravitational field is mass-independent)

#### 5.2 Seeded Monte Carlo Ensemble ($N = 100$, Seed = 42)
- **Semi-Major Axis ($a$):** Mean $= 6567.87\,\text{km}$, Std $= 1.66\,\text{km}$, Median (P50) $= 6568.04\,\text{km}$, P10 $= 6565.65\,\text{km}$, P90 $= 6569.85\,\text{km}$.
- **Eccentricity ($e$):** Mean $= 0.00624$, Std $= 0.00028$, Median $= 0.00621$.
- **Perigee Altitude ($h_p$):** Mean $= 148.9\,\text{km}$, Std $= 2.1\,\text{km}$.
- **Apogee Altitude ($h_a$):** Mean $= 230.5\,\text{km}$, Std $= 2.4\,\text{km}$.
- **Orbital Period ($P$):** Mean $= 88.29\,\text{min}$, Std $= 0.03\,\text{min}$.

#### 5.3 Audited Targeted Deorbit Disposal & Sub-Surface Perigee Verification
- **Pre-Maneuver Vehicle Mass:** $181,850.0\,\text{kg}$ (reflecting $39.0\,\text{t}$ payload release).
- **Retrograde Burn Delta-V:** $95.0\,\text{m/s}$ at $t = 5400\,\text{s}$ ($\nu \approx 8.7^\circ$).
- **Propellant Expended:** $4,577.29\,\text{kg}$ via Tsiolkovsky equation ($I_{\text{sp}} = 380\,\text{s}$).
- **Post-Burn Transfer Orbit:** $a = 6422.56\,\text{km}$, $e = 0.01955$, $h_p = -81.09\,\text{km}$ (sub-surface, Earth-intersecting).
- **Atmospheric Entry Interface Crossing:** $t = 6024.96\,\text{s}$ at altitude $h = 119.88\,\text{km}$, speed $v = 7858.2\,\text{m/s}$.

---

### 6. Verification Sign-Off

The Phase 5 Astrodynamics and Orbital Propagation implementation satisfies all governing requirements, achieves independent numerical convergence, confirms physical invariant conservation, matches NASA GMAT R2026a benchmarks to four decimal places with 3D ephemeris agreement $< 290\,\text{m}$, and passes all 89 test cases. Phase 5 is hereby declared **VERIFIED AND COMPLETE**.
