# STARSHIP FLIGHT 14 DIGITAL ENGINEERING LAB
## PHASE 7 — MODEL ARCHITECTURE & DYNAMICS FORMULATION

**Document ID:** `DOC-P7-ARCH-001`  
**Revision:** 1.0.0  
**Date:** 2026-10-25  
**Classification:** Engineering Specification Document  
**Target Package:** `src/landing/`  
**Target CLI:** `src/phase7.py`  

---

### 1. Architectural Overview & Fidelity Ladder

Phase 7 implements a state-driven, physically coupled simulation of terminal landing dynamics. In accordance with the project guidelines, the simulation avoids speculative high-cell-count CFD or proprietary SpaceX software claims, establishing instead an auditable, modular engineering architecture built on a verified **Fidelity Ladder**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 7 FIDELITY LADDER                              │
├───────┬───────────────────────────────────┬────────────────────────────────┤
│ Level │ Model                             │ Primary Purpose & Scope        │
├───────┼───────────────────────────────────┼────────────────────────────────┤
│  L0   │ Discrete Event State Machine &    │ Logical event transitions,     │
│       │ Kinematic Visualization           │ continuous root-finding contact│
├───────┼───────────────────────────────────┼────────────────────────────────┤
│  L1   │ Planar 2D/3-DOF Translation       │ Gravity, drag, thrust vector,  │
│       │ with Prescribed Kinematic Flip    │ variable mass, throttle bounds │
├───────┼───────────────────────────────────┼────────────────────────────────┤
│  L2   │ Planar Translation + Rotational   │ Torque balance, pitch inertia, │
│       │ Pitch Dynamics                    │ TVC gimbal moment, flap torque │
├───────┼───────────────────────────────────┼────────────────────────────────┤
│  L3   │ 6-DOF Rigid-Body Dynamics         │ Deferred/Optional extension    │
│       │ (Quaternions + Full Inertia)      │ pending measured inertia/aero  │
└───────┴───────────────────────────────────┴────────────────────────────────┘
```

The minimum baseline deliverable is **L1 Translation with Prescribed Kinematic Flip**, accompanied by an independently selectable **L2 Planar Pitch Dynamics Mode**.

---

### 2. Coordinate System & Sign Conventions

All landing dynamics are computed in a **Local Terminal Frame (LTF)** centered at the target landing pad:
- **Origin ($O_{\text{LTF}}$):** Target touchdown point ($z = 0\,\text{m}$, ground/ocean surface datum).
- **$z$-axis:** Local vertical, pointing upward away from Earth's center ($+z = \text{altitude}$).
- **$x$-axis:** Horizontal downrange in the flight plane ($+x = \text{downrange}$).
- **$y$-axis:** Horizontal crossrange, forming a right-handed orthogonal triad ($\hat{\mathbf{y}} = \hat{\mathbf{z}} \times \hat{\mathbf{x}}$).
- **Pitch Angle ($\theta$):** Rotation angle of the vehicle longitudinal body axis relative to the local vertical:
  - $\theta = 0^\circ$: Vehicle is perfectly vertical (engines pointing straight down, $+z$).
  - $\theta = -90^\circ$: Vehicle is horizontal in belly-flop attitude (heatshield facing oncoming airflow).
  - $\theta = +90^\circ$: Inverted horizontal attitude.
- **Thrust Gimbal Angle ($\delta_{\text{gimbal}}$):** Engine nozzle deflection relative to vehicle centerline:
  - Effective thrust angle in LTF: $\psi = \theta + \delta_{\text{gimbal}}$.
  - Thrust components:
    $$F_{\text{thrust}, z} = T \cos(\psi)$$
    $$F_{\text{thrust}, x} = -T \sin(\psi)$$

---

### 3. Equations of Motion

#### 3.1 Translational Dynamics (L1 & L2)
The translational state vector is $\mathbf{y}_{\text{trans}} = [x, z, v_x, v_z, m]^T$.
$$\frac{dx}{dt} = v_x$$
$$\frac{dz}{dt} = v_z$$
$$\frac{dv_x}{dt} = \frac{F_{\text{aero}, x} + F_{\text{thrust}, x}}{m}$$
$$\frac{dv_z}{dt} = \frac{F_{\text{aero}, z} + F_{\text{thrust}, z}}{m} - g_0$$
$$\frac{dm}{dt} = -\dot{m}_{\text{prop}} = -\frac{T}{I_{\text{sp}} g_0}$$

Where:
- $V_{\text{rel}} = \sqrt{v_x^2 + v_z^2}$ is relative airspeed.
- Dynamic pressure: $q = \frac{1}{2} \rho(z) V_{\text{rel}}^2$.
- Aerodynamic Drag magnitude: $D = q C_D(\alpha) A_{\text{ref}}$, opposing the velocity vector.
- Aerodynamic Lift magnitude: $L = q C_L(\alpha) A_{\text{ref}}$, perpendicular to velocity vector.
- Total aerodynamic force vector in LTF:
  $$\mathbf{F}_{\text{aero}} = -D \frac{\mathbf{v}}{V_{\text{rel}}} + L \hat{\mathbf{n}}_L$$

#### 3.2 Rotational Pitch Dynamics (L2 Mode)
In L2 mode, the state vector expands to $\mathbf{y} = [x, z, v_x, v_z, m, \theta, \omega_y]^T$, where $\omega_y = \dot{\theta}$:
$$\frac{d\theta}{dt} = \omega_y$$
$$\frac{d\omega_y}{dt} = \frac{M_{\text{total}}}{I_{yy}(m)}$$

The total pitching moment about the center of mass is:
$$M_{\text{total}} = M_{\text{TVC}} + M_{\text{aero}} + M_{\text{control}}$$
- **TVC Moment:** $M_{\text{TVC}} = T \sin(\delta_{\text{gimbal}}) \cdot l_{\text{arm}}$, where $l_{\text{arm}} = x_{\text{CoM}} - x_{\text{gimbal}} \approx 20.0\,\text{m}$.
- **Aerodynamic Moment:** $M_{\text{aero}} = q A_{\text{ref}} L_{\text{ref}} C_m(\alpha)$.
- **Control / RCS Moment:** $M_{\text{control}} = \tau_{\text{cmd}}$, subject to maximum control torque saturation $|\tau_{\text{cmd}}| \le \tau_{\text{max}}$.
- **Pitch Moment of Inertia:** $I_{yy}(m) \approx \frac{1}{12} m (L_{\text{ship}}^2 + 3 R_{\text{ship}}^2)$ scaled dynamically with propellant mass depletion.

---

### 4. Engine, Propulsion & Throttle Model

The landing propulsion system models 3 Center Raptor engines with independent throttle bounds and ignition dynamics:
1. **Ignition Delay:** Following command trigger, an ignition delay $\Delta t_{\text{delay}}$ (nominally $0.5\text{--}1.5\,\text{s}$) elapses during which engines produce zero thrust while propellant lines prime and turbopumps spin up.
2. **Thrust Ramp:** Once ignited, thrust rises continuously according to a quadratic / S-curve ramp over duration $\Delta t_{\text{ramp}}$ (nominally $0.8\,\text{s}$):
   $$T(t) = T_{\text{cmd}} \cdot \sin^2\left(\frac{\pi}{2} \frac{t - t_{\text{ign}}}{\Delta t_{\text{ramp}}}\right) \quad \text{for } t_{\text{ign}} \le t < t_{\text{ign}} + \Delta t_{\text{ramp}}$$
3. **Throttle Limits:** Commanded throttle is strictly bounded between minimum deep-throttle ($40\%$) and maximum landing thrust ($100\%$):
   $$T \in [0.40 \cdot T_{\text{max}}, 1.00 \cdot T_{\text{max}}]$$
4. **Throttle Slew-Rate Limits:** Maximum rate of throttle change: $|\dot{\delta}_{\text{throttle}}| \le 50\% / \text{s}$.
5. **Gimbal Limits:** Maximum TVC deflection $|\delta_{\text{gimbal}}| \le 15.0^\circ$, slew rate $|\dot{\delta}_{\text{gimbal}}| \le 20.0^\circ/\text{s}$.
6. **Propellant Exhaustion:** If usable propellant reaches zero ($m \le m_{\text{dry}} + m_{\text{reserve}}$), thrust cuts to zero immediately.

---

### 5. Guidance and Feedback Controller

The baseline guidance controller regulates altitude and vertical velocity to follow a parabolic deceleration profile to a soft touchdown target:
$$v_{z, \text{target}}(z) = -\sqrt{2 a_{\text{target}} \max(z - z_{\text{standoff}}, 0)} - v_{\text{touchdown}}$$
Where $a_{\text{target}} \approx 12.0\,\text{m/s}^2$ and $v_{\text{touchdown}} = 1.5\,\text{m/s}$.

The commanded vertical thrust is computed via proportional-derivative (PD) feedback:
$$T_{z, \text{cmd}} = m \left(g_0 + a_{\text{target}} + K_p (z_{\text{target}} - z) + K_d (v_{z, \text{target}} - v_z)\right)$$

Simultaneously, the horizontal guidance commands a tilt angle to null out lateral drift:
$$\theta_{\text{tilt, cmd}} = \text{clamp}\left(\frac{K_{p, x} (x_{\text{target}} - x) + K_{d, x} (v_{x, \text{target}} - v_x)}{g_0}, -\theta_{\text{max}}, +\theta_{\text{max}}\right)$$

---

### 6. Event State Machine & Outcome Classification

The simulation executes through an explicit 16-state automaton:

```
[APPROACH] ──► [FLIP_INITIATION] ──► [FLIP_ROTATION] ──► [VERTICAL_ALIGNMENT]
                                                               │
                                                               ▼
[POWERED_DECELERATION] ◄── [THRUST_RAMP] ◄── [ENGINE_IGNITION_PENDING]
         │
         ▼
[TERMINAL_DESCENT] ──► [TOUCHDOWN_EVENT] ──► [POST_CONTACT_ASSESSMENT]
                                                     │
         ┌───────────────────────────────────────────┴───────────────────────────────────────────┐
         ▼                                           ▼                                           ▼
[SUCCESS_CANDIDATE]                          [HARD_IMPACT]                               [ATTITUDE_FAILURE]
(|v_z| <= 3.0 m/s,                           (|v_z| > 5.0 m/s,                           (|theta| > 10.0 deg,
 |v_x| <= 1.5 m/s,                            structural envelope                         tip-over risk)
 |theta| <= 5.0 deg)                          breached)
```

Terminal classifications:
- `SUCCESS_CANDIDATE`: All engineering criteria met (soft landing envelope).
- `HARD_IMPACT`: Surface reached with excessive vertical/lateral velocity.
- `ATTITUDE_FAILURE`: Surface reached with uncorrected tilt angle $> 10^\circ$.
- `PROPELLANT_MARGIN_FAILURE`: Usable propellant exhausted prior to touchdown.
- `MISSED_TARGET`: Touchdown offset from pad exceeds allowed radius ($> 50\,\text{m}$).
- `SIMULATION_ABORTED`: Numerical divergence or invalid state.
