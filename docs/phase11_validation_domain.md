# Phase 11: Validation Domain Specification & Operating Envelopes
**Starship Flight 14 Digital Engineering Lab**  
**Standards Reference:** NASA-STD-7009B Section 5.4, NASA-HDBK-7009B  
**Author:** Lead Independent Verification, Flight-Dynamics Validation & Software-Assurance Engineer

---

## 1. Concept of Validation Domain

Under NASA-STD-7009B, a simulation's validated domain defines the exact multidimensional space of inputs, environmental states, and operating conditions for which empirical or independent benchmark evidence exists.

Predictions made **inside** the validated domain are supported by verification tests and reference comparisons. Predictions made **outside** the validated domain are unverified extrapolations and must trigger explicit `OUT_OF_DOMAIN` flags in software and dashboards.

---

## 2. Subsystem Validation Domains & Operating Limits

### 2.1 Ascent Propulsion & Flight Dynamics (Phase 3 & 4)

| Parameter | Validated Operational Range | Benchmark / Evidence Basis | Out-of-Domain Boundaries |
| :--- | :---: | :--- | :--- |
| **Altitude ($h$)** | $0.0\,\text{m} \le h \le 165,000\,\text{m}$ | 1976 US Standard Atmosphere | $h < 0\,\text{m}$ (sub-surface) or $h > 200\,\text{km}$ (thermosphere breakdown) |
| **Mach Number ($M$)** | $0.0 \le M \le 8.5$ | Semi-empirical $C_D(M)$ wave drag | $M > 10.0$ in dense air ($h < 30\,\text{km}$) — real gas dissociation |
| **Dynamic Pressure ($q$)** | $0.0\,\text{kPa} \le q \le 45.0\,\text{kPa}$ | Max-Q flight corridor ($36.9\,\text{kPa}$) | $q > 60.0\,\text{kPa}$ — structural aeroelastic divergence |
| **Felt Acceleration ($g$)** | $1.0\,\text{g} \le a_{\text{felt}} \le 4.5\,\text{g}$ | Booster & ship throttle schedules | $a_{\text{felt}} > 5.5\,\text{g}$ — structural yield limit exceeded |
| **Clearance Representation** | Center-of-Mass $\Delta r_{\text{CM}}$ only | 3-DOF translational dynamics | True hardware surface clearance (requires 6-DOF geometric mesh collision) |

---

### 2.2 Orbital Astrodynamics (Phase 5)

| Parameter | Validated Operational Range | Benchmark / Evidence Basis | Out-of-Domain Boundaries |
| :--- | :---: | :--- | :--- |
| **Perigee Altitude ($h_p$)** | $140\,\text{km} \le h_p \le 350\,\text{km}$ | NASA GMAT R2026a ($< 0.1\%$ SMA diff) | $h_p < 120\,\text{km}$ (requires aerodynamic entry integration) |
| **Apogee Altitude ($h_a$)** | $200\,\text{km} \le h_a \le 400\,\text{km}$ | NASA GMAT R2026a ($< 0.001$ ecc diff) | $h_a > 1,000\,\text{km}$ (lunar/solar 3rd-body perturbations required) |
| **Orbital Inclination ($i$)** | $25.0^\circ \le i \le 30.0^\circ$ | Starbase launch corridor ($26.3^\circ$) | Polar or retrograde orbits ($i > 80^\circ$) without re-verifying J2 nodal drift |
| **Propagation Horizon** | $t \le 36,000\,\text{s}$ ($\le 6$ orbits) | GMAT ephemeris residual validation | $t > 72\,\text{hours}$ (unmodeled atmospheric drag decay dominates) |

---

### 2.3 Hypersonic Reentry Aerodynamics & Heat Flux (Phase 6 & 9)

| Parameter | Validated Operational Range | Benchmark / Evidence Basis | Out-of-Domain Boundaries |
| :--- | :---: | :--- | :--- |
| **Entry Velocity ($v_{\text{entry}}$)** | $7,000\,\text{m/s} \le v \le 7,850\,\text{m/s}$ | Sutton-Graves & DKR correlations | $v > 8,500\,\text{m/s}$ (super-orbital lunar return — radiative shock heating) |
| **Angle of Attack ($\alpha$)** | $35.0^\circ \le \alpha \le 45.0^\circ$ | High-AOA windward belly-flop trim | $\alpha < 20^\circ$ (stagnation point moves to nosecone ogive, changing $R_n$) |
| **Peak Heat Flux ($\dot{q}$)** | $0.1\,\text{MW/m}^2 \le \dot{q} \le 1.2\,\text{MW/m}^2$ | Sutton-Graves blunt body formula | $\dot{q} > 2.5\,\text{MW/m}^2$ — silica tile surface melting ($> 1950\,\text{K}$) |
| **Tile Thickness ($t_{\text{tile}}$)** | $20\,\text{mm} \le t \le 35\,\text{mm}$ | TDMA 1D conduction trade study | $t < 15\,\text{mm}$ (RTV bondline exceeds $533.15\,\text{K}$ limit) |
| **End of Flight Velocity** | $200\,\text{m/s} \le v \le 220\,\text{m/s}$ | Subsonic aerodynamic terminal equilibrium | Classifying sea-level impact as a soft landing (violates physics) |

---

### 2.4 Structural Tank Section FEA (Phase 8)

| Parameter | Validated Operational Range | Benchmark / Evidence Basis | Out-of-Domain Boundaries |
| :--- | :---: | :--- | :--- |
| **Internal Pressure ($p$)** | $4.0\,\text{bar} \le p \le 8.5\,\text{bar}$ | Roark membrane stress ($0.0008\%$ residual) | $p > 9.5\,\text{bar}$ — plastic yield in 304L stainless steel ($\sigma_y = 950\,\text{MPa}$) |
| **Axial G-Load** | $1.0\,\text{g} \le n_z \le 4.0\,\text{g}$ | Linear elastic S4R shell analysis | Compressive axial load exceeding critical buckling load ($P_{\text{cr}}$) |
| **Material Temperature** | $90\,\text{K} \le T \le 350\,\text{K}$ | Room-temp / cryogenic 304L properties | $T > 600\,\text{K}$ (severe stainless steel yield strength degradation) |

---

## 3. Runtime Guardrail Requirements

1. **Dashboard Warning Flags:** If a user selects an off-nominal parametric condition outside the tables above, the Phase 10 dashboard HUD must display:
   `STATUS: OUT OF VALIDATED DOMAIN — PREDICTION UNVERIFIED`
2. **Synthetic Landing Guard:** The Phase 7 terminal flip and vertical touchdown simulation must permanently retain the disclaimer:
   `SYNTHETIC — NOT FLIGHT 14 HISTORY. Isolated Phase 7 Terminal Landing Dynamics Simulation.`
