# Phase 10: Digital Engineering Spatial Dashboard — Known Limitations

**Document Version:** 2.0.0  
**Project:** Starship Flight 14 Digital Engineering Lab  
**Date:** 2026-10-25  

---

## 1. Scope & Disclaimer

This project is an independent educational engineering reconstruction and digital simulation based exclusively on publicly available data, standard aerospace physics, NASA standards, and peer-reviewed literature. It is not affiliated with, endorsed by, or produced using internal proprietary software, live telemetry feeds, or classified models from Space Exploration Technologies Corp. (SpaceX) or NASA.

---

## 2. Documented Engineering Limitations

1. **Synthetic Reusable Landing Isolation:**
   - Starship Flight 14 was an orbital test mission with an upper stage ocean disposal in the Pacific Ocean (~330 km off Hawaii) at an impact velocity of $\approx 209.74\text{ m/s}$.
   - The vertical landing burn, flip maneuver, and catch simulation provided in the "SYNTHETIC LANDING LAB" profile is strictly an isolated synthetic test from Phase 7. It is not historical Flight 14 telemetry and is clearly designated with a permanent amber warning banner.

2. **Speed of Sound in Vacuum:**
   - Above $h = 100\text{ km}$ (the Kármán line), atmospheric density drops toward vacuum ($\rho \approx 0$). In this regime, acoustic wave propagation ceases and Mach number ceases to be physically meaningful. The dashboard identifies this state as `N/A (Orbital Vacuum)`.

3. **Subsampled Visual Playback Mesh:**
   - To maintain 60 FPS performance on standard laptop GPUs and avoid memory crashes, raw solver CSV outputs (often containing 50,000+ RK4 time steps) are subsampled to $\sim 1,000$ keyframes for WebGL trajectory ribbon and timeline playback. Full-resolution data remains accessible in the Data Inspector and raw solver CSVs.

4. **Earth Atmospheric Shader Model:**
   - The Earth atmosphere is rendered using a single-scattering Fresnel approximation suitable for real-time WebGL rather than full volumetric non-linear radiative transfer. While visually realistic from orbit, it is an engineering visualization approximation.

5. **Local Browser CORS Policy:**
   - When opened directly via `file:///` protocol in certain browsers, standard `fetch()` API calls are restricted by browser security policies. The dashboard automatically falls back to `window.EMBEDDED_SCENARIO_DATA` provided via `<script src="data/scenario_data_embedded.js">` ensuring complete offline functionality without requiring an external web server.
