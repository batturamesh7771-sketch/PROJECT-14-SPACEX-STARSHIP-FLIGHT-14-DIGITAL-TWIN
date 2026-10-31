# Starship Flight 14 Cinematic Mission Replay — Camera Choreography & Event Timeline

**Document Date:** 2026-10-27  
**Project:** Starship Flight 14 Digital Engineering Lab  

---

## 1. Twenty-One (21) Broadcast Camera Choreography States

The Cinematic Camera Director (`CinematicCameraDirector`) operates a deterministic state machine with 21 distinct broadcast viewpoints. Each state defines target coordinates, camera offsets, field of view (FOV), smoothing half-life, and contextual constraints:

| ID | State Name | Description | Target Object | Typical Epoch / Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `PAD_WIDE` | Panoramic Starbase view showing OLM, Mechazilla tower, chopsticks, and lagoon. | Launch Mount | T-10s to T-0s (Prelaunch) |
| **02** | `PAD_LOW_ANGLE` | Dramatic ground-level looking up the 121 m stacked vehicle against the tower. | Vehicle Stack | Prelaunch countdown |
| **03** | `IGNITION_TRACK` | Close framing on the 33 Raptor engine skirt and deluge water vapor bloom. | Aft Skirt | T-0s to T+12s (Liftoff) |
| **04** | `ASCENT_CHASE` | Cinematic rear-quarter chase camera tracking vehicle through condensation clouds. | Full Stack | T+12s to T+140s (Ascent) |
| **05** | `ASCENT_LONG_LENS` | Ground telephoto tracking perspective capturing high-altitude expansion plume. | Full Stack | T+60s to T+120s (Max Q) |
| **06** | `STAGING_WIDE` | Wide perspective keeping both Super Heavy and Starship in frame simultaneously. | Staging Ring | T+160s to T+180s (Hot Staging) |
| **07** | `STAGING_CLOSE` | Close-up on the vented interstage ring as Starship engines ignite. | Interstage Ring | T+162s to T+166s |
| **08** | `BOOSTER_RETURN_CHASE` | Tracking Super Heavy through its flip maneuver and boostback burn. | Super Heavy | T+168s to T+280s |
| **09** | `BOOSTER_GULF_WIDE` | Horizon camera in the Gulf of Mexico showing booster soft water landing. | Super Heavy | T+380s to T+430s (Gulf Splash) |
| **10** | `SHIP_SPACE_CHASE` | Solo Starship upper stage accelerating toward low Earth orbit against sunrise. | Starship Upper | T+170s to T+522s (Orbit Insert) |
| **11** | `ORBIT_OVERVIEW` | Wide orbital framing with curved Earth horizon and glowing trajectory ribbon. | Starship Upper | T+530s to T+1300s |
| **12** | `SATELLITE_DEPLOY_CLOSE` | Close telephoto framing on the forward PEZ dispenser mouth and exit slot. | Dispenser Mouth | T+1320s to T+1680s (Deploy) |
| **13** | `SATELLITE_TRAIN_WIDE` | Panoramic constellation view showing the 26 Starlinks separating forward. | Satellite Train | T+1400s to T+1800s |
| **14** | `ORBITAL_EARTH_LIMB` | Cinematic Earth limb framing with subtle sunlight reflections on 304L stainless hull. | Starship Upper | T+1800s to T+9800s (Coast) |
| **15** | `DEORBIT_CHASE` | Following Starship through 180° retrograde flip and center engine deorbit burn. | Starship Upper | T+9900s to T+9960s (Deorbit) |
| **16** | `ENTRY_LONG_LENS` | Hypersonic entry at 70° angle of attack with glowing bow-shock plasma sheath. | Windward Hull | T+10800s to T+11200s (Reentry) |
| **17** | `ENTRY_DRONE_TRACK` | Exterior drone-style tracking camera orbiting the spacecraft path during entry. | Starship Upper | T+11100s to T+11340s |
| **18** | `PACIFIC_APPROACH` | Low-altitude descent toward the Northern Pacific ocean horizon. | Starship Upper | T+11340s to T+11360s |
| **19** | `SPLASHDOWN_WIDE` | Wide Pacific Ocean view showing flip maneuver, landing burn, and water impact. | Splashdown Point | T+11360s to T+11732s (Splash) |
| **20** | `SPLASHDOWN_WATER_LEVEL` | Surface water-level camera capturing splash spray, vapor cloud, and wave rings. | Water Surface | Terminal touchdown |
| **21** | `POST_SPLASHDOWN_HOLD` | Contemplative lingering aftermath over the calm Pacific waters. | Ocean Horizon | Post-touchdown hold |

---

## 2. Event-Driven Milestone Timeline (Observed Profile)

```
Epoch                  Event ID                     Camera Trigger               Description
-----------------------------------------------------------------------------------------------------------------------------
T-10s to T-0s          PRELAUNCH_INTRO              PAD_WIDE / LOW_ANGLE         Starbase launchpad, stacked vehicle standing
T+00:00:00 (12:48:00Z) LIFTOFF                      IGNITION_TRACK               33 Raptor 3 engines ignite; tower clearance
T+00:01:08             MAX_Q                        ASCENT_CHASE                 Maximum aerodynamic dynamic pressure (36.9 kPa)
T+00:00:45             BOOSTER_ENGINE_EVENT         ASCENT_CHASE                 1 outer Raptor engine shut down during climb
T+00:02:42 (T+162s)    HOT_STAGING                  STAGING_WIDE / CLOSE         Interstage ring firing; booster & ship separate
T+00:02:48             BOOSTER_BOOSTBACK            BOOSTER_RETURN_CHASE         Super Heavy flip and boostback burn
T+00:07:05 (T+425s)    BOOSTER_GULF_SPLASHDOWN      BOOSTER_GULF_WIDE            Controlled soft water landing in Gulf of Mexico
T+00:08:42 (T+522s)    ORBITAL_INSERTION            SHIP_SPACE_CHASE             Starship SECO cutoff; ~200 x 275 km orbit
T+00:22:00 (T+1320s)   STARLINK_DEPLOY_START        SATELLITE_DEPLOY_CLOSE       Forward PEZ mouth door opens (71° angle)
T+00:28:00 (T+1680s)   STARLINK_DEPLOY_COMPLETE     SATELLITE_TRAIN_WIDE         26th Starlink V3 ejected; 26/26 deployed
T+00:30:00 to 45:00    ORBITAL_COAST                ORBITAL_EARTH_LIMB           Quiet spaceflight; Earth limb tracking
T+00:45:00 (T+2700s)   EARLY_RETURN_DECISION        ORBIT_OVERVIEW               Mission adjusted to 2 laps after engine event
T+02:45:00 (T+9900s)   DEORBIT_BURN                 DEORBIT_CHASE                180° retrograde flip; 1-engine disposal burn
T+03:00:00 (T+10800s)  ATMOSPHERIC_ENTRY            ENTRY_LONG_LENS              Entry interface (120 km); 70° belly-flop AoA
T+03:06:00 (T+11160s)  PEAK_HEATING                 ENTRY_DRONE_TRACK            Max stagnation flux (0.794 MW/m²); plasma glow
T+03:09:00 (T+11340s)  LANDING_FLIP_BURN            PACIFIC_APPROACH             Flip to vertical; 3-engine landing burn
T+03:09:24 (T+11364s)  PACIFIC_SPLASHDOWN           SPLASHDOWN_WIDE / WATER      Touchdown in Northern Pacific; impact spray
T+03:10:00+            MISSION_COMPLETE             POST_SPLASHDOWN_HOLD         Final splashdown status; summary card
```
