/**
 * Phase 10: Multi-Series Synchronized Engineering Charts Module
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - 6 synchronized Canvas-based engineering plots (Alt, Vel, Mach, Dynamic Pressure, Heat Flux, G-Force)
 *   - Real-time time scrubber cursor line
 *   - Peak / Max-Q annotations
 *   - Offline lightweight Canvas rendering without heavy external charting bloat
 */

class EngineeringChartsManager {
  constructor() {
    this.charts = [
      { id: "chart-altitude", key: "altitude_km", label: "Altitude", unit: "km", color: "#00e5ff" },
      { id: "chart-velocity", key: "velocity_km_s", label: "Velocity", unit: "km/s", color: "#2979ff" },
      { id: "chart-mach", key: "mach", label: "Mach Number", unit: "M", color: "#00e676" },
      { id: "chart-q", key: "dynamic_pressure_kpa", label: "Dynamic Pressure (q)", unit: "kPa", color: "#ff9100" },
      { id: "chart-flux", key: "heat_flux_mw_m2", label: "Stagnation Heat Flux", unit: "MW/m²", color: "#ff1744" },
      { id: "chart-g", key: "apparent_g", label: "Felt Acceleration", unit: "g", color: "#d500f9" },
    ];

    this.trajectory = [];
    this.maxTime = 100.0;
    this.currentTime = 0.0;

    window.addEventListener("resize", () => this.redrawAll());
  }

  setTrajectory(trajectoryPoints, maxTime) {
    this.trajectory = trajectoryPoints || [];
    this.maxTime = maxTime || 100.0;
    this.redrawAll();
  }

  updateTime(currentTime_s) {
    this.currentTime = currentTime_s;
    this.redrawAll();
  }

  redrawAll() {
    if (!this.trajectory || this.trajectory.length === 0) return;

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
  }

  renderSingleChart(ctx, w, h, cfg) {
    ctx.clearRect(0, 0, w, h);

    // Padding
    const pLeft = 32;
    const pRight = 10;
    const pTop = 14;
    const pBottom = 16;
    const plotW = w - pLeft - pRight;
    const plotH = h - pTop - pBottom;

    // Find min and max
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

      // Axis label
      const valAtGrid = (maxVal - (maxVal / 3) * g).toFixed(maxVal < 10 ? 1 : 0);
      ctx.fillStyle = "rgba(120, 144, 156, 0.6)";
      ctx.font = "8px 'JetBrains Mono', monospace";
      ctx.textAlign = "right";
      ctx.fillText(valAtGrid, pLeft - 4, gy + 3);
    }

    // Plot full trajectory line
    ctx.beginPath();
    ctx.strokeStyle = cfg.color;
    ctx.lineWidth = 1.5;

    for (let i = 0; i < this.trajectory.length; i++) {
      const pt = this.trajectory[i];
      const x = pLeft + (pt.time_s / this.maxTime) * plotW;
      const y = pTop + plotH - ((pt[cfg.key] || 0) / maxVal) * plotH;

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Area fill below curve
    ctx.lineTo(pLeft + plotW, pTop + plotH);
    ctx.lineTo(pLeft, pTop + plotH);
    ctx.closePath();
    ctx.fillStyle = `${cfg.color}15`;
    ctx.fill();

    // Current Time Vertical Scrubber Bar
    const curX = pLeft + (this.currentTime / this.maxTime) * plotW;
    ctx.beginPath();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 2]);
    ctx.moveTo(curX, pTop);
    ctx.lineTo(curX, pTop + plotH);
    ctx.stroke();
    ctx.setLineDash([]);

    // Current cursor circle dot
    const curVal = this.getValAtTime(cfg.key, this.currentTime);
    const curY = pTop + plotH - (curVal / maxVal) * plotH;
    ctx.beginPath();
    ctx.arc(curX, curY, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    // Max peak tag
    ctx.fillStyle = cfg.color;
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    ctx.fillText(`Peak: ${maxVal.toFixed(1)} ${cfg.unit}`, w - pRight, pTop - 3);
  }

  getValAtTime(key, targetTime) {
    if (!this.trajectory || this.trajectory.length === 0) return 0;
    for (let i = 0; i < this.trajectory.length - 1; i++) {
      if (targetTime >= this.trajectory[i].time_s && targetTime <= this.trajectory[i + 1].time_s) {
        const t0 = this.trajectory[i].time_s;
        const t1 = this.trajectory[i + 1].time_s;
        const v0 = this.trajectory[i][key] || 0;
        const v1 = this.trajectory[i + 1][key] || 0;
        const frac = t1 > t0 ? (targetTime - t0) / (t1 - t0) : 0;
        return v0 + (v1 - v0) * frac;
      }
    }
    return this.trajectory[this.trajectory.length - 1][key] || 0;
  }
}

window.EngineeringChartsManager = EngineeringChartsManager;
