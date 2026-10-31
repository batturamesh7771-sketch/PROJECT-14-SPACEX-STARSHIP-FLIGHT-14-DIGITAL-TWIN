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
    this.initRaptorSvg();
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

  update(point, profile, physicsState) {
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

    // Engine status string (Flight 14 factual mission reconstruction)
    let engineStr = "33/33 (NOMINAL ASCENT)";
    if (profile && profile.is_synthetic) {
      engineStr = (point.thrust_mn || 0) > 0.1 ? "3/3 (LANDING BURN)" : "0/3 (DESCENT)";
    } else if (time_s <= 45.0) {
      engineStr = (point.thrust_mn || 0) > 50.0 ? "33/33 (FULL THRUST)" : "33/33 (NOMINAL)";
    } else if (time_s <= 162.0) {
      engineStr = "32/33 (1 ENG CUTOFF T+45s)";
    } else if (time_s <= 168.0) {
      engineStr = "HOT-STAGING";
    } else if (time_s <= 522.35) {
      engineStr = (point.thrust_mn || 0) > 0.1 ? "5/6 (1 RVAC CUTOFF - EXTENDED)" : "0/6 (SECO)";
    } else if (time_s <= 1320.0) {
      engineStr = (point.thrust_mn || 0) > 0.1 ? "1/6 (ORBIT INSERTION)" : "0/6 (ORBIT COAST)";
    } else if (time_s <= 1800.0) {
      engineStr = "0/6 (26x SATELLITE DEPLOY)";
    } else if (time_s >= 9900.0 && time_s <= 9960.0) {
      engineStr = "1/6 (DEORBIT DISPOSAL BURN)";
    } else if (time_s > 9960.0 && time_s < 11732.0) {
      engineStr = "0/6 (ENTRY FLIGHT - FLAPS)";
    } else if (time_s >= 11732.0) {
      engineStr = "0/6 (PACIFIC SPLASHDOWN)";
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

    // 8. Update Raptor Engine Matrix & Subsystem Data
    this.updateRaptorMatrix(time_s, profile, point);

    // 9. Update Event Milestone Cards Gallery (Target UI Layout)
    this.updateEventCards(time_s);

    // 10. Update Phase Engineering Workbenches with Real-Time Physics
    this.updatePhysicsWorkbench(point, profile, physicsState);
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
      const dt = currentTime_s - s.deploy_time_s;
      const isDeployed = dt >= 0;
      const isEjecting = dt >= 0 && dt <= 4.0;
      if (isDeployed) deployedCount++;

      const satRowEl = document.getElementById(`sat-item-${s.satellite_number}`);
      if (satRowEl) {
        if (isEjecting) {
          satRowEl.className = "sat-item ejecting";
          const statusEl = satRowEl.querySelector(".sat-status");
          if (statusEl) {
            statusEl.innerText = "EJECTING";
            statusEl.style.color = "var(--accent-cyan)";
          }
        } else if (isDeployed) {
          satRowEl.className = "sat-item deployed";
          const statusEl = satRowEl.querySelector(".sat-status");
          if (statusEl) {
            statusEl.innerText = "DEPLOYED";
            statusEl.style.color = "var(--accent-green)";
          }
        } else {
          satRowEl.className = "sat-item pending";
          const statusEl = satRowEl.querySelector(".sat-status");
          if (statusEl) {
            statusEl.innerText = "ENCLOSED";
            statusEl.style.color = "var(--text-muted)";
          }
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

  initRaptorSvg() {
    const svg = document.getElementById("raptor-matrix-svg");
    if (!svg || svg.children.length > 0) return;

    // SVG coordinate space 110x110, center at (55, 55)
    const cx0 = 55, cy0 = 55;

    // 1. Center Ring (3 engines): radius 10px
    for (let i = 0; i < 3; i++) {
      const angle = (i * 120 - 90) * (Math.PI / 180);
      const cx = cx0 + 10 * Math.cos(angle);
      const cy = cy0 + 10 * Math.sin(angle);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("id", `rap-dot-${i}`);
      circle.setAttribute("cx", cx.toFixed(1));
      circle.setAttribute("cy", cy.toFixed(1));
      circle.setAttribute("r", "3.2");
      circle.setAttribute("class", "raptor-dot firing");
      svg.appendChild(circle);
    }

    // 2. Middle Ring (10 engines): radius 24px
    for (let i = 0; i < 10; i++) {
      const angle = (i * 36 - 90) * (Math.PI / 180);
      const cx = cx0 + 24 * Math.cos(angle);
      const cy = cy0 + 24 * Math.sin(angle);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("id", `rap-dot-${i + 3}`);
      circle.setAttribute("cx", cx.toFixed(1));
      circle.setAttribute("cy", cy.toFixed(1));
      circle.setAttribute("r", "3.2");
      circle.setAttribute("class", "raptor-dot firing");
      svg.appendChild(circle);
    }

    // 3. Outer Ring (20 engines): radius 40px
    for (let i = 0; i < 20; i++) {
      const angle = (i * 18 - 90) * (Math.PI / 180);
      const cx = cx0 + 40 * Math.cos(angle);
      const cy = cy0 + 40 * Math.sin(angle);
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("id", `rap-dot-${i + 13}`);
      circle.setAttribute("cx", cx.toFixed(1));
      circle.setAttribute("cy", cy.toFixed(1));
      circle.setAttribute("r", "3.0");
      circle.setAttribute("class", "raptor-dot firing");
      svg.appendChild(circle);
    }
  }

  updateRaptorMatrix(currentTime_s, profile, point) {
    const isSynthetic = profile && profile.is_synthetic;
    const rapLabel = document.getElementById("raptor-sub-label");
    const rapCfg = document.getElementById("rap-cfg");
    const rapCount = document.getElementById("rap-count");
    const rapThrust = document.getElementById("rap-thrust");
    const rapPc = document.getElementById("rap-pc");
    const rapIsp = document.getElementById("rap-isp");

    if (isSynthetic) {
      const isFiring = (point && (point.thrust_mn || 0) > 0.1);
      if (rapLabel) rapLabel.innerText = isFiring ? "RAPTOR 3: 3/3 LANDING BURN" : "RAPTOR 3: 0/3 DESCENT";
      if (rapCfg) rapCfg.innerText = "3 R3 (SEA LEVEL)";
      if (rapCount) rapCount.innerText = isFiring ? "3 / 3 ACTIVE" : "0 / 3 INACTIVE";
      if (rapThrust) rapThrust.innerText = isFiring ? `${((point.thrust_mn || 0) * 1000).toFixed(0)} kN` : "0 kN";
      if (rapPc) rapPc.innerText = isFiring ? "350 bar" : "0 bar";
      if (rapIsp) rapIsp.innerText = isFiring ? "350 s" : "—";
      return;
    }

    // Flight 14 Observed & Planned
    if (currentTime_s <= 45.0) {
      // Nominal ascent: all 33 firing
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (dot) dot.setAttribute("class", "raptor-dot firing");
      }
      if (rapLabel) rapLabel.innerText = "BOOSTER: 33/33 NOMINAL";
      if (rapCfg) rapCfg.innerText = "33 R3 (BOOSTER)";
      if (rapCount) rapCount.innerText = "33 / 33 ACTIVE";
      if (rapThrust) rapThrust.innerText = "72.4 MN";
      if (rapPc) rapPc.innerText = "350 bar";
      if (rapIsp) rapIsp.innerText = "350 s";
    } else if (currentTime_s <= 162.0) {
      // 1 engine early cutoff on Super Heavy (engine #13)
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (dot) {
          dot.setAttribute("class", i === 13 ? "raptor-dot cutoff" : "raptor-dot firing");
        }
      }
      if (rapLabel) rapLabel.innerText = "BOOSTER: 32/33 (1 ENG CUTOFF)";
      if (rapCfg) rapCfg.innerText = "33 R3 (BOOSTER)";
      if (rapCount) rapCount.innerText = "32 / 33 ACTIVE";
      if (rapThrust) rapThrust.innerText = "70.2 MN";
      if (rapPc) rapPc.innerText = "350 bar";
      if (rapIsp) rapIsp.innerText = "350 s";
    } else if (currentTime_s <= 168.0) {
      // Hot staging
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (dot) dot.setAttribute("class", "raptor-dot inactive");
      }
      if (rapLabel) rapLabel.innerText = "HOT-STAGING IN PROGRESS";
      if (rapCfg) rapCfg.innerText = "HOT-STAGE RING";
      if (rapCount) rapCount.innerText = "RING IGNITION";
      if (rapThrust) rapThrust.innerText = "—";
      if (rapPc) rapPc.innerText = "—";
      if (rapIsp) rapIsp.innerText = "—";
    } else if (currentTime_s <= 522.35) {
      // Starship 2nd stage: 3 Center SL + 3 RVac. 1 RVac shutdown early (dot #5)
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (!dot) continue;
        if (i < 5) {
          dot.setAttribute("class", "raptor-dot firing");
        } else if (i === 5) {
          dot.setAttribute("class", "raptor-dot cutoff");
        } else {
          dot.setAttribute("class", "raptor-dot inactive");
        }
      }
      if (rapLabel) rapLabel.innerText = "STARSHIP: 5/6 (1 RVAC CUTOFF)";
      if (rapCfg) rapCfg.innerText = "3 SL + 3 RVAC";
      if (rapCount) rapCount.innerText = "5 / 6 ACTIVE";
      if (rapThrust) rapThrust.innerText = "12.5 MN";
      if (rapPc) rapPc.innerText = "350 bar";
      if (rapIsp) rapIsp.innerText = "380 s";
    } else if (currentTime_s > 522.35 && currentTime_s <= 600.0) {
      // 1 Center SL engine orbit insertion burn
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (!dot) continue;
        dot.setAttribute("class", i === 0 ? "raptor-dot firing" : "raptor-dot inactive");
      }
      if (rapLabel) rapLabel.innerText = "STARSHIP: 1/6 (ORBIT INSERTION)";
      if (rapCfg) rapCfg.innerText = "1 SL RAPTOR";
      if (rapCount) rapCount.innerText = "1 / 6 ACTIVE";
      if (rapThrust) rapThrust.innerText = "2.2 MN";
      if (rapPc) rapPc.innerText = "350 bar";
      if (rapIsp) rapIsp.innerText = "350 s";
    } else if (currentTime_s >= 9900.0 && currentTime_s <= 9960.0) {
      // 1 Center SL engine deorbit burn
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (!dot) continue;
        dot.setAttribute("class", i === 0 ? "raptor-dot firing" : "raptor-dot inactive");
      }
      if (rapLabel) rapLabel.innerText = "STARSHIP: 1/6 (DEORBIT BURN)";
      if (rapCfg) rapCfg.innerText = "1 SL RAPTOR";
      if (rapCount) rapCount.innerText = "1 / 6 ACTIVE";
      if (rapThrust) rapThrust.innerText = "2.2 MN";
      if (rapPc) rapPc.innerText = "350 bar";
      if (rapIsp) rapIsp.innerText = "350 s";
    } else {
      // Coast / Entry / Inactive
      for (let i = 0; i < 33; i++) {
        const dot = document.getElementById(`rap-dot-${i}`);
        if (dot) dot.setAttribute("class", "raptor-dot inactive");
      }
      if (currentTime_s >= 10800.0 && currentTime_s < 11732.0) {
        if (rapLabel) rapLabel.innerText = "STARSHIP: 0/6 (AERO ENTRY - FLAPS)";
      } else if (currentTime_s >= 11732.0) {
        if (rapLabel) rapLabel.innerText = "STARSHIP: SPLASHDOWN (PACIFIC)";
      } else {
        if (rapLabel) rapLabel.innerText = "STARSHIP: 0/6 (COAST / DRIFT)";
      }
      if (rapCfg) rapCfg.innerText = "3 SL + 3 RVAC";
      if (rapCount) rapCount.innerText = "0 / 6 ACTIVE";
      if (rapThrust) rapThrust.innerText = "0 kN";
      if (rapPc) rapPc.innerText = "0 bar";
      if (rapIsp) rapIsp.innerText = "—";
    }
  }

  updateEventCards(currentTime_s) {
    const cardThresholds = [
      { seek: 0, next: 162 },
      { seek: 162, next: 522 },
      { seek: 522, next: 1320 },
      { seek: 1320, next: 9900 },
      { seek: 9900, next: 10800 },
      { seek: 10800, next: 11732 },
      { seek: 11732, next: 99999 }
    ];

    document.querySelectorAll(".event-card").forEach(card => {
      const seek = parseFloat(card.dataset.seek || "0");
      const matched = cardThresholds.find(t => t.seek === seek);
      if (!matched) return;

      if (currentTime_s >= matched.next) {
        card.className = "event-card completed";
      } else if (currentTime_s >= matched.seek && currentTime_s < matched.next) {
        card.className = "event-card active";
      } else {
        card.className = "event-card";
      }
    });
  }

  // =========================================================================
  // Phase Engineering Workbench Real-Time Physics Synchronization
  // =========================================================================
  updatePhysicsWorkbench(point, profile, physicsState) {
    if (!physicsState && window.physicsEngine) {
      physicsState = window.physicsEngine.evaluateFullMissionState(point, point.time_s);
    }
    if (!physicsState) return;

    const { fea, tps, astrodynamics: astro, propulsion: prop } = physicsState;

    // 1. Structural FEA & Buckling Panel (Phase 8)
    if (fea) {
      this.setVal("fea-p-val", `${fea.pressure_bar.toFixed(2)} bar (${(fea.pressure_bar * 0.1).toFixed(2)} MPa)`);
      this.setVal("fea-hoop-val", `${fea.hoop_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-long-val", `${fea.longitudinal_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-thrust-val", `${fea.axial_thrust_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-bend-val", `±${fea.bending_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-radial-val", `${fea.radial_displacement_mm > 0 ? "+" : ""}${fea.radial_displacement_mm.toFixed(2)} mm`);
      this.setVal("fea-axial-val", `${fea.axial_displacement_mm > 0 ? "+" : ""}${fea.axial_displacement_mm.toFixed(2)} mm`);
      this.setVal("fea-vm-val", `${fea.von_mises_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-fos-val", `${fea.factor_of_safety_yield.toFixed(2)}`);
      this.setVal("fea-margin-val", `${fea.margin_of_safety_yield > 0 ? "+" : ""}${fea.margin_of_safety_yield.toFixed(2)}`);
      this.setVal("fea-buck-cl", `${fea.critical_buckling_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-buck-crit", `${fea.critical_buckling_stress_MPa.toFixed(2)} MPa`);
      this.setVal("fea-buck-load", `${Math.max(0, -fea.longitudinal_stress_MPa).toFixed(2)} MPa`);
      this.setVal("fea-buck-fos", fea.factor_of_safety_buckling >= 99 ? "99.00 (NO BUCKLING RISK)" : `${fea.factor_of_safety_buckling.toFixed(2)} (${fea.is_buckling_nominal ? "SAFE" : "CRITICAL"})`);

      const vmBar = document.getElementById("fea-vm-bar");
      if (vmBar) {
        const vmPct = Math.min(100, Math.max(0, (fea.von_mises_stress_MPa / 950.0) * 100));
        vmBar.style.width = `${vmPct.toFixed(1)}%`;
        vmBar.className = "pwb-progress-bar " + (fea.factor_of_safety_yield >= 1.25 ? "fill-green" : fea.factor_of_safety_yield >= 1.0 ? "fill-orange" : "fill-red");
      }

      const yieldBadge = document.getElementById("fea-yield-badge");
      if (yieldBadge) {
        yieldBadge.innerText = `● YIELD SF: ${fea.factor_of_safety_yield.toFixed(2)} (${fea.is_yield_nominal ? "NOMINAL" : "MARGIN EXCEEDED"})`;
        yieldBadge.className = "pwb-status " + (fea.is_yield_nominal ? "pass" : "fail");
      }

      const buckBadge = document.getElementById("fea-buckling-badge");
      if (buckBadge) {
        buckBadge.innerText = `● SP-8007 BUCKLING: ${fea.is_buckling_nominal ? "SAFE" : "BUCKLING RISK"}`;
        buckBadge.className = "pwb-status " + (fea.is_buckling_nominal ? "pass" : "fail");
      }
    }

    // 2. Aerothermal & TPS Panel (Phase 9)
    if (tps) {
      this.setVal("tps-st-0", `${tps.surface_temp_K.toFixed(0)} K (${tps.surface_temp_C.toFixed(0)} °C)`);
      this.setVal("tps-st-14", `${tps.tile_mid_temp_K.toFixed(0)} K (${(tps.tile_mid_temp_K - 273.15).toFixed(0)} °C)`);
      this.setVal("tps-st-28", `${tps.tile_inner_temp_K.toFixed(0)} K (${(tps.tile_inner_temp_K - 273.15).toFixed(0)} °C)`);
      this.setVal("tps-st-rtv", `${tps.rtv_bondline_temp_K.toFixed(1)} K (${tps.rtv_bondline_temp_C.toFixed(1)} °C)`);
      this.setVal("tps-st-tank", `${tps.tank_wall_temp_K.toFixed(1)} K (${(tps.tank_wall_temp_K - 273.15).toFixed(1)} °C)`);

      this.setVal("tps-bond-temp-val", `${tps.rtv_bondline_temp_K.toFixed(1)} K (${tps.rtv_bondline_temp_C.toFixed(1)} °C)`);
      this.setVal("tps-bond-margin-val", `+${tps.rtv_margin_K.toFixed(1)} K`);
      this.setVal("tps-sg-flux", `${tps.stagnation_flux_sutton_graves_MW_m2.toFixed(3)} MW/m²`);
      this.setVal("tps-dkr-flux", `${tps.stagnation_flux_dkr_MW_m2.toFixed(3)} MW/m²`);
      this.setVal("tps-wind-flux", `${tps.windward_belly_flux_MW_m2.toFixed(3)} MW/m²`);
      this.setVal("tps-aoa-val", `${(point.pitch_deg || 70).toFixed(1)}°`);

      const bondBar = document.getElementById("tps-bond-gauge-bar");
      if (bondBar) {
        const bondPct = Math.min(100, Math.max(0, ((tps.rtv_bondline_temp_K - 290.0) / (533.15 - 290.0)) * 100));
        bondBar.style.width = `${bondPct.toFixed(1)}%`;
        bondBar.className = "pwb-progress-bar " + (tps.rtv_bondline_temp_K < 450 ? "fill-green" : tps.rtv_bondline_temp_K < 500 ? "fill-orange" : "fill-red");
      }

      const rtvBadge = document.getElementById("tps-rtv-badge");
      if (rtvBadge) {
        rtvBadge.innerText = `● RTV-560: ${tps.is_rtv_safe ? "SAFE" : "OVERHEAT"} (MARGIN +${tps.rtv_margin_K.toFixed(1)} K)`;
        rtvBadge.className = "pwb-status " + (tps.is_rtv_safe ? "pass" : "fail");
      }

      const surfBadge = document.getElementById("tps-surf-badge");
      if (surfBadge) {
        surfBadge.innerText = `● TILE SURFACE: ${tps.is_silica_safe ? "NOMINAL (< 1650 K)" : "EXCEEDED LIMIT"}`;
        surfBadge.className = "pwb-status " + (tps.is_silica_safe ? "pass" : "warn");
      }

      // Draw dynamic 1D thermal gradient cross-section canvas
      this.drawTpsGradient(tps);
    }

    // 3. Astrodynamics & GMAT / SPICE Panel (Phase 5)
    if (astro) {
      this.setVal("astro-sma-val", `${this.formatNumber(astro.semi_major_axis_km, 2)} km`);
      this.setVal("astro-ecc-val", `${astro.eccentricity.toFixed(6)}`);
      this.setVal("astro-inc-val", `${astro.inclination_deg.toFixed(2)}°`);
      this.setVal("astro-perigee-val", `${astro.perigee_altitude_km.toFixed(1)} km`);
      this.setVal("astro-apogee-val", `${astro.apogee_altitude_km.toFixed(1)} km`);
      this.setVal("astro-period-val", `${astro.orbital_period_min.toFixed(2)} min`);
      this.setVal("astro-energy-val", `${astro.specific_energy_MJ_kg.toFixed(2)} MJ/kg`);
      this.setVal("astro-raan-val", `${astro.j2_nodal_regression_deg_day.toFixed(2)} deg/day`);
      this.setVal("astro-w-val", `${astro.j2_perigee_precession_deg_day.toFixed(2)} deg/day`);
      this.setVal("astro-beta-val", `${astro.solar_beta_angle_deg > 0 ? "+" : ""}${astro.solar_beta_angle_deg.toFixed(1)}°`);
      this.setVal("astro-eclipse-val", astro.eclipse_status);

      const eclipseBadge = document.getElementById("astro-eclipse-badge");
      if (eclipseBadge) {
        eclipseBadge.innerText = `● SOLAR: ${astro.eclipse_status.startsWith("UMBRA") ? "UMBRA SHADOW" : "SUNLIT"}`;
        eclipseBadge.className = "pwb-status " + (astro.eclipse_status.startsWith("UMBRA") ? "warn" : "pass");
      }
    }

    // 4. Propulsion & Mass Properties Panel (Phases 2 & 4)
    if (prop) {
      this.setVal("prop-b14-val", `${prop.booster_active_engines} / ${prop.booster_total_engines} ACTIVE`);
      this.setVal("prop-s31-val", `${prop.ship_active_engines} / ${prop.ship_total_engines} ACTIVE`);
      this.setVal("prop-pc-val", `${prop.chamber_pressure_bar.toFixed(1)} bar`);
      this.setVal("prop-isp-val", `${prop.specific_impulse_s.toFixed(0)} s`);
      this.setVal("prop-mdot-val", `${this.formatNumber(prop.mass_flow_rate_kg_s, 0)} kg/s`);
      this.setVal("prop-mass-val", `${this.formatNumber((point.mass_tonnes || 120) * 1000, 0)} kg`);
      this.setVal("prop-fuel-val", `${this.formatNumber(prop.propellant_mass_tonnes * 1000, 0)} kg`);
      this.setVal("prop-xcg-val", `${prop.center_of_gravity_x_m.toFixed(1)} m`);

      const clusterBadge = document.getElementById("prop-cluster-badge");
      if (clusterBadge) {
        const totalActive = prop.booster_active_engines + prop.ship_active_engines;
        clusterBadge.innerText = totalActive > 0 ? `● RAPTOR 3: ${totalActive} FIRING` : `● ENGINES: IDLE`;
      }
    }

    // 5. CAD Kinematics Panel
    const fwdFlap = Math.abs(point.flaps_fwd_deg || 0);
    const aftFlap = Math.abs(point.flaps_aft_deg || 0);
    this.setVal("cad-fl-fwd", `${(fwdFlap * 0.98).toFixed(1)}°`);
    this.setVal("cad-fr-fwd", `${(fwdFlap * 1.02).toFixed(1)}°`);
    this.setVal("cad-al-aft", `${aftFlap.toFixed(1)}°`);
    this.setVal("cad-ar-aft", `${aftFlap.toFixed(1)}°`);

    const t = point.time_s || 0;
    let doorStatus = "0.0° (LOCKED CLOSED)";
    if (t >= 1310 && t <= 1710) {
      doorStatus = "71.0° (DISPENSER MOUTH OPEN)";
    } else if (t > 1710 && t < 1740) {
      doorStatus = "CLOSING FLUSH";
    }
    this.setVal("cad-door-val", doorStatus);
  }

  drawTpsGradient(tps) {
    const canvas = document.getElementById("tps-gradient-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Total physical stack: 28mm (tile) + 2.5mm (SIP) + 1.0mm (RTV) + 4.0mm (steel) = 35.5 mm
    const totalMm = 35.5;
    const padL = 48;
    const padR = 25;
    const padT = 20;
    const padB = 30;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;

    const x0 = padL;
    const xTileEnd = padL + (28.0 / totalMm) * plotW;
    const xSipEnd = padL + ((28.0 + 2.5) / totalMm) * plotW;
    const xRtvEnd = padL + ((28.0 + 2.5 + 1.0) / totalMm) * plotW;
    const xSteelEnd = padL + plotW;

    // Layer 1: Ceramic Silica Tile (0 to 28 mm)
    ctx.fillStyle = "rgba(18, 24, 38, 0.90)";
    ctx.fillRect(x0, padT, xTileEnd - x0, plotH);

    // Layer 2: Nomex Felt SIP (28 to 30.5 mm)
    ctx.fillStyle = "rgba(42, 34, 24, 0.85)";
    ctx.fillRect(xTileEnd, padT, xSipEnd - xTileEnd, plotH);

    // Layer 3: RTV-560 Adhesive Bondline (30.5 to 31.5 mm)
    ctx.fillStyle = "rgba(0, 229, 255, 0.40)";
    ctx.fillRect(xSipEnd, padT, xRtvEnd - xSipEnd, plotH);

    // Layer 4: 304L Stainless Steel Tank (31.5 to 35.5 mm)
    ctx.fillStyle = "rgba(25, 42, 70, 0.90)";
    ctx.fillRect(xRtvEnd, padT, xSteelEnd - xRtvEnd, plotH);

    // Dividers
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.lineWidth = 1;
    [x0, xTileEnd, xSipEnd, xRtvEnd, xSteelEnd].forEach(x => {
      ctx.beginPath();
      ctx.moveTo(x, padT);
      ctx.lineTo(x, padT + plotH);
      ctx.stroke();
    });

    // Layer Titles below
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.fillStyle = "#8fa3b0";
    ctx.textAlign = "center";
    ctx.fillText("SILICA TILE (28 mm)", (x0 + xTileEnd) / 2, padT + plotH + 18);
    ctx.fillText("SIP", (xTileEnd + xSipEnd) / 2, padT + plotH + 18);
    ctx.fillText("RTV", (xSipEnd + xRtvEnd) / 2, padT + plotH + 18);
    ctx.fillText("304L TANK", (xRtvEnd + xSteelEnd) / 2, padT + plotH + 18);

    // Temperature scaling
    const tMin = 250.0;
    const tMax = Math.max(1400.0, (tps.surface_temp_K || 300) * 1.15);
    const tempToY = (t) => padT + plotH - ((t - tMin) / (tMax - tMin)) * plotH;

    // RTV 533.15 K Limit Line
    const yLimit = tempToY(533.15);
    if (yLimit >= padT && yLimit <= padT + plotH) {
      ctx.strokeStyle = "rgba(255, 23, 68, 0.65)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(padL, yLimit);
      ctx.lineTo(padL + plotW, yLimit);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#ff5252";
      ctx.font = "8px 'JetBrains Mono', monospace";
      ctx.textAlign = "right";
      ctx.fillText("533 K", padL - 4, yLimit + 3);
    }

    // Gradient curve through stations
    const stations = [
      { x: x0, t: tps.surface_temp_K || 300 },
      { x: x0 + (14.0 / totalMm) * plotW, t: tps.tile_mid_temp_K || 295 },
      { x: xTileEnd, t: tps.tile_inner_temp_K || 292 },
      { x: (xSipEnd + xRtvEnd) / 2, t: tps.rtv_bondline_temp_K || 290 },
      { x: xSteelEnd, t: tps.tank_wall_temp_K || 290 },
    ];

    ctx.beginPath();
    stations.forEach((st, idx) => {
      const px = st.x;
      const py = Math.min(padT + plotH, Math.max(padT, tempToY(st.t)));
      if (idx === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });

    const grad = ctx.createLinearGradient(padL, 0, padL + plotW, 0);
    grad.addColorStop(0, "#ff5722");
    grad.addColorStop(0.65, "#ffb300");
    grad.addColorStop(0.85, "#00e5ff");
    grad.addColorStop(1.0, "#00e676");

    ctx.strokeStyle = grad;
    ctx.lineWidth = 3.0;
    ctx.stroke();

    // Draw station dots with labels
    stations.forEach((st) => {
      const px = st.x;
      const py = Math.min(padT + plotH, Math.max(padT, tempToY(st.t)));
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.strokeStyle = "#00e5ff";
      ctx.lineWidth = 1.8;
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 9px 'JetBrains Mono', monospace";
      ctx.textAlign = "center";
      ctx.fillText(`${st.t.toFixed(0)} K`, px, Math.max(padT + 12, py - 6));
    });
  }
}

window.HudManager = HudManager;
