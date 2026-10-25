# Phase 8: Propellant Tank Structural FEA Benchmark — Limitations and Risks

## 1. Modeling Assumptions and Limitations

| Domain | Assumption / Simplification | Physical Reality & Starship Architecture | Impact on Benchmark Validity |
| :--- | :--- | :--- | :--- |
| **Material Plasticity** | Linear elastic isotropic Hookean behavior ($E = 193\,\text{GPa}, \nu = 0.29$). | Real stainless steel exhibits non-linear hardening, yielding, and plastic flow beyond $\sim 500\,\text{MPa}$. | Conservative for design stress estimation below yield; overpredicts stress if local yielding relieves stress concentrations. |
| **Geometry** | Smooth, uniform cylindrical barrel section ($t = 4.0\,\text{mm}$ constant). | Real tanks feature longitudinal roll-welds, circumferential ring welds, weld beads, heat-affected zones (HAZ), and ring stiffeners. | High-frequency stress peaks at weld seams are not captured in the global membrane benchmark. |
| **Dome & Knuckle Junctions** | Clamped/restrained edge ring with Hetenyi attenuation decay. | Real tanks interface with torispherical or ellipsoidal dome knuckles that share bending moments. | Hetenyi edge attenuation accurately models the characteristic decay length ($\lambda = 32.7\,\text{cm}$), but full dome geometry requires 3D solid/shell junction modeling. |
| **Temperature Profile** | Uniform room temperature ($293\,\text{K}$). | Tank exterior experiences ambient/aerodynamic heating while interior holds liquid methane ($112\,\text{K}$) or oxygen ($90\,\text{K}$). | Thermal gradients generate through-thickness thermal stresses ($\sigma_{\text{th}} = \frac{E \alpha \Delta T}{1 - \nu}$), which are superimposed on pressure stresses. |
| **Hydrostatic Fluid Head** | Uniform internal pressure ($p = 6.0\,\text{bar}$ throughout cylinder). | Full propellant load ($1200\,\text{t}$) under $3\,\text{g}$ acceleration adds hydrostatic pressure gradient ($\Delta p = \rho g_{\text{eff}} h$). | Peak pressure is higher at the bottom dome than at the upper ullage space. |

---

## 2. Engineering Risk Register

| Risk ID | Severity | Likelihood | Risk Description | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-FEA-01** | High | Low | Plastic rupture under proof pressurization ($8.5\,\text{bar}$). | Verify cold-worked yield strength ($\sigma_y > 800\,\text{MPa}$) and cryogenic strengthening prior to proof tests. |
| **RSK-FEA-02** | High | Medium | Elastic-plastic compressive buckling during max-Q acceleration if ullage pressure decays below $2.0\,\text{bar}$. | Maintain redundant autogenous pressurization systems; confirm NASA SP-8007 pressure stabilization margins. |
| **RSK-FEA-03** | Medium | Medium | Weld seam fatigue and stress concentration at longitudinal weld joints. | Include weld seam knock-down factors ($J_w = 0.85\text{--}0.90$) in production margin assessments. |
| **RSK-FEA-04** | Low | Low | Solver divergence or hourglassing in reduced-integration shell elements (S4R). | Enforce physical hourglass stiffness controls and benchmark against full integration (SHELL181 KEYOPT(3)=2). |
