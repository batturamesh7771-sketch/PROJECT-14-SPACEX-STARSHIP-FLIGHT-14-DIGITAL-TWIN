# Phase 10: Digital Engineering Spatial Dashboard — Interaction Matrix

**Document Version:** 2.0.0  
**Project:** Starship Flight 14 Digital Engineering Lab  
**Date:** 2026-10-25  

---

## 1. Overview

This matrix exhaustively catalogs every interactive control, button, slider, camera perspective, modal, and dock tab available in the SpaceX-style mission control dashboard.

---

## 2. Interactive Controls Catalog

| Component Category | Element Selector / ID | Action / Input | Expected System Response | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Profile Selection** | `#profile-active-badge` | Click | Toggles profile dropdown menu | Dropdown opens/closes |
| **Profile Selection** | `.profile-dropdown-item[data-profile="observed_reconstruction"]` | Click | Loads Observed Flight 14 Reconstruction; resets trajectory ribbon, timeline, and charts; hides synthetic warning banner | Active badge updates; duration = 11,732s |
| **Profile Selection** | `.profile-dropdown-item[data-profile="planned_flight14"]` | Click | Loads Planned 6-Orbit Nominal Baseline; trajectory spans 36,000s; hides synthetic warning banner | Active badge updates; duration = 36,000s |
| **Profile Selection** | `.profile-dropdown-item[data-profile="synthetic_landing_lab"]` | Click | Loads Phase 7 Reusable Landing simulation; shows permanent prominent amber synthetic warning banner; duration = 30.0s | Amber banner appears; destination = "Starbase Landing Pad (Synthetic)" |
| **Playback Control** | `#btn-play` | Click | Toggles between Play and Pause states; button text switches `PLAY` / `PAUSE` | Animation loop pauses/resumes |
| **Playback Control** | `#btn-reset` | Click | Rewinds simulation clock to $t = 0.0\text{s}$ | Scrubber snaps to left, clocks reset to T+00:00:00 |
| **Playback Control** | `#btn-step-fwd` | Click | Steps forward exactly $+1.0\text{s}$; pauses continuous playback | Clock advances $+1.0\text{s}$, HUD updates |
| **Playback Control** | `#btn-step-back` | Click | Steps backward exactly $-1.0\text{s}$; pauses continuous playback | Clock decrements $-1.0\text{s}$, HUD updates |
| **Playback Control** | `.speed-btn[data-speed]` | Click | Sets playback multiplier: `0.1x`, `0.5x`, `1.0x`, `2.0x`, `5.0x`, `10x` | Speed multiplier takes effect immediately |
| **Playback Control** | `#timeline-scrubber` | Slider Drag / Input | Directly scrubs simulation time $t \in [0, T_{\max}]$ with smooth state interpolation | Real-time vehicle position, HUD telemetry, and chart cursor move in lockstep |
| **Camera Perspectives** | `input[name="camMode"][value="ORBIT_FOLLOW"]` | Radio select | Smoothly interpolates camera to follow vehicle from orbital perspective showing Earth limb | Camera transitions smoothly without jumping |
| **Camera Perspectives** | `input[name="camMode"][value="EARTH_GLOBAL"]` | Radio select | Transitions camera to global planetary view showing complete orbital arc | Camera zooms out to global Earth view |
| **Camera Perspectives** | `input[name="camMode"][value="STAGE_SEP"]` | Radio select | Angles camera toward booster/ship interstage region | Camera positions near staging interface |
| **Camera Perspectives** | `input[name="camMode"][value="ENTRY_BELLY"]` | Radio select | Angles camera to view windward black TPS tile belly during hypersonic reentry | Camera faces vehicle windward heat shield |
| **Camera Perspectives** | `input[name="camMode"][value="FREE_ORBIT"]` | Radio select | Disables automated camera tracking; enables free user orbit/pan/zoom via mouse controls | Left-drag rotates, right-drag pans, scroll zooms |
| **3D Viewport Toggles** | `.vp-btn[data-view]` | Click | Switches viewport focus presets (`EARTH`, `VEHICLE`, `TRAJECTORY`, `ORBIT`, `CUSTOM`) | Viewport state updates |
| **Flight Phases Stepper**| `.flight-phase-item[data-seek]` | Click | Jumps playback time directly to start of clicked phase (e.g., Hot-stage Sep at 170s) | Timeline seeks, phase item highlights as active |
| **Mission Events Table** | `.event-row[data-time]` | Click | Jumps playback time directly to selected event timestamp | Timeline seeks, table row highlights |
| **Channel Inspector** | `.metric-info-icon[data-channel]` | Click | Opens Provenance & Governing Formula modal for that telemetry metric | Modal pops up with title, description, formula, and solver source |
| **Channel Inspector** | `#modal-close-btn` | Click / Backdrop | Dismisses channel provenance modal | Modal disappears |
| **Dock Navigation** | `.dock-tab[data-tab="tab-charts"]` | Click | Displays 6-series synchronized engineering plots; triggers canvas redraw | Charts tab active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-inspector"]`| Click | Displays live state inspector showing exact numeric values and coordinates | Data inspector active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-logs"]` | Click | Displays timestamped mission control console logs | Logs console active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-env"]` | Click | Displays 3D celestial and rendering settings (Earth, atmosphere, clouds, stars) | Environment controls active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-satellites"]`| Click | Displays 26 Starlink V3 manifest with individual deployment statuses | Manifest grid active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-verification"]`| Click | Displays Phase 11 validation cards (NASA GMAT, Roark FEA, Detra-Kemp, Monte Carlo UQ) | Verification cards active |
| **Dock Navigation** | `.dock-tab[data-tab="tab-manifest"]` | Click | Displays full JSON verification run manifest | Manifest preformatted text active |
