# Phase 4 Dependency Map & Data Pipeline Flow

**Document ID:** `DOC-P4-DEP-001`  
**Classification:** Dependency Mapping & Interface Contract  
**Revision:** 1.0  
**Lead:** Software Integration Architect  

---

## 1. Upstream & Downstream Interfaces

Phase 4 couples upstream aerodynamic, atmospheric, and propulsion models to downstream multi-body relative motion dynamics, orbital propagation, and CAD visualization.

```mermaid
graph LR
    subgraph Data_Inputs ["Configuration & Provenance Inputs"]
        D1["data/propulsion/parameters.yaml"]
        D2["data/config/assumptions.yaml"]
        D3["research/phase4_sources.csv"]
        D4["data/mission/flight14_actual_events.csv"]
    end

    subgraph Core_Physics ["Core Physics Engines"]
        P1["src/environment/atmosphere_1976.py"]
        P2["src/propulsion/raptor3_model.py"]
        P3["src/numerics/rk4_solver.py"]
        P4["src/integration/scipy_solver.py"]
    end

    subgraph Phase3_Ascent ["Ascent Integration"]
        A1["src/dynamics/ascent_3dof.py"]
    end

    subgraph Phase4_Separation ["Phase 4 Separation Pipeline"]
        S1["src/dynamics/staging_separation.py"]
        S2["src/dynamics/booster_recovery.py"]
        S3["src/dynamics/starship_ascent_to_orbit.py"]
    end

    subgraph Outputs_Consumers ["Verification & Visualization"]
        O1["output/flight14_staging_relative_motion.csv"]
        O2["output/flight14_booster_return.csv"]
        O3["output/flight14_starship_upper_ascent.csv"]
        O4["src/orbit/gmat_starship_orbital_insertion.script"]
        O5["cad/freecad/assemblies/Assembly_Flight14_FullStack.FCStd"]
    end

    D1 & D2 --> P2 & A1
    P1 & P2 & P3 --> A1
    A1 --> S1
    S1 --> S2 & S3
    S2 --> O2
    S3 --> O3
    S2 & S3 --> O1
    O3 --> O4
    O1 --> O5
```

---

## 2. File and Module Dependency Table

| Module / Script | File Path | Direct Dependencies | Consumed By | Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **Atmospheric Model** | `src/environment/atmosphere_1976.py` | Python `math` | `ascent_3dof.py`, `booster_recovery.py` | `test_phase3_propulsion_ascent.py` |
| **Raptor 3 Model** | `src/propulsion/raptor3_model.py` | `atmosphere_1976.py` | `ascent_3dof.py`, `starship_ascent_to_orbit.py` | `test_phase3_propulsion_ascent.py` |
| **RK4 Solver** | `src/numerics/rk4_solver.py` | Python `math` | `ascent_3dof.py`, `booster_recovery.py` | `test_phase3_acceptance.py` |
| **Ascent Core** | `src/dynamics/ascent_3dof.py` | `raptor3_model.py`, `rk4_solver.py` | `staging_separation.py` | `test_phase3_acceptance.py` |
| **Staging Separation**| `src/dynamics/staging_separation.py` | `ascent_3dof.py`, `booster_recovery.py`, `starship_ascent_to_orbit.py` | `src/run_phase4_staging.py` | `test_phase4_staging_recovery.py` |
| **Booster Recovery** | `src/dynamics/booster_recovery.py` | `atmosphere_1976.py`, `rk4_solver.py` | `staging_separation.py` | `test_phase4_staging_recovery.py` |
| **Starship Orbit** | `src/dynamics/starship_ascent_to_orbit.py` | `raptor3_model.py`, `rk4_solver.py` | `staging_separation.py` | `test_phase4_staging_recovery.py` |
| **GMAT Orbit Script**| `src/orbit/gmat_starship_orbital_insertion.script`| `flight14_starship_upper_ascent.csv` | NASA GMAT Console R2026a | GMAT execution test |
