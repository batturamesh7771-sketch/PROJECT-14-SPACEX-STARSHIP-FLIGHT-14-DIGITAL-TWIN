# Phase 9: Aerothermal Reentry & Thermal Protection Model — Initial Inspection

## 1. Inspection Context & Objectives

**Phase:** 9 (Aerothermal Reentry & Thermal Protection System Model)  
**Parent Roadmap:** `docs/implementation_roadmap.md` (Lines 208–227)  
**Traceability ID:** `REQ-THM-001` (`docs/requirements_traceability.csv`)  
**Baseline Git Commit:** `f44e320` (Phase 8 Structural FEA completed and verified)

---

## 2. Input Trajectory Verification

Phase 9 consumes hypersonic reentry trajectory states generated in Phase 6:
- **Trajectory Source:** `output/phase6/entry_trajectory.csv`
- **Data Points:** 933 rows spanning $t = 0.0\,\text{s}$ to $t = 932.0\,\text{s}$ ($15.5\,\text{min}$).
- **Entry Interface Conditions:**
  - Initial Altitude: $120.2\,\text{km}$
  - Initial Velocity: $7.356\,\text{km/s}$ (Mach 17.8)
  - Flight Path Angle: $\gamma_0 \approx -0.75^\circ$
  - Atmospheric Density: US 1976 Standard Atmosphere ($3.44 \times 10^{-8}\,\text{kg/m}^3$ at $120\,\text{km}$, rising to $> 0.1\,\text{kg/m}^3$ at $20\,\text{km}$)
  - Angle of Attack: $\alpha = 40.0^\circ$ nominal hypersonic windward pitch.

---

## 3. Structural & Thermal Stack Configuration

The thermal protection system (TPS) installed on the windward side of Starship consists of:
1. **Ceramic Tile (Reaction-Cured Glass Coated Porous Fibrous Silica):**
   - Thickness: $L_{\text{tile}} = 28.0\,\text{mm}$ ($0.028\,\text{m}$)
   - Bulk Density: $\rho_{\text{tile}} \approx 190.0\,\text{kg/m}^3$
   - Surface Emissivity: $\varepsilon = 0.85$
   - Temperature Limits: $T_{\text{max,reusable}} \approx 1650\,\text{K}$ ($1377^\circ\text{C}$), $T_{\text{max,single}} \approx 1850\,\text{K}$
2. **Strain Isolation Pad (SIP) & RTV Silicone Adhesive Layer:**
   - Thickness: $L_{\text{sip}} = 2.5\,\text{mm}$ ($0.0025\,\text{m}$)
   - Bulk Density: $\rho_{\text{sip}} \approx 250.0\,\text{kg/m}^3$
   - Critical Adhesive Limit: $T_{\text{bond,limit}} = 533.15\,\text{K}$ ($260^\circ\text{C} = 500^\circ\text{F}$)
3. **Stainless Steel Tank Wall (AISI 304L Cold-Rolled Substrate):**
   - Thickness: $L_{\text{steel}} = 4.0\,\text{mm}$ ($0.004\,\text{m}$)
   - Bulk Density: $\rho_{\text{steel}} = 7900.0\,\text{kg/m}^3$
   - Specific Heat: $c_{p,\text{steel}} = 500.0\,\text{J/(kg}\cdot\text{K)}$

---

## 4. Quality Gate Acceptance Thresholds

1. **Gate 1 (Aerothermal Flux):** Sutton-Graves peak stagnation heat flux occurs between $60\,\text{km}$ and $70\,\text{km}$ altitude and reaches $0.8\text{--}1.5\,\text{MW/m}^2$.
2. **Gate 2 (Radiative Equilibrium):** Peak windward surface equilibrium temperature reaches $1400\text{--}1750\,\text{K}$.
3. **Gate 3 (1D Transient Conduction):** Implicit Crank-Nicolson finite difference energy conservation residual $< 10^{-4}$.
4. **Gate 4 (Thermal Soak & Lag):** Bondline peak temperature exhibits physical diffusion delay ($\Delta t_{\text{lag}} > 100\,\text{s}$ after peak aerothermal flux).
5. **Gate 5 (Bondline Margin):** For nominal $28\,\text{mm}$ tile, peak RTV bondline temperature remains below the $533.15\,\text{K}$ limit ($\text{Margin} > 50\,\text{K}$).
6. **Gate 6 (System Regression):** 15 new Phase 9 tests pass; all 158 prior tests pass (173 total tests).
