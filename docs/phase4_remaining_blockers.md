# Phase 4 Remaining Blockers & Technical Risk Register

**Document ID:** `DOC-P4-BLK-001`  
**Classification:** Risk Assessment & Blocker Register  
**Revision:** 1.0  
**Lead:** Systems Engineering Lead & Risk Manager  

---

## 1. Blocker Status Assessment

Prior to this audit cycle, several critical blockers prevented technical defense of Phase 4:
1. **Contradictory Mass Ledger:** *RESOLVED.* Reconciled to exactly 4,939.8 t liftoff mass ($1,338.975\,\text{t}$ Ship + $3,600.825\,\text{t}$ Booster).
2. **Ambiguous Engine Anomaly Timestamps:** *RESOLVED.* Decoupled into 3 distinct scenarios (`flight14_public_reconstruction`, `planned_mission_reference`, `hypothetical_engine_out`).
3. **Unexecuted NASA GMAT Script:** *RESOLVED.* Script defects fixed (ASCII encoding, ReportFile elements, SECO state); GMAT R2026a executed successfully in 0.284s, confirming orbital parameters.
4. **Normalized Convergence Scale:** *RESOLVED.* Re-normalized against trajectory scale ($0.0066\%$).
5. **Clearance vs Range Ambiguity:** *RESOLVED.* Strictly defined as `center_range_m` under Level 1 (L1) 3-DOF point-mass dynamics.

---

## 2. Active Technical Risks & Mitigation Strategy

| Risk ID | Risk Description | Severity | Probability | Impact on Simulation | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-P4-01** | Proximity Aerodynamic Interference Uncertainty | Medium | High | Point-mass trajectory neglects localized shock wave interference between stages | Explicitly declare model as Level 1 (L1 3-DOF); do not extrapolate into aerodynamically coupled multi-body regimes without tunnel data. |
| **RSK-P4-02** | Hot-Staging Plume Impingement Force Uncertainty | Medium | High | True transient plume pushback force on forward dome is proprietary | Bound plume force using NASA HECC published pressure integrals ($1.90\,\text{MN} \pm 35\%$); provide selectable `zero_impulse` benchmark mode. |
| **RSK-P4-03** | Lack of Flown Stage 2 Mass Distribution for 6-DOF | High | High | Without exact $I_{xx}, I_{yy}, I_{zz}$ and propellant slosh parameters, 6-DOF attitude dynamics would be ungrounded guesswork | Defer full 6-DOF tumbling/attitude dynamics until Stage 2 structural mass distribution is verified. |
| **RSK-P4-04** | Booster Boostback Guidance Exactness | Low | Medium | Flown boostback pitch steering profile was autonomously adjusted by SpaceX GNC | Calibrate nominal pitch program ($-2.8^\circ$ bias) to match observed Gulf splashdown point ($26.0^\circ\,\text{N}, 96.5^\circ\,\text{W}$) within $5\,\text{km}$. |
| **RSK-P4-05** | FreeCAD Assembly Motion Synchronization | Low | Low | FreeCAD joint simulations drive kinematic offsets rather than flight dynamics | Trajectory state vector from Python must be imported into FreeCAD via explicit coordinate placement scripts, not internal FreeCAD physics. |

---

## 3. Decision Gate Recommendation

All Gate 0, Gate 1, and Gate 2 prerequisites are satisfied:
- Research pack (Sources F4-01 to F4-08) is fully ingested in `research/phase4_sources.csv`.
- Research brief is authored in `docs/research/phase4_source_brief.md`.
- All engineering claims (Problems A through G) are reconciled in `docs/engineering_claims_audit.md`.
- NASA GMAT R2026a has been executed and independently confirmed the orbit insertion state.
- FreeCAD native CAD files, drawings, and 100k SQLite database are verified on disk.
- Complete documentation suite is in place.

**Recommendation:** Proceed with Gate 3–6 implementation (refining `staging_separation.py` API contracts and expanding acceptance tests to the full 20-point suite) upon user confirmation.
