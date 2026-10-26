/**
 * SpaceX Flight 14 Trajectory Profile Infographic Canvas
 * Exact faithful interactive implementation of spacex.com/launches/starship-flight-14
 * Dual-branching post-hot-staging: Booster to Gulf of America, Starship to Pacific Ocean.
 */

var SpacexTrajectoryProfile = class SpacexTrajectoryProfile {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.currentTime_s = 0;
    this.hoverMilestone = null;

    // Define all milestones matching SpaceX flight 14 infographic
    this.milestones = [
      { id: "engine_start", label: "SUPER HEAVY\nENGINE START", time_s: 0, xU: 0.08, yU: 0.88, type: "stack" },
      { id: "launch", label: "LAUNCH", time_s: 2, xU: 0.08, yU: 0.74, type: "stack" },
      { id: "ascent", label: "ASCENT", time_s: 60, xU: 0.14, yU: 0.52, type: "stack" },
      { id: "hot_staging", label: "HOT STAGING", time_s: 162, xU: 0.24, yU: 0.42, type: "staging" },
      // Booster branch
      { id: "flip", label: "FLIP MANEUVER", time_s: 172, xU: 0.22, yU: 0.32, type: "booster" },
      { id: "boostback", label: "BOOSTBACK BURN", time_s: 200, xU: 0.16, yU: 0.28, type: "booster" },
      { id: "booster_descent", label: "SUPER HEAVY DESCENT", time_s: 320, xU: 0.25, yU: 0.58, type: "booster" },
      { id: "booster_splashdown", label: "WATER LANDING\nGulf of America", time_s: 425, xU: 0.29, yU: 0.84, type: "booster" },
      // Ship branch
      { id: "ship_ascent", label: "STARSHIP ASCENT", time_s: 280, xU: 0.34, yU: 0.35, type: "ship" },
      { id: "meco", label: "STARSHIP ENGINE CUTOFF", time_s: 510, xU: 0.40, yU: 0.30, type: "ship" },
      { id: "insertion", label: "ORBITAL INSERTION BURN", time_s: 522, xU: 0.48, yU: 0.20, type: "ship" },
      { id: "deploy", label: "STARLINK DEPLOY\n(26 SATELLITES)", time_s: 1320, xU: 0.60, yU: 0.14, type: "ship" },
      { id: "coast", label: "ORBITAL COAST PHASE", time_s: 4500, xU: 0.72, yU: 0.14, type: "ship" },
      { id: "deorbit", label: "DEORBIT BURN", time_s: 9900, xU: 0.81, yU: 0.14, type: "ship" },
      { id: "entry", label: "STARSHIP ENTRY", time_s: 10800, xU: 0.88, yU: 0.33, type: "ship" },
      { id: "ship_splashdown", label: "LANDING BURN\nAND SPLASHDOWN\nPacific Ocean", time_s: 11732, xU: 0.92, yU: 0.84, type: "ship" }
    ];

    this.initEvents();
    this.resize();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width || 1200;
    this.height = rect.height || 600;
    this.canvas.width = this.width * (window.devicePixelRatio || 1);
    this.canvas.height = this.height * (window.devicePixelRatio || 1);
    this.canvas.style.width = this.width + "px";
    this.canvas.style.height = this.height + "px";
    this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    this.render();
  }

  initEvents() {
    window.addEventListener("resize", () => this.resize());

    this.canvas.addEventListener("click", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      for (let m of this.milestones) {
        const mx = m.xU * this.width;
        const my = m.yU * this.height;
        const dist = Math.hypot(clickX - mx, clickY - my);
        if (dist < 35) {
          if (window.timelineController) {
            window.timelineController.seekTo(m.time_s);
          }
          break;
        }
      }
    });

    this.canvas.addEventListener("mousemove", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      let found = null;
      for (let m of this.milestones) {
        const mx = m.xU * this.width;
        const my = m.yU * this.height;
        if (Math.hypot(mouseX - mx, mouseY - my) < 35) {
          found = m;
          break;
        }
      }
      if (this.hoverMilestone !== found) {
        this.hoverMilestone = found;
        this.canvas.style.cursor = found ? "pointer" : "default";
        this.render();
      }
    });
  }

  updateTime(time_s) {
    this.currentTime_s = time_s;
    this.render();
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // 1. Pure Pitch-Black Space Background
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, w, h);

    // Subtle star background
    ctx.fillStyle = "#ffffff";
    for (let i = 0; i < 70; i++) {
      const sx = (Math.sin(i * 123.45) * 0.5 + 0.5) * w;
      const sy = (Math.cos(i * 456.78) * 0.5 + 0.5) * (h * 0.85);
      const sz = (i % 3 === 0) ? 1.5 : 0.8;
      ctx.globalAlpha = 0.2 + (i % 5) * 0.15;
      ctx.fillRect(sx, sy, sz, sz);
    }
    ctx.globalAlpha = 1.0;

    // 2. Water Surface Base Line (Gulf and Pacific)
    const waterY = h * 0.90;
    ctx.strokeStyle = "rgba(0, 180, 216, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(w * 0.22, waterY);
    ctx.lineTo(w * 0.36, waterY);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(w * 0.86, waterY);
    ctx.lineTo(w * 0.97, waterY);
    ctx.stroke();

    // 3. Draw Starbase Launch Pad & Mechazilla Tower (Bottom Left)
    this.drawLaunchTower(ctx, w * 0.08, waterY);

    // 4. Primary Trajectory Curves
    this.drawTrajectoryArcs(ctx, w, h);

    // 5. Draw Flight Attitude Vehicle Silhouettes Along Trajectory
    this.drawAttitudeVehicles(ctx, w, h);

    // 6. Draw Text Labels and Leader Lines
    this.drawMilestoneLabels(ctx, w, h);

    // 7. Draw Live Animated Vehicle Position Indicators
    this.drawLiveTracking(ctx, w, h);
  }

  drawLaunchTower(ctx, x, y) {
    ctx.strokeStyle = "#5a6878";
    ctx.lineWidth = 1.5;

    // Mechazilla Tower Frame
    const towerH = 120;
    const towerW = 18;
    ctx.strokeRect(x - towerW - 8, y - towerH, towerW, towerH);

    // Cross-bracing trusses
    ctx.beginPath();
    for (let ty = y - towerH; ty < y; ty += 20) {
      ctx.moveTo(x - towerW - 8, ty);
      ctx.lineTo(x - 8, ty + 20);
      ctx.moveTo(x - 8, ty);
      ctx.lineTo(x - towerW - 8, ty + 20);
    }
    ctx.stroke();

    // Chopstick Arms & OLM base
    ctx.strokeStyle = "#00e5ff";
    ctx.beginPath();
    ctx.moveTo(x - 8, y - towerH * 0.65);
    ctx.lineTo(x + 2, y - towerH * 0.65);
    ctx.moveTo(x - 8, y - towerH * 0.72);
    ctx.lineTo(x + 2, y - towerH * 0.72);
    ctx.stroke();

    // Launch Mount (OLM)
    ctx.fillStyle = "#333e4c";
    ctx.fillRect(x - 14, y - 10, 28, 10);
  }

  drawTrajectoryArcs(ctx, w, h) {
    const padX = w * 0.08;
    const padY = h * 0.90;
    const sepX = w * 0.24;
    const sepY = h * 0.42;

    // A. Main Powered Ascent Arc (Solid White)
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.moveTo(padX, padY - 60);
    ctx.quadraticCurveTo(padX + 5, h * 0.60, sepX, sepY);
    ctx.stroke();

    // B. Super Heavy Booster Return Branch (Dashed Cyan Curve)
    ctx.save();
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 1.8;
    ctx.setLineDash([4, 4]);

    // Flip Loop
    const flipCenterX = w * 0.21;
    const flipCenterY = h * 0.35;
    ctx.beginPath();
    ctx.arc(flipCenterX, flipCenterY, 26, Math.PI * 0.1, Math.PI * 1.8, false);
    ctx.stroke();

    // Boostback Burn Arc
    ctx.beginPath();
    ctx.moveTo(flipCenterX - 20, flipCenterY);
    ctx.quadraticCurveTo(w * 0.15, h * 0.38, w * 0.20, h * 0.50);
    // Descent to Gulf
    ctx.quadraticCurveTo(w * 0.26, h * 0.65, w * 0.29, h * 0.88);
    ctx.stroke();
    ctx.restore();

    // Flip rotation arrow
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(flipCenterX, flipCenterY, 32, -Math.PI * 0.3, Math.PI * 0.7, false);
    ctx.stroke();
    // Arrowhead
    const arrX = flipCenterX + Math.cos(Math.PI * 0.7) * 32;
    const arrY = flipCenterY + Math.sin(Math.PI * 0.7) * 32;
    ctx.fillStyle = "#00e5ff";
    ctx.beginPath();
    ctx.moveTo(arrX, arrY);
    ctx.lineTo(arrX - 6, arrY - 2);
    ctx.lineTo(arrX - 2, arrY - 6);
    ctx.closePath();
    ctx.fill();

    // C. Starship Upper Stage Orbital & Reentry Track (Solid White)
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    // From separation to insertion
    ctx.moveTo(sepX, sepY);
    ctx.bezierCurveTo(w * 0.32, h * 0.34, w * 0.40, h * 0.26, w * 0.49, h * 0.20);
    // Orbit Insertion to Deploy & Coast (Top flat arc)
    ctx.bezierCurveTo(w * 0.54, h * 0.16, w * 0.60, h * 0.14, w * 0.80, h * 0.14);
    // Deorbit to Reentry Curve
    ctx.bezierCurveTo(w * 0.86, h * 0.16, w * 0.89, h * 0.28, w * 0.92, h * 0.88);
    ctx.stroke();

    // Starlink Deploy Forward Ejection Dashed Vector
    ctx.save();
    ctx.strokeStyle = "#00e5ff";
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(w * 0.60, h * 0.14);
    ctx.lineTo(w * 0.66, h * 0.14);
    ctx.stroke();
    ctx.restore();
  }

  drawAttitudeVehicles(ctx, w, h) {
    // 1. Full Stack at Launch (Vertical, bottom-left)
    this.drawMiniRocket(ctx, w * 0.08, h * 0.72, -Math.PI / 2, "stack", true);

    // 2. Full Stack during Ascent (Tilted 45 deg)
    this.drawMiniRocket(ctx, w * 0.14, h * 0.54, -Math.PI / 4, "stack", true);

    // 3. Hot Staging (Booster + Ship separating with glowing ring)
    this.drawMiniRocket(ctx, w * 0.23, h * 0.43, -Math.PI / 5, "booster", false);
    this.drawMiniRocket(ctx, w * 0.25, h * 0.41, -Math.PI / 5, "ship", true);
    // Staging exhaust glow
    ctx.fillStyle = "rgba(255, 170, 0, 0.6)";
    ctx.beginPath();
    ctx.arc(w * 0.24, h * 0.42, 6, 0, Math.PI * 2);
    ctx.fill();

    // 4. Booster Boostback Burn (Aft firing engines, heading left)
    this.drawMiniRocket(ctx, w * 0.17, h * 0.32, Math.PI * 0.9, "booster", true);

    // 5. Booster Descent (Engines down, grid fins out)
    this.drawMiniRocket(ctx, w * 0.26, h * 0.60, Math.PI * 0.58, "booster", false);

    // 6. Booster Landing Burn & Water Landing (Vertical in Gulf)
    this.drawMiniRocket(ctx, w * 0.29, h * 0.84, Math.PI / 2, "booster", true);

    // 7. Starship Ascent (Powered 5-engine burn)
    this.drawMiniRocket(ctx, w * 0.33, h * 0.36, -Math.PI / 6, "ship", true);

    // 8. Starship Orbital Insertion Burn
    this.drawMiniRocket(ctx, w * 0.49, h * 0.20, -Math.PI * 0.08, "ship", true);

    // 9. Starlink Deployment (Horizontal, nose door open, deploying forward)
    this.drawMiniRocket(ctx, w * 0.58, h * 0.14, 0, "ship", false, true);
    // Draw 3 mini flatpacks deploying forward!
    ctx.fillStyle = "#00e5ff";
    for (let sp = 1; sp <= 3; sp++) {
      ctx.fillRect(w * 0.58 + 14 + sp * 8, h * 0.14 - 2, 5, 2);
    }

    // 10. Starship Orbital Coast Phase
    this.drawMiniRocket(ctx, w * 0.72, h * 0.14, 0, "ship", false);

    // 11. Starship Deorbit Burn (Retrograde, engines forward)
    this.drawMiniRocket(ctx, w * 0.81, h * 0.14, Math.PI, "ship", true);

    // 12. Starship Entry (60 deg Belly-Flop with plasma shockwave!)
    this.drawMiniRocket(ctx, w * 0.88, h * 0.34, Math.PI * 0.38, "ship", false);
    // Plasma shockwave curve
    ctx.strokeStyle = "rgba(255, 109, 0, 0.85)";
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(w * 0.88 - 4, h * 0.34 + 6, 14, -Math.PI * 0.4, Math.PI * 0.4, false);
    ctx.stroke();

    // 13. Starship Splashdown in Pacific (Vertical landing burn into water)
    this.drawMiniRocket(ctx, w * 0.92, h * 0.84, Math.PI / 2, "ship", true);
  }

  drawMiniRocket(ctx, x, y, angle, type, firing = false, doorOpen = false) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);

    ctx.strokeStyle = "#e0e8f0";
    ctx.fillStyle = "#121820";
    ctx.lineWidth = 1.2;

    if (type === "stack") {
      // Full Stack (Super Heavy + Starship)
      // Booster
      ctx.strokeRect(-16, -4, 20, 8);
      ctx.fillRect(-16, -4, 20, 8);
      // Starship Nose
      ctx.beginPath();
      ctx.moveTo(4, -4);
      ctx.lineTo(14, 0);
      ctx.lineTo(4, 4);
      ctx.closePath();
      ctx.stroke();
      ctx.fill();
    } else if (type === "booster") {
      // Super Heavy Booster
      ctx.strokeRect(-12, -3.5, 24, 7);
      ctx.fillRect(-12, -3.5, 24, 7);
      // Grid fins
      ctx.beginPath();
      ctx.moveTo(8, -5); ctx.lineTo(10, -3.5);
      ctx.moveTo(8, 5); ctx.lineTo(10, 3.5);
      ctx.stroke();
    } else if (type === "ship") {
      // Starship
      ctx.strokeRect(-8, -3.5, 12, 7);
      ctx.fillRect(-8, -3.5, 12, 7);
      // Nose cone
      ctx.beginPath();
      ctx.moveTo(4, -3.5);
      ctx.lineTo(13, 0);
      ctx.lineTo(4, 3.5);
      ctx.closePath();
      ctx.stroke();
      ctx.fill();
      // Flaps
      ctx.beginPath();
      ctx.moveTo(-6, -5); ctx.lineTo(-4, -3.5);
      ctx.moveTo(-6, 5); ctx.lineTo(-4, 3.5);
      ctx.moveTo(2, -4.5); ctx.lineTo(4, -3.5);
      ctx.moveTo(2, 4.5); ctx.lineTo(4, 3.5);
      ctx.stroke();
      if (doorOpen) {
        ctx.strokeStyle = "#00e5ff";
        ctx.beginPath();
        ctx.moveTo(5, -3.5);
        ctx.lineTo(8, -6);
        ctx.stroke();
      }
    }

    // Engine exhaust plume
    if (firing) {
      ctx.fillStyle = "#ffaa00";
      ctx.beginPath();
      const tailX = (type === "stack" ? -16 : (type === "booster" ? -12 : -8));
      ctx.moveTo(tailX, -2.5);
      ctx.lineTo(tailX - 12, 0);
      ctx.lineTo(tailX, 2.5);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.moveTo(tailX, -1);
      ctx.lineTo(tailX - 6, 0);
      ctx.lineTo(tailX, 1);
      ctx.closePath();
      ctx.fill();
    }

    ctx.restore();
  }

  drawMilestoneLabels(ctx, w, h) {
    ctx.font = "bold 9.5px 'JetBrains Mono', monospace";
    ctx.textBaseline = "middle";

    this.milestones.forEach((m) => {
      const isHovered = (this.hoverMilestone === m);
      const isPast = (this.currentTime_s >= m.time_s);

      const mx = m.xU * w;
      const my = m.yU * h;

      // Milestone dot
      ctx.fillStyle = isHovered ? "#ffffff" : (isPast ? "#00ff88" : "#00e5ff");
      ctx.beginPath();
      ctx.arc(mx, my, isHovered ? 4.5 : 3.0, 0, Math.PI * 2);
      ctx.fill();

      // Text callout
      ctx.fillStyle = isHovered ? "#ffffff" : (isPast ? "#00e5ff" : "#b0c4de");
      ctx.textAlign = (m.xU > 0.7) ? "right" : "left";

      const lines = m.label.split("\n");
      const textX = (m.xU > 0.7) ? mx - 10 : mx + 10;
      let textY = my - (lines.length - 1) * 6;

      lines.forEach((l) => {
        ctx.fillText(l, textX, textY);
        textY += 12;
      });
    });
  }

  drawLiveTracking(ctx, w, h) {
    const t = this.currentTime_s;

    // Track active position
    let activeX = w * 0.08;
    let activeY = h * 0.88;

    if (t <= 162) {
      const u = t / 162.0;
      const padX = w * 0.08;
      const padY = h * 0.88;
      const sepX = w * 0.24;
      const sepY = h * 0.42;
      activeX = padX + u * (sepX - padX);
      activeY = padY - Math.sin(u * Math.PI * 0.5) * (padY - sepY);
    } else if (t <= 425) {
      // Booster descent tracking
      const u = (t - 162) / (425 - 162);
      activeX = w * 0.24 + u * (w * 0.29 - w * 0.24);
      activeY = h * 0.42 + u * (h * 0.88 - h * 0.42);

      // Pulse ring on booster
      ctx.strokeStyle = "rgba(0, 229, 255, 0.7)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(activeX, activeY, 12, 0, Math.PI * 2);
      ctx.stroke();

      // Also track Ship
      const shipU = (t - 162) / (522 - 162);
      const shipX = w * 0.24 + shipU * (w * 0.48 - w * 0.24);
      const shipY = h * 0.42 - shipU * (h * 0.42 - h * 0.20);
      ctx.strokeStyle = "rgba(0, 255, 136, 0.8)";
      ctx.beginPath();
      ctx.arc(shipX, shipY, 12, 0, Math.PI * 2);
      ctx.stroke();
      return;
    } else if (t <= 1320) {
      const u = (t - 425) / (1320 - 425);
      activeX = w * 0.48 + u * (w * 0.60 - w * 0.48);
      activeY = h * 0.20 - u * (h * 0.20 - h * 0.14);
    } else if (t <= 9900) {
      const u = (t - 1320) / (9900 - 1320);
      activeX = w * 0.60 + u * (w * 0.81 - w * 0.60);
      activeY = h * 0.14;
    } else if (t <= 11732) {
      const u = (t - 9900) / (11732 - 9900);
      activeX = w * 0.81 + u * (w * 0.92 - w * 0.81);
      activeY = h * 0.14 + Math.pow(u, 2) * (h * 0.88 - h * 0.14);
    } else {
      activeX = w * 0.92;
      activeY = h * 0.88;
    }

    // Glowing pulsing active vehicle tracker node
    const pulse = 10 + Math.sin(Date.now() * 0.008) * 3;
    ctx.strokeStyle = "#00e5ff";
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.arc(activeX, activeY, pulse, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(activeX, activeY, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }
}

// Global exposure
if (typeof window !== "undefined") {
  window.SpacexTrajectoryProfile = SpacexTrajectoryProfile;
}
