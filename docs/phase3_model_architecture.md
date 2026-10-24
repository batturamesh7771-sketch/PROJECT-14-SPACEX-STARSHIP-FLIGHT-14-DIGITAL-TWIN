# Starship Flight 14 Digital Engineering Laboratory
## Phase 3 — Model Architecture & Mathematical Formulations

**Document ID:** `DOC-P3-ARCH-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-25`  
**Author:** Senior Flight-Dynamics Engineer & Simulation Architect  

---

### 1. State-Vector Formulation (3-DOF ECI Frame)

The translational equations of motion are formulated in Earth-Centered Inertial (ECI) coordinates:

$$\mathbf{y}(t) = \begin{bmatrix} \mathbf{r}(t) \\ \mathbf{v}(t) \\ m(t) \end{bmatrix} = \begin{bmatrix} x & y & z & v_x & v_y & v_z & m \end{bmatrix}^T$$

#### Differential State Equations:
$$\frac{d\mathbf{r}}{dt} = \mathbf{v}$$

$$\frac{d\mathbf{v}}{dt} = \frac{\mathbf{F}_{\text{thrust}}(t, P_a) + \mathbf{F}_{\text{drag}}(h, \mathbf{v}_{\text{rel}})}{m(t)} + \mathbf{g}_{J_2}(\mathbf{r})$$

$$\frac{dm}{dt} = -\sum_{i=1}^{N_{\text{active}}} \dot{m}_i(t)$$

---

### 2. Physical Subsystem Models

#### 2.1 Gravitational Field with $J_2$ Oblateness Perturbation
The gravitational acceleration vector accounts for Earth oblateness:

$$\mathbf{g}(\mathbf{r}) = -\frac{\mu_E}{r^3} \mathbf{r} + \mathbf{a}_{J_2}(\mathbf{r})$$

Where $\mu_E = 3.986004418 \times 10^{14}\,\text{m}^3/\text{s}^2$, $R_E = 6,378,137\,\text{m}$, and $J_2 = 1.08262668 \times 10^{-3}$:

$$\mathbf{a}_{J_2}(\mathbf{r}) = -\frac{3}{2} \frac{J_2 \mu_E R_E^2}{r^5} \begin{bmatrix} x \left( 1 - 5 \frac{z^2}{r^2} \right) \\ y \left( 1 - 5 \frac{z^2}{r^2} \right) \\ z \left( 3 - 5 \frac{z^2}{r^2} \right) \end{bmatrix}$$

#### 2.2 Rotating Atmosphere & Aerodynamic Drag
The atmospheric-relative velocity accounts for the rotating Earth:

$$\mathbf{v}_{\text{rel}} = \mathbf{v} - \boldsymbol{\omega}_E \times \mathbf{r}, \quad \boldsymbol{\omega}_E = \begin{bmatrix} 0 & 0 & 7.292115 \times 10^{-5} \end{bmatrix}^T\,\text{rad/s}$$

$$\mathbf{F}_{\text{drag}} = -\frac{1}{2} \rho(h) \, \|\mathbf{v}_{\text{rel}}\| \, C_D(M) \, A_{\text{ref}} \, \mathbf{v}_{\text{rel}}$$

- $\rho(h)$ is evaluated from the **1976 US Standard Atmosphere** piecewise barometric tables across all atmospheric layers.
- Geometric altitude $h$ is evaluated via Bowring's closed-form algorithm relative to the WGS-84 ellipsoid.
- $C_D(M)$ models continuous subsonic ($0.28$), transonic drag rise (peaking at $0.63$ at $M=1.05$), and supersonic decay.

#### 2.3 Raptor 3 Propulsion & Mass Depletion
Instantaneous engine thrust varies with ambient pressure $P_a$:

$$F_i(P_a, \tau) = F_{\text{vac}} \cdot \tau - A_e P_a$$

$$\dot{m}_i = \frac{F_{\text{vac}}}{I_{\text{sp,vac}} \, g_0} \cdot \tau$$

For the 33-engine booster cluster, liftoff thrust produces $81.69\,\text{MN}$ at $T=0\,\text{s}$ ramping to $91.26\,\text{MN}$ at $T=2\,\text{s}$. Throttling to $60\%$ between $T+30\,\text{s}$ and $T+68\,\text{s}$ regulates dynamic pressure through the Max-Q bucket to $39.01\,\text{kPa}$.
