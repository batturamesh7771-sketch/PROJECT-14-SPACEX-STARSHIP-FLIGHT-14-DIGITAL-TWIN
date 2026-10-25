# Starship Flight 14 — Coordinate Frames, Transformation Matrices & Time Conventions

**Version:** 1.0.0  
**Effective Date:** October 26, 2026  
**Document ID:** `SPEC-FRAMES-TIME-01`  

---

## 1. Reference Coordinate Frames

| Frame Name | Type | Origin | Fundamental Plane | Primary Axis ($X$) | Tertiary Axis ($Z$) | Secondary Axis ($Y$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **ECI J2000** | Inertial | Earth Center of Mass | Celestial Equator at epoch J2000.0 | Vernal Equinox ($\Upsilon$) | Earth Spin Axis (True North) | Completes RH ($\mathbf{Z} \times \mathbf{X}$) |
| **ECEF WGS-84** | Rotating | Earth Center of Mass | Equatorial Plane | Prime Meridian ($0^\circ$ Lon) | Reference Pole ($90^\circ$ N) | Completes RH ($90^\circ$ E Lon) |
| **Three.js Scene** | Graphical | Scene Origin (Earth Center) | Ground Plane ($X$-$Z$) | $+X_{\text{scene}}$ (Inertial $X$) | $+Z_{\text{scene}}$ (Negative Inertial $Y$) | $+Y_{\text{scene}}$ (Celestial North) |
| **Vehicle Body** | Local Vehicle | Vehicle Center of Mass | Vehicle Symmetry Plane | Starboard Flap Axis | Windward TPS Belly (Nadir) | Vehicle Long Nose Axis ($\hat{\mathbf{v}}$) |

---

## 2. Orthogonal ECI-to-Three.js Transformation

To map classical orbital physics to the Three.js coordinate system (where $+Y$ is "Up" towards the celestial pole and the camera default looks down $-Z$), the exact transformation matrix $R_{\text{scene}}$ is defined as:

$$\begin{bmatrix} X_{\text{scene}} \\ Y_{\text{scene}} \\ Z_{\text{scene}} \end{bmatrix} = s \begin{bmatrix} 1 & 0 & 0 \\ 0 & 0 & 1 \\ 0 & -1 & 0 \end{bmatrix} \begin{bmatrix} X_{\text{ECI}} \\ Y_{\text{ECI}} \\ Z_{\text{ECI}} \end{bmatrix}$$

where $s = 1.0 \times 10^{-6}\text{ Three.js units / meter}$ ($1\text{ unit} = 1,000\text{ km}$).

### Orthogonality Proof & Parity Preservation
$$\det(R_{\text{scene}}) = 1 \cdot (0 \cdot 0 - 1 \cdot (-1)) = +1.0$$
$$R_{\text{scene}}^T R_{\text{scene}} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 0 & -1 \\ 0 & 1 & 0 \end{bmatrix} \begin{bmatrix} 1 & 0 & 0 \\ 0 & 0 & 1 \\ 0 & -1 & 0 \end{bmatrix} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix} = \mathbf{I}_{3\times3}$$

This is an isometry (rigid-body rotation $R_x(-90^\circ)$). It preserves all distances, dot products, cross products, and handedness with zero reflection or chiral distortion.

---

## 3. Physical Attitude Kinematics & Orthonormal Basis

To eliminate the "standing rocket pencil" bug during orbital flight, vehicle orientation is computed directly from physical orbit vectors rather than arbitrary Euler angles:

1. **Velocity Direction (Nose Vector):**
   $$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|}$$
   $$\mathbf{y}_{\text{body}} = \hat{\mathbf{v}}$$
2. **Nadir Direction (Radial Inward):**
   $$\hat{\mathbf{r}} = \frac{\mathbf{r}}{\|\mathbf{r}\|}$$
3. **Belly Vector (Black TPS Heatshield facing Earth):**
   $$\mathbf{z}_{\text{body}} = -\hat{\mathbf{r}}$$
4. **Starboard Wing Vector (Cross Product):**
   $$\mathbf{x}_{\text{body}} = \frac{\mathbf{y}_{\text{body}} \times \mathbf{z}_{\text{body}}}{\|\mathbf{y}_{\text{body}} \times \mathbf{z}_{\text{body}}\|}$$
5. **Re-orthogonalized Belly Vector:**
   $$\mathbf{z}_{\text{body}} = \mathbf{x}_{\text{body}} \times \mathbf{y}_{\text{body}}$$

The rotation matrix $M_{\text{basis}} = [\mathbf{x}_{\text{body}} \mid \mathbf{y}_{\text{body}} \mid \mathbf{z}_{\text{body}}]$ is converted directly to a Three.js quaternion $q_{\text{vehicle}}$ at every animation frame, ensuring true horizontal prograde orbital flight, continuous gravity turn during ascent, and retrograde attitude during deorbit.

---

## 4. Master Time & Synchronization Conventions

1. **Mission Elapsed Time (MET):**
   $$t \in [0.0, t_{\text{max}}]\text{ seconds}$$
   Sub-second floating-point integrator clock.
2. **Flight 14 Launch Epoch:**
   $$\text{Epoch} = \text{2026-09-28T12:48:59.000Z}\quad (07:48:59\text{ CDT})$$
3. **UTC Clock Conversion:**
   $$\text{UTC}(t) = \text{Epoch} + (t \times 1000)\text{ ms}$$
   Formatted as `YYYY-MM-DD HH:MM:SS UTC`.
