# Phase 10: Digital Engineering Spatial Dashboard — Calculation and Source Register

## 1. External Source Registry

| Source ID | Title & Publishing Organization | Reference URL / Document Number | Date / Version | Role in Digital Twin |
| :--- | :--- | :--- | :--- | :--- |
| **SRC-001** | Starship Flight 14 Mission Overview, SpaceX | `https://www.spacex.com/launches/starship-flight-14` | September 2026 | Planned mission profile, nominal orbit ($275\,\text{km}$), 6 orbits, 10h duration |
| **SRC-002** | Reuters: "SpaceX Starship Completes 14th Test Flight" | Reuters Aerospace & Defense Wire | 28 Sept 2026 | Observed outcome: orbit reached, 26 Starlinks deployed, engine issue at ~3h, Pacific splashdown |
| **SRC-003** | FCC Starlink Gen3 Orbital Manifest Filings | FCC SAT-LOA-2026-F14 | August 2026 | 26 Starlink V3 payload units, individual mass ($1750\,\text{kg}$), deployment timeline |
| **SRC-004** | NASA Standard for Models and Simulations | NASA-STD-7009B / NASA-HDBK-7009 | 2024 / 2026 | Verification gates, model credibility assessment, data provenance rules |
| **SRC-005** | Roark's Formulas for Stress and Strain (8th Ed.) | McGraw-Hill, Young, Budynas, Sadegh | Table 13.1 | Thin-walled cylindrical shell membrane stress equations ($\sigma_h, \sigma_l, \sigma_{\text{vm}}$) |
| **SRC-006** | NASA SP-8007: Buckling of Thin Cylinders | NASA Langley Research Center | NASA SP-8007 | Classical shell buckling $\sigma_{\text{cl}}$, knockdown $\gamma = 0.20$, ullage pressure stabilization |
| **SRC-007** | Sutton-Graves Convective Heat Flux Correlation | NASA TR R-376 | 1971 | Stagnation-point hypersonic heating in planetary atmospheres ($q \propto \sqrt{\rho / R_n} v^3$) |
| **SRC-008** | Detra-Kemp-Riddell Hypersonic Heat Transfer | Jet Propulsion / AVCO Research | 1957 | High-velocity stagnation correlation ($v^{3.15}$ power scaling) |

---

## 2. Mathematical Formulations & Derivations

### 2.1 Atmospheric & Flight Dynamics
- **Dynamic Pressure:**
  $$q_\infty = \frac{1}{2} \rho v_{\text{rel}}^2 \quad [\text{Pa}]$$
- **Mach Number:**
  $$M = \frac{v_{\text{rel}}}{a(T)} = \frac{v_{\text{rel}}}{\sqrt{\gamma R_{\text{air}} T}}$$
  Where $\gamma = 1.4$, $R_{\text{air}} = 287.05\,\text{J/(kg}\cdot\text{K)}$.
- **Apparent Specific Force / G-Load:**
  $$n_z = \frac{\|\mathbf{F}_{\text{thrust}} + \mathbf{F}_{\text{aero}}\|}{m \cdot g_0} \quad [g]$$

### 2.2 Aerothermal & TPS Thermal Response
- **Sutton-Graves Stagnation Heat Flux:**
  $$q_{\text{stag}} = C_{\text{sg}} \sqrt{\frac{\rho}{R_n}} v^3 = 1.74153 \times 10^{-4} \sqrt{\frac{\rho}{4.5}} v^3 \quad [\text{W/m}^2]$$
- **Windward Acreage Flux ($\alpha = 40.0^\circ$):**
  $$q_{\text{windward}} = q_{\text{stag}} \cdot (\sin 40^\circ)^{1.6} \cdot 0.40 \approx 0.1974 \cdot q_{\text{stag}}$$
- **Radiative Equilibrium Temperature:**
  $$T_{\text{surf}} = \left( \frac{q_{\text{windward}}}{\varepsilon \sigma} + T_\infty^4 \right)^{1/4} \quad [\text{K}]$$

### 2.3 Structural Membrane Stresses (Roark & FEA)
- **Hoop Stress:**
  $$\sigma_h = \frac{p \cdot r}{t} = \frac{0.60 \times 10^6 \times 4.5}{0.004} = 675.00\,\text{MPa}$$
- **Longitudinal Stress with 3g Launch Compression:**
  $$\sigma_l = \frac{p \cdot r}{2t} - \frac{F_{\text{axial}}}{2\pi r t} = 337.50 - 31.22 = 306.28\,\text{MPa}$$
- **Von Mises Equivalent Stress:**
  $$\sigma_{\text{vm}} = \sqrt{\sigma_h^2 - \sigma_h \sigma_l + \sigma_l^2} = 585.40\,\text{MPa}$$
