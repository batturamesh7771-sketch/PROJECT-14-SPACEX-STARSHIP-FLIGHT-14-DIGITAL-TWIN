# Starship Flight 14 Digital Engineering Lab — Phase 6 Limitations and Risk Register

**Document ID:** `DOC-P6-LIMITATIONS-RISKS-001`  
**Phase:** 6 — Atmospheric Reentry, Hypersonic Aerodynamics, Aerothermal Heating, Guidance, and Splashdown Assessment  
**Classification:** Digital Engineering Technical Limitations & System Risk Assessment  
**Baseline Git Commit Target:** Phase 6 Final  

---

## 1. Scope and Modeling Fidelity Limitations

This simulation is an independent, physics-based, open-data digital engineering model designed to explore hypersonic reentry dynamics, deceleration regimes, Sutton-Graves aerothermal heating, and trajectory guidance. The following explicit engineering boundaries define the limits of applicability:

### 1.1 3-DOF Point-Mass vs. 6-DOF Rigid-Body Dynamics
- **Current Model:** Implements a 3-Degree-of-Freedom (3-DOF) point-mass translational dynamic model ($x, y, z, \dot{x}, \dot{y}, \dot{z}$). Aerodynamic attitude is parameterized through trim angle of attack ($\alpha = 70^\circ$) and aerodynamic roll/bank angle ($\sigma$).
- **Limitation:** Does not solve 6-DOF rotational equations of motion (Euler angles, body rates, moments of inertia, center-of-pressure vs. center-of-mass shifts). Body stabilization and flap hinge moments are assumed to possess sufficient control power to maintain commanded trim.
- **Flight Reality:** Starship actively modulates four body flaps (two forward, two aft) to balance aerodynamic moments, manage cross-axis trim, and control pitch/roll/yaw attitude against dynamic pressures exceeding $60\,\text{kPa}$.

### 1.2 Continuum Aerodynamics vs. Rarefied Flow Regime
- **Current Model:** Employs modified Newtonian cross-flow aerodynamic theory blended with subsonic cross-flow coefficients across all atmospheric layers down to sea level.
- **Limitation:** Between $86\,\text{km}$ and $120\,\text{km}$, the Knudsen number exceeds $Kn > 0.01$, placing the vehicle in the transitional and free-molecular flow regimes where continuum gas dynamic assumptions degrade.
- **Consequence:** Aerodynamic drag and lift forces at the entry interface ($h = 100\text{--}120\,\text{km}$) are small ($\sim 0.001\text{--}0.1\,\text{N}$) and have minimal cumulative effect on the trajectory; however, exact aerodynamic control surfaces are ineffective in this regime without Reaction Control System (RCS) cold/hot gas thrusters.

### 1.3 Aerothermodynamics & Surface Heat Shield Modeling
- **Current Model:** Convective heat flux is evaluated using the classical Sutton-Graves stagnation correlation ($k_{\text{SG}} = 1.7415 \times 10^{-4}\,\text{W}\cdot\text{s}^3/(\text{m}^{3.5}\cdot\text{kg}^{0.5})$) with an effective nose radius $R_n = 4.5\,\text{m}$. Outer mold line (OML) wall temperature is evaluated via gray-body radiative equilibrium ($\epsilon = 0.85$).
- **Limitation:**
  1. Does not solve compressible Navier-Stokes or DSMC equations with chemical non-equilibrium (air dissociation into $\text{N}, \text{O}, \text{NO}^+$ ions).
  2. Neglects radiative gas heating from the shock layer, which becomes non-trivial above $v > 7.5\,\text{km/s}$.
  3. Does not model transient 1D/2D thermal conduction through the ceramic Thermal Protection System (TPS) tile thickness into the underlying 304L/300-series stainless steel tank walls.
  4. Does not model localized gap heating, plasma impingement between tile joints, or vehicle flap seal heating.

### 1.4 Atmospheric Environment Model
- **Current Model:** US Standard Atmosphere 1976 with a continuous thermospheric continuum extension up to $150\,\text{km}$.
- **Limitation:** Represents an idealized, globally averaged, static non-rotating atmosphere. Real-world upper atmospheric density exhibits diurnal tides, solar EUV flux variations ($F_{10.7}$ index), geomagnetic storms, and latitude-dependent seasonal shifts of up to $\pm 25\text{--}50\%$.

### 1.5 Terminal Phase & Recovery Boundaries
- **Current Model:** Trajectory integration terminates upon detecting ellipsoid surface datum ($h = 0\,\text{m}$ WGS-84).
- **Limitation:**
  1. The simulation does NOT model the terminal subsonic belly-flop pitch-up maneuver ("flip maneuver").
  2. Does NOT model Raptor center-engine chill, relight, gimbaling, or propulsive landing deceleration burn.
  3. Impact at sea level occurs at aerodynamic terminal velocity ($v_{\text{rel}} \approx 208\text{--}210\,\text{m/s}$); surface intersection does not imply soft ocean recovery or structural survival.

---

## 2. Engineering Risk Assessment Matrix

| Risk ID | Failure / Dispersion Mode | Physical Mechanism | Simulated Sensitivity | Mitigation in Real Flight / Simulation |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-P6-01** | **Steep Entry Angle ($\gamma < -1.5^\circ$)** | Over-aggressive deorbit burn lowers perigee excessively, causing steep entry. | Peak $g$-load increases beyond $6.5\,\text{g}$; peak heat flux exceeds $1.5\,\text{MW/m}^2$. | Precision closed-loop deorbit burn guidance with ground tracking verification. |
| **RSK-P6-02** | **Shallow Entry Skip ($\gamma > -0.4^\circ$)** | Insufficient deorbit $\Delta v$ causes skip-out back into elliptical orbit with high perigee. | Inability to capture in atmosphere; delayed orbit decay over days/months. | Mandatory disposal margin ensuring perigee $< -50\,\text{km}$. |
| **RSK-P6-03** | **Aerodynamic Tile Stripping / Gap Heating** | Hypersonic shear stresses and vibrations detach windward ceramic tiles. | Heat load enters bare stainless steel tank, risking burn-through. | Secondary thermal blanket barrier and high melting point ($1400^\circ\text{C}$) of stainless steel structure. |
| **RSK-P6-04** | **Flap Actuator Saturation / Rate Limit** | Extreme dynamic pressure ($q > 65\,\text{kPa}$) exceeds hydraulic/electric actuator torque limit. | Vehicle loses roll/yaw trim; uncontrollable bank angle drift. | Aerodynamic load relief; vehicle trim modulation to keep hinge moments within bounds. |
| **RSK-P6-05** | **Atmospheric Density Dispersion (Solar Storm)** | Elevated thermospheric density shifts deceleration peak higher and earlier. | Terminal impact occurs several tens of kilometers downrange of nominal target. | Real-time adaptive bank angle guidance with energy-altitude tracking. |
| **RSK-P6-06** | **Ballistic Impact Without Landing Burn** | Engine relight failure during terminal flip maneuver. | Vehicle strikes water at terminal velocity ($\sim 210\,\text{m/s}$), causing total structural breakup. | Modeled realistically as high-speed splashdown; no false claim of recovery. |

---

## 3. Usage Guidelines for Downstream Phases

1. **CAD / Structural Load Handoff:** Use peak dynamic pressure ($q_{\text{dyn,max}} = 68.26\,\text{kPa}$) and peak deceleration ($a_{\max} = 3.23\,\text{g}$) as limit load cases for structural verification and flap hinge torque requirements.
2. **Thermal Analysis Handoff:** Use cumulative stagnation heat load ($Q_{\text{stag}} \approx 240.67\,\text{MJ/m}^2$) and peak flux ($\dot{q}_{\text{stag}} = 0.794\,\text{MW/m}^2$) to size insulation thickness and tile bond line temperatures.
3. **Trajectory & Range Safety:** Ensure exclusion corridors account for the $3\sigma$ Monte Carlo dispersion ellipse ($\sim 75\,\text{km}$ semi-major axis) around the splashdown target.
