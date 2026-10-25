# Starship Flight 14 Digital Engineering Lab — Audit Decision Log

**Document ID:** `DOC-AUDIT-DECISIONS-001`  
**Audit Lead:** Systems Engineering & Software Verification Lead  
**Baseline Git Commit Target:** Audit & Reconciliation Baseline  

---

## 1. Audit Decisions & Directives

### DEC-001: Strict Discontinuation of Phase Expansion Until Existing Phases Are Reconciled
- **Decision:** Halt all progression to Phase 7 or subsequent phases until all cross-phase state handoffs, mass balances, coordinate conventions, and geographic labels in Phases 1–6 are mathematically consistent and verified against physical evidence.
- **Rationale:** Adding new phases on top of unreconciled assumptions compounds errors and builds software tests that verify code behavior rather than physical flight mechanics.

### DEC-002: Formal Separation of 12 FreeCAD B-Rep Solids vs 100k Relational BOM
- **Decision:** All documentation, reports, and code comments must strictly distinguish the **12 core parametric B-Rep solid geometries** modeled in FreeCAD from the **100,065 component records** indexed in the SQLite relational database (`starship_100k_part_registry.db`).
- **Rationale:** Generating 100,000 distinct solid geometries in a single CAD assembly requires 40–64 GB of RAM and immediately crashes the 8 GB workstation. The 4-level multi-resolution architecture is the correct engineering approach, but it must be described honestly.

### DEC-003: Reclassification of Separation Clearance as Center-of-Mass Displacement
- **Decision:** Reclassify the separation increments ($5.50\,\text{m}$ at $t=1\,\text{s}$ and $48.06\,\text{m}$ at $t=5\,\text{s}$) as **Center-of-Mass relative displacement increments** ($\Delta r_{\text{CM}}(t) = \|\mathbf{r}_{\text{ship}}(t) - \mathbf{r}_{\text{booster}}(t)\| - \|\mathbf{r}_{\text{ship}}(0) - \mathbf{r}_{\text{booster}}(0)\|$), NOT physical surface clearance.
- **Rationale:** In a 3-DOF point-mass model, geometric vehicle dimensions ($71\,\text{m}$ booster, $50\,\text{m}$ ship) are not modeled as bounding collision envelopes. True surface clearance requires 6-DOF geometric envelope detection.

### DEC-004: Correction of Phase 6 Splashdown Geographic Designation to South Atlantic Ocean
- **Decision:** Formally correct all documentation, scenario configs, and telemetry outputs to identify the baseline disposal impact location ($14.0441^\circ\,\text{S}, 15.4063^\circ\,\text{W}$) as the **South Atlantic Ocean Disposal Track**, eliminating the erroneous "Indian Ocean" label.
- **Rationale:** Longitude $15.4063^\circ\,\text{W}$ at latitude $14.0441^\circ\,\text{S}$ is unequivocally in the South Atlantic Ocean (midway between Brazil and southern Africa). The Indian Ocean lies exclusively east of the African continent ($> 30^\circ\,\text{E}$).

### DEC-005: Explicit Identification of Negative Perigee as an Earth-Intersecting Trajectory
- **Decision:** Terminate orbital propagation at the $120.0\,\text{km}$ atmospheric entry interface and document the retrograde deorbit burn as producing an **Earth-intersecting suborbital disposal trajectory** with an osculating perigee of $-81.09\,\text{km}$.
- **Rationale:** An osculating perigee below Earth's surface ($r_p < R_E$) mathematically proves that the Keplerian ellipse intersects the solid Earth datum. It is an intentional suborbital disposal burn, not an elliptical orbit.

### DEC-006: High-Speed Terminal Water Impact vs. Soft Touchdown
- **Decision:** Explicitly classify the $h = 0\,\text{m}$ sea-level termination state ($v_{\text{rel}} \approx 209.7\,\text{m/s}$ / Mach $0.62$) as an **uncontrolled high-speed aerodynamic water impact**.
- **Rationale:** The simulation does not model the subsonic $90^\circ$ pitch-up flip maneuver, header tank propellant slosh settling, or Raptor center-engine landing relight burn. Reaching $h = 0\,\text{m}$ must never be described as a successful landing or recovery.
