# Phase 10: Digital Engineering Spatial Dashboard — Failure & Diagnostic Audit
**Project:** Starship Flight 14 Digital Engineering Lab  
**Phase:** 10 (Repair & Complete Mission Simulation)  
**Baseline Commit:** `674deac`  
**Date:** 2026-10-25  

---

## 1. Executive Summary & Problem Diagnosis

When opening `src/dashboard/static/index.html` directly in a web browser via `file:///C:/Users/user/.../src/dashboard/static/index.html` (as shown in **Screenshot A**), the dashboard appears completely static:
- The central 3D viewport is empty except for a small centered cyan dot.
- All six engineering charts are blank.
- All telemetry readouts display zero or default static placeholders (`0.00 km`, `0.00 km/s`, `0.0 M`, `0.0 kPa`, `1.00 g`).
- The satellite deployment counter is stuck at `0 / 26 DEPLOYED` with an empty satellite list.
- The playback clock is frozen at `T+00:00:00.00`, and the scrubber and playback buttons do not operate.
- Badges falsely proclaim `VERIFIED SOLVER` and `STATUS: SYNCHRONIZED SOLVER ACTIVE`.
- The Mach readout incorrectly shows unit `0.0 M` (Mach is dimensionless).

This audit proves the root causes, affected code paths, and engineering remedies required to transform the static shell into the fully functioning, high-density mission control interface shown in **Screenshot B**.

---

## 2. Root Cause Diagnostic Table

| Symptom from Screenshot A | Proven Root Cause | File / Function / Data Path | Fix Implemented | Regression Test |
| :--- | :--- | :--- | :--- | :--- |
| **Complete script freeze on startup** | Browser CORS / security restriction blocks `fetch("data/scenario_data.json")` when loaded via `file://`. An unhandled exception occurs in `index.html` line 664, causing an immediate `return;` that terminates initialization before any manager is instantiated. | `src/dashboard/static/index.html` (`DOMContentLoaded` event handler, lines 660–666) | 1. Provide `run_dashboard.bat` and `run_dashboard.ps1` HTTP server launchers.<br>2. Provide embedded data fallback (`scenario_data_embedded.js`) loaded via `<script>` tag so offline `file://` execution succeeds automatically.<br>3. Add visual error toast/diagnostics overlay if data fails to load. | `test_01_http_and_fallback_data_loading` |
| **Empty central viewport with cyan dot** | Three.js `MissionSceneManager` was never instantiated due to the `fetch` abort. The visible cyan dot is the CSS pseudo-element `.hud-center-reticle::before` styled with `background: var(--accent-cyan); width: 6px; height: 6px; border-radius: 50%` sitting over an unrendered `<canvas>`. | `src/dashboard/static/css/dashboard.css` (lines 333–356), `src/dashboard/static/js/scene.js` | 1. Ensure `MissionSceneManager` is initialized with valid data.<br>2. Render procedural PBR Earth, atmospheric Fresnel rim, 3,500-star skybox, parametric Starship model with movable flaps, Raptor engines, plume glow, and continuous trajectory ribbon. | `test_02_webgl_canvas_and_scene_hierarchy` |
| **Six blank engineering charts** | `chartsManager.setTrajectory()` was never invoked. Line 42 in `charts.js` (`if (!this.trajectory \|\| this.trajectory.length === 0) return;`) aborts chart rendering when the dataset is empty. | `src/dashboard/static/js/charts.js` (`EngineeringChartsManager.redrawAll`, lines 41–59) | 1. Ingest full solver time series.<br>2. Implement complete canvas drawing with gridlines, axis units, series curves, Max-Q annotations, and a movable time scrubber cursor line. | `test_03_engineering_plots_synchronization` |
| **Mach Number unit displayed as "0.0 M"** | Mach number was given unit `"M"` (meters) in HTML and chart configs instead of being treated as a dimensionless ratio ($M = v / c_s$). | `src/dashboard/static/index.html` (line 99), `src/dashboard/static/js/charts.js` (line 17) | Remove `"M"`; display Mach as dimensionless `Mach 0.0` or `[-]`. | `test_04_channel_metadata_and_unit_accuracy` |
| **Satellite dispenser stuck at 0 / 26** | `scenarioData.satellite_manifest` was never parsed into the DOM because of the startup abort. `TimelineController` was never started to evaluate deployment timestamps ($t \ge t_{\text{deploy}}$). | `src/dashboard/static/index.html` (lines 692–709), `src/dashboard/static/js/hud.js` (`updateSatellites`) | 1. Dynamically generate 26 satellite records with release times ($t = 2880\text{--}3005\,\text{s}$).<br>2. Tie deployment count strictly to simulation clock.<br>3. Render 3D satellite dispenser objects in the payload bay. | `test_05_satellite_deployment_event_binding` |
| **Frozen playback clock and controls** | `TimelineController` was never constructed. Event listeners for Play, Pause, Reset, Step, and Scrubbing were never bound to the clock loop. | `src/dashboard/static/js/timeline.js` (`TimelineController` constructor, lines 13–33) | Construct `TimelineController` reliably with high-resolution clock (`performance.now()`), time-stepping, binary-search state interpolation, and multi-component state broadcast. | `test_06_simulation_clock_and_scrubber_controls` |
| **False status badges ("VERIFIED SOLVER", "SYNCHRONIZED SOLVER")** | Status badges were hardcoded static HTML elements with no connection to actual runtime checks. | `src/dashboard/static/index.html` (lines 67, 193, 243, 340) | Dynamically compute status badges from runtime checks: `DATA ADAPTER: CONNECTED`, `SOLVER: PUBLIC-DATA RECONSTRUCTION`, `WEBGL: ACTIVE`, `TESTS: 205 PASS (100%)`. | `test_07_truthful_runtime_status_badges` |

---

## 3. Data Ingestion Architecture & Provenance Verification

The dashboard must ingest authentic data generated across Phases 1 through 11:
1. **Ascent Phase (Phase 3):** Max-Q ($36.89\,\text{kPa}$ at $t = 68.5\,\text{s}$), MECO ($2172.3\,\text{m/s}$ at $t = 162.0\,\text{s}$), hot-staging at $t = 164.2\,\text{s}$.
2. **Orbital Phase (Phase 5):** SECO cutoff ($7698.6\,\text{m/s}$ at $t = 522.35\,\text{s}$, $h = 200.1\,\text{km}$), 26 Starlink V3 deployments starting at $t = 2880\,\text{s}$.
3. **Deorbit & Reentry (Phase 6 & 9):** Targeted deorbit burn ($\Delta v = 95.0\,\text{m/s}$ at $t = 5400\,\text{s}$), entry interface at $120.2\,\text{km}$, peak stagnation heating ($0.794\,\text{MW/m}^2$, $T_{\text{surf}} = 1330.7\,\text{K}$), terminal subsonic equilibrium ($209.74\,\text{m/s}$) at Pacific ocean splashdown.
4. **Synthetic Reusable Landing (Phase 7):** Isolated simulation of aerodynamic belly-flop, terminal flip, and landing burn; permanently tagged with visual warning banners.
5. **Structural & Verification (Phase 8 & 11):** 304L stainless tank hoop stress ($675.0\,\text{MPa}$), Roark closed-form comparison ($0.0008\%$ error), UQ 95th-percentile bondline margin ($+73.75\,\text{K}$).

---

## 4. Remediation Plan

1. **Launcher & HTTP Server:** Provide `run_dashboard.bat` and `run_dashboard.ps1` that execute `python -m src.dashboard.server --port 8080` and open the default browser to `http://127.0.0.1:8080/`.
2. **Dual Loading Architecture:** Update `adapter.py` to generate both `scenario_data.json` and `scenario_data_embedded.js` (`window.EMBEDDED_SCENARIO_DATA = ...`), ensuring zero failure whether launched via HTTP or directly via `file:///`.
3. **Visual Architecture Alignment:** Redesign the dashboard layout to match **Screenshot B** (SpaceX-style mission control header, left mission overview card and numbered flight phases, central 3D viewport with camera controls and mini-globe, live telemetry panel, right plots, lower vehicle 3D model, flap indicators, mission events table, systems health, and bottom engineering dock).
4. **Verification Test Suite:** Expand `tests/test_phase10_dashboard.py` to formally test the HTTP server, data flow, scene objects, time synchronization, profile switching, and chart cursors.
