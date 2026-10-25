# Starship Flight 14 Digital Engineering Lab — Frame and Time Conventions

**Document ID:** `DOC-INT-FRAME-TIME-001`  
**Classification:** Reference Frame & Geodetic Standards Specification  

---

## 1. Geophysical Constants and Ellipsoid Parameters

All astrodynamic, aerodynamic, and geodetic algorithms throughout the digital lab must adhere strictly to WGS-84 / EGM96 standard values:

| Parameter | Symbol | Value | Units | Reference Standard |
| :--- | :---: | :---: | :---: | :--- |
| **Earth Gravitational Parameter** | $\mu_E$ | $3.986004418 \times 10^{14}$ | $\text{m}^3/\text{s}^2$ | WGS-84 Standard |
| **Earth Equatorial Radius** | $R_E$ | $6,378,137.0$ | $\text{m}$ | WGS-84 Reference Ellipsoid |
| **Earth Polar Radius** | $R_p$ | $6,356,752.3142$ | $\text{m}$ | $R_p = R_E (1 - f)$ |
| **Earth Flattening** | $f$ | $1 / 298.257223563$ | dimensionless | WGS-84 Ellipsoid |
| **First Eccentricity Squared** | $e^2$ | $6.69437999014 \times 10^{-3}$ | dimensionless | $e^2 = 2f - f^2$ |
| **Earth Rotation Rate** | $\omega_E$ | $7.2921150 \times 10^{-5}$ | $\text{rad/s}$ | IERS Standards |
| **Second Zonal Harmonic** | $J_2$ | $1.08262668 \times 10^{-3}$ | dimensionless | EGM96 Geopotential Model |
| **Standard Gravitational Accel**| $g_0$ | $9.80665$ | $\text{m/s}^2$ | CODATA / ISO Standard |

---

## 2. Geodetic Coordinate Conversion (Bowring 1988 Closed-Form)

Transforming ECEF Cartesian position $\mathbf{r}_{\text{ECEF}} = [x, y, z]^T$ into WGS-84 geodetic coordinates (latitude $\phi$, longitude $\lambda$, geometric altitude $h$):

1. **Longitude:**
   $$\lambda = \text{atan2}(y, x)$$
2. **Equatorial Distance:**
   $$p = \sqrt{x^2 + y^2}$$
3. **Parametric Reduced Latitude ($\theta$):**
   $$\theta = \text{atan2}\left(z R_E, p R_p\right)$$
4. **Geodetic Latitude ($\phi$):**
   $$\phi = \text{atan2}\left(z + e'^2 R_p \sin^3(\theta), p - e^2 R_E \cos^3(\theta)\right)$$
   where second eccentricity $e'^2 = \frac{R_E^2 - R_p^2}{R_p^2}$.
5. **Radius of Curvature in Prime Vertical ($N$):**
   $$N(\phi) = \frac{R_E}{\sqrt{1 - e^2 \sin^2(\phi)}}$$
6. **Geodetic Altitude ($h$):**
   $$h = \frac{p}{\cos(\phi)} - N(\phi)$$

*Precision:* Accurate to within $1.0\,\text{mm}$ of true geodetic altitude globally.

---

## 3. Atmospheric-Relative Velocity Vector Derivation

Inertial velocity $\mathbf{v}_{\text{ECI}}$ does NOT represent the aerodynamic flow velocity experienced by the vehicle hull. Because Earth's atmosphere co-rotates with the solid crust at angular velocity $\boldsymbol{\omega}_E = [0, 0, \omega_E]^T$:
$$\mathbf{v}_{\text{rel,ECI}} = \mathbf{v}_{\text{ECI}} - \boldsymbol{\omega}_E \times \mathbf{r}_{\text{ECI}}$$
$$\mathbf{v}_{\text{rel,ECI}} = \begin{bmatrix} v_x + \omega_E y \\ v_y - \omega_E x \\ v_z \end{bmatrix}$$

At the entry interface ($h = 120\,\text{km}$), neglecting Earth rotation produces an error of over **$420\,\text{m/s}$** in relative velocity, skewing dynamic pressure by $> 11\,\text{kPa}$ and stagnation heating by $> 15\%$. All aerodynamic calculations in Phase 3, Phase 4, and Phase 6 MUST use $\mathbf{v}_{\text{rel}}$.
