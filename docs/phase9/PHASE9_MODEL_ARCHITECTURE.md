# Phase 9: Aerothermal Reentry & Thermal Protection System (TPS) Model — Architecture

## 1. Executive Summary & Purpose

Phase 9 establishes the **Aerothermal Reentry and Thermal Protection System (TPS)** engineering simulation for Starship Flight 14.
It couples the 3-DOF hypersonic entry trajectory states (velocity, altitude, ambient air density) to:
1. **Convective Stagnation Heat Flux:** Sutton-Graves ($q_{\text{stag}} \propto \sqrt{\rho / R_n} \cdot v^3$) and Detra-Kemp-Riddell (DKR) correlations.
2. **Windward Acreage Heat Flux:** Fay-Riddell / Lees laminar boundary layer scaling ($q_{\text{windward}} \approx q_{\text{stag}} \cdot (\sin \alpha)^{1.6} \cdot f_{\text{body}}$) at $\alpha = 40.0^\circ$ hypersonic entry pitch.
3. **Surface Radiative Equilibrium:** Non-linear Stefan-Boltzmann surface radiation balance ($\varepsilon \sigma T^4$).
4. **1D Transient Multi-Layer Conduction:** Thomas algorithm (TDMA) implicit non-linear finite-difference solver across the 3-layer composite stack:
   - Outer Layer: Reaction-Cured Glass (RCG) coated porous fibrous silica tiles ($L_{\text{tile}} = 28.0\,\text{mm}$).
   - Middle Layer: Strain Isolation Pad (SIP) Nomex/quartz felt and RTV-560 silicone adhesive ($L_{\text{sip}} = 2.5\,\text{mm}$).
   - Substrate Layer: AISI 304L cold-rolled stainless steel propellant tank skin ($L_{\text{steel}} = 4.0\,\text{mm}$).
5. **Heat Soak & RTV Margin Assessment:** Captures the physical diffusion time lag ($\approx 313\,\text{s}$) where the bondline reaches peak temperature long after peak aerothermal heating, assessing structural thermal margins against the $533.15\,\text{K}$ ($260^\circ\text{C} / 500^\circ\text{F}$) adhesive limit.

---

## 2. Aerothermal Flux Correlations

### 2.1 Sutton-Graves Stagnation-Point Correlation
$$q_{\text{stag}} = C_{\text{sg}} \sqrt{\frac{\rho}{R_n}} v^3 \quad [\text{W/m}^2]$$
- $C_{\text{sg}} = 1.74153 \times 10^{-4}\,\text{W}\cdot\text{s}^3 / (\text{m}^3 \cdot \sqrt{\text{kg/m}^3})$ for Earth atmosphere.
- $R_n = 4.5\,\text{m}$ (effective blunt nose radius of Starship).
- $\rho$: US 1976 Standard Atmosphere density at altitude $z$.
- $v$: Vehicle relative velocity through the atmosphere.

### 2.2 Detra-Kemp-Riddell (DKR) Formulation
$$q_{\text{dkr}} = \frac{11030}{\sqrt{R_{n,\text{ft}}}} \left(\frac{\rho}{\rho_0}\right)^{0.5} \left(\frac{v}{v_c}\right)^{3.15} \times 11356.5267 \quad [\text{W/m}^2]$$
- $\rho_0 = 1.225\,\text{kg/m}^3$.
- $v_c = 7925.0\,\text{m/s}$ (circular orbital velocity).

### 2.3 Windward Acreage Heating (Belly Tiles)
Behind the bow shock on the flat windward belly at angle of attack $\alpha = 40^\circ$:
$$q_{\text{windward}} = q_{\text{stag}} \cdot (\sin \alpha)^{1.6} \cdot f_{\text{body}}$$
For $\alpha = 40^\circ$:
$$\sin(40^\circ)^{1.6} \approx 0.4934$$
With body distribution factor $f_{\text{body}} = 0.40$:
$$q_{\text{windward}} \approx 0.197 \cdot q_{\text{stag}}$$

### 2.4 Surface Radiative Equilibrium Temperature
$$T_{\text{rad}} = \left( \frac{q_{\text{windward}}}{\varepsilon \sigma} + T_\infty^4 \right)^{1/4}$$
- $\varepsilon = 0.85$ (emissivity of black RCG coating).
- $\sigma = 5.670374 \times 10^{-8}\,\text{W/(m}^2 \cdot \text{K}^4)$.
- $T_\infty \approx 220.0\,\text{K}$ (mesosphere/stratosphere background temperature).

---

## 3. 1D Transient Composite Heat Conduction Formulation

### 3.1 Non-Linear Heat Equation
$$\rho_m c_{p,m}(T) \frac{\partial T}{\partial t} = \frac{\partial}{\partial x} \left( k_m(T) \frac{\partial T}{\partial x} \right)$$
Where index $m \in \{\text{Tile}, \text{SIP}, \text{Steel}\}$.

### 3.2 Temperature-Dependent Material Properties
1. **Silica Tile:**
   - $k(T) = 0.032 + 0.025 (T/1000) + 0.028 (T/1000)^3 \quad [\text{W/(m}\cdot\text{K)}]$
   - $c_p(T) = 1260.0 - 900.0 \exp(-T / 380.0) \quad [\text{J/(kg}\cdot\text{K)}]$
   - $\rho = 190.0\,\text{kg/m}^3$
2. **SIP Felt / RTV Adhesive Layer:**
   - $k(T) = 0.040 + 0.035 (T/1000) \quad [\text{W/(m}\cdot\text{K)}]$
   - $c_p(T) = 800.0 + 0.5 T \quad [\text{J/(kg}\cdot\text{K)}]$
   - $\rho = 250.0\,\text{kg/m}^3$
3. **AISI 304L Stainless Steel Substrate:**
   - $k(T) = 14.0 + 0.0075 T \quad [\text{W/(m}\cdot\text{K)}]$
   - $c_p(T) = 450.0 + 0.15 T \quad [\text{J/(kg}\cdot\text{K)}]$
   - $\rho = 7900.0\,\text{kg/m}^3$

### 3.3 Boundary Conditions
1. **Outer Tile Surface ($x = 0$):**
   $$-k \left.\frac{\partial T}{\partial x}\right|_{x=0} = q_{\text{windward}}(t) - \varepsilon \sigma (T_0^4 - T_\infty^4)$$
   Linearized implicitly about current time step:
   $$T_0^{n+1, 4} \approx 4 (T_0^n)^3 T_0^{n+1} - 3 (T_0^n)^4$$
2. **Inner Steel Skin Backface ($x = L_{\text{total}}$):**
   Adiabatic boundary (worst-case thermal soak into structure):
   $$\left.\frac{\partial T}{\partial x}\right|_{x=L} = 0$$

### 3.4 Numerical Discretization (TDMA)
The domain is discretized into 55 nodes (35 in tile, 10 in SIP, 10 in steel). The resulting tridiagonal system is solved unconditionally stably via the Thomas algorithm in $O(N)$ operations per time step.
