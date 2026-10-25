# Phase 4 Source Brief: Aerodynamic Separation, Multibody Dynamics, and Mission Grounding

**Document ID:** `DOC-P4-SB-001`  
**Classification:** Research Synthesis & Technical Evidence Base  
**Status:** APPROVED / BASELINE  
**Author:** Aerospace Simulation Verification Lead & Flight Dynamics Specialist  
**Project:** Starship Flight 14 Digital Engineering Lab  

---

## 1. Executive Summary & Purpose

This source brief synthesizes the technical literature and independent observational reporting governing **Phase 4: Stage Separation, Relative Motion Dynamics, and Mission Event Reconciliation**. 

Rather than relying on generic rocket animations or unverified claims, this document establishes the mathematical, fluid-dynamic, computational, and observational boundaries for our reconstruction. It directly grounds the transition from a combined single-stack vehicle to two independently propagating 3-DOF bodies (Super Heavy Booster Stage 1 and Starship Stage 2).

---

## 2. Ingested Evidence Base (Sources F4-01 through F4-08)

### 2.1 Source F4-01: NASA Two-Stage Reusable Launch Vehicle Separation (2007)
- **Title:** *Simulation and Analyses of Stage Separation of Two-Stage Reusable Launch Vehicles* (NASA/TM-2008-215118 / NTRS 20080000856).
- **Authors & Organization:** Dr. Jeremy T. Pinier et al., NASA Langley Research Center.
- **Key Methodologies:**
  - Employs a 6-DOF simulation framework coupled with static and proximity aerodynamic databases derived from extensive wind-tunnel testing.
  - Varies vehicle mass properties, center-of-gravity locations, flight-path angles, altitude, and separation impulses.
  - Demonstrates that stage separation is heavily governed by proximity aerodynamic interactions (shock impingement, mutual interference, and wake ingestion) when dynamic pressure $q_\infty > 0.1\,\text{kPa}$.
  - Uses Monte Carlo dispersion analyses to establish safe separation corridors.
- **Applicability & Boundary to Starship Flight 14:**
  - **Methodology Reference Only:** The specific vehicle geometry (biconic/winged orbiter on winged booster) and aerodynamic coefficients cannot be transferred to the Starship/Super Heavy axisymmetric hot-staging geometry.
  - **Implication:** Establishes that relative motion cannot be treated as simple kinematics; however, because proximity aerodynamic matrices for Starship are proprietary, our desktop simulation must explicitly declare its aerodynamic fidelity boundaries.

### 2.2 Source F4-02: NASA Starship Hot Staging CFD (HECC / SC24 / HECC_11-24.pdf)
- **Title:** *SpaceX Starship Hot Staging — From Concept to Flight*.
- **Authors & Organization:** Dr. Derek Liechty & NASA High-End Computing Capability (HECC) Project Office, NASA Ames Research Center.
- **Key Methodologies:**
  - Conducted high-performance computational fluid dynamics (CFD) using the compressible Navier-Stokes solver `Loci/CHEM`.
  - Solved time-accurate moving-body overset grids exceeding 500 million grid cells.
  - Consumed over 40 million CPU hours on the NASA Pleiades supercomputer.
  - Analyzed the intense plume impingement from Starship's three sea-level and three vacuum Raptor engines blasting onto the Super Heavy forward dome and through the slotted hot-staging interstage ring.
- **Applicability & Boundary to Starship Flight 14:**
  - **Fidelity Ceiling Definition:** Proves conclusively that high-fidelity hot-staging plume interaction, dome overpressure, and mutual gas-dynamic forces cannot be computed on desktop workstations.
  - **Implication:** Our Phase 4 model must be categorized strictly as **L1 (3-DOF Point-Mass Separation Dynamics)**. We must explicitly reject any claim that a desktop simulation has "validated" hot-staging plume aerodynamics or dome thermal/pressure loads.

### 2.3 Source F4-03: NASA Ares I Separation Aerodynamics (SC11 Demo 6)
- **Title:** *Powered Stage Separation Aerodynamics of the Ares I Launch Vehicle*.
- **Authors & Organization:** Stuart E. Rogers et al., NASA Advanced Supercomputing Division (NAS).
- **Key Methodologies:**
  - Investigated transient aerodynamic flowfields and separation motor plume interactions during stage separation of the Ares I crew launch vehicle.
  - Utilized time-dependent chimera overset grid systems and unsteady Navier-Stokes equations to track booster tumbling and stage deceleration.
- **Applicability & Boundary to Starship Flight 14:**
  - **Methodological Reference:** Confirms the sensitivity of separating stages to thrust tail-off transients, motor ignition transients, and wake effects.
  - **Implication:** Highlights that discrete event boundaries (e.g. booster throttle cut to 40%, Ship ignition ramp) must be modeled with clear temporal segmentation.

### 2.4 Source F4-04: NASA Constraint Force Multibody Formulation (2016)
- **Title:** *Development of Constraint Force Equation Methodology for Application to Multi-Body Dynamics Including Launch Vehicle Stage Separation* (NASA/TP-2016-218221).
- **Authors & Organization:** Eric L. Stewart, NASA Marshall Space Flight Center (MSFC).
- **Key Methodologies:**
  - Formulates constraint force equations using Lagrange multipliers to transition smoothly from mechanically locked kinematic constraints to free-flight independent bodies.
  - Eliminates artificial numerical stiffness that arises from high-spring-rate penalty contact methods.
- **Applicability & Boundary to Starship Flight 14:**
  - **Kinematic Formulation Reference:** Informs our state split architecture: at $T = T_{\text{stage}}$, the single constraint state vector $\mathbf{X}_{\text{stack}}$ is decomposed into $\mathbf{X}_{\text{booster}}$ and $\mathbf{X}_{\text{ship}}$ while enforcing exact conservation of linear momentum and mass continuity.

### 2.5 Source F4-05: Reuters Actual Flight 14 Outcome (September 28–29, 2026)
- **Title:** *SpaceX's Starship makes orbital debut deploying Starlinks before early ending*.
- **Journalist & Organization:** Joey Roulette, Reuters Commercial Spaceflight Bureau.
- **Key Empirical Observations:**
  - Launch took place successfully from Starbase, Texas, on September 28, 2026.
  - Reached orbital velocity and executed the first deployment of 26 Starlink V3 operational satellites.
  - Super Heavy booster executed boostback and landing burns, completing a controlled soft splashdown in the Gulf of Mexico.
  - Upper stage Starship experienced a premature engine anomaly / early shutdown during orbit operations, truncating the nominal 10-hour profile to approximately 3 hours.
  - Starship performed a controlled entry and splashed down in the Pacific Ocean north of Hawaii.
- **Applicability & Boundary to Starship Flight 14:**
  - **Ground Truth for Flown Timeline:** Mandates that our mission architecture distinguish between the preflight planned 10-hour profile and the actual flown 3-hour profile.

### 2.6 Source F4-06: SpaceX Flight 14 Preflight Mission Profile
- **Title:** *Starship's Fourteenth Flight Test Pre-Flight Mission Overview*.
- **Organization:** SpaceX Mission Operations.
- **Key Intended Parameters:**
  - Liftoff from Starbase orbital pad.
  - Nominal hot-staging sequence at $T+2\,\text{min}\,40\,\text{s}$ ($T+160\,\text{s}$) or $T+2\,\text{min}\,22\,\text{s}$ depending on payload mass.
  - Intended booster catch/splashdown and orbital payload door deployment demonstration over a 10-hour circularization/decay trajectory.
- **Applicability & Boundary to Starship Flight 14:**
  - **Nominal Reference Only:** Used to structure the `planned_mission_reference` scenario, but not conflated with the observed anomaly timeline.

### 2.7 Source F4-07: SciPy solve_ivp Numerical Integration Standards
- **Title:** *Integration of Initial Value Problems for Ordinary Differential Equations*.
- **Authors & Organization:** Pauli Virtanen et al., SciPy Core Development Team.
- **Key Algorithmic Rules:**
  - Continuous ODE integration with adaptive step control (Runge-Kutta 4(5) / Dormand-Prince DOP853).
  - Explicit warning: *Event detection is evaluated via zero-crossing root finders ($g(t, y) = 0$). If multiple events or sharp discontinuities occur within a single solver internal step, crossings will be missed or cause numerical instability.*
- **Applicability & Boundary to Starship Flight 14:**
  - **Segmented Integration Requirement:** Trajectory propagation cannot be run as a single blind `solve_ivp` call across stage separation. The integration must stop at $T_{\text{stage}}$, execute the algebraic mass and momentum handoff, and instantiate two independent propagators for Booster and Ship.

### 2.8 Source F4-08: FreeCAD Assembly Workbench & Kinematics
- **Title:** *FreeCAD Assembly Workbench Documentation & Create Simulation Reference*.
- **Authors & Organization:** FreeCAD Project Team & Ondsel Open Source Engineering.
- **Key Capabilities:**
  - Solves geometric kinematic joints (Revolute, Prismatic, Fixed, Cylindrical) via the Ondsel solver.
  - `Create Simulation` provides frame-by-frame joint degree-of-freedom animation.
- **Applicability & Boundary to Starship Flight 14:**
  - **Visualization Only:** Confirms that FreeCAD Assembly is a kinematic mechanism viewer, not a flight dynamics integrator. Trajectory motion must be computed in Python/SciPy and imported as coordinate placements.

---

## 3. Summary of Engineering Constraints Imposed on Phase 4

| Domain | Engineering Requirement | Reference Source | Implementation Rule |
| :--- | :--- | :--- | :--- |
| **Separation Fidelity** | Must declare simulation as L1 3-DOF point-mass | F4-02, F4-03 | Reject any claim of desktop CFD plume validation |
| **Metrics Terminology** | Distance between COMs is `center_range_m` | F4-01, F4-04 | Do not label COM distance as `min_surface_clearance_m` |
| **Mass Bookkeeping** | Stack mass = Booster mass + Ship mass | F4-04 | Enforce strict algebraic mass conservation at split |
| **Momentum Conservation**| Internal impulse must yield equal & opposite momentum | F4-04 | Verify $\Delta (m_1 \mathbf{v}_1 + m_2 \mathbf{v}_2) = \mathbf{0}$ |
| **Solver Architecture** | Segment integration at discrete staging events | F4-07 | Avoid discontinuous step failures in `solve_ivp` |
| **Mission Traceability** | Separate flown reconstruction from planned profile | F4-05, F4-06 | Tag all datasets with scenario IDs |
| **CAD Integration** | CAD is geometry and kinematic visual replay only | F4-08 | Keep dynamics math strictly in Python/SciPy |
