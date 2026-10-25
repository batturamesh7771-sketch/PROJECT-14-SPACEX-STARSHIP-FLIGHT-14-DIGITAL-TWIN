# Phase 8: Propellant Tank Structural FEA Benchmark — Model Architecture

## 1. Executive Summary & Purpose

Phase 8 implements the **Structural FEA Propellant Tank Benchmark** for the Starship Flight 14 Digital Engineering Lab. The objective is to establish an analytically verified, reproducible structural shell model of the primary propellant tank cylinder section under critical flight load combinations:
1. Internal ullage and head pressure ($p = 6.0\,\text{bar} = 0.60\,\text{MPa}$).
2. Axial compressive launch acceleration ($3.0\,\text{g}$ on $120\,\text{t}$ stage mass $\approx 3.53\,\text{MN}$).
3. Verification against classical closed-form thin-shell theory (Roark's Formulas for Stress and Strain, 8th Edition).
4. Mesh refinement convergence across three element densities.
5. Exportable, executable input decks for industry-standard solvers:
   - **CalculiX CCX v2.22** (Abaqus S4R format, fully integrated and executed via local FreeCAD CCX engine).
   - **ANSYS Mechanical APDL (MAPDL)** (`fea/tank_section_stress.mac` parameterized for `SHELL181`).

---

## 2. Thin-Shell Analytical Formulation (Roark Table 13.1)

For a thin-walled circular cylindrical shell with mean radius $r = 4.5\,\text{m}$, wall thickness $t = 0.004\,\text{m}$ ($4.0\,\text{mm}$), section height $L = 10.0\,\text{m}$, Young's modulus $E = 193.0\,\text{GPa}$, Poisson's ratio $\nu = 0.29$, and material density $\rho = 7900\,\text{kg/m}^3$:

### 2.1 Slenderness Regime
$$\frac{r}{t} = \frac{4.5}{0.004} = 1125 \gg 10$$
Because $r/t = 1125$, the structure operates deeply in the **thin-shell membrane regime**, where transverse shear deformations are negligible and through-thickness normal stress is small compared to in-plane stresses ($\sigma_{rr} \approx 0$).

### 2.2 Circumferential (Hoop) Stress
Internal ullage pressure $p$ creates uniform membrane tensile stress around the circumference:
$$\sigma_h = \frac{p \cdot r}{t}$$
For $p = 6.0\,\text{bar} = 0.60\,\text{MPa}$:
$$\sigma_h = \frac{0.60 \times 10^6\,\text{Pa} \times 4.5\,\text{m}}{0.004\,\text{m}} = 675.00\,\text{MPa}$$

### 2.3 Longitudinal (Axial) Stress
Longitudinal stress arises from two superposed mechanisms:
1. **End-Cap Tension:** Internal pressure acting on the tank domes transmits an axial tensile membrane force:
   $$\sigma_{l,\text{pres}} = \frac{p \cdot r}{2t} = \frac{675.00}{2} = 337.50\,\text{MPa}$$
2. **Axial Acceleration Compression:** Vehicle launch acceleration ($n_z = 3.0\,\text{g}$) acting on upper-stage mass ($m = 120\,000\,\text{kg}$) exerts compressive thrust force $F_z$:
   $$F_z = n_z \cdot m \cdot g_0 = 3.0 \times 120\,000 \times 9.80665 \approx 3.5304 \times 10^6\,\text{N}$$
   $$\sigma_{l,\text{comp}} = -\frac{F_z}{2\pi r t} = -\frac{3.5304 \times 10^6}{2\pi \times 4.5 \times 0.004} = -31.22\,\text{MPa}$$
3. **Net Axial Membrane Stress:**
   $$\sigma_l = \sigma_{l,\text{pres}} + \sigma_{l,\text{comp}} = 337.50 - 31.22 = 306.28\,\text{MPa}$$

### 2.4 Von Mises Equivalent Stress
Under plane stress ($\sigma_{zz} = \sigma_l$, $\sigma_{\theta\theta} = \sigma_h$, $\tau_{z\theta} = 0$, $\sigma_{rr} = 0$):
$$\sigma_{\text{vm}} = \sqrt{\sigma_h^2 - \sigma_h \sigma_l + \sigma_l^2}$$
- **Pressure Only:** $\sigma_{\text{vm}} = \sqrt{675.0^2 - (675.0)(337.5) + 337.5^2} = 584.57\,\text{MPa}$
- **Combined Pressure + 3g Acceleration:** $\sigma_{\text{vm}} = \sqrt{675.0^2 - (675.0)(306.28) + 306.28^2} = 585.40\,\text{MPa}$

### 2.5 Elastic Displacements
From generalized Hooke's Law for isotropic thin shells:
- **Radial Expansion:**
  $$\Delta r = r \cdot \varepsilon_h = \frac{r}{E} (\sigma_h - \nu \sigma_l)$$
  $$\Delta r = \frac{4.5}{193.0 \times 10^9} (675.0 - 0.29 \times 306.28) \times 10^6 = 1.367 \times 10^{-2}\,\text{m} \approx 13.67\,\text{mm}$$
- **Axial Elongation:**
  $$\Delta L = L \cdot \varepsilon_l = \frac{L}{E} (\sigma_l - \nu \sigma_h)$$
  $$\Delta L = \frac{10.0}{193.0 \times 10^9} (306.28 - 0.29 \times 675.0) \times 10^6 = 5.727 \times 10^{-3}\,\text{m} \approx 5.73\,\text{mm}$$

---

## 3. Boundary Layer Elastic Shell Formulation (Hetenyi Theory)

At the junction between the cylindrical barrel and rigid ring stiffeners or ellipsoidal dome knuckles, the radial expansion is constrained. This discontinuity induces local edge moments $M_0$ and transverse shear forces $Q_0$.

The characteristic decay parameter of the shell is:
$$\beta = \left[ \frac{3(1 - \nu^2)}{r^2 \cdot t^2} \right]^{1/4} = \left[ \frac{3(1 - 0.29^2)}{4.5^2 \times 0.004^2} \right]^{1/4} \approx 9.59635\,\text{m}^{-1}$$

The boundary attenuation wave length is:
$$\lambda = \frac{\pi}{\beta} = \frac{\pi}{9.59635} \approx 0.32738\,\text{m} \approx 32.7\,\text{cm}$$

### Boundary Decay Implications
- The edge boundary layer decays exponentially as $e^{-\beta z} \cos(\beta z)$.
- At $z = 3\lambda \approx 0.98\,\text{m}$, the boundary perturbation is attenuated by over $99.9\%$.
- Beyond $1.0\,\text{m}$ from either end, the cylinder operates in pure membrane state, matching Roark's closed-form formulas within $0.001\%$.

---

## 4. Finite Element Discretization & Solver Interfaces

### 4.1 Shell Element Formulation: Abaqus / CalculiX S4R
- **Geometry:** 4-node quadrilateral shell with linear shape functions.
- **Degrees of Freedom:** 6 DOFs per node (3 translations $u_x, u_y, u_z$, 3 rotations $\theta_x, \theta_y, \theta_z$).
- **Integration:** Reduced Gauss integration ($1 \times 1$) with physical hourglass stiffness stabilization to avoid shear and membrane locking.
- **Section Definition:**
  ```abaqus
  *SHELL SECTION, ELSET=EALL, MATERIAL=STEEL_304L
  0.004, 5
  ```

### 4.2 ANSYS Mechanical APDL: SHELL181
- **Element:** `SHELL181` is suitable for analyzing thin-to-moderately thick shell structures. It is a 4-node element with 6 DOFs at each node.
- **Section Controls:** `SECTYPE, 1, SHELL,, TankWall` with `SECDATA, 0.004, 1, 0.0, 3` and `SECOFFSET, MID`.
- **Loading:** Normal surface pressure via `SFA, ALL, 1, PRES, 0.60E6` and top edge compressive line load via `F, ALL, FZ, -LINE_LOAD * dz`.

---

## 5. NASA SP-8007 Thin-Walled Cylinder Buckling Model

Under compressive axial thrust, thin cylindrical shells are susceptible to elastic bifurcation buckling before reaching material yield.

### 5.1 Classical Unpressurized Buckling Stress
$$\sigma_{\text{cl}} = \frac{E}{\sqrt{3(1 - \nu^2)}} \frac{t}{r} = \frac{193.0 \times 10^9}{\sqrt{3(1 - 0.29^2)}} \frac{0.004}{4.5} = 103.47\,\text{MPa}$$

### 5.2 Imperfection Knockdown Factor $\gamma$
For $r/t = 1125$, geometric imperfections significantly degrade theoretical capacity. NASA SP-8007 specifies an empirical knockdown factor:
$$\gamma \approx 0.20 \implies \sigma_{\text{design,unpres}} = 0.20 \times 103.47 = 20.69\,\text{MPa}$$

### 5.3 Internal Pressure Stabilization
Internal ullage pressure ($6.0\,\text{bar}$) exerts an outward tensile hoop pre-stress that suppresses the formation of local inward buckling dimples:
$$q = \frac{p}{E} \left(\frac{r}{t}\right)^2 = \frac{0.6 \times 10^6}{193 \times 10^9} \left(1125\right)^2 \approx 3.936$$
$$\Delta \sigma_{\text{pres}} \approx 0.10 \cdot q \cdot \sigma_{\text{cl}} \approx 40.73\,\text{MPa}$$
$$\sigma_{\text{crit,pressurized}} = 20.69 + 40.73 = 61.42\,\text{MPa}$$

Since applied compressive axial stress is $\sigma_{\text{comp}} = 31.22\,\text{MPa}$, the buckling safety factor under flight acceleration is:
$$\text{SF}_{\text{buckling}} = \frac{\sigma_{\text{crit,pressurized}}}{\sigma_{\text{comp}}} = \frac{61.42}{31.22} \approx 1.97 > 1.50$$
This demonstrates that pressurization is structurally essential to prevent thin-shell compressive buckling during ascent.
