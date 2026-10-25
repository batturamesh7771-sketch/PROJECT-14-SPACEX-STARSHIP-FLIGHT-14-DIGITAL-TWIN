# Phase 9: Aerothermal Reentry & Thermal Protection System — Limitations and Risks

## 1. Modeling Assumptions and Limitations

| Domain | Assumption / Simplification | Physical Reality & Starship Architecture | Impact on Benchmark Validity |
| :--- | :--- | :--- | :--- |
| **Dimensionality** | 1D through-thickness thermal conduction normal to outer skin. | Real tiles experience 3D heat flow across tile gaps, plasma penetration into tile kerfs, and radiative heat transfer between adjacent tile sidewalls. | 1D analysis accurately represents center-of-tile acreage heating, but gap heating can locally raise corner/edge temperatures. |
| **Catalycity & Chemistry** | Equilibrium / standard Sutton-Graves convective coefficient ($C_{\text{sg}}$). | Hypersonic dissociative shock layer ($v \approx 7\,\text{km/s}$) creates non-equilibrium $N, O, NO$ chemistry; catalytic efficiency of RCG coating governs recombination heating. | Partially catalytic RCG coatings reduce heat flux relative to fully catalytic walls. Model provides conservative envelope. |
| **Tile Damage / Loss** | Intact, continuous ceramic tile coverage ($28.0\,\text{mm}$ thickness everywhere). | Flight observations reveal tile shedding, plasma burn-through, flap hinge gap plasma ingress, and tile chipping during dynamic flight. | Tile loss exposes bare stainless steel to direct aerothermal heating ($> 1600\,\text{K}$), potentially exceeding steel melting point ($1670\,\text{K}$). |
| **Internal Fluid Cooling** | Adiabatic backface boundary on inner tank skin. | Internal ullage gas and remaining cryogenic landing propellants (header tanks) act as heat sinks. | Adiabatic boundary provides an engineering upper-bound on structural steel temperatures (worst-case heat soak). |

---

## 2. Engineering Risk Register

| Risk ID | Severity | Likelihood | Risk Description | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-THM-01** | Critical | Medium | Tile loss or detachment exposing steel skin to hypersonic plasma stream. | Implement mechanical tile locking pins and secondary ceramic backup blanket layers beneath tiles. |
| **RSK-THM-02** | High | Medium | Plasma ingress into forward flap hinge seal gaps during peak pitch maneuver. | Install active seal purges and high-temperature inconel/cobalt superalloy seal barriers. |
| **RSK-THM-03** | High | Low | RTV adhesive degradation ($T_{\text{bond}} > 260^\circ\text{C}$) during extended atmospheric coast before flip. | Maintain minimum tile thickness $> 22\,\text{mm}$ to guarantee $> 100\,\text{K}$ thermal margin. |
| **RSK-THM-04** | Medium | Medium | Non-uniform atmospheric density waves increasing peak heat flux by $> 20\%$. | Design thermal protection systems with $> 1.4$ thermal safety factor above nominal US 1976 baseline. |
