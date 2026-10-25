# Phase 4 Scope & Engineering Assumptions: Stage Separation & Relative Motion

**Document ID:** `DOC-P4-SCO-001`  
**Classification:** Scope & Assumption Baseline  
**Revision:** 1.0  
**Lead:** Flight Dynamics Lead & Systems Architect  

---

## 1. Project Fidelity Level (The Fidelity Ladder)

As established in the Phase 4 research packet, launch vehicle stage-separation models span multiple tiers of fidelity:

| Level | Model Type | What It Establishes | What It CANNOT Establish |
| :--- | :--- | :--- | :--- |
| **L0** | Kinematic Animation | Visual rendering of bodies moving apart | Physical forces, true trajectory, clearance safety |
| **L1** | **3-DOF Translational Point-Mass Split** | **Translational state propagation ($\mathbf{r}_i, \mathbf{v}_i, m_i$), COM range, relative velocity, mass decay** | **Vehicle attitude/tumbling, detailed plume shock interaction, contact forces, true surface clearance** |
| **L2** | 6-DOF Rigid Body Split | Translational + rotational attitude ($q, \boldsymbol{\omega}, \mathbf{I}$), plume impingement moments | Full unsteady fluid dynamics, structural aeroelastic coupling |
| **L3** | Aerodynamic-Coupled Relative Motion | Proximity aerodynamic database interpolation | Generalizability outside wind-tunnel test points |
| **L4** | Time-Accurate Navier-Stokes Moving Body CFD | Detailed transient shock-on-dome pressure, plume venting | Unvalidated physics without multi-million CPU-hour supercomputing |

### Explicit Scope Definition:
**Phase 4 is strictly targeted at Level 1 (L1: 3-DOF Translational Point-Mass Split).**  
Any extension to 6-DOF attitude dynamics is deferred to a future phase once validated mass moments of inertia ($I_{xx}, I_{yy}, I_{zz}$) and aerodynamic moment derivatives ($C_{m\alpha}, C_{mq}$) are available. Under no circumstances will desktop calculations be claimed as L3 or L4 CFD plume validation.

---

## 2. Separation Metrics & Terminology Contract

To prevent confusion between center-to-center distance and physical contact risk, the following naming contract is mandatory across all data files, APIs, and plots:

1. **`center_range_m` ($\|\mathbf{r}_{\text{ship}} - \mathbf{r}_{\text{booster}}\|$):**
   - The Euclidean distance between the declared Centers of Mass of the two vehicles in the common ECI frame.
   - At $t = t_{\text{stage}}^-$, the stack is a rigid body with physical distance between stage COMs of $\approx 73\,\text{m}$.
   - The reported relative separation represents $\Delta r_{\text{COM}}(t) = \|\mathbf{r}_{\text{rel}}(t)\| - \|\mathbf{r}_{\text{rel}}(0)\|$.
2. **`relative_speed_mps` ($\|\mathbf{v}_{\text{ship}} - \mathbf{v}_{\text{booster}}\|$):**
   - Magnitude of the relative velocity vector in the common inertial frame.
3. **`min_surface_clearance_m`:**
   - The minimum distance between the aft heat shield/engine bells of Starship and the forward ring/dome of Super Heavy.
   - In the pure 3-DOF point-mass model, **this value is NOT computed** and must be explicitly recorded as `not_computed` or `null`.
4. **`clearance_method`:**
   - Recorded as `point_mass_translation_only`.

---

## 3. Physical Assumptions & Separation Mechanics

### 3.1 Pre-Separation State Handoff
- The pre-separation state comes continuously from Phase 3 ascent integration at $T = 140.0\,\text{s}$ (Booster MECO).
- Position and velocity are expressed in the Earth-Centered Inertial (ECI J2000) frame:
  $$\mathbf{r}_{\text{stack}}(T_{\text{MECO}}) = [-565,124.8, -5,774,902.1, 2,801,104.5]\,\text{m}$$
  $$\mathbf{v}_{\text{stack}}(T_{\text{MECO}}) = [1,540.2, -1,021.4, 212.8]\,\text{m/s} \quad (v_{\text{rel}} = 1,480.2\,\text{m/s}, v_{\text{inertial}} = 1,861.3\,\text{m/s})$$
  $$h(T_{\text{MECO}}) = 66.81\,\text{km}, \quad q_\infty(T_{\text{MECO}}) = 0.28\,\text{kPa}$$

### 3.2 Hot-Staging Event Sequence (Scenario `flight14_public_reconstruction`)
1. **$T = 140.0\,\text{s}$ (Stage 1 MECO):**
   - 30 outer Raptor engines shut down.
   - 3 center Raptor engines remain throttled at 40% ($F_{\text{center}} \approx 3 \times 2.90 \times 0.40 \approx 3.48\,\text{MN}$) to provide positive forward acceleration and propellant settling ullage for Starship.
2. **$T = 142.0\,\text{s}$ (Hot-Staging Ignition & Mechanical Release):**
   - Starship ignites its 3 Sea-Level and 3 Vacuum Raptor engines.
   - Vented interstage ring allows exhaust gas venting.
   - Super Heavy center engines shut down.
   - Idealized internal separation impulse $J_{\text{sep}} = 0$ (separation driven purely by upper stage thrust and differential aerodynamic drag).
   - Conservative net plume pushback on booster forward dome modeled as an external force $F_{\text{plume}} = 1.90\,\text{MN}$ decaying over a $1.5\,\text{s}$ duration (derived from NASA HECC pressure integral bounds).
3. **$T > 142.0\,\text{s}$ (Independent Propagation):**
   - Super Heavy initiates cold-gas flip, pitch program, and boostback burn at $T+155.0\,\text{s}$ to return to the Gulf of Mexico.
   - Starship Stage 2 accelerates under PEG guidance to orbital insertion at $T+522.35\,\text{s}$.

### 3.3 Mass Conservation Identity
At $T = 140.0\,\text{s}$:
$$m_{\text{stack}}(T) = m_{\text{booster}}(T) + m_{\text{ship}}(T)$$
$$1,678,800\,\text{kg} = 339,825\,\text{kg} + 1,338,975\,\text{kg} \quad (\text{Exact balance})$$
Propellant depletion on both stages proceeds independently following $dm/dt = -\dot{m}_{\text{engines}}$.
