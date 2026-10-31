/**
 * Starship Flight 14 — Master Deterministic Mission Replay Controller
 * Strict Namespace: CFR (Cinematic Flight Replay)
 *
 * Implements:
 *   - Authoritative missionElapsedSeconds timeline clock
 *   - Accurate 1x wall-clock playback (~3h 09m / 11,364s - 18,540s for observed Flight 14)
 *   - Playback rate multipliers: 0.1x, 0.25x, 0.5x, 1x, 2x, 5x, 10x, 30x, 60x
 *   - Staged prelaunch visual countdown (T-10 to T-0) outside T+ mission time
 *   - Profile segregation: planned (10h/6 orbits), observed (3h09m/2 orbits), synthetic (sandbox)
 *   - Scrubbing, step forward/backward, milestone seek, and pause clamping
 */

class CfrReplayController {
  constructor(options = {}) {
    this.scenarioData = options.scenarioData || window.EMBEDDED_SCENARIO_DATA || {};
    this.onTick = options.onTick || (() => {});
    this.onProfileChange = options.onProfileChange || (() => {});
    this.onEventTrigger = options.onEventTrigger || (() => {});

    // Time & Playback State
    this.currentTime_s = 0.0;
    this.countdownTime_s = 10.0; // T-10 down to 0
    this.isPrelaunchCountdown = true;
    this.isPlaying = false;
    this.playbackSpeed = 1.0;
    this.lastFrameTimestamp = null;

    // Profiles
    this.activeProfileKey = "flight14_observed_reconstruction";
    this.activeProfile = null;
    this.trajectory = [];
    this.duration_s = 11364.0; // 3h 09m 24s

    // Registered Milestones
    this.milestones = [];
    this.currentMilestoneIndex = 0;

    this.initProfile(this.activeProfileKey);
    this.bindKeyboardShortcuts();
    this.startLoop();
  }

  initProfile(profileKey) {
    const aliases = this.scenarioData.profile_aliases || {
      flight14_observed_reconstruction: "observed_reconstruction",
      flight14_planned: "planned_flight14",
      synthetic_engineering_test: "synthetic_landing_lab",
    };
    const canonicalKey = aliases[profileKey] || profileKey;
    const profiles = this.scenarioData.profiles || {};
    this.activeProfile = profiles[canonicalKey] || profiles[profileKey] || profiles["observed_reconstruction"] || Object.values(profiles)[0] || {};

    this.trajectory = this.activeProfile.trajectory || [];
    this.boosterTrajectory = this.activeProfile.booster_trajectory || [];
    this.duration_s = this.activeProfile.duration_s || 11364.0;

    // Define profile-specific milestone schedule
    if (this.activeProfile.is_synthetic) {
      this.milestones = [
        { time_s: 0, id: "SYNTH_IGNITION", title: "Landing Burn Relight", camera: "PAD_LOW_ANGLE" },
        { time_s: 6, id: "SYNTH_FLIP", title: "Aerodynamic Flip Maneuver", camera: "ENTRY_DRONE_TRACK" },
        { time_s: 14, id: "SYNTH_TERMINAL", title: "Tower Approach & Deceleration", camera: "PAD_WIDE" },
        { time_s: 20, id: "SYNTH_CATCH", title: "Mechazilla Chopstick Catch", camera: "PAD_WIDE" },
      ];
    } else if (profileKey === "flight14_planned") {
      this.milestones = [
        { time_s: 0, id: "LIFTOFF", title: "Liftoff from Starbase", camera: "IGNITION_TRACK" },
        { time_s: 68.5, id: "MAX_Q", title: "Maximum Dynamic Pressure", camera: "ASCENT_CHASE" },
        { time_s: 162.0, id: "HOT_STAGING", title: "Hot-Staging Separation", camera: "STAGING_WIDE" },
        { time_s: 425.0, id: "BOOSTER_SPLASH", title: "Booster Water Landing", camera: "BOOSTER_GULF_WIDE" },
        { time_s: 522.0, id: "ORBIT_INSERT", title: "Orbital Insertion (275 km)", camera: "SHIP_SPACE_CHASE" },
        { time_s: 1320.0, id: "STARLINK_DEPLOY", title: "Starlink V3 PEZ Deploy", camera: "SATELLITE_DEPLOY_CLOSE" },
        { time_s: 21600.0, id: "ORBIT_COAST_6", title: "6-Orbit Flight Plan", camera: "ORBITAL_EARTH_LIMB" },
        { time_s: 34200.0, id: "DEORBIT_BURN", title: "Planned Deorbit Burn", camera: "DEORBIT_CHASE" },
        { time_s: 36000.0, id: "PACIFIC_SPLASH", title: "Planned Pacific Splashdown", camera: "SPLASHDOWN_WIDE" },
      ];
    } else {
      // Historical Observed Flight 14 Profile (Sept 28, 2026)
      this.milestones = [
        {
          time_s: 0,
          id: "LIFTOFF",
          title: "Liftoff (07:48:00 CT) — 33 Raptors at Full Thrust",
          desc: "Ignition of all 33 Raptor 3 engines (81.7 MN thrust). The water deluge system expels 400,000 gallons creating massive steam clouds (H2O, H2) mixed with combustion products (CO2, NOx, soot) across the Starbase coastal pad.",
          camera: "IGNITION_TRACK"
        },
        {
          time_s: 35.0,
          id: "ENGINE_CUTOFF",
          title: "Booster Engine Event (1 Outer Engine Cutoff)",
          desc: "Telemetry confirms one outer-ring Raptor shutdown; autonomous flight computer dynamically throttles remaining 32 engines to maintain nominal ascent trajectory and acceleration.",
          camera: "ASCENT_CHASE"
        },
        {
          time_s: 62.0,
          id: "MAX_Q",
          title: "Max Q Dynamic Pressure (48.0 kPa)",
          desc: "Starship full stack breaches peak aerodynamic pressure envelope at Mach 1.6. Hull structure and cast titanium grid fins sustain maximum aerodynamic loads without aeroelastic flutter.",
          camera: "ASCENT_LONG_LENS"
        },
        {
          time_s: 140.0,
          id: "HOT_STAGING",
          title: "Hot-Staging Ring Separation",
          desc: "Booster throttles down to 3 center engines; Starship upper stage 6 Raptors ignite while still mated, blowing exhaust out through the vented interstage slots before clean physical separation push.",
          camera: "STAGING_WIDE"
        },
        {
          time_s: 148.0,
          id: "BOOSTER_BOOSTBACK",
          title: "Booster Boostback Burn (13 Raptor Engines)",
          desc: "Super Heavy executes aerodynamic flip and ignites 13 engines for retro-propulsion, reversing downrange velocity to return towards the Gulf of Mexico waters off Starbase, Texas.",
          camera: "BOOSTER_RETURN_CHASE"
        },
        {
          time_s: 218.0,
          id: "BOOSTER_DESCENT",
          title: "Booster Atmospheric Entry & Grid Fin Guidance",
          desc: "Boostback complete. Super Heavy descends through the upper atmosphere using 4 cast titanium grid fins for hypersonic aerodynamic steering towards the coastal splashdown corridor.",
          camera: "BOOSTER_RETURN_CHASE"
        },
        {
          time_s: 398.0,
          id: "BOOSTER_LANDING_BURN",
          title: "Booster 3-Engine Landing Burn",
          desc: "Center 3 Raptor engines reignite at high thrust to decelerate the 71-meter booster for a controlled vertical touchdown over the Gulf of Mexico.",
          camera: "BOOSTER_GULF_WIDE"
        },
        {
          time_s: 422.0,
          id: "BOOSTER_SPLASH",
          title: "Super Heavy Booster Soft Splashdown (Gulf of Mexico)",
          desc: "Super Heavy completes soft vertical splashdown in the Gulf of Mexico off the coast of Boca Chica, Texas amidst boiling sea spray and expanding wave ripples.",
          camera: "BOOSTER_GULF_WIDE"
        },
        {
          time_s: 525.0,
          id: "ORBIT_INSERT",
          title: "Starship SECO Cutoff (200 x 275 km Orbit)",
          desc: "Starship upper stage achieves orbital insertion velocity (28,046 km/h, Mach 22.9). All 6 vacuum and sea-level Raptor engines shut down nominal in low Earth orbit.",
          camera: "SHIP_SPACE_CHASE"
        },
        {
          time_s: 1200.0,
          id: "PEZ_DOOR_OPEN",
          title: "Forward PEZ Dispenser Door Unlatch",
          desc: "Starship forward leeward payload bay door rotates open to expose the vertical satellite deployment slot in stable low Earth orbit.",
          camera: "SATELLITE_DEPLOY_CLOSE"
        },
        {
          time_s: 1320.0,
          id: "STARLINK_DEPLOY_START",
          title: "Starlink V3 Satellite Deployment Sequence Start",
          desc: "Sequential release of 26 Starlink V3 direct-to-cell satellites initiated via spring push through the PEZ slot, safely drifting into independent orbital trajectories.",
          camera: "SATELLITE_DEPLOY_CLOSE"
        },
        {
          time_s: 1680.0,
          id: "STARLINK_DEPLOY_DONE",
          title: "All 26 Starlink V3 Satellites Confirmed Deployed",
          desc: "Deployment complete. All 26 spacecraft safely clear the Starship envelope, unfolding sapphire photovoltaic solar wings into a permanent orbital constellation train.",
          camera: "SATELLITE_TRAIN_WIDE"
        },
        {
          time_s: 5400.0,
          id: "EARLY_RETURN",
          title: "Early Return Decision (2 Laps Orbital Adjustment)",
          desc: "Flight controllers initiate contingency early deorbit sequence after monitoring upper-stage engine parameters, shifting endpoint from 6-orbit plan to controlled Northern Pacific landing.",
          camera: "ORBIT_OVERVIEW"
        },
        {
          time_s: 9900.0,
          id: "DEORBIT_BURN",
          title: "Retrograde Deorbit Burn",
          desc: "Upper stage relights center Raptor engines in retrograde attitude, reducing orbital velocity to lower perigee into the dense upper atmosphere over the Pacific Ocean.",
          camera: "DEORBIT_CHASE"
        },
        {
          time_s: 10434.0,
          id: "ATMOSPHERIC_ENTRY",
          title: "Atmospheric Entry Interface (120 km Altitude)",
          desc: "AERODYNAMIC BELLY-FLOP ATTITUDE: Vehicle establishes 70° horizontal angle-of-attack (AoA). Windward black ceramic tiles absorb hypersonic shock compression heating as air density rises.",
          camera: "ENTRY_LONG_LENS"
        },
        {
          time_s: 11160.0,
          id: "PEAK_HEATING",
          title: "Peak Plasma Heating — Belly-Flop Aerobraking (Horizontal AoA)",
          desc: "WHY HORIZONTAL: Starship skydiver belly-flop acts as an aerodynamic brake, shedding 28,000 km/h without using rocket fuel. Stagnation heat flux reaches 0.818 MW/m². Terminal flip to 90° straight vertical occurs below 2 km.",
          camera: "ENTRY_DRONE_TRACK"
        },
        {
          time_s: 11335.0,
          id: "LANDING_BURN",
          title: "Terminal Flip Maneuver to 90° Vertical & 3-Raptor Landing Burn",
          desc: "TERMINAL FLIP TO STRAIGHT VERTICAL: Aerodynamic flaps deflect and 3 center Raptor engines ignite, pitching the vehicle 90° upright. Rocket descends vertically, boiling sea water with intense exhaust plume.",
          camera: "PACIFIC_APPROACH"
        },
        {
          time_s: 11364.0,
          id: "PACIFIC_SPLASHDOWN",
          title: "Controlled Pacific Ocean Touchdown & Naval Recovery Complete",
          desc: "Controlled soft water landing confirmed in the Northern Pacific Ocean. Starship touches down vertically at zero relative velocity amidst sea spray and steam. Recovery vessel and rescue craft on standby.",
          camera: "SPLASHDOWN_WIDE"
        },
      ];
    }

    this.onProfileChange(this.activeProfile, profileKey);
  }

  // Master Animation / Clock Loop
  startLoop() {
    const loop = (timestamp) => {
      if (this.lastFrameTimestamp === null) {
        this.lastFrameTimestamp = timestamp;
      }
      const deltaSec = Math.min(0.2, (timestamp - this.lastFrameTimestamp) / 1000.0);
      this.lastFrameTimestamp = timestamp;

      if (this.isPlaying) {
        if (this.isPrelaunchCountdown) {
          // Prelaunch Countdown Phase (T-10 down to T-0)
          this.countdownTime_s -= deltaSec * this.playbackSpeed;
          if (this.countdownTime_s <= 0.0) {
            this.countdownTime_s = 0.0;
            this.isPrelaunchCountdown = false;
            this.currentTime_s = 0.0;
            this.triggerEvent("LIFTOFF");
          }
        } else {
          // Mission Elapsed Flight Phase
          this.currentTime_s += deltaSec * this.playbackSpeed;
          if (this.currentTime_s >= this.duration_s) {
            this.currentTime_s = this.duration_s;
            this.isPlaying = false;
            this.triggerEvent("MISSION_COMPLETE");
          }
        }
      }

      this.updateState();
      requestAnimationFrame(loop);
    };

    requestAnimationFrame(loop);
  }

  updateState() {
    const statePoint = this.interpolateState(this.currentTime_s);
    const boosterState = this.interpolateBoosterState(this.currentTime_s);
    this.onTick(this.currentTime_s, statePoint, boosterState, this.activeProfile, {
      isPlaying: this.isPlaying,
      isPrelaunch: this.isPrelaunchCountdown,
      countdownSec: this.countdownTime_s,
      speed: this.playbackSpeed,
      duration_s: this.duration_s,
    });
  }

  // Physical State Interpolation (Strict Null-Checking, No Falsy Zero Defaults)
  interpolateState(time_s) {
    if (!this.trajectory || this.trajectory.length === 0) return null;

    if (time_s <= this.trajectory[0].time_s) return this.trajectory[0];
    const lastIdx = this.trajectory.length - 1;
    if (time_s >= this.trajectory[lastIdx].time_s) return this.trajectory[lastIdx];

    // Binary search for interval
    let low = 0;
    let high = lastIdx;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (this.trajectory[mid].time_s <= time_s && (mid === lastIdx || this.trajectory[mid + 1].time_s > time_s)) {
        const p1 = this.trajectory[mid];
        const p2 = this.trajectory[mid + 1];
        const dt = p2.time_s - p1.time_s;
        const u = dt > 0 ? (time_s - p1.time_s) / dt : 0;

        // Smooth spatial linear interpolation
        const pos1 = p1.scene_pos || [0, 6.4, 0];
        const pos2 = p2.scene_pos || [0, 6.4, 0];
        const interpolatedPos = [
          pos1[0] + u * (pos2[0] - pos1[0]),
          pos1[1] + u * (pos2[1] - pos1[1]),
          pos1[2] + u * (pos2[2] - pos1[2]),
        ];

        const interp = (v1, v2, def) => {
          const val1 = (v1 !== undefined && v1 !== null) ? v1 : def;
          const val2 = (v2 !== undefined && v2 !== null) ? v2 : def;
          return val1 + u * (val2 - val1);
        };

        return {
          time_s: time_s,
          altitude_km: interp(p1.altitude_km, p2.altitude_km, 0),
          velocity_km_s: interp(p1.velocity_km_s, p2.velocity_km_s, 0),
          dynamic_pressure_kpa: interp(p1.dynamic_pressure_kpa, p2.dynamic_pressure_kpa, 0),
          heat_flux_mw_m2: interp(p1.heat_flux_mw_m2, p2.heat_flux_mw_m2, 0),
          apparent_g: interp(p1.apparent_g, p2.apparent_g, 0.0),
          thrust_mn: interp(p1.thrust_mn, p2.thrust_mn, 0),
          mass_tonnes: interp(p1.mass_tonnes, p2.mass_tonnes, 120.0),
          pitch_deg: interp(p1.pitch_deg, p2.pitch_deg, 0.0),
          flaps_fwd_deg: interp(p1.flaps_fwd_deg, p2.flaps_fwd_deg, 0),
          flaps_aft_deg: interp(p1.flaps_aft_deg, p2.flaps_aft_deg, 0),
          surface_temp_k: interp(p1.surface_temp_k, p2.surface_temp_k, 300.0),
          bondline_temp_k: interp(p1.bondline_temp_k, p2.bondline_temp_k, 300.0),
          phase: p1.phase,
          scene_pos: interpolatedPos,
        };
      } else if (this.trajectory[mid].time_s > time_s) {
        high = mid - 1;
      } else {
        low = mid + 1;
      }
    }

    return this.trajectory[0];
  }

  // Multi-Body Dynamics: Super Heavy Booster State Interpolation
  interpolateBoosterState(time_s) {
    if (!this.boosterTrajectory || this.boosterTrajectory.length === 0) return null;
    const bTraj = this.boosterTrajectory;
    const tStart = bTraj[0].time_s;
    const tEnd = bTraj[bTraj.length - 1].time_s;

    if (time_s < tStart) {
      return { isAttached: true, time_s: time_s };
    }
    if (time_s >= tEnd) {
      const pLast = bTraj[bTraj.length - 1];
      return {
        isAttached: false,
        time_s: time_s,
        altitude_km: 0.0,
        velocity_km_s: 0.0,
        thrust_mn: 0.0,
        active_engines: 0,
        apparent_g: 1.0,
        phase: "BOOSTER_SPLASHDOWN",
        event: "SPLASHDOWN_AFTERMATH",
        scene_pos: pLast.scene_pos || [-0.618328, 2.81099, 5.691805],
      };
    }

    let low = 0;
    let high = bTraj.length - 1;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (bTraj[mid].time_s <= time_s && (mid === bTraj.length - 1 || bTraj[mid + 1].time_s > time_s)) {
        const p1 = bTraj[mid];
        const p2 = bTraj[mid + 1];
        const dt = p2.time_s - p1.time_s;
        const u = dt > 0 ? (time_s - p1.time_s) / dt : 0;
        const pos1 = p1.scene_pos || [-0.6, 2.8, 5.7];
        const pos2 = p2.scene_pos || [-0.6, 2.8, 5.7];
        const interp = (v1, v2, def) => {
          const val1 = (v1 !== undefined && v1 !== null) ? v1 : def;
          const val2 = (v2 !== undefined && v2 !== null) ? v2 : def;
          return val1 + u * (val2 - val1);
        };
        return {
          isAttached: false,
          time_s: time_s,
          altitude_km: interp(p1.altitude_km, p2.altitude_km, 0),
          velocity_km_s: interp(p1.velocity_km_s, p2.velocity_km_s, 0),
          thrust_mn: interp(p1.thrust_mn, p2.thrust_mn, 0),
          active_engines: p1.active_engines !== undefined ? p1.active_engines : 0,
          apparent_g: interp(p1.apparent_g, p2.apparent_g, 1.0),
          phase: p1.phase,
          event: p1.event,
          scene_pos: [
            pos1[0] + u * (pos2[0] - pos1[0]),
            pos1[1] + u * (pos2[1] - pos1[1]),
            pos1[2] + u * (pos2[2] - pos1[2]),
          ],
        };
      } else if (bTraj[mid].time_s > time_s) {
        high = mid - 1;
      } else {
        low = mid + 1;
      }
    }
    return bTraj[0];
  }

  // Controls API
  play() {
    this.isPlaying = true;
  }

  pause() {
    this.isPlaying = false;
  }

  togglePlay() {
    this.isPlaying = !this.isPlaying;
  }

  seekTo(time_s) {
    this.isPrelaunchCountdown = false;
    this.countdownTime_s = 0.0;
    this.currentTime_s = Math.max(0.0, Math.min(this.duration_s, time_s));
    this.updateState();
    if (window.cfrCameraDirector) {
      window.cfrCameraDirector.snapCamera();
    }
  }

  step(deltaSeconds) {
    this.seekTo(this.currentTime_s + deltaSeconds);
  }

  restart() {
    this.isPrelaunchCountdown = true;
    this.countdownTime_s = 10.0;
    this.currentTime_s = 0.0;
    this.updateState();
  }

  setSpeed(speedVal) {
    this.playbackSpeed = parseFloat(speedVal) || 1.0;
  }

  jumpToMilestone(milestoneId) {
    const m = this.milestones.find((item) => item.id === milestoneId);
    if (m) {
      this.seekTo(m.time_s);
      if (m.camera && window.cfrCameraDirector) {
        window.cfrCameraDirector.setCameraState(m.camera);
      }
    }
  }

  jumpToNextMilestone() {
    const next = this.milestones.find((m) => m.time_s > this.currentTime_s + 2.0);
    if (next) this.jumpToMilestone(next.id);
  }

  jumpToPrevMilestone() {
    const prevs = this.milestones.filter((m) => m.time_s < this.currentTime_s - 2.0);
    if (prevs.length > 0) {
      const prev = prevs[prevs.length - 1];
      this.jumpToMilestone(prev.id);
    } else {
      this.restart();
    }
  }

  triggerEvent(eventId) {
    this.onEventTrigger(eventId, this.currentTime_s, this.activeProfile);
  }

  bindKeyboardShortcuts() {
    window.addEventListener("keydown", (e) => {
      // Avoid intercepting input fields
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

      if (e.code === "Space") {
        e.preventDefault();
        this.togglePlay();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        this.step(e.shiftKey ? 30.0 : 5.0);
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        this.step(e.shiftKey ? -30.0 : -5.0);
      } else if (e.code === "KeyR") {
        this.restart();
      } else if (e.code === "BracketRight") {
        this.jumpToNextMilestone();
      } else if (e.code === "BracketLeft") {
        this.jumpToPrevMilestone();
      }
    });
  }
}

window.CfrReplayController = CfrReplayController;
