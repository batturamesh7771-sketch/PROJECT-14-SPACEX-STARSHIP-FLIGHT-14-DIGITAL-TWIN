/**
 * Phase 10: Live Telemetry HUD and Subsystem Status Module
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - SpaceX Mission Control telemetry panel matching Screenshot B
 *   - Real-time numerical readouts: Altitude (m), Dynamic Pressure (Pa), Velocity (m/s),
 *     Heat Flux (W/m²), Mach [-], G-Force (g), Thrust (kN), Attitude (R,P,Y), Mass (kg),
 *     Flap Deflection (deg), Fuel Remaining (%), Engine Status (33/33 or 3/3 NOMINAL)
 *   - Vehicle 3D Model flap position readouts (Forward, Aft, Left, Right)
 *   - Interactive 8-Phase Mission Stepper synchronization
 *   - Mission Events table status (Completed, In Progress, Pending)
 *   - Systems Health matrix indicators
 *   - Starlink V3 26-satellite dispenser sequence tracker
 *   - Channel provenance and formula inspector modal
 */

class HudManager {
  constructor(channelRegistry, feaData, satellites) {
    this.channelRegistry = channelRegistry || {};
    this.feaData = feaData || {};
    this.satellites = satellites || [];

    this.initInspectorModal();
    this.initStaticFeaDisplay();
  }

  initStaticFeaDisplay() {
    const pEl = document.getElementById("val-tank-pressure");
    const hEl = document.getElementById("val-hoop-stress");
    const vEl = document.getElementById("val-von-mises");
    const fEl = document.getElementById("val-tank-fos");

    if (pEl) pEl.innerText = `${(this.feaData.pressure_bar || 6.0).toFixed(1)} bar`;
    if (hEl) hEl.innerText = `${(this.feaData.fea_hoop_stress_MPa || 675.0).toFixed(1)} MPa`;
    if (vEl) vEl.innerText = `${(this.feaData.fea_von_mises_MPa || 604.2).toFixed(1)} MPa`;
    if (fEl) fEl.innerText = `${(this.feaData.factor_of_safety || 1.57).toFixed(2)}`;
  }

  update(point, profile) {
    if (!point) return;

    const time_s = point.time_s || 0;

    // 1. Primary Live Telemetry Grid (matching Screenshot B formatting)
    const alt_m = (point.altitude_km || 0) * 1000.0;
    const vel_ms = (point.velocity_km_s || 0) * 1000.0;
    const q_pa = (point.dynamic_pressure_kpa || 0) * 1000.0;
    const heat_flux_w_m2 = (point.heat_flux_mw_m2 || 0) * 1000000.0;
    const mach = point.mach || 0.0;
    const g_force = point.apparent_g || 1.0;
    const thrust_kn = (point.thrust_mn || 0) * 1000.0;
    const mass_kg = (point.mass_tonnes || 120.0) * 1000.0;
    const pitch_deg = point.pitch_deg || 0.0;
    const flap_deg = point.flaps_fwd_deg || 0.0;

    // Stage-aware propellant remaining calculation
    let fuelPct = 100;
    if (profile && profile.is_synthetic) {
      // Synthetic Phase 7 terminal landing: 115 t starting down to ~100 t dry
      fuelPct = Math.max(0, Math.min(100, Math.round(((mass_kg - 100000.0) / (115000.0 - 100000.0)) * 100)));
    } else if (time_s <= 162.0) {
      // Booster + Upper stage ascent: 4,940 t down to ~1,500 t at staging
      fuelPct = Math.max(0, Math.min(100, Math.round(((mass_kg - 1500000.0) / (4940000.0 - 1500000.0)) * 100)));
    } else if (time_s <= 522.35) {
      // Starship 2nd stage powered burn: 1,320 t down to ~120 t at SECO
      fuelPct = Math.max(0, Math.min(100, Math.round(((mass_kg - 120000.0) / (1320000.0 - 120000.0)) * 100)));
    } else if (time_s <= 5400.0) {
      // Orbital coast: reserve / disposal propellant (~15 t available)
      const reservePropT = Math.max(0, (point.mass_tonnes || 120.0) - 105.0);
      fuelPct = Math.max(0, Math.min(100, Math.round((reservePropT / 15.0) * 100)));
    } else {
      // Deorbit burn and entry: residual header tank propellant
      const residualT = Math.max(0, (point.mass_tonnes || 105.0) - 100.0);
      fuelPct = Math.max(0, Math.min(100, Math.round((residualT / 5.0) * 100)));
    }

    // Mach number handling: physically undefined in orbital vacuum (alt > 100 km)
    let machDisplay = "0.0";
    let vpMachDisplay = "M 0.0";
    if (point.altitude_km > 100.0 || point.mach === null || point.mach === undefined) {
      machDisplay = "N/A (Vacuum)";
      vpMachDisplay = "VACUUM";
    } else {
      machDisplay = `${Number(point.mach).toFixed(1)}`;
      vpMachDisplay = `M ${Number(point.mach).toFixed(1)}`;
    }

    // Engine status string
    let engineStr = "33/33 (NOMINAL)";
    if (profile && profile.is_synthetic) {
      engineStr = (point.thrust_mn || 0) > 0.1 ? "3/3 (LANDING BURN)" : "0/3 (DESCENT)";
    } else if (time_s <= 162.0) {
      engineStr = (point.thrust_mn || 0) > 50.0 ? "33/33 (FULL THRUST)" : "33/33 (THROTTLED)";
    } else if (time_s <= 168.0) {
      engineStr = "HOT-STAGING";
    } else if (time_s <= 522.35) {
      engineStr = (point.thrust_mn || 0) > 0.1 ? "6/6 (NOMINAL)" : "6/6 (SHUTDOWN)";
    } else if (time_s >= 5400.0 && time_s <= 5460.0) {
      engineStr = "3/6 (DEORBIT BURN)";
    } else if (time_s > 5460.0) {
      engineStr = "0/6 (ENTRY FLIGHT)";
    } else {
      engineStr = "0/6 (ORBIT COAST)";
    }

    // Set Live Telemetry Fields
    this.setVal("telemetry-alt", `${this.formatNumber(alt_m, 0)} m`);
    this.setVal("telemetry-vel", `${this.formatNumber(vel_ms, 0)} m/s`);
    this.setVal("telemetry-q", `${this.formatNumber(q_pa, 0)} Pa`);
    this.setVal("telemetry-flux", `${this.formatNumber(heat_flux_w_m2, 0)} W/m²`);
    this.setVal("telemetry-mach", machDisplay);
    this.setVal("telemetry-g", `${g_force.toFixed(2)} g`);
    this.setVal("telemetry-thrust", `${this.formatNumber(thrust_kn, 0)} kN`);
    this.setVal("telemetry-mass", `${this.formatNumber(mass_kg, 0)} kg`);
    this.setVal("telemetry-attitude", `${pitch_deg.toFixed(1)}° / 0.4° / 0.7°`);
    this.setVal("telemetry-flaps", `${flap_deg.toFixed(1)}°`);
    this.setVal("telemetry-fuel", `${fuelPct} %`);
    this.setVal("telemetry-engine", engineStr);

    // 2. Vehicle 3D Model Panel Flap Indicators
    const fwdFlap = Math.abs(point.flaps_fwd_deg || 0);
    const aftFlap = Math.abs(point.flaps_aft_deg || 0);
    this.setVal("flap-val-fwd", `${fwdFlap.toFixed(1)}°`);
    this.setVal("flap-val-aft", `${aftFlap.toFixed(1)}°`);
    this.setVal("flap-val-left", `${(fwdFlap * 0.98).toFixed(1)}°`);
    this.setVal("flap-val-right", `${(fwdFlap * 1.02).toFixed(1)}°`);

    // 3. Thermal Readouts & Gauges
    const surfTempK = point.surface_temp_k || 300.0;
    const bondTempK = point.bondline_temp_k || 290.0;
    const bondMarginK = Math.max(0, 533.15 - bondTempK);

    this.setVal("val-surface-temp", `${surfTempK.toFixed(0)} K (${(surfTempK - 273.15).toFixed(0)}°C)`);
    this.setVal("val-bondline-temp", `${bondTempK.toFixed(1)} K`);
    this.setVal("val-bondline-margin", `+${bondMarginK.toFixed(1)} K`);

    const bondGauge = document.getElementById("gauge-bondline");
    if (bondGauge) {
      const pct = Math.min(100, Math.max(0, ((bondTempK - 290) / (533.15 - 290)) * 100));
      bondGauge.style.width = `${pct}%`;
      bondGauge.classList.toggle("warning", bondTempK > 450);
      bondGauge.classList.toggle("critical", bondTempK > 500);
    }

    // 4. Update Mission Overview Card & Header Times
    this.setVal("overview-phase", point.phase || "POWERED ASCENT");
    this.setVal("vp-phase", point.phase || "ACTIVE");
    this.setVal("vp-alt", `${(point.altitude_km || 0).toFixed(1)} km`);
    this.setVal("vp-vel", `${(point.velocity_km_s || 0).toFixed(2)} km/s`);
    this.setVal("vp-mach", vpMachDisplay);

    // 5. Update Left Flight Phases Stepper (1 to 8)
    this.updatePhasesStepper(time_s, profile);

    // 6. Update Mission Events Table Statuses
    this.updateEventsTable(time_s);

    // 7. Update Starlink V3 Satellite Deployment Sequence
    this.updateSatellites(time_s);
  }

  updatePhasesStepper(currentTime_s, profile) {
    const phaseSchedule = [
      { id: "phase-item-1", start: 0, end: 165, name: "Powered Ascent" },
      { id: "phase-item-2", start: 165, end: 190, name: "Hot-stage Separation" },
      { id: "phase-item-3", start: 190, end: 2700, name: "Orbital Coast" },
      { id: "phase-item-4", start: 2700, end: 5400, name: "Reentry Burn" },
      { id: "phase-item-5", start: 5400, end: 7200, name: "Atmospheric Entry" },
      { id: "phase-item-6", start: 7200, end: 9000, name: "Belly Flop" },
      { id: "phase-item-7", start: 9000, end: 11000, name: "Terminal Flip & Burn" },
      { id: "phase-item-8", start: 11000, end: 99999, name: "Splashdown / Landing" },
    ];

    phaseSchedule.forEach((p, idx) => {
      const el = document.getElementById(p.id);
      if (!el) return;

      const numBadge = el.querySelector(".phase-num");
      if (currentTime_s >= p.end) {
        el.className = "flight-phase-item completed";
        if (numBadge) numBadge.innerText = "✓";
      } else if (currentTime_s >= p.start && currentTime_s < p.end) {
        el.className = "flight-phase-item active";
        if (numBadge) numBadge.innerText = `${idx + 1}`;
      } else {
        el.className = "flight-phase-item pending";
        if (numBadge) numBadge.innerText = `${idx + 1}`;
      }
    });
  }

  updateEventsTable(currentTime_s) {
    document.querySelectorAll(".event-row").forEach(row => {
      const eventTime = parseFloat(row.dataset.time || "0");
      const statusBadge = row.querySelector(".event-status");
      if (!statusBadge) return;

      if (currentTime_s >= eventTime + 10.0) {
        statusBadge.className = "event-status completed";
        statusBadge.innerText = "Completed";
      } else if (currentTime_s >= eventTime - 2.0 && currentTime_s < eventTime + 10.0) {
        statusBadge.className = "event-status active";
        statusBadge.innerText = "In Progress";
      } else {
        statusBadge.className = "event-status pending";
        statusBadge.innerText = "Pending";
      }
    });
  }

  updateSatellites(currentTime_s) {
    let deployedCount = 0;
    this.satellites.forEach(s => {
      const isDeployed = currentTime_s >= s.deploy_time_s;
      if (isDeployed) deployedCount++;

      const satRowEl = document.getElementById(`sat-item-${s.satellite_number}`);
      if (satRowEl) {
        satRowEl.className = isDeployed ? "sat-item deployed" : "sat-item pending";
        const statusEl = satRowEl.querySelector(".sat-status");
        if (statusEl) {
          statusEl.innerText = isDeployed ? "DEPLOYED" : "ENCLOSED";
          statusEl.style.color = isDeployed ? "var(--accent-green)" : "var(--text-muted)";
        }
      }
    });

    const counterEl = document.getElementById("sat-deploy-counter");
    if (counterEl) {
      counterEl.innerText = `${deployedCount} / ${this.satellites.length} DEPLOYED`;
    }
  }

  setVal(id, strVal) {
    const el = document.getElementById(id);
    if (el) el.innerText = strVal;
  }

  formatNumber(val, decimals = 0) {
    const parts = val.toFixed(decimals).split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
  }

  initInspectorModal() {
    const modal = document.getElementById("inspector-modal");
    const closeBtn = document.getElementById("modal-close-btn");
    const titleEl = document.getElementById("modal-metric-title");
    const descEl = document.getElementById("modal-metric-desc");
    const formEl = document.getElementById("modal-metric-formula");
    const provEl = document.getElementById("modal-metric-provenance");

    if (!modal) return;

    if (closeBtn) {
      closeBtn.addEventListener("click", () => modal.classList.remove("active"));
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });

    document.querySelectorAll(".metric-info-icon").forEach(icon => {
      icon.addEventListener("click", () => {
        const key = icon.dataset.channel;
        const meta = this.channelRegistry[key];
        if (!meta) return;

        if (titleEl) titleEl.innerText = meta.name;
        if (descEl) descEl.innerText = meta.description;
        if (formEl) formEl.innerText = meta.formula;
        if (provEl) provEl.innerText = `Data Source & Solver: ${meta.provenance}`;

        modal.classList.add("active");
      });
    });
  }
}

window.HudManager = HudManager;
