# Phase 10: Digital Engineering Spatial Dashboard — Data Flow Architecture
**Project:** Starship Flight 14 Digital Engineering Lab  
**Phase:** 10  
**Baseline Commit:** `674deac`  
**Standard:** NASA-STD-7009B / JCGM 101:2008  

---

## 1. End-to-End Pipeline Overview

The data flow connects raw engineering solver outputs and public evidence ledgers across Phases 1 through 11 to the interactive WebGL dashboard:

```
[Phase 1: Evidence & Events]  ──> data/phase11/flight14_events.json ──┐
[Phase 2: FreeCAD BOM Specs] ──> data/cad/bom_metadata.json         ──┤
[Phase 3: Ascent 3-DOF RK4]  ──> output/phase3/ascent_trajectory.csv ─┤
[Phase 4: Hot-Staging Kin.]  ──> output/phase4/separation_kin.csv    ─┤
[Phase 5: J2 Orbit Prop.]    ──> output/phase5/orbit_ephemeris.csv   ─┼──> [src/dashboard/adapter.py]
[Phase 6: Reentry 6-DOF]     ──> output/phase6/entry_trajectory.csv  ─┤       (build_scenario_data)
[Phase 7: Synthetic Landing] ──> output/phase7/landing_dynamics.csv  ─┤
[Phase 8: Structural FEA]    ──> output/phase8/solve_summary.json    ─┤
[Phase 9: TPS Thermal 1D]    ──> output/phase9/tps_thermal_trace.csv ─┤
[Phase 11: UQ & Benchmarks]  ──> output/phase11/uq_summary.json      ─┘
                                                │
                                                ▼
                             [Data Bundling & Serialization]
                               ├── data/scenario_data.json (HTTP API)
                               └── data/scenario_data_embedded.js (Offline Fallback)
                                                │
                                                ▼
                               [Frontend Initialization]
                              (src/dashboard/static/index.html)
                                                │
                                                ▼
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
             [TimelineController (Clock)]                 [Channel Registry & Meta]
                          │                                           │
         ┌────────────────┼────────────────┬──────────────────────────┤
         ▼                ▼                ▼                          ▼
[MissionSceneManager] [HudManager] [EngineeringChartsManager] [DataExplorerManager]
  - 3D Starship Pos     - Telemetry Cards   - 6 Sync Canvases         - Virtualized Table
  - Flap Deflections    - TPS Gauges        - Time Scrubber Line      - Milestones Log
  - Plume / Glow        - 26x Starlinks     - Max-Q Annotations       - Run Manifest
  - Orbit Ribbon        - Structural FoS    - Hover Tooltips          - Provenance View
```

---

## 2. Ingestion & Transformation Stages

### Stage 1: Solver Artifact Discovery & Parsing (`src/dashboard/adapter.py`)
- **Ascent State Ingestion:** Reads `output/phase3/ascent_trajectory.csv` ($t \in [0, 162]\,\text{s}$), extracting altitude ($h$), velocity ($v$), dynamic pressure ($q$), acceleration ($g$), and thrust.
- **Orbital Coast Ingestion:** Reads `output/phase5/orbit_ephemeris.csv` ($t \in [522.35, 5400]\,\text{s}$), transforming ECI Cartesian coordinates $[x, y, z]$ into geodetic latitude, longitude, and scene-space Cartesian coordinates.
- **Atmospheric Entry Ingestion:** Reads `output/phase6/entry_trajectory.csv` ($t \in [5400, 11364]\,\text{s}$), extracting Mach number, pitch angle, flap deflections, stagnation heat flux, and surface/bondline temperatures.
- **Synthetic Landing Isolation:** Ingests `output/phase7/landing_dynamics.csv` exclusively into `synthetic_landing_lab` profile; strictly isolated from `planned_flight14` and `observed_reconstruction`.

### Stage 2: Time Harmonization & Scene Projection
- Converts all spatial vectors into normalized Three.js rendering coordinates:
  $$r_{\text{scene}} = R_E + \frac{h_{\text{km}}}{1000}$$
  where $R_E = 6.378137$ units ($1\,\text{unit} = 1000\,\text{km}$).
- Subsamples high-frequency solver data (100 Hz $\to$ 1 Hz) for fluid 60 FPS animation while preserving peak extremum points (Max-Q, MECO, SECO, Peak Flux).

### Stage 3: Master Clock & Synchronization (`src/dashboard/static/js/timeline.js`)
- Single authoritative clock running via `requestAnimationFrame(loop)`.
- Binary-search state interpolation (`interpolateState(targetTime)`) provides smooth state estimation between discrete solver sample points.
- Dispatches state updates atomically to `sceneManager`, `hudManager`, and `chartsManager`.

### Stage 4: Profile Switching Semantics
When switching between `PLANNED FLIGHT 14`, `OBSERVED RECONSTRUCTION`, and `SYNTHETIC LANDING LAB`:
- Trajectory ribbons are re-meshed and uploaded to the GPU.
- Chart time domains and series buffers are swapped.
- Timeline milestones are regenerated.
- Satellite dispenser states are reset.
- Synthetic warning banners are toggled on/off.
