# Starship Flight 14 Digital Engineering Project
## Architecture Decision Log (ADR)

**Document ID:** `DOC-ADR-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-24`  
**Author:** Senior Aerospace Systems Engineering Lead & Simulation Architect  
**Classification:** Engineering Decisions Baseline  

---

### ADR-001: Separation of Planned Profile from Observed Flight 14 Reconstruction

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  SpaceX's official Flight 14 pre-flight materials projected a ~10-hour orbital mission with a planned deorbit burn occurring many revolutions after launch. However, contemporaneous post-flight reporting (Reuters, Spaceflight Now) confirmed that an upper-stage single Raptor shutdown prompted mission controllers to execute an early deorbit, shortening the mission to approximately 3 hours and 8 minutes, terminating in a Pacific Ocean splashdown. Mixing these timelines produces unphysical telemetry.
- **Decision:**
  Enforce two completely separate, version-controlled mission data files: `data/mission/flight14_planned_events.csv` (10h plan) and `data/mission/flight14_actual_events.csv` (3h flown reconstruction). The simulator and UI must never mix planned and actual timestamps.
- **Consequences:**
  Eliminates timeline confusion; allows side-by-side discrepancy analysis; guarantees 100% adherence to physical evidence.

---

### ADR-002: Dual-Track Dynamics Framework (MATLAB Baseline + Self-Contained Python RK4 Core)

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  The system possesses MathWorks MATLAB R2026a Update 5 on PATH with existing flight dynamics classes in `StarshipV3_GNC_Simulation`. However, the Python scientific environment (`pythoncore-3.14-64`) currently lacks `scipy.integrate.solve_ivp`.
- **Decision:**
  Implement a dual-track dynamics approach:
  1. *Track 1 (Python Core):* Build a self-contained, lightweight Runge-Kutta 4th-order (RK4) numerical integrator (`src/numerics/rk4_solver.py`) using NumPy (which is verified installed). This ensures pure Python execution without third-party solver dependencies.
  2. *Track 2 (MATLAB Baseline):* Retain and refactor the existing MATLAB OOP classes (`MasterAscentSimulator.m`, `GuidanceComputer.m`) as an independent cross-check, fixing the line 140 `rho` scoping bug and removing the fictional "Antigravity Module".
- **Consequences:**
  Zero external blocker on Python dynamics; cross-verification between Python RK4 and MATLAB RK4 guarantees numerical fidelity.

---

### ADR-003: NASA GMAT R2026a via Official `gmatpy` Python 3.14 API

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  NASA GMAT R2026a is installed at `E:\NASA\GMAT-R2026a\`. Live inspection revealed that GMAT includes pre-compiled C-extensions for Python 3.14 (`bin/gmatpy/_py314`). A live smoke test proved that `import gmatpy` works cleanly.
- **Decision:**
  Use the official `gmatpy` Python bindings as the primary interface for orbital propagation, perturbation modeling, and independent cross-verification against Python 2-body/J2 propagators.
- **Consequences:**
  Seamless in-memory Python-to-GMAT data exchange without brittle file parsing or GUI dependencies; enables high-precision orbital benchmarking.

---

### ADR-004: Parametric CAD Strategy via Autodesk Fusion Python API & Neutral STEP Exports

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  Autodesk Fusion is the user's preferred CAD tool. Script directories exist at `%APPDATA%\Autodesk Fusion 360\API\Scripts\`. However, downstream solvers (OpenFOAM, ANSYS) require neutral geometry formats (STEP / STL).
- **Decision:**
  Author native Fusion Python scripts utilizing the `.manifest` + `.py` architecture to generate fully parametric, feature-tree-driven geometry. The script will automatically trigger an export of neutral STEP files (`starship_flight14_fullstack.step`, `booster.step`, `ship.step`) into `cad/exports/`.
- **Consequences:**
  Maintains an editable parametric CAD tree in Fusion while decoupling meshing and CFD/FEA solvers from proprietary Autodesk file locks.

---

### ADR-005: Fluid Dynamics Solver Selection (OpenFOAM WSL Primary + ANSYS Fluent Benchmark)

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  OpenFOAM v2012 is installed and running inside WSL Ubuntu with helper command scripts in `E:\OpenFOAM_Windows_Commands\`. ANSYS Fluent 2026 R1 Student is installed on Windows with a 512,000-cell limit. The physical machine has 7.92 GB RAM.
- **Decision:**
  Use OpenFOAM v2012 (via WSL) as the primary open-source CFD engine for compressible supersonic external aerodynamics. Use ANSYS Fluent Student strictly for low-cell ($< 350,000$ cells) 2D axisymmetric benchmark cases. Full 3D moving-body Navier-Stokes simulations of hot-staging (which required 500 million cells on NASA supercomputers) are strictly out of scope for desktop execution and will be represented via documented empirical drag polars.
- **Consequences:**
  Prevents OOM crashes; respects ANSYS Student licensing caps; delivers defensible desktop aerodynamics.

---

### ADR-006: Structural FEA Solver Selection via ANSYS Mechanical APDL (MAPDL)

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  ANSYS Mechanical APDL (`ANSYS.exe`, `MAPDL.exe`) is installed in `E:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\`. CalculiX is missing. Fusion cloud simulation requires unverified subscription tokens.
- **Decision:**
  Select ANSYS Mechanical APDL (v261) as the primary structural solver. FEA scripts will be authored as parametric APDL macro decks (`.mac`), focusing on thin-walled propellant tank hoop stress and axial launch acceleration benchmarks ($< 400,000$ nodes).
- **Consequences:**
  Scriptable, reproducible structural analysis without requiring interactive GUI clicks; results can be validated against classical Roark formulas.

---

### ADR-007: WebGL Three.js Frontend Reusing Existing Spatial Workstation Architecture

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  `project_08_elon_inspiration` contains an advanced, high-contrast, production-ready Three.js WebGL rendering pipeline, custom shaders, and UI architecture.
- **Decision:**
  Reuse the Three.js rendering pipeline, lighting rigs, and UI card components from `project_08_elon_inspiration` for the Starship Flight 14 Mission Dashboard. Strictly decouple rendering loops from physics equations; the dashboard will consume static trajectory CSVs output by the solvers.
- **Consequences:**
  Avoids redundant web development; ensures immediate 60 FPS performance; guarantees that displayed telemetry is 100% grounded in solver outputs.

---

### ADR-008: Management of Missing Python Packages (`scipy`, `pytest`, `matplotlib`)

- **Status:** **APPROVED & ENFORCED**
- **Context:**
  Python 3.14.5 currently lacks `scipy`, `pytest`, and `matplotlib`. Modifying environment packages without user authorization is restricted during read-only audit.
- **Decision:**
  Design Phase 1–3 code to operate autonomously using Python's standard library (`unittest`, `csv`, `math`) and NumPy. Implement an in-house Runge-Kutta 4th-order integrator. Recommend user run `pip install scipy pytest matplotlib` when convenient.
- **Consequences:**
  Project remains 100% executable and verifiable immediately without being blocked by package installation delays.
