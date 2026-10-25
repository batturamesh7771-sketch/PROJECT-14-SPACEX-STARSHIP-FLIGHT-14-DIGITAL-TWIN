/**
 * Phase 10: Timeline and Synchronized Playback Controller
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - Master simulation playback clock with sub-second precision
 *   - Playback controls: Play/Pause, Rewind, Step (+/- 1s), Speed Multipliers (0.1x to 10x)
 *   - Direct timeline scrubbing with state interpolation
 *   - Dual timestamp display: Mission Elapsed Time (T+HH:MM:SS) and Total Duration (HH:MM:SS)
 *   - Event milestone scrubbing and camera focus
 */

class TimelineController {
  constructor(callbacks) {
    this.callbacks = callbacks || {};
    this.currentTime = 0.0;
    this.isPlaying = true;
    this.playbackSpeed = 1.0;
    this.lastTimestamp = performance.now();

    this.currentProfile = null;
    this.trajectory = [];
    this.maxTime = 100.0;

    // DOM Elements
    this.clockEl = document.getElementById("master-clock");
    this.hudElapsedEl = document.getElementById("hud-elapsed-time");
    this.overviewElapsedEl = document.getElementById("overview-elapsed-time");
    this.scrubberEl = document.getElementById("timeline-scrubber");
    this.playBtn = document.getElementById("btn-play");
    this.speedBtns = document.querySelectorAll(".speed-btn");

    this.initEvents();
    this.loop = this.loop.bind(this);
    requestAnimationFrame(this.loop);
  }

  setProfile(profileData) {
    this.currentProfile = profileData;
    this.trajectory = profileData.trajectory || [];
    this.maxTime = profileData.duration_s || (this.trajectory.length > 0 ? this.trajectory[this.trajectory.length - 1].time_s : 100.0);
    this.currentTime = 0.0;

    if (this.scrubberEl) {
      this.scrubberEl.min = 0;
      this.scrubberEl.max = this.maxTime;
      this.scrubberEl.value = 0;
    }

    this.renderMilestones(profileData.milestones || []);
    this.updateClockDisplay();
    this.notifyState();
  }

  initEvents() {
    if (this.playBtn) {
      this.playBtn.addEventListener("click", () => this.togglePlay());
    }

    const stepFwd = document.getElementById("btn-step-fwd");
    if (stepFwd) {
      stepFwd.addEventListener("click", () => this.step(1.0));
    }

    const stepBack = document.getElementById("btn-step-back");
    if (stepBack) {
      stepBack.addEventListener("click", () => this.step(-1.0));
    }

    const resetBtn = document.getElementById("btn-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => this.seekTo(0.0));
    }

    if (this.scrubberEl) {
      this.scrubberEl.addEventListener("input", (e) => {
        this.seekTo(parseFloat(e.target.value));
      });
    }

    this.speedBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        this.speedBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.playbackSpeed = parseFloat(btn.dataset.speed || "1.0");
      });
    });
  }

  renderMilestones(milestones) {
    const container = document.getElementById("milestones-container");
    if (!container) return;
    container.innerHTML = "";

    milestones.forEach(m => {
      const btn = document.createElement("button");
      btn.className = "milestone-btn ctrl-btn";
      btn.innerText = `${m.name} (T+${m.time_s.toFixed(0)}s)`;
      btn.addEventListener("click", () => {
        this.seekTo(m.time_s);
        if (this.callbacks.onMilestoneSelect) {
          this.callbacks.onMilestoneSelect(m);
        }
      });
      container.appendChild(btn);
    });
  }

  togglePlay() {
    this.isPlaying = !this.isPlaying;
    if (this.playBtn) {
      this.playBtn.innerText = this.isPlaying ? "PAUSE" : "PLAY";
      this.playBtn.classList.toggle("active", this.isPlaying);
    }
  }

  step(deltaSeconds) {
    this.isPlaying = false;
    if (this.playBtn) {
      this.playBtn.innerText = "PLAY";
      this.playBtn.classList.remove("active");
    }
    this.seekTo(this.currentTime + deltaSeconds);
  }

  seekTo(time_s) {
    this.currentTime = Math.max(0.0, Math.min(this.maxTime, time_s));
    if (this.scrubberEl) {
      this.scrubberEl.value = this.currentTime;
    }
    this.updateClockDisplay();
    this.notifyState();
  }

  updateClockDisplay() {
    const totalSec = Math.floor(this.currentTime);
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    const frac = Math.floor((this.currentTime - totalSec) * 100);

    const pad = (n, len = 2) => String(n).padStart(len, "0");
    const formatted = `T+${pad(hrs)}:${pad(mins)}:${pad(secs)}.${pad(frac)}`;
    const standardFormat = `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;

    if (this.clockEl) this.clockEl.innerText = formatted;
    if (this.hudElapsedEl) this.hudElapsedEl.innerText = standardFormat;
    if (this.overviewElapsedEl) this.overviewElapsedEl.innerText = standardFormat;

    // Flight 14 Launch Epoch: September 28, 2026, 12:48:59 UTC
    const LAUNCH_EPOCH_MS = Date.UTC(2026, 8, 28, 12, 48, 59);
    const currentUtc = new Date(LAUNCH_EPOCH_MS + this.currentTime * 1000);
    const utcFormatted = currentUtc.toISOString().replace("T", " ").substring(0, 19);
    const utcEl = document.getElementById("header-utc-clock");
    if (utcEl) utcEl.innerText = utcFormatted;

    const scrubberClock = document.getElementById("scrubber-clock-readout");
    if (scrubberClock) {
      const totHrs = Math.floor(this.maxTime / 3600);
      const totMins = Math.floor((this.maxTime % 3600) / 60);
      const totSecs = Math.floor(this.maxTime % 60);
      scrubberClock.innerText = `${standardFormat} / ${pad(totHrs)}:${pad(totMins)}:${pad(totSecs)}`;
    }
  }

  interpolateState(targetTime) {
    if (!this.trajectory || this.trajectory.length === 0) return null;
    if (this.trajectory.length === 1 || targetTime <= this.trajectory[0].time_s) {
      return this.trajectory[0];
    }
    if (targetTime >= this.trajectory[this.trajectory.length - 1].time_s) {
      return this.trajectory[this.trajectory.length - 1];
    }

    // Binary search for surrounding interval
    let low = 0;
    let high = this.trajectory.length - 1;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (this.trajectory[mid].time_s <= targetTime) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }

    const p0 = this.trajectory[high];
    const p1 = this.trajectory[low];
    if (!p1) return p0;

    const dt = p1.time_s - p0.time_s;
    const alpha = dt > 0 ? (targetTime - p0.time_s) / dt : 0;

    // Linearly interpolate numeric fields
    const lerp = (a, b) => a + (b - a) * alpha;

    return {
      time_s: targetTime,
      altitude_km: lerp(p0.altitude_km || 0, p1.altitude_km || 0),
      velocity_km_s: lerp(p0.velocity_km_s || 0, p1.velocity_km_s || 0),
      mach: lerp(p0.mach || 0, p1.mach || 0),
      dynamic_pressure_kpa: lerp(p0.dynamic_pressure_kpa || 0, p1.dynamic_pressure_kpa || 0),
      thrust_mn: lerp(p0.thrust_mn || 0, p1.thrust_mn || 0),
      mass_tonnes: lerp(p0.mass_tonnes || 0, p1.mass_tonnes || 0),
      apparent_g: lerp(p0.apparent_g || 1.0, p1.apparent_g || 1.0),
      pitch_deg: lerp(p0.pitch_deg || 0, p1.pitch_deg || 0),
      flaps_fwd_deg: lerp(p0.flaps_fwd_deg || 0, p1.flaps_fwd_deg || 0),
      flaps_aft_deg: lerp(p0.flaps_aft_deg || 0, p1.flaps_aft_deg || 0),
      heat_flux_mw_m2: lerp(p0.heat_flux_mw_m2 || 0, p1.heat_flux_mw_m2 || 0),
      surface_temp_k: lerp(p0.surface_temp_k || 300, p1.surface_temp_k || 300),
      bondline_temp_k: lerp(p0.bondline_temp_k || 290, p1.bondline_temp_k || 290),
      phase: p0.phase,
      event: p0.event || p1.event,
      scene_pos: [
        lerp(p0.scene_pos[0], p1.scene_pos[0]),
        lerp(p0.scene_pos[1], p1.scene_pos[1]),
        lerp(p0.scene_pos[2], p1.scene_pos[2]),
      ],
    };
  }

  notifyState() {
    const currentState = this.interpolateState(this.currentTime);
    if (this.callbacks.onStateUpdate && currentState) {
      this.callbacks.onStateUpdate(currentState, this.currentProfile);
    }
  }

  loop(timestamp) {
    requestAnimationFrame(this.loop);

    const deltaMs = timestamp - this.lastTimestamp;
    this.lastTimestamp = timestamp;

    if (this.isPlaying && this.currentProfile) {
      // In orbital profile, trajectory spans hours; scale playback step naturally:
      const timeScaleFactor = this.maxTime > 1000 ? 40.0 : 1.0;
      const dt = (deltaMs / 1000.0) * this.playbackSpeed * timeScaleFactor;

      this.currentTime += dt;
      if (this.currentTime >= this.maxTime) {
        this.currentTime = this.maxTime;
        this.isPlaying = false;
        if (this.playBtn) this.playBtn.innerText = "REPLAY";
      }

      if (this.scrubberEl) {
        this.scrubberEl.value = this.currentTime;
      }
      this.updateClockDisplay();
      this.notifyState();
    }
  }
}

window.TimelineController = TimelineController;
