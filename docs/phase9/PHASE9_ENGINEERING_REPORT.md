# Phase 9: Aerothermal Reentry & Thermal Protection System (TPS) — Engineering Report

**Project:** Starship Flight 14 Digital Engineering Lab  
**Phase:** 9 (Aerothermal Reentry & Thermal Protection System Model)  
**Date:** October 2026  
**Status:** **PASSED & VERIFIED (15/15 Phase 9 Tests, 173/173 Total Suite Tests)**

---

## 1. Executive Summary

Phase 9 establishes the aerothermal environment and thermal protection system (TPS) analysis for Starship Flight 14 during its hypersonic descent through the atmosphere to its modeled Pacific landing zone.

The model couples actual 3-DOF entry trajectory states from Phase 6 ($933\,\text{s}$ descent from $120.2\,\text{km}$ altitude at Mach 17.8) with classical convective heat flux correlations and a 1D transient finite-difference conduction solver through the composite tile-SIP-steel wall.

Key engineering findings:
1. **Hypersonic Heating Interface:** Peak stagnation heat flux reaches **$0.794\,\text{MW/m}^2$** ($794\,\text{kW/m}^2$) at $t = 318.0\,\text{s}$ at an altitude of **$64.2\,\text{km}$** and relative velocity of $6.82\,\text{km/s}$ (Mach ~22).
2. **Windward Acreage Heating:** At $\alpha = 40.0^\circ$ pitch angle, the peak belly heat flux is **$0.157\,\text{MW/m}^2$** ($157\,\text{kW/m}^2$), driving a peak outer tile surface temperature of **$1330.7\,\text{K}$** ($1057.6^\circ\text{C}$).
3. **Physical Heat Soak Diffusion Delay:** Owing to the extremely low thermal diffusivity of porous silica ($\alpha \approx 3.2 \times 10^{-7}\,\text{m}^2/\text{s}$), the peak temperature at the RTV silicone adhesive bondline is delayed by **$313.4\,\text{seconds}$** (~5.2 minutes) relative to peak surface heating, occurring at $t = 631.4\,\text{s}$ when the vehicle has already slowed to subsonic speeds at lower altitudes.
4. **Thermal Protection Margin:** For the nominal $28.0\,\text{mm}$ tile thickness, the peak RTV bondline temperature reaches **$377.1\,\text{K}$** ($104.0^\circ\text{C}$), providing **$156.0\,\text{K}$** of positive thermal margin below the allowable $533.15\,\text{K}$ ($260^\circ\text{C} / 500^\circ\text{F}$) structural adhesive limit.

---

## 2. Quantitative Reentry Aerothermal Heating Summary

| Metric | Stagnation Point ($R_n = 4.5\,\text{m}$) | Windward Belly Acreage ($\alpha = 40^\circ$) |
| :--- | :--- | :--- |
| **Peak Heat Flux** | **$0.794\,\text{MW/m}^2$** | **$0.157\,\text{MW/m}^2$** |
| **Peak Surface Radiative Equilibrium Temp** | $2015.4\,\text{K}$ ($1742.3^\circ\text{C}$) | **$1330.7\,\text{K}$** ($1057.6^\circ\text{C}$) |
| **Epoch of Peak Heating** | T+318.0 s | T+318.0 s |
| **Altitude of Peak Heating** | $64.2\,\text{km}$ | $64.2\,\text{km}$ |
| **Relative Velocity at Peak** | $6820\,\text{m/s}$ | $6820\,\text{m/s}$ |
| **Integrated Total Heat Load** | **$268.4\,\text{MJ/m}^2$** | **$52.9\,\text{MJ/m}^2$** |

---

## 3. Transient Composite TPS Conduction & Heat Soak

The thermal response across the multi-layer stack:

| Stack Layer | Material | Thickness | Initial Temp | Peak Temp | Time of Peak | Thermal Margin |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Outer Surface** | RCG Coated Silica Tile | $28.0\,\text{mm}$ | $293.2\,\text{K}$ | **$1330.7\,\text{K}$** ($1057.6^\circ\text{C}$) | T+318.0 s | $+319.3\,\text{K}$ (vs reusable limit) |
| **RTV Bondline** | Silicone Adhesive / SIP | $2.5\,\text{mm}$ | $293.2\,\text{K}$ | **$377.1\,\text{K}$** ($104.0^\circ\text{C}$) | T+631.4 s | **$+156.0\,\text{K}$** (vs $533.15\,\text{K}$ limit) |
| **Inner Backface** | 304L Stainless Steel Skin | $4.0\,\text{mm}$ | $293.2\,\text{K}$ | **$355.2\,\text{K}$** ($82.1^\circ\text{C}$) | T+720.0 s | $+744.8\,\text{K}$ (vs yield limit) |

---

## 4. Tile Thickness Sizing Trade Study

To investigate TPS weight optimization versus thermal safety margin, tile thickness was parameterized from $15.0\,\text{mm}$ to $40.0\,\text{mm}$:

| Tile Thickness [mm] | Peak Surface Temp [°C] | Peak Bondline Temp [°C] | Bondline Margin [K] | Margin of Safety (MoS) | Sizing Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **15.0** | 1057.6 | 238.4 | **+21.6** | +0.099 | Marginal (Near Limit) |
| **18.0** | 1057.6 | 192.1 | **+67.9** | +0.395 | Acceptable |
| **22.0** | 1057.6 | 148.5 | **+111.5** | +0.870 | Safe |
| **25.0** | 1057.6 | 123.4 | **+136.6** | +1.345 | Robust |
| **28.0 (Nominal)** | 1057.6 | 104.0 | **+156.0** | **+1.860** | **Baseline Optimal** |
| **32.0** | 1057.6 | 84.7 | **+175.3** | +2.701 | Heavy / High Margin |
| **36.0** | 1057.6 | 70.3 | **+189.7** | +3.985 | Heavy / High Margin |
| **40.0** | 1057.6 | 59.8 | **+200.2** | +5.994 | Heavy / High Margin |

> [!NOTE]
> The nominal $28.0\,\text{mm}$ tile thickness provides an optimal balance between mass penalty and thermal buffer, maintaining a margin of safety of $+1.86$ against RTV silicone adhesive degradation.

---

## 5. Atmospheric Density Uncertainty Sensitivity

Evaluating $\pm 20\%$ variations in upper atmospheric density:

| Density Perturbation | Peak Heat Flux [MW/m²] | Total Heat Load [MJ/m²] | Peak Surface Temp [K] | Peak Bondline Temp [K] | Bondline Margin [K] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **-20%** | 0.141 | 47.31 | 1294.6 | 368.5 | **+164.6** |
| **-10%** | 0.149 | 50.19 | 1313.1 | 372.9 | **+160.2** |
| **Nominal (0%)** | 0.157 | 52.92 | 1330.7 | 377.1 | **+156.0** |
| **+10%** | 0.165 | 55.49 | 1347.4 | 381.1 | **+152.0** |
| **+20%** | 0.172 | 57.94 | 1363.3 | 384.9 | **+148.2** |

Even under a $+20\%$ atmospheric density surge, peak bondline temperature reaches only $384.9\,\text{K}$ ($111.8^\circ\text{C}$), preserving a robust $148.2\,\text{K}$ margin of safety.
