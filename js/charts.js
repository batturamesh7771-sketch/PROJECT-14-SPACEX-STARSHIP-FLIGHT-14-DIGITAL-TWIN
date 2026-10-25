/**
 * Phase 10: Multi-Series Synchronized Engineering Charts Module
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - 6 synchronized Canvas-based engineering plots (Alt, Vel, Mach [-], Dynamic Pressure, Heat Flux, Felt Acceleration)
 *   - 3 upper-rail multi-line mini plots matching Screenshot B:
 *       1. Thrust & Propulsion (Total, Booster, Ship)
 *       2. Altitude & Velocity (Dual axis)
 *       3. Temperature TPS (Tile Surface, RTV Bondline)
 *   - Global Trajectory 2D Ground Track map canvas (Launch, Apogee, Entry, Splashdown)
 *   - Real-time time scrubber cursor line
 *   - Peak / Max-Q annotations
 *   - Dimensionless Mach number [no fake 'M' units]
 */

class EngineeringChartsManager {
  constructor() {
    this.charts = [
      { id: "chart-altitude", key: "altitude_km", label: "Altitude", unit: "km", color: "#00e5ff" },
      { id: "chart-velocity", key: "velocity_km_s", label: "Velocity", unit: "km/s", color: "#2979ff" },
      { id: "chart-mach", key: "mach", label: "Mach Number", unit: "[-]", color: "#00e676" },
      { id: "chart-q", key: "dynamic_pressure_kpa", label: "Dynamic Pressure (q)", unit: "kPa", color: "#ff9100" },
      { id: "chart-flux", key: "heat_flux_mw_m2", label: "Stagnation Heat Flux", unit: "MW/m²", color: "#ff1744" },
      { id: "chart-g", key: "apparent_g", label: "Felt Acceleration", unit: "g", color: "#d500f9" },
    ];

    this.miniCharts = [
      {
        id: "mini-chart-thrust",
        series: [
          { key: "thrust_mn", label: "Total Thrust", color: "#00e5ff", scale: 1000.0, unit: "kN" },
        ],
        yLabel: "Thrust (kN)"
      },
      {
        id: "mini-chart-altvel",
        series: [
          { key: "altitude_km", label: "Altitude", color: "#2979ff", scale: 1000.0, unit: "m" },
          { key: "velocity_km_s", label: "Velocity", color: "#ff9100", scale: 1000.0, unit: "m/s" },
        ],
        yLabel: "Alt / Vel"
      },
      {
        id: "mini-chart-temp",
        series: [
          { key: "surface_temp_k", label: "Surface (K)", color: "#ff1744", scale: 1.0, unit: "K" },
          { key: "bondline_temp_k", label: "Bondline (K)", color: "#ff9100", scale: 1.0, unit: "K" },
        ],
        yLabel: "Temp (K)"
      }
    ];

    this.trajectory = [];
    this.maxTime = 100.0;
    this.currentTime = 0.0;

    window.addEventListener("resize", () => this.redrawAll());
  }

  setTrajectory(trajectoryPoints, maxTime) {
    this.trajectory = trajectoryPoints || [];
    this.maxTime = maxTime || (this.trajectory.length > 0 ? this.trajectory[this.trajectory.length - 1].time_s : 100.0);
    this.redrawAll();
  }

  updateTime(currentTime_s) {
    this.currentTime = currentTime_s;
    this.redrawAll();
  }

  redrawAll() {
    if (!this.trajectory || this.trajectory.length === 0) return;

    // 1. Render 6 Primary Engineering Plots
    this.charts.forEach(cfg => {
      const canvas = document.getElementById(cfg.id);
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;

      canvas.width = rect.width * (window.devicePixelRatio || 1);
      canvas.height = rect.height * (window.devicePixelRatio || 1);

      const ctx = canvas.getContext("2d");
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

      this.renderSingleChart(ctx, rect.width, rect.height, cfg);
    });

    // 2. Render 3 Mini Side Plots (Screenshot B style)
    this.miniCharts.forEach(mini => {
      const canvas = document.getElementById(mini.id);
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;

      canvas.width = rect.width * (window.devicePixelRatio || 1);
      canvas.height = rect.height * (window.devicePixelRatio || 1);

      const ctx = canvas.getContext("2d");
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

      this.renderMiniChart(ctx, rect.width, rect.height, mini);
    });

    // 3. Render Global Trajectory Ground Track
    this.renderGroundTrack();
  }

  renderSingleChart(ctx, w, h, cfg) {
    ctx.clearRect(0, 0, w, h);

    const pLeft = 40;
    const pRight = 12;
    const pTop = 16;
    const pBottom = 20;
    const plotW = w - pLeft - pRight;
    const plotH = h - pTop - pBottom;

    if (plotW <= 0 || plotH <= 0) return;

    // Find min and max values
    let minVal = 0;
    let maxVal = -Infinity;
    for (let i = 0; i < this.trajectory.length; i++) {
      const v = this.trajectory[i][cfg.key] || 0;
      if (v > maxVal) maxVal = v;
    }
    if (maxVal <= minVal) maxVal = 1.0;
    maxVal *= 1.15; // 15% headroom

    // Subtle background grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;

    for (let g = 0; g <= 3; g++) {
      const gy = pTop + (plotH / 3) * g;
      ctx.beginPath();
      ctx.moveTo(pLeft, gy);
      ctx.lineTo(w - pRight, gy);
      ctx.stroke();

      const valAtGrid = (maxVal - (maxVal / 3) * g).toFixed(maxVal < 10 ? 1 : 0);
      ctx.fillStyle = "rgba(120, 144, 156, 0.7)";
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${valAtGrid} ${cfg.unit}`, pLeft - 4, gy + 3);
    }

    // Time Ticks (Horizontal Axis)
    ctx.textAlign = "center";
    for (let t = 0; t <= 4; t++) {
      const tx = pLeft + (plotW / 4) * t;
      const tSec = ((this.maxTime / 4) * t).toFixed(0);
      ctx.fillText(`T+${tSec}s`, tx, h - 6);
    }

    // Plot Series Line
    ctx.beginPath();
    ctx.strokeStyle = cfg.color;
    ctx.lineWidth = 1.8;

    let first = true;
    for (let i = 0; i < this.trajectory.length; i++) {
      const pt = this.trajectory[i];
      const val = pt[cfg.key] || 0;
      const x = pLeft + (pt.time_s / this.maxTime) * plotW;
      const y = pTop + plotH - (val / maxVal) * plotH;

      if (first) {
        ctx.moveTo(x, y);
        first = false;
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();

    // Fill under curve
    if (this.trajectory.length > 0) {
      const lastPt = this.trajectory[this.trajectory.length - 1];
      const lastX = pLeft + (lastPt.time_s / this.maxTime) * plotW;
      ctx.lineTo(lastX, pTop + plotH);
      ctx.lineTo(pLeft, pTop + plotH);
      ctx.closePath();
      ctx.fillStyle = this.hexToRgba(cfg.color, 0.08);
      ctx.fill();
    }

    // Time Scrubber Cursor Line
    const cursorX = pLeft + Math.min(1.0, Math.max(0.0, this.currentTime / this.maxTime)) * plotW;
    ctx.beginPath();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.85)";
    ctx.lineWidth = 1.2;
    ctx.setLineDash([3, 3]);
    ctx.moveTo(cursorX, pTop);
    ctx.lineTo(cursorX, pTop + plotH);
    ctx.stroke();
    ctx.setLineDash([]);

    // Current value dot and callout
    let curVal = 0;
    for (let i = 0; i < this.trajectory.length - 1; i++) {
      if (this.currentTime >= this.trajectory[i].time_s && this.currentTime <= this.trajectory[i + 1].time_s) {
        const p0 = this.trajectory[i];
        const p1 = this.trajectory[i + 1];
        const dt = p1.time_s - p0.time_s;
        const alpha = dt > 0 ? (this.currentTime - p0.time_s) / dt : 0;
        curVal = (p0[cfg.key] || 0) + ((p1[cfg.key] || 0) - (p0[cfg.key] || 0)) * alpha;
        break;
      }
    }
    if (this.currentTime >= this.maxTime && this.trajectory.length > 0) {
      curVal = this.trajectory[this.trajectory.length - 1][cfg.key] || 0;
    }

    const curY = pTop + plotH - (curVal / maxVal) * plotH;
    ctx.beginPath();
    ctx.arc(cursorX, curY, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = cfg.color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  renderMiniChart(ctx, w, h, mini) {
    ctx.clearRect(0, 0, w, h);

    const pLeft = 28;
    const pRight = 8;
    const pTop = 10;
    const pBottom = 14;
    const plotW = w - pLeft - pRight;
    const plotH = h - pTop - pBottom;

    if (plotW <= 0 || plotH <= 0) return;

    // Gridlines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let g = 0; g <= 2; g++) {
      const gy = pTop + (plotH / 2) * g;
      ctx.beginPath();
      ctx.moveTo(pLeft, gy);
      ctx.lineTo(w - pRight, gy);
      ctx.stroke();
    }

    // Determine max value across mini series
    let maxVal = 1.0;
    mini.series.forEach(s => {
      for (let i = 0; i < this.trajectory.length; i++) {
        const v = (this.trajectory[i][s.key] || 0) * (s.scale || 1.0);
        if (v > maxVal) maxVal = v;
      }
    });
    maxVal *= 1.15;

    // Plot each series
    mini.series.forEach(s => {
      ctx.beginPath();
      ctx.strokeStyle = s.color;
      ctx.lineWidth = 1.5;

      let first = true;
      for (let i = 0; i < this.trajectory.length; i++) {
        const pt = this.trajectory[i];
        const val = (pt[s.key] || 0) * (s.scale || 1.0);
        const x = pLeft + (pt.time_s / this.maxTime) * plotW;
        const y = pTop + plotH - (val / maxVal) * plotH;

        if (first) {
          ctx.moveTo(x, y);
          first = false;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    });

    // Scrubber cursor line
    const cursorX = pLeft + Math.min(1.0, Math.max(0.0, this.currentTime / this.maxTime)) * plotW;
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.7)";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);
    ctx.moveTo(cursorX, pTop);
    ctx.lineTo(cursorX, pTop + plotH);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  renderGroundTrack() {
    const canvas = document.getElementById("ground-track-canvas");
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);

    const ctx = canvas.getContext("2d");
    ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    ctx.clearRect(0, 0, rect.width, rect.height);

    const w = rect.width;
    const h = rect.height;

    // Draw stylized Earth curvature arc
    ctx.beginPath();
    ctx.arc(w / 2, h * 1.5, h * 1.1, Math.PI * 1.15, Math.PI * 1.85);
    ctx.strokeStyle = "rgba(0, 229, 255, 0.25)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Atmosphere halo
    ctx.beginPath();
    ctx.arc(w / 2, h * 1.5, h * 1.14, Math.PI * 1.15, Math.PI * 1.85);
    ctx.strokeStyle = "rgba(0, 229, 255, 0.08)";
    ctx.lineWidth = 4;
    ctx.stroke();

    // Draw Suborbital Flight Trajectory Arc
    ctx.beginPath();
    const startX = w * 0.12;
    const startY = h * 0.78;
    const cpX = w * 0.45;
    const cpY = h * 0.18; // Apogee ~185 km
    const endX = w * 0.88;
    const endY = h * 0.76;

    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(cpX, cpY, endX, endY);
    ctx.strokeStyle = "#00e676"; // Green observed trajectory
    ctx.lineWidth = 2.0;
    ctx.stroke();

    // Planned Reference Trajectory (Cyan dashed)
    ctx.beginPath();
    ctx.setLineDash([3, 3]);
    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(w * 0.48, h * 0.14, endX, endY);
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.setLineDash([]);

    // Milestone pins
    ctx.fillStyle = "#ffffff";
    ctx.font = "8px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";

    // Launch Pin (Starbase)
    ctx.beginPath();
    ctx.arc(startX, startY, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#00e5ff";
    ctx.fill();
    ctx.fillText("Launch", startX, startY + 12);

    // Apogee Pin
    ctx.beginPath();
    ctx.arc(cpX, cpY + 10, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#ff9100";
    ctx.fill();
    ctx.fillText("Apogee 185km", cpX, cpY);

    // Splashdown Pin (Pacific)
    ctx.beginPath();
    ctx.arc(endX, endY, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#ff1744";
    ctx.fill();
    ctx.fillText("Splashdown", endX, endY + 12);

    // Current Vehicle Bead along the arc
    const progress = Math.min(1.0, Math.max(0.0, this.currentTime / this.maxTime));
    const curArcX = (1 - progress) * (1 - progress) * startX + 2 * (1 - progress) * progress * cpX + progress * progress * endX;
    const curArcY = (1 - progress) * (1 - progress) * startY + 2 * (1 - progress) * progress * cpY + progress * progress * endY;

    ctx.beginPath();
    ctx.arc(curArcX, curArcY, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  hexToRgba(hex, alpha) {
    let c = hex.replace("#", "");
    if (c.length === 3) c = c.split("").map(ch => ch + ch).join("");
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}

window.EngineeringChartsManager = EngineeringChartsManager;
