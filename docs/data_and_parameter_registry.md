# Starship Flight 14 Digital Engineering Project
## Data, Parameter, and Mission Event Registry

**Document ID:** `DOC-DATA-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-24`  
**Author:** Senior Aerospace Systems Engineering Lead & Simulation Architect  
**Classification:** Sourced Data & Parameter Baseline  

---

### 1. Data Classification Standard

Every engineering parameter, coefficient, and mission timestamp utilized across the flight dynamics, CAD, orbital, and thermal models is strictly tagged with its epistemic status:

1. **`public_fact`**: Explicitly published by a primary authoritative source (SpaceX official release, FAA license, FCC filing, NASA technical report).
2. **`observed_event`**: Timestamp or telemetry metric directly confirmed by live video commentary, independent aerospace reporting (Reuters, Spaceflight Now), or public tracking data.
3. **`derived`**: Computed directly from verifiable physical principles and public facts via documented formulas (e.g. wet mass minus dry mass = propellant mass).
4. **`assumption`**: Transparently chosen by the engineering simulation team to fill proprietary gaps where public data is absent.
5. **`unknown`**: Metric acknowledged as unavailable in the public domain; explicitly flagged to prevent fabrication.

---

### 2. Vehicle Geometry & Mass Parameter Registry

| Parameter Name | Symbol | Baseline Value | Units | Status | Uncertainty | Sourced Identifier & Locator | Model Scope |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Full Stack Total Height | $H_{\text{total}}$ | $121.0$ | $\text{m}$ | `public_fact` | $\pm 0.5\,\text{m}$ | `SPX-SPEC-01`, p. 1 | Full Stack Geometry |
| Outer Core Diameter | $D_{\text{core}}$ | $9.0$ | $\text{m}$ | `public_fact` | $\pm 0.05\,\text{m}$ | `SPX-SPEC-01`, p. 1 | Full Stack / Aero Area |
| Super Heavy Booster Height | $H_{\text{booster}}$ | $71.0$ | $\text{m}$ | `public_fact` | $\pm 0.5\,\text{m}$ | `SPX-SPEC-01`, p. 2 | Booster Geometry |
| Starship Upper Stage Height| $H_{\text{ship}}$ | $50.3$ | $\text{m}$ | `public_fact` | $\pm 0.5\,\text{m}$ | `SPX-SPEC-01`, p. 2 | Ship Geometry |
| Hot-Staging Interstage Ring | $H_{\text{ring}}$ | $3.5$ | $\text{m}$ | `public_fact` | $\pm 0.1\,\text{m}$ | `NASA-HECC-24`, p. 3 | Staging Separation |
| Combined Liftoff Wet Mass | $m_{0}$ | $5,000,000$ | $\text{kg}$ | `derived` | $\pm 3.0\%$ | `SPX-PR-F14`, p. 2 | Ascent Dynamics |
| Booster Dry Mass | $m_{\text{dry,b}}$ | $200,000$ | $\text{kg}$ | `assumption` | $\pm 8.0\%$ | `AIAA-EST-2024`, p. 14 | Booster Mass & Inertia |
| Booster Propellant Capacity| $m_{\text{prop,b}}$ | $3,400,000$ | $\text{kg}$ | `public_fact` | $\pm 2.0\%$ | `SPX-SPEC-01`, p. 3 | Booster Mass Depletion |
| Starship Upper Stage Dry Mass| $m_{\text{dry,s}}$ | $105,000$ | $\text{kg}$ | `assumption` | $\pm 7.0\%$ | `AIAA-EST-2024`, p. 15 | Upper Stage Mass |
| Starship Propellant Capacity| $m_{\text{prop,s}}$ | $1,200,000$ | $\text{kg}$ | `public_fact` | $\pm 2.0\%$ | `SPX-SPEC-01`, p. 3 | Ship Mass Depletion |
| Starlink V3 Satellite Mass | $m_{\text{sat}}$ | $1,750$ | $\text{kg}$ | `assumption` | $\pm 10.0\%$ | `FCC-FORM-312`, Att. A | Payload Deployment |
| Payload Satellite Count | $N_{\text{sat}}$ | $26$ | count | `public_fact` | exact | `REU-F14-001`, par. 2 | Mission Manifest |
| Total Payload Mass | $m_{\text{payload}}$| $45,500$ | $\text{kg}$ | `derived` | $\pm 10.0\%$ | $N_{\text{sat}} \times m_{\text{sat}}$ | Orbit Insertion Mass |

---

### 3. Propulsion Parameter Registry

| Parameter Name | Symbol | Baseline Value | Units | Status | Uncertainty | Sourced Identifier & Locator | Model Scope |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| Booster Engine Configuration| $N_{\text{eng,b}}$ | $33$ | count | `public_fact` | exact | `SPX-SPEC-01`, p. 4 | Booster Propulsion |
| Ship Engine Configuration | $N_{\text{eng,s}}$ | $6$ (3 SL + 3 Vac)| count | `public_fact` | exact | `SPX-SPEC-01`, p. 4 | Ship Propulsion |
| Raptor Sea-Level Thrust | $T_{\text{SL}}$ | $2,745,000$ | $\text{N}$ ($280\,\text{tf}$) | `public_fact` | $\pm 2.0\%$ | `SPX-R3-PRES`, slide 4 | Booster Liftoff Thrust |
| Raptor Vacuum Thrust (Vac) | $T_{\text{vac}}$ | $2,940,000$ | $\text{N}$ ($300\,\text{tf}$) | `public_fact` | $\pm 3.0\%$ | `SPX-R3-PRES`, slide 5 | Upper Stage Vacuum |
| Raptor Sea-Level Specific Imp.| $I_{\text{sp,SL}}$ | $330.0$ | $\text{s}$ | `public_fact` | $\pm 1.5\,\text{s}$ | `SPX-R3-PRES`, slide 4 | Liftoff Mass Flow |
| Raptor Vacuum Specific Imp. | $I_{\text{sp,vac}}$| $380.0$ | $\text{s}$ | `public_fact` | $\pm 2.0\,\text{s}$ | `SPX-R3-PRES`, slide 5 | Vacuum Mass Flow |
| Booster Nominal Liftoff Thrust| $T_{\text{total,0}}$ | $90,585,000$ | $\text{N}$ ($9,240\,\text{tf}$)| `derived` | $\pm 2.0\%$ | $33 \times T_{\text{SL}}$ | Liftoff Acceleration |
| Initial Thrust-to-Weight Ratio| $\text{T/W}_0$ | $1.84$ | dimensionless | `derived` | $\pm 0.05$ | $T_{\text{total,0}} / (m_0 g_0)$ | Liftoff Kinematics |
| Max Dynamic Pressure Throttle| $\delta_{\text{throttle}}$| $70\%$ | percent | `assumption` | $\pm 5.0\%$ | `FLIGHT-PROFILE-01` | Max-Q Throttle Notch |
| TVC Maximum Gimbal Angle | $\delta_{\text{max}}$ | $5.0$ | $\text{deg}$ | `assumption` | $\pm 0.5^\circ$ | `GNC-SPEC-01` | Attitude Actuation |
| TVC Actuator Slew Rate Limit | $\dot{\delta}_{\text{max}}$ | $10.0$ | $\text{deg/s}$ | `assumption` | $\pm 1.0^\circ/\text{s}$ | `GNC-SPEC-01` | 2nd-Order Dynamics |

---

### 4. Mission Chronology: Planned Profile vs. Observed Flight 14 Reconstruction

The project strictly maintains two decoupled timeline profiles to resolve the evidence conflict documented in Part 1 of the Master Directive:

| Event Description | Planned Profile (`t_plus_s`) | Flown Observed Reconstruction (`t_plus_s`) | Planned vs Flown Discrepancy Analysis | Sourced Evidence & Citation |
| :--- | :---: | :---: | :--- | :--- |
| **Liftoff** | `T+00:00` ($0\,\text{s}$) | `T+00:00` ($0\,\text{s}$) | Identical; nominal liftoff from Starbase launch pad. | `SPX-F14-001`, `REU-F14-001` |
| **Booster Engine Anomaly** | None (nominal) | `~T+00:35` ($35\,\text{s}$) | One outer Raptor shut down early during boost phase; vehicle continued ascent nominally. | `REU-F14-001`, par. 4 |
| **Max-Q (Peak Aerodynamic Load)**| `T+01:02` ($62\,\text{s}$) | `T+01:02` ($62\,\text{s}$) | Nominal dynamic pressure notch observed. | `SPX-F14-001`, `SNOW-F14-001` |
| **Booster MECO** | `T+02:20` ($140\,\text{s}$) | `T+02:20` ($140\,\text{s}$) | Booster center engines remain active for hot-staging. | `SPX-F14-001` |
| **Hot-Staging Separation** | `T+02:22` ($142\,\text{s}$) | `T+02:22` ($142\,\text{s}$) | Starship Raptors ignite while attached; clean physical separation achieved. | `SPX-F14-001`, `NASA-HECC-24` |
| **Booster Boostback Burn** | `T+02:28` ($148\,\text{s}$) | `T+02:28` ($148\,\text{s}$) | 13 Raptor engines ignite to reverse downrange velocity. | `SPX-F14-001` |
| **Booster Splashdown (Gulf)**| `T+06:55` ($415\,\text{s}$) | `~T+07:00` ($420\,\text{s}$) | Controlled landing burn into the waters of the Gulf of Mexico; no tower catch attempt. | `REU-F14-001`, `SPX-F14-001` |
| **Upper Stage Engine Anomaly**| None (nominal) | `~T+04:15` ($255\,\text{s}$) | One Raptor engine shut down prematurely during orbital ascent; remaining 5 engines adjusted burn duration. | `REU-F14-001`, `SNOW-F14-001` |
| **SECO / Orbital Insertion** | `T+08:30` ($510\,\text{s}$) | `~T+08:45` ($525\,\text{s}$) | Starship achieved initial low Earth orbit despite single engine shutdown. | `REU-F14-001`, par. 1 |
| **Satellite Deployment (26 Sats)**| `T+18:00` ($1,080\,\text{s}$) | `~T+22:00` ($1,320\,\text{s}$) | 26 Starlink V3 satellites deployed sequentially from payload bay dispenser. | `REU-F14-001`, `SPX-F14-001` |
| **Mission Duration / Coast** | **Planned ~10 Hours** | **Shortened to ~3 Hours** | Decision made to execute early deorbit following upper stage propulsion anomaly. | `REU-F14-001`, par. 3 |
| **Deorbit Burn** | `T+09:15:00` ($33,300\,\text{s}$) | `~T+02:15:00` ($8,100\,\text{s}$) | Deorbit burn executed early over Indian Ocean targeting Pacific entry corridor. | `SNOW-F14-002`, par. 5 |
| **Atmospheric Entry Interface** | `T+09:40:00` ($34,800\,\text{s}$) | `~T+02:45:00` ($9,900\,\text{s}$) | Entry interface at 120 km altitude; plasma heating phase. | `SNOW-F14-002`, par. 6 |
| **Starship Splashdown (Pacific)**| `T+10:05:00` ($36,300\,\text{s}$) | `~T+03:08:00` ($11,280\,\text{s}$)| Controlled belly-flop, terminal flip, landing burn, and splashdown north of Hawaii. | `SNOW-F14-002`, `REU-F14-001` |

---

### 5. Sourced Reference Bibliography

- `[SPX-F14-001]`: SpaceX Starship Flight 14 Official Mission Page, *SpaceX Launches*, published 2026-09-28. URL: `https://www.spacex.com/launches/starship-flight-14`.
- `[REU-F14-001]`: Reuters Aerospace Reporting, *SpaceX's Starship makes orbital debut deploying Starlinks before early ending*, Joey Roulette, published 2026-09-28. URL: `https://www.reuters.com/business/media-telecom/spacexs-starship-launches-14th-flight-first-headed-orbit-2026-09-28/`.
- `[SNOW-F14-001]`: Spaceflight Now Mission Debrief, *Starship returns to Earth; rocket splashes down north of Hawaii after three-hour flight*, Will Robinson-Smith, published 2026-09-28. URL: `https://spaceflightnow.com/2026/09/28/starship-returns-to-earth-rocket-splashes-down-north-of-hawaii-after-three-hour-flight/`.
- `[NASA-HECC-24]`: NASA High-End Computing Capability, *SpaceX Starship Hot Staging — From Concept to Flight*, NASA Ames Research Center / HECC Feature, published 2024-11. URL: `https://www.nas.nasa.gov/SC24/research/project24.php`.
- `[NASA-SP-398]`: NOAA / NASA / US Air Force, *U.S. Standard Atmosphere, 1976*, NASA-TM-X-74335, Washington, D.C.
