# Phase 4 Verification Plan: 20-Point Multi-Body Staging Suite

**Document ID:** `DOC-P4-VER-001`  
**Classification:** Verification Plan & Acceptance Criteria  
**Revision:** 1.0  
**Lead:** Independent Verification Lead & Quality Architect  

---

## 1. Verification Philosophy

Verification of Phase 4 requires proving five distinct dimensions of engineering validity:
1. **Software Sanity:** Zero syntax errors, deterministic execution, correct exception handling.
2. **Numerical Verification:** Discretization convergence, momentum conservation, zero numerical jumps.
3. **Multi-Body Dynamics:** Exact mass accounting ($m_{\text{stack}} = m_1 + m_2$), independent force integration.
4. **Independent Tool Cross-Check:** Agreement with NASA GMAT R2026a for orbital insertion elements.
5. **Observational Validation:** Consistency with public Flight 14 observations (Reuters, SpaceX preflight, FCC).

---

## 2. 20-Point Acceptance Test Matrix

| Test ID | Test Category | Target Property / Invariant | Method / Benchmark | Tolerance / Acceptance Criterion |
| :--- | :--- | :--- | :--- | :--- |
| **TEST-P4-01** | Synthetic Baseline | Two bodies propagate from shared state | Analytical ballistic motion | $\Delta r < 10^{-6}\,\text{m}$ |
| **TEST-P4-02** | Zero Impulse Limit | $J = 0 \implies \mathbf{v}_{\text{rel}}(0^+) = \mathbf{0}$ | Kinematic split test | $\|\mathbf{v}_{\text{rel}}(0^+)\| \equiv 0.0$ |
| **TEST-P4-03** | Momentum Conservation| Internal impulse $\mathbf{J}$ yields equal & opp momentum | $\Delta(m_1 \mathbf{v}_1 + m_2 \mathbf{v}_2) = \mathbf{0}$ | Relative error $< 10^{-12}$ |
| **TEST-P4-04** | Mass Accounting | $m_{\text{stack}}(T^-) = m_{\text{booster}}(T^+) + m_{\text{ship}}(T^+)$ | Algebraic ledger balance | $|m_{\text{stack}} - (m_1 + m_2)| < 10^{-6}\,\text{kg}$ |
| **TEST-P4-05** | State Continuity | No unmodeled coordinate jumps across split | Position vector difference | $\|\mathbf{r}(T^+) - \mathbf{r}(T^-)\| = 0.0$ |
| **TEST-P4-06** | Event Idempotence | Separation fires exactly once | Event flag transition counter | `execution_count == 1` |
| **TEST-P4-07** | Shared Frame Arithmetic| Both bodies share identical ECI J2000 frame | Frame identifier inspection | `frame_booster == frame_ship == 'ECI_J2000'` |
| **TEST-P4-08** | Coordinate Round-Trip | ECI $\to$ ECEF $\to$ Geodetic $\to$ ECI | Bowring closed-form algorithm | Position round-trip error $< 1\,\text{mm}$ |
| **TEST-P4-09** | Independent Forces | Post-split engines operate on separate schedules | Thrust log inspection | Booster throttle cuts; Ship ignites 6 engines |
| **TEST-P4-10** | Free-Fall Limiting Case | No thrust & no drag $\implies$ Keplerian two-body | Vis-viva energy conservation | Specific orbital energy constant to $10^{-8}$ |
| **TEST-P4-11** | Monotonic Separation | Under positive forward thrust, range increases | Derivative of `center_range_m` | $d(\text{range})/dt > 0$ for $t \in [142, 160]\,\text{s}$ |
| **TEST-P4-12** | Time-Step Convergence| Compare $h = 0.05\,\text{s}$ vs $h = 0.01\,\text{s}$ | Richardson extrapolation | Relative range error $< 0.01\%$ |
| **TEST-P4-13** | Interpolation Safety | No extrapolation outside valid time span | Grid boundary validation | No NaN or inf outside $[140, 522.35]\,\text{s}$ |
| **TEST-P4-14** | SI Output Integrity | All units in meters, kg, seconds, Newtons | Schema validation | Numeric values finite and within physical bounds |
| **TEST-P4-15** | Terminology Compliance| Center range labeled as `center_range_m` | Column name audit | `min_surface_clearance_m` is null / uncomputed |
| **TEST-P4-16** | Provenance Completeness| Every parameter tagged with status & source ID | Configuration dictionary audit | Zero untagged parameters |
| **TEST-P4-17** | Scenario Isolation | Distinct files for reconstruction vs planned | Scenario ID tag check | `scenario_id` uniquely identifies dataset |
| **TEST-P4-18** | GMAT Orbital Check | Match SECO state in NASA GMAT R2026a | GmatConsole execution | Apogee/Perigee match within $< 0.1\%$ |
| **TEST-P4-19** | Phase 1-3 Regression | All 46 existing tests continue to pass | `python -m unittest discover tests` | 46/46 PASS |
| **TEST-P4-20** | Full Reproducibility | Deterministic replay from git commit | End-to-end rerun | Bitwise identical CSV checksums |
