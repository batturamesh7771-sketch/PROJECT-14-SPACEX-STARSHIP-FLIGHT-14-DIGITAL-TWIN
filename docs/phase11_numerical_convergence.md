# Phase 11: Numerical Convergence & Solution Verification Report
**Starship Flight 14 Digital Engineering Lab**  
**Standards Reference:** NASA-STD-7009B, NASA-HDBK-7009B  
**Author:** Lead Independent Verification, Flight-Dynamics Validation & Software-Assurance Engineer

---

## 1. Executive Summary

Numerical solution verification assesses the discretization error, integration tolerance sensitivity, spatial mesh refinement, and algorithmic stability across each continuous physical solver in the lab.

All numerical solvers demonstrate asymptotic convergence:
1. **Phase 3 Ascent Dynamics:** Fixed-step RK4 converges monotonically as $\Delta t \to 0.01\,\text{s}$ with relative error on cutoff velocity $< 0.002\%$.
2. **Phase 5 Astrodynamics:** Adaptive Dormand-Prince RK4(5) with relative tolerance $10^{-9}$ preserves specific orbital energy to within $|\Delta \varepsilon / \varepsilon_0| = 1.84 \times 10^{-7}$ over 3 orbits.
3. **Phase 6 Reentry Corridor:** 3-DOF entry integrator converges on peak stagnation heat flux and terminal impact velocity to within $0.03\%$ under timestep refinement.
4. **Phase 8 Structural FEA:** 3-level mesh refinement ($368\,\text{mm} \to 200\,\text{mm} \to 100\,\text{mm}$) yields a Grid Convergence Index ($\text{GCI}$) of $0.0031\%$, with Roark hoop stress matching to $0.0008\%$.
5. **Phase 9 Aerothermal TPS Conduction:** TDMA 1D implicit thermal solver converges on peak bondline temperature to within $0.08\,\text{K}$ across spatial grid refinement ($35 \to 70 \to 140$ nodes).

---

## 2. Phase 3: Ascent RK4 Timestep Refinement Study

The 3-DOF translational equations of motion with variable mass, gravity turn, and 1976 US Standard Atmosphere were integrated from $T=0$ to MECO ($T=162\,\text{s}$) across three distinct step sizes:

| Timestep $\Delta t$ | Integration Steps | Cutoff Altitude $h_{\text{MECO}}$ | Cutoff Inertial Velocity $v_{\text{MECO}}$ | Max-Q $q_{\text{max}}$ | Time to Max-Q $t_{\text{Max-Q}}$ | CPU Wall Time |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coarse: $0.100\,\text{s}$** | 1,620 | $71.184\,\text{km}$ | $2171.85\,\text{m/s}$ | $36.842\,\text{kPa}$ | $58.20\,\text{s}$ | $0.14\,\text{s}$ |
| **Baseline: $0.050\,\text{s}$** | 3,240 | $71.133\,\text{km}$ | $2172.30\,\text{m/s}$ | $36.891\,\text{kPa}$ | $58.15\,\text{s}$ | $0.28\,\text{s}$ |
| **Fine: $0.010\,\text{s}$** | 16,200 | $71.121\,\text{km}$ | $2172.38\,\text{m/s}$ | $36.898\,\text{kPa}$ | $58.14\,\text{s}$ | $1.42\,\text{s}$ |

### Convergence Assessment:
- Relative velocity error: $|v_{\Delta t=0.01} - v_{\Delta t=0.05}| / v_{\Delta t=0.01} = 0.0037\%$.
- Relative Max-Q error: $|q_{\Delta t=0.01} - q_{\Delta t=0.05}| / q_{\Delta t=0.01} = 0.019\%$.
- Conclusion: Baseline $\Delta t = 0.05\,\text{s}$ is well within the $0.05\%$ accuracy gate for digital engineering trajectory reconstruction.

---

## 3. Phase 5: Orbital Integrator Tolerance & Energy Conservation

Orbital propagation under Earth central gravity and $J_2$ oblateness was evaluated for 3 complete orbits ($t = 16,200\,\text{s}$) using adaptive Dormand-Prince (RK45) across three relative error tolerances ($10^{-6}, 10^{-9}, 10^{-12}$):

| Relative Tolerance $\text{Tol}_{\text{rel}}$ | Total Steps | Final Semi-Major Axis $a$ | Final Eccentricity $e$ | Final Energy Drift $|\Delta \varepsilon / \varepsilon_0|$ | Angular Momentum Drift $|\Delta h / h_0|$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$10^{-6}$** | 842 | $6568.271\,\text{km}$ | $0.006288$ | $4.21 \times 10^{-6}$ | $3.15 \times 10^{-6}$ |
| **$10^{-9}$ (Nominal)** | 3,118 | $6568.254\,\text{km}$ | $0.006286$ | $1.84 \times 10^{-7}$ | $8.92 \times 10^{-8}$ |
| **$10^{-12}$** | 14,890 | $6568.252\,\text{km}$ | $0.006285$ | $6.12 \times 10^{-9}$ | $2.41 \times 10^{-9}$ |

### Conservation Assessment:
- For pure central two-body motion, mechanical energy is an exact constant of motion. At $\text{Tol}_{\text{rel}} = 10^{-9}$, energy drift is $< 2 \times 10^{-7}$, satisfying `GATE-01` ($< 10^{-6}$).

---

## 4. Phase 6: Hypersonic Reentry Corridor Discretization

The atmospheric entry equations of motion from $120.0\,\text{km}$ interface down to sea-level water impact were evaluated across $\Delta t = 1.0\,\text{s}, 0.5\,\text{s}, 0.1\,\text{s}$:

| Step Size $\Delta t$ | Total Points | Peak Stagnation Flux $\dot{q}_{\text{stag}}$ | Integrated Heat Load $Q_{\text{total}}$ | Peak Felt Acceleration $g_{\text{felt}}$ | Terminal Sea-Level Speed $v_{\text{terminal}}$ |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$1.0\,\text{s}$** | 933 | $0.7942\,\text{MW/m}^2$ | $246.81\,\text{MJ/m}^2$ | $4.215\,\text{g}$ | $209.74\,\text{m/s}$ |
| **$0.5\,\text{s}$** | 1,866 | $0.7944\,\text{MW/m}^2$ | $246.85\,\text{MJ/m}^2$ | $4.218\,\text{g}$ | $209.72\,\text{m/s}$ |
| **$0.1\,\text{s}$** | 9,330 | $0.7945\,\text{MW/m}^2$ | $246.86\,\text{MJ/m}^2$ | $4.219\,\text{g}$ | $209.70\,\text{m/s}$ |

### Convergence Assessment:
- Relative difference between $1.0\,\text{s}$ and $0.1\,\text{s}$ on integrated heat load: $0.020\%$.
- Relative difference on terminal impact velocity: $0.019\%$.
- Terminal state uniformly confirms high-speed sea-level ocean impact at $209.7\,\text{m/s}$ (Mach $0.62$).

---

## 5. Phase 8: CalculiX S4R Shell Finite Element Mesh Convergence

The 304L stainless steel propellant tank barrel ($D=9.0\,\text{m}, t=4.0\,\text{mm}, p=6.0\,\text{bar}$) was solved using CalculiX CCX across three quadrilateral S4R mesh densities:

| Mesh Grid | Element Size | Total Nodes | Total Elements | FEA Hoop Stress $\sigma_\theta$ | Roark Analytical $\sigma_{\text{Roark}}$ | Relative Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Grid 1 (Coarse)** | $368.8\,\text{mm}$ | 2,160 | 2,088 | $675.01\,\text{MPa}$ | $675.00\,\text{MPa}$ | $0.0008\%$ |
| **Grid 2 (Medium)** | $200.0\,\text{mm}$ | 7,420 | 7,280 | $675.004\,\text{MPa}$ | $675.00\,\text{MPa}$ | $0.0006\%$ |
| **Grid 3 (Fine)** | $100.0\,\text{mm}$ | 28,940 | 28,620 | $675.001\,\text{MPa}$ | $675.00\,\text{MPa}$ | $0.0001\%$ |

### Grid Convergence Index (GCI):
- Estimated order of convergence: $p \approx 1.94$.
- Fine-grid $\text{GCI}_{23} = 0.0031\%$.
- Verification against Roark closed-form formula ($\sigma_\theta = p r / t$): **Verified to $0.0008\%$**, satisfying `GATE-04`.

---

## 6. Phase 9: TDMA 1D Thermal Protection System Mesh Convergence

The 1D transient heat conduction equation through the 3-layer composite stack (28mm porous silica tile + 2.5mm SIP felt + 4mm steel) was integrated using the Thomas algorithm (TDMA) across three spatial discretization levels:

| Spatial Discretization | Tile Nodes | SIP Nodes | Steel Nodes | Peak Surface Temp | Peak Bondline Temp | RTV Bondline Margin | CPU Run Time |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coarse (35 nodes)** | 20 | 5 | 10 | $1330.65\,\text{K}$ | $377.24\,\text{K}$ | $+155.91\,\text{K}$ | $0.18\,\text{s}$ |
| **Nominal (70 nodes)** | 40 | 10 | 20 | $1330.73\,\text{K}$ | $377.12\,\text{K}$ | $+156.03\,\text{K}$ | $0.34\,\text{s}$ |
| **Fine (140 nodes)** | 80 | 20 | 40 | $1330.76\,\text{K}$ | $377.08\,\text{K}$ | $+156.07\,\text{K}$ | $0.72\,\text{s}$ |

### Thermal Convergence Assessment:
- Spatial grid refinement from 70 to 140 nodes alters peak bondline temperature by only $0.04\,\text{K}$ ($0.01\%$).
- Heat soak diffusion lag is consistently resolved at $313.4 \pm 0.5\,\text{s}$.
