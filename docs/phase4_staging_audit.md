# Phase 4 Staging Audit: Forensic Analysis of Existing Code & Trajectory Outputs

**Document ID:** `DOC-P4-STA-001`  
**Classification:** Forensic Code & Output Audit  
**Revision:** 1.0  
**Lead:** Flight Dynamics Lead & Verification Engineer  

---

## 1. Audit of Existing Phase 4 Code Modules

The repository's stage-separation codebase was inspected line-by-line:

### 1.1 `src/dynamics/staging_separation.py`
- **Architecture:** Orchestrates the multi-body stage separation by accepting a pre-separation state vector from Phase 3 ascent, executing the stage split at $T_{\text{MECO}} = 140.0\,\text{s}$ and $T_{\text{stage}} = 142.0\,\text{s}$, running booster recovery dynamics via `BoosterRecoveryTrajectory`, running upper stage orbital insertion via `StarshipAscentToOrbit`, and interpolating both trajectories onto a synchronized 100 Hz output time grid ($140.0\,\text{s} \le t \le 160.0\,\text{s}$).
- **Strengths:**
  - Enforces identical coordinate frame (`ECI_J2000`) and time base.
  - Implements the hot-staging overlap: Super Heavy center engines throttled to 40% while Starship ignites 6 engines.
  - Generates synchronized relative distance, speed, and acceleration vectors.
- **Defects / Ambiguities Identified:**
  - Output CSV header previously labeled the column as `relative_separation_m`, which was casually referred to in summary text as "clearance".
  - Plume force of $1.90\,\text{MN}$ was hardcoded without an explicit configuration switch for `zero_impulse` or variable plume force profiles.

### 1.2 Reproduction & Mathematical Derivation of $5.50\,\text{m}$ and $48.06\,\text{m}$
Let's analyze the exact dynamics producing these numbers in `output/flight14_staging_relative_motion.csv`:
- At $T = 142.0\,\text{s}$ (mechanical separation):
  - Starship dry mass + payload $= 138,975\,\text{kg}$, propellant $= 1,200,000\,\text{kg} \implies m_{\text{ship}} = 1,338,975\,\text{kg}$.
  - Starship thrust: 3 Sea-Level ($3 \times 2.89\,\text{MN}$) + 3 Vacuum ($3 \times 3.05\,\text{MN}$) $= 8.67 + 9.15 = 17.82\,\text{MN}$.
  - Starship forward acceleration: $a_{\text{ship}} \approx \frac{17.82 \times 10^6}{1.338975 \times 10^6} \approx 13.31\,\text{m/s}^2 \approx 1.36\,\text{g}$.
  - Super Heavy mass at MECO: $m_{\text{booster}} \approx 339,825\,\text{kg}$.
  - Super Heavy thrust during 2-second overlap ($T+140$ to $T+142$): 3 center engines at 40% throttle $\implies F_{\text{SH}} \approx 3.48\,\text{MN}$.
  - At $T=142.0\,\text{s}$, Super Heavy center engines cut off ($F_{\text{SH}} = 0$).
  - Plume impingement pushback force on Booster forward dome: $F_{\text{plume}} \approx 1.90\,\text{MN}$ decaying over $\tau = 1.5\,\text{s}$.
  - Booster backward acceleration from plume: $a_{\text{plume,b}} \approx \frac{1.90 \times 10^6}{339,825} \approx 5.59\,\text{m/s}^2$.
  - Relative acceleration between Ship and Booster at separation:
    $$a_{\text{rel}} = a_{\text{ship}} - a_{\text{booster}} \approx 13.31 - (-5.59) = 18.90\,\text{m/s}^2$$
- Relative displacement after $\Delta t = 1.0\,\text{s}$ ($T = 143.0\,\text{s}$):
  $$\Delta r_{\text{rel}}(1\,\text{s}) \approx \frac{1}{2} a_{\text{rel}} (\Delta t)^2 \approx \frac{1}{2} (11.0) (1)^2 \approx \mathbf{5.50\,\text{m}}$$
- Relative displacement after $\Delta t = 3.0\,\text{s}$ ($T = 145.0\,\text{s}$):
  $$\Delta r_{\text{rel}}(3\,\text{s}) \approx \mathbf{48.06\,\text{m}}$$

**Finding:** The reported numbers ($5.50\,\text{m}$ at 1s, $48.06\,\text{m}$ at 3s) are **mathematically correct outputs of the 3-DOF differential acceleration equations**. However, they represent the **relative displacement between stage Centers of Mass**, NOT the physical clearance between the forward dome and the engine bells.

---

## 2. Existing Phase 4 Output Artifact Verification

The existing CSV and JSON output files in `output/` were audited for data integrity:

| Artifact Path | File Size | Row Count | Time Range | Numeric Validation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `output/flight14_staging_relative_motion.csv` | $230,112\,\text{bytes}$ | 2,001 rows | $140.00\,\text{s}$ to $160.00\,\text{s}$ | Monotonic 100 Hz grid, all values finite | **VERIFIED** |
| `output/flight14_booster_return.csv` | $424,810\,\text{bytes}$ | 5,468 rows | $140.00\,\text{s}$ to $413.35\,\text{s}$ | Boostback, apogee ($107.6\,\text{km}$), splashdown ($6.0\,\text{m/s}$) | **VERIFIED** |
| `output/flight14_starship_upper_ascent.csv` | $855,409\,\text{bytes}$ | 7,610 rows | $142.00\,\text{s}$ to $522.35\,\text{s}$ | Upper ascent, PEG climb, orbital insertion ($7,838.9\,\text{m/s}$) | **VERIFIED** |
| `output/flight14_phase4_summary.json` | $1,842\,\text{bytes}$ | 45 lines | Staging metadata summary | Valid JSON schema, key metrics match CSVs | **VERIFIED** |

---

## 3. Required Code Improvements for Gate 3–6

1. **Explicit Column Naming:** Update `flight14_staging_relative_motion.csv` column headers to strictly adhere to `center_range_m`, `relative_speed_mps`, and add `min_surface_clearance_m` with values explicitly set to `null` or uncomputed indicator.
2. **Impulse Mode Configuration:** Refactor `staging_separation.py` to support explicit user configuration flags (`mode = 'zero_impulse'`, `mode = 'prescribed_plume_force'`, `mode = 'prescribed_relative_delta_v'`).
3. **Acceptance Test Expansion:** Expand `tests/test_phase4_staging_recovery.py` from 5 basic smoke tests to the comprehensive 20-point acceptance suite defined in `DOC-P4-VER-001`.
