# Starship Flight 14 Digital Engineering Laboratory
## Phase 3 — Dependency Map & Module Integration Graph

**Document ID:** `DOC-P3-DEP-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-25`  
**Author:** Software Integration Architect  

---

### 1. Module Dependency Flow

```mermaid
flowchart TD
    subgraph Data Layer
        P1["data/propulsion/parameters.yaml"]
        M1["data/mission/flight14_actual_events.csv"]
        M2["data/mission/flight14_planned_events.csv"]
    end

    subgraph Environment Module
        A1["src/environment/atmosphere_1976.py"]
        A2["WGS-84 Geodesy: Bowring Algorithm"]
        A3["J2 Earth Gravitational Oblateness"]
    end

    subgraph Propulsion Module
        R1["src/propulsion/raptor3_model.py"]
        R2["Raptor3Engine (SL & VAC)"]
        R3["BoosterCluster33 (Throttling & Anomaly)"]
    end

    subgraph Numerics & Solvers
        N1["src/numerics/rk4_solver.py"]
        N2["src/integration/scipy_solver.py (solve_ivp)"]
    end

    subgraph Flight Dynamics
        D1["src/dynamics/ascent_3dof.py"]
        D2["src/run_phase3_simulation.py"]
    end

    subgraph Outputs & Verification
        O1["output/flight14_ascent_nominal.csv"]
        O2["output/flight14_ascent_anomaly.csv"]
        O3["output/ascent_log.csv"]
        O4["output/flight14_phase3_ascent_plots.png"]
        T1["tests/test_phase3_propulsion_ascent.py"]
        G1["src/orbit/gmat_starship_orbital_insertion.script"]
    end

    P1 --> R1
    M1 --> R3
    A1 --> D1
    A2 --> D1
    A3 --> D1
    R1 --> D1
    N1 --> D1
    N2 --> D1
    D1 --> D2
    D2 --> O1
    D2 --> O2
    D2 --> O3
    O1 --> O4
    D1 --> T1
    O1 --> G1
```

---

### 2. Task Readiness & Blocker Status

| Task ID | Component Name | Prerequisites | Dependency Status | Execution Status |
| :--- | :--- | :--- | :--- | :--- |
| **P3.0** | Prerequisite Audit & Analytical Smoke Test | Python & NumPy | READY | **VERIFIED** |
| **P3.1** | Parameter Registry (`parameters.yaml`) | Public Source Ledger | READY | **VERIFIED** |
| **P3.2** | 1976 Atmosphere & Geodesy Models | WGS-84 & NOAA-76 | READY | **VERIFIED** |
| **P3.3** | Raptor 3 Engine & 33-Cluster Propulsion | Thermodynamic Specs | READY | **VERIFIED** |
| **P3.4** | 3-DOF Numerical Ascent Solver (RK4 & solve_ivp) | State ODE Formulations | READY | **VERIFIED** |
| **P3.5** | Flight 14 Baseline & Anomaly Simulation | Webcast Telemetry | READY | **VERIFIED** |
| **P3.6** | Output Manifests, CSVs & Matplotlib Figures | Telemetry Solvers | READY | **VERIFIED** |
| **P3.7** | GMAT Script Generation & Orbital Cross-Check | SECO State Vector | READY | **VERIFIED** |
| **P3.8** | Verification Test Suite & Acceptance Checks | Unit Test Framework | READY | **VERIFIED** |
