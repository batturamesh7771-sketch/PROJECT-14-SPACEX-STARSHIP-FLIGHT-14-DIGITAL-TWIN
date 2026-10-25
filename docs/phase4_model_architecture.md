# Phase 4 Model Architecture: Modular Staging Dynamics Pipeline

**Document ID:** `DOC-P4-ARCH-001`  
**Classification:** System Software & Computational Architecture  
**Revision:** 1.0  
**Lead:** Software Architecture & Numerical Systems Lead  

---

## 1. System Pipeline Architecture

The Phase 4 architecture cleanly separates the continuous single-stack ascent trajectory from the multi-body event execution, independent numerical propagation, and metric synthesis.

```mermaid
flowchart TD
    subgraph Phase3_Ascent ["Phase 3: Powered Ascent Core"]
        A["data/propulsion/parameters.yaml"] --> B["src/dynamics/ascent_3dof.py"]
        C["US Standard Atmosphere 1976"] --> B
        D["WGS-84 / ECI Gravity J2"] --> B
        B --> E["Ascent Solution [0 to 140s]"]
    end

    subgraph Event_Handoff ["Gate 4: Staging Event Split"]
        E --> F["src/dynamics/staging_separation.py"]
        G["Event Registry: MECO & Hot-Stage"] --> F
        F --> H1["Booster Pre-State [r, v, m]"]
        F --> H2["Ship Pre-State [r, v, m]"]
        F --> I["Mass & Momentum Balance Check"]
    end

    subgraph Independent_Propagation ["Gate 5: Dual Independent Solvers"]
        H1 --> J1["src/dynamics/booster_recovery.py"]
        H2 --> J2["src/dynamics/starship_ascent_to_orbit.py"]
        J1 --> K1["Booster Boostback, Coast & Entry [140 to 414s]"]
        J2 --> K2["Ship Upper Ascent to SECO [140 to 522s]"]
    end

    subgraph Relative_Motion_Engine ["Relative Motion Engine"]
        K1 --> L["Synchronized Time-Grid Interpolation"]
        K2 --> L
        L --> M["Relative State Vector: r_rel, v_rel, a_rel"]
        M --> N["center_range_m, relative_speed_mps"]
    end

    subgraph Output_Artifacts ["Output Artifacts & Visualization"]
        N --> O["output/flight14_staging_relative_motion.csv"]
        K1 --> P["output/flight14_booster_return.csv"]
        K2 --> Q["output/flight14_starship_upper_ascent.csv"]
        N --> R["output/flight14_phase4_summary.json"]
        Q --> S["NASA GMAT Orbit Propagation"]
        O --> T["FreeCAD Kinematic Visual Replay"]
    end
```

---

## 2. Mathematical Equations of Motion

For each stage $i \in \{\text{booster}, \text{ship}\}$ after separation ($t \ge T_{\text{stage}}$):

$$\frac{d\mathbf{r}_i}{dt} = \mathbf{v}_i$$

$$\frac{d\mathbf{v}_i}{dt} = \mathbf{g}(\mathbf{r}_i) + \frac{\mathbf{F}_{\text{thrust}, i}(t) + \mathbf{F}_{\text{aero}, i}(\mathbf{r}_i, \mathbf{v}_i) + \mathbf{F}_{\text{external}, i}(t)}{m_i(t)}$$

$$\frac{dm_i}{dt} = -\dot{m}_{\text{prop}, i}(t)$$

### Gravitational Field Model:
$$\mathbf{g}(\mathbf{r}) = -\frac{\mu}{\|\mathbf{r}\|^3} \mathbf{r} + \mathbf{a}_{J_2}(\mathbf{r})$$
where:
$$\mathbf{a}_{J_2}(\mathbf{r}) = -\frac{3}{2} J_2 \frac{\mu R_E^2}{\|\mathbf{r}\|^5} \begin{bmatrix} x \left(1 - 5 \frac{z^2}{\|\mathbf{r}\|^2}\right) \\ y \left(1 - 5 \frac{z^2}{\|\mathbf{r}\|^2}\right) \\ z \left(3 - 5 \frac{z^2}{\|\mathbf{r}\|^2}\right) \end{bmatrix}$$

### Aerodynamic Force Model:
$$\mathbf{F}_{\text{aero}, i} = -\frac{1}{2} \rho(h) \|\mathbf{v}_{\text{rel}, i}\| \mathbf{v}_{\text{rel}, i} S_{\text{ref}, i} C_{D, i}(M_i)$$
where relative velocity accounts for Earth rotation:
$$\mathbf{v}_{\text{rel}, i} = \mathbf{v}_i - \boldsymbol{\omega}_E \times \mathbf{r}_i$$

---

## 3. Relative Motion Engine

To ensure mathematical rigor, relative quantities are computed on a synchronized, uniform 100 Hz output time grid ($t_k = 140.0 + k \times 0.01\,\text{s}$):

$$\mathbf{r}_{\text{rel}}(t_k) = \mathbf{r}_{\text{ship}}(t_k) - \mathbf{r}_{\text{booster}}(t_k)$$
$$\mathbf{v}_{\text{rel}}(t_k) = \mathbf{v}_{\text{ship}}(t_k) - \mathbf{v}_{\text{booster}}(t_k)$$
$$\text{center\_range\_m}(t_k) = \|\mathbf{r}_{\text{rel}}(t_k)\|$$
$$\text{relative\_speed\_mps}(t_k) = \|\mathbf{v}_{\text{rel}}(t_k)\|$$

Any missing values or out-of-bounds queries must be bounded: extrapolation outside each vehicle's valid integration span is strictly prohibited.
