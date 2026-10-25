# Phase 11: Uncertainty Quantification & Sensitivity Methodology
**Starship Flight 14 Digital Engineering Lab**  
**Standards Reference:** NIST TN 1297, JCGM 101:2008, NASA-STD-7009B Section 5.5  
**Author:** Lead Independent Verification, Flight-Dynamics Validation & Software-Assurance Engineer

---

## 1. Mathematical Framework & Propagation Hierarchy

Uncertainty Quantification (UQ) within the lab combines two complementary mathematical formulations:
1. **First-Order Covariance Propagation (NIST TN 1297):** Applied to smooth, continuous submodels (e.g., orbital cutoff velocity and Max-Q).
2. **Seeded Monte Carlo Propagation (JCGM 101:2008):** Applied to nonlinear flight dynamics with discontinuous boundaries (hypersonic heating, aerodynamic decelerations, thermal TPS diffusion).

```mermaid
flowchart LR
    subgraph Inputs["Characterized Input Distributions"]
        T["Raptor Thrust: N(1.0, 0.02)"]
        ISP["Raptor Isp: N(1.0, 0.01)"]
        M0["Liftoff Mass: N(4939.8t, 15t)"]
        RHO["Atmosphere: U(0.85, 1.15)"]
        CD["Drag Coeff: U(0.90, 1.10)"]
        KSG["Sutton-Graves: N(1.0, 0.05)"]
        TH["Tile Thickness: N(28.0, 0.8mm)"]
    end

    subgraph Engines["UQ Engine (src/verification/uq_engine.py)"]
        COV["First-Order Covariance\nSigma_y ≈ J Sigma_x J^T"]
        OAT["Sensitivity Screening\nElasticity S_i = (p0/y0)(dy/dp)"]
        MC["Monte Carlo (N=200, Seed 42)\nBatch Quantile Convergence"]
    end

    subgraph Outputs["Statistical Uncertainty Metrics"]
        P5_95["Percentile Bands (P5, P50, P95)"]
        CONV["Batch Convergence Trace (< 2%)"]
        SENS["Normalized Influence Ranking"]
    end

    Inputs --> Engines
    Engines --> Outputs
```

---

## 2. First-Order Covariance Propagation (NIST TN 1297)

For a locally differentiable vector function $\mathbf{y} = \mathbf{f}(\mathbf{x})$ mapping uncertain inputs $\mathbf{x} = [p_{\text{thrust}}, p_{\text{isp}}, m_0]^T$ to trajectory states $\mathbf{y} = [v_{\text{SECO}}, q_{\text{max}}]^T$:

$$\Sigma_y \approx \mathbf{J} \Sigma_x \mathbf{J}^T$$

Where the Jacobian $\mathbf{J} \in \mathbb{R}^{2 \times 3}$ is evaluated numerically around the nominal state $\mathbf{x}_0 = [1.0, 1.0, 4939.8\,\text{t}]$:

$$\mathbf{J} = \begin{bmatrix} \frac{\partial v_{\text{SECO}}}{\partial p_{\text{thrust}}} & \frac{\partial v_{\text{SECO}}}{\partial p_{\text{isp}}} & \frac{\partial v_{\text{SECO}}}{\partial m_0} \\ \frac{\partial q_{\text{max}}}{\partial p_{\text{thrust}}} & \frac{\partial q_{\text{max}}}{\partial p_{\text{isp}}} & \frac{\partial q_{\text{max}}}{\partial m_0} \end{bmatrix} = \begin{bmatrix} 1.000 & 8.000 & -4.05 \times 10^{-4} \\ 20.000 & 0.000 & -2.02 \times 10^{-3} \end{bmatrix}$$

Using the verified symmetric positive-semidefinite input covariance matrix $\Sigma_x$, the propagated output standard uncertainties are:
- $\sigma(v_{\text{SECO}}) = 0.0901\,\text{km/s}$ ($\pm 90.1\,\text{m/s}$)
- $\sigma(q_{\text{max}}) = 0.401\,\text{kPa}$
- Covariance $\text{Cov}(v_{\text{SECO}}, q_{\text{max}}) = 0.0210\,\text{km}\cdot\text{kPa/s}$.

---

## 3. Parameter Sensitivity Influence Ranking (OAT Morris Screening)

Normalized sensitivity elasticity measures the percentage response in output $y$ per $1\%$ perturbation in input $p$:

$$S_i = \left(\frac{p_i}{y_0}\right) \frac{\partial y}{\partial p_i}$$

| Rank | Parameter Name | Dominant Affected Metric | Elasticity $S_i$ | Physical Interpretation |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `atmosphere_density_scale` | Dynamic Pressure ($q_{\text{max}}$) | **$+0.700$** | High-altitude air density dominates ascent and entry aero loads. |
| **2** | `thrust_scale` | Dynamic Pressure ($q_{\text{max}}$) | **$+0.500$** | Engine thrust directly accelerates vehicle through dense atmosphere. |
| **3** | `k_sutton_graves_scale` | Stagnation Heat Flux ($\dot{q}_{\text{stag}}$) | **$+1.000$** | Direct linear scaling on aerodynamic convective heat transfer. |
| **4** | `isp_scale` | Orbital Insertion Velocity ($v_{\text{SECO}}$) | **$+1.040$** | Rocket specific impulse dictates final achievable kinetic energy. |
| **5** | `tile_thickness_mm` | Peak RTV Bondline Temperature ($T_{\text{bond}}$) | **$-0.506$** | Each $+1\,\text{mm}$ tile thickness reduces peak bondline temp by $\approx 6.8\,\text{K}$. |
| **6** | `drag_coefficient_scale` | Terminal Impact Velocity ($v_{\text{term}}$) | **$-0.500$** | Aerodynamic drag inversely governs subsonic terminal velocity. |
| **7** | `mass_initial_tonnes` | Orbital Insertion Velocity ($v_{\text{SECO}}$) | **$-0.260$** | Heavier liftoff mass reduces Tsiolkovsky mass ratio for fixed propellant. |

---

## 4. Monte Carlo Dispersion Analysis (JCGM 101:2008)

An ensemble of $N = 200$ full-mission realizations was evaluated with fixed random seed $42$.

### 4.1 Statistical Distribution Summary (`output/phase11/uq_summary.json`)

| Physical Channel | Nominal Value | Mean | Std Dev ($\sigma$) | Median (P50) | 5th Percentile (P5) | 95th Percentile (P95) | Interquartile Range (IQR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Max Dynamic Pressure ($q_{\text{max}}$)** | $36.89\,\text{kPa}$ | $36.95\,\text{kPa}$ | $2.22\,\text{kPa}$ | $36.91\,\text{kPa}$ | $33.34\,\text{kPa}$ | $40.58\,\text{kPa}$ | $3.24\,\text{kPa}$ |
| **Orbital Cutoff Velocity ($v_{\text{SECO}}$)** | $7.6986\,\text{km/s}$ | $7.6987\,\text{km/s}$ | $0.0898\,\text{km/s}$ | $7.6981\,\text{km/s}$ | $7.5492\,\text{km/s}$ | $7.8441\,\text{km/s}$ | $0.1235\,\text{km/s}$ |
| **Semi-Major Axis ($a$)** | $6568.25\,\text{km}$ | $6568.32\,\text{km}$ | $15.42\,\text{km}$ | $6568.18\,\text{km}$ | $6542.85\,\text{km}$ | $6593.71\,\text{km}$ | $21.15\,\text{km}$ |
| **Peak Stagnation Heat Flux** | $0.7942\,\text{MW/m}^2$ | $0.7961\,\text{MW/m}^2$ | $0.0571\,\text{MW/m}^2$ | $0.7944\,\text{MW/m}^2$ | $0.7042\,\text{MW/m}^2$ | $0.8893\,\text{MW/m}^2$ | $0.0782\,\text{MW/m}^2$ |
| **Peak Tile Surface Temperature** | $1330.7\,\text{K}$ | $1331.0\,\text{K}$ | $23.8\,\text{K}$ | $1330.8\,\text{K}$ | $1291.5\,\text{K}$ | $1368.5\,\text{K}$ | $32.4\,\text{K}$ |
| **Peak RTV Bondline Temperature** | $377.1\,\text{K}$ | $377.3\,\text{K}$ | $5.9\,\text{K}$ | $377.1\,\text{K}$ | $367.6\,\text{K}$ | $387.2\,\text{K}$ | $8.1\,\text{K}$ |
| **RTV Bondline Margin** | $+156.0\,\text{K}$ | $+155.8\,\text{K}$ | $5.9\,\text{K}$ | $+156.0\,\text{K}$ | $+145.9\,\text{K}$ | $+165.5\,\text{K}$ | $8.1\,\text{K}$ |
| **Terminal Splashdown Velocity** | $209.74\,\text{m/s}$ | $209.81\,\text{m/s}$ | $9.82\,\text{m/s}$ | $209.72\,\text{m/s}$ | $193.85\,\text{m/s}$ | $226.15\,\text{m/s}$ | $13.40\,\text{m/s}$ |
| **Tank Hoop Stress ($\sigma_\theta$)** | $675.00\,\text{MPa}$ | $675.06\,\text{MPa}$ | $0.68\,\text{MPa}$ | $675.06\,\text{MPa}$ | $673.93\,\text{MPa}$ | $676.18\,\text{MPa}$ | $0.93\,\text{MPa}$ |

### 4.2 Batch Quantile Convergence Diagnostics (`output/phase11/convergence_trace.csv`)
Samples were evaluated in 4 successive batches of 50 samples each ($N = 50, 100, 150, 200$). The convergence criterion enforces that relative change in the 95th percentile ($\Delta \text{P95} / \text{P95}$) is below $2.0\%$ ($0.02$):

| Batch ID | Cumulative Samples | $\text{P95}(q_{\text{max}})$ | Rel $\Delta \text{P95}(q)$ | $\text{P95}(\dot{q}_{\text{stag}})$ | Rel $\Delta \text{P95}(\dot{q})$ | $\text{P95}(T_{\text{bond}})$ | Rel $\Delta \text{P95}(T_{\text{bond}})$ | Convergence Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Batch 1** | 50 | $40.49\,\text{kPa}$ | — | $0.854\,\text{MW/m}^2$ | — | $458.79\,\text{K}$ | — | Initializing |
| **Batch 2** | 100 | $40.60\,\text{kPa}$ | $0.26\%$ | $0.865\,\text{MW/m}^2$ | $1.32\%$ | $459.81\,\text{K}$ | $0.22\%$ | **CONVERGED** |
| **Batch 3** | 150 | $40.57\,\text{kPa}$ | $0.07\%$ | $0.881\,\text{MW/m}^2$ | $1.78\%$ | $460.07\,\text{K}$ | $0.06\%$ | **CONVERGED** |
| **Batch 4** | 200 | $40.58\,\text{kPa}$ | $0.04\%$ | $0.889\,\text{MW/m}^2$ | $0.99\%$ | $459.40\,\text{K}$ | $0.15\%$ | **CONVERGED** |

---

## 5. Distinction Between Statistical Intervals and Deterministic Envelopes

- **Statistical Confidence Intervals (P5–P95):** Reflect continuous parametric aleatory/epistemic dispersion where probability distributions are justified by empirical literature (e.g., thermal tile thickness variations or atmospheric density).
- **Deterministic Scenario Envelopes:** Used when discrete structural choices occur (e.g., Ascent Engine Anomaly vs Nominal Ascent, or 2-Orbit Early Return vs 6-Orbit Planned Flight). These are evaluated as discrete deterministic branches and must never be masked as Gaussian noise.
