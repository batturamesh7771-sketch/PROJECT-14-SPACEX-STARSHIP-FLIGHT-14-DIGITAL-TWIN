# Phase 11: Flight 14 Public Evidence Ledger
**Starship Flight 14 Digital Engineering Lab**  
**Evidence Standard:** Primary Public Sourced Data (SpaceX, Space.com, AP, Reuters)  
**Profile Segregation:** `flight14_planned_public_reference` vs. `flight14_observed_public_reconstruction`

---

## 1. Evidence Principles & Provenance Rules

1. **Explicit Time Semantics:** Every milestone declares its `time_type`:
   - `planned`: Stated on preflight timeline.
   - `reported_approximate`: Stated in contemporaneous media coverage or live mission broadcast.
   - `measured`: Confirmed by sensor data with published timestamp (unavailable for classified/proprietary channels).
   - `derived`: Numerically integrated or computed from kinematic principles.
2. **Explicit Uncertainty:** Every time entry includes an uncertainty bound ($\pm \delta t$).
3. **No Fabricated Telemetry:** A public report stating that an engine shut down or that splashdown occurred at roughly 3 hours 9 minutes does not authorize inventing high-rate telemetry traces between milestones.

---

## 2. Chronological Public Evidence Matrix

| Event ID | Event Name | Profile ID | Nominal / Stated Time | Time Type | Uncertainty | Source ID | Contemporaneous Description & Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `F14-P-001` | Launch Window Commit | `flight14_planned_public_reference` | `T+00:00:00` | `planned` | $\pm 0\,\text{s}$ | `SRC-SPX-F14` | SpaceX preflight schedule for 28 September 2026. |
| `F14-P-002` | Max Q (Maximum Dynamic Pressure) | `flight14_planned_public_reference` | `T+00:00:58` | `planned` | $\pm 5\,\text{s}$ | `SRC-SPX-F14` | Preflight nominal mission timeline. |
| `F14-P-003` | Super Heavy MECO | `flight14_planned_public_reference` | `T+00:02:20` | `planned` | $\pm 2\,\text{s}$ | `SRC-SPX-F14` | Planned most-engines-cutoff before hot-staging. |
| `F14-P-004` | Hot-Staging Separation | `flight14_planned_public_reference` | `T+00:02:22` | `planned` | $\pm 2\,\text{s}$ | `SRC-SPX-F14` | Upper-stage ignition and interstage ring separation. |
| `F14-P-005` | Starship SECO-1 (Orbit Insertion) | `flight14_planned_public_reference` | `T+00:08:42` | `planned` | $\pm 10\,\text{s}$ | `SRC-SPX-F14` | Insertion into ~275 km circular parking orbit. |
| `F14-P-006` | Starlink V3 Deployment Sequence | `flight14_planned_public_reference` | `T+00:42:00` to `T+00:58:00` | `planned` | $\pm 60\,\text{s}$ | `SRC-SPX-F14` | Planned dispensing of 26 Starlink V3 satellites across orbits 2–4. |
| `F14-P-007` | Deorbit Burn Commit | `flight14_planned_public_reference` | `T+09:30:00` | `planned` | $\pm 120\,\text{s}$ | `SRC-SPX-F14` | Planned retrograde burn after 6 orbits (~10 h total mission). |
| `F14-P-008` | Pacific Controlled Splashdown | `flight14_planned_public_reference` | `T+10:00:00` | `planned` | $\pm 300\,\text{s}$ | `SRC-SPX-F14` | Target splashdown in remote Pacific Ocean west of Chile. |
| **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** |
| `F14-O-001` | Actual Liftoff | `flight14_observed_public_reconstruction` | `08:49 EDT` (`12:49 UTC`) | `reported_approximate` | $\pm 30\,\text{s}$ | `SRC-SC-LIVE` | Liftoff from Starbase, Texas on 28 September 2026. |
| `F14-O-002` | Hot-Staging Observed | `flight14_observed_public_reconstruction` | `T+00:02:34` | `reported_approximate` | $\pm 5\,\text{s}$ | `SRC-SC-LIVE` | Live coverage described stage separation at ~2m 34s into flight. |
| `F14-O-003` | Super Heavy Splashdown | `flight14_observed_public_reconstruction` | `T+00:06:40` | `reported_approximate` | $\pm 20\,\text{s}$ | `SRC-REUTERS` | Booster executed landing burn and splashed down in Gulf of Mexico (expended). Not a tower catch. |
| `F14-O-004` | Upper-Stage Engine Anomaly | `flight14_observed_public_reconstruction` | `T+00:04:30` | `reported_approximate` | $\pm 30\,\text{s}$ | `SRC-AP-F14` | One Starship Raptor engine shut down prematurely during ascent. Spacecraft continued into orbit. |
| `F14-O-005` | Orbital Insertion Achieved | `flight14_observed_public_reconstruction` | `T+00:08:42` | `reported_approximate` | $\pm 15\,\text{s}$ | `SRC-SPX-UPD` | Starship achieved orbital insertion at approximately 275 km (170 miles). |
| `F14-O-006` | Starlink Deployment Start | `flight14_observed_public_reconstruction` | `T+00:34:00` | `reported_approximate` | $\pm 60\,\text{s}$ | `SRC-SC-LIVE` | Payload deployment sequence initiated in orbit 1. |
| `F14-O-007` | 26 Starlinks Deployed Complete | `flight14_observed_public_reconstruction` | `T+01:04:00` | `reported_approximate` | $\pm 120\,\text{s}$ | `SRC-AP-F14` | All 26 Starlink V3 satellites confirmed deployed. Three equipped with camera pods to inspect tiles. |
| `F14-O-008` | Early Return & Deorbit Decision | `flight14_observed_public_reconstruction` | `T+02:45:00` | `reported_approximate` | $\pm 120\,\text{s}$ | `SRC-REUTERS` | Mission control commanded early disposal after ~2 orbits due to upper stage engine issue. |
| `F14-O-009` | Atmospheric Reentry Interface | `flight14_observed_public_reconstruction` | `T+03:00:00` | `derived` | $\pm 60\,\text{s}$ | `SRC-SC-LIVE` | Starship entered dense atmosphere over Northern Pacific. |
| `F14-O-010` | Northern Pacific Splashdown | `flight14_observed_public_reconstruction` | `T+03:09:00` | `reported_approximate` | $\pm 60\,\text{s}$ | `SRC-AP-F14` | Starship splashed down in Northern Pacific north of Hawaii. Vehicle tipped over and ignited. Expended. |

---

## 3. Key Public Ground Truth Assertions

1. **No Tower Catch or Vertical Recovery on Flight 14:** Both Super Heavy (Gulf of Mexico) and Starship (Northern Pacific) ended in offshore ocean splashdowns. Neither vehicle was recovered or caught.
2. **Early Mission Termination (~3.2 h vs ~10 h planned):** The mission completed roughly 2 orbits rather than the 6 planned orbits due to the upper-stage Raptor engine shutdown anomaly.
3. **Discrete Payload Success (26 Satellites):** All 26 Starlink V3 satellites were successfully deployed into orbit. Individual separation velocities and precise timestamps are treated as model assumptions bounded by the reported ~30-minute deployment window.
