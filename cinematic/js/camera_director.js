/**
 * Starship Flight 14 — Cinematic Broadcast Camera Director
 * Strict Namespace: CFR (Cinematic Flight Replay)
 *
 * Implements:
 *   - 21 Broadcast Camera Choreography States with authentic aerospace broadcast angles
 *   - Orthonormal vehicle tracking basis (rHat: Radial Up, vHat: In-track Forward, hHat: Cross-track Lateral)
 *   - Smooth cubic / slerp target and eye position transitions
 *   - Dynamic FOV transitions (wide 65° down to telephoto 18° for long lens tracking)
 *   - Camera shake vibration effect during ignition, liftoff, Max Q, and atmospheric entry
 *   - Auto Director mode (automatically switches states based on timeline milestones)
 *   - Manual operator override with smooth return to auto mode
 */

class CfrCameraDirector {
  constructor(camera, options = {}) {
    this.camera = camera;
    this.controls = options.controls || null;
    this.isAutoDirector = true;
    this.isInteractiveMode = false;

    // Current and Target Camera Vectors
    this.currentEye = new THREE.Vector3(-0.7, 3.2, 6.2);
    this.currentTarget = new THREE.Vector3(-0.71, 2.78, 5.69);
    this.currentFov = 48.0;

    this.desiredEye = new THREE.Vector3(-0.7, 3.2, 6.2);
    this.desiredTarget = new THREE.Vector3(-0.71, 2.78, 5.69);
    this.desiredFov = 48.0;

    // Smoothing speed (higher = faster response)
    this.smoothHalfLife = 0.09;

    // Camera Shake
    this.shakeIntensity = 0.0;
    this.shakeOffset = new THREE.Vector3(0, 0, 0);

    // Active State
    this.currentStateId = "PAD_WIDE";
    this.stateDefinitions = this.initCameraStates();

    // Set initial preset
    this.applyStatePreset(this.currentStateId, true);
  }

  setInteractionMode(interactive) {
    this.isInteractiveMode = !!interactive;
    this.isAutoDirector = !interactive;
    if (this.controls) {
      this.controls.enabled = this.isInteractiveMode;
    }
    const modeBtn = document.getElementById("cfr-btn-camera-mode");
    if (modeBtn) {
      if (this.isInteractiveMode) {
        modeBtn.innerHTML = "<span>🕹️</span> FREE 3D CAMERA";
        modeBtn.classList.add("active");
        modeBtn.title = "Interactive 3D Camera Active (Orbit: Drag / Zoom: Scroll / Pan: Right Click). Click to switch to Auto Broadcast.";
      } else {
        modeBtn.innerHTML = "<span>🎥</span> AUTO BROADCAST";
        modeBtn.classList.remove("active");
        modeBtn.title = "Auto Broadcast Director Active. Click to enable Free 3D Camera.";
      }
    }
  }

  toggleInteractionMode() {
    this.setInteractionMode(!this.isInteractiveMode);
  }

  initCameraStates() {
    // Offsets are specified in local vehicle orthonormal frame:
    // x: Cross-track (hHat) Lateral offset
    // y: Radial Up (rHat) Elevation above vehicle
    // z: Downrange (vHat) In-track distance ahead (+) or behind (-)
    return {
      // 01. Starbase Launch Mount & Tower Wide View (Heroic Center Framing)
      PAD_WIDE: {
        id: "PAD_WIDE",
        name: "01. Pad Panoramic (Starbase OLM & Mechazilla)",
        targetMode: "PAD",
        fov: 50.0,
        offset: new THREE.Vector3(0.0, 0.16, -0.45),
        lookOffset: new THREE.Vector3(0.0, 0.18, 0.0),
        shake: 0.0,
      },

      // 02. Ground Level Low-Angle Hero Shot Looking Up the 121m Stack
      PAD_LOW_ANGLE: {
        id: "PAD_LOW_ANGLE",
        name: "02. Pad Low-Angle (121m Stack Up-Look)",
        targetMode: "VEHICLE",
        fov: 60.0,
        offset: new THREE.Vector3(0.0, 0.05, -0.22),
        lookOffset: new THREE.Vector3(0.0, 0.18, 0.0),
        shake: 0.0,
      },

      // 03. Engine Skirt Ignition & Water Deluge Cloud Bloom
      IGNITION_TRACK: {
        id: "IGNITION_TRACK",
        name: "03. Ignition & Deluge Vapor Track",
        targetMode: "VEHICLE",
        fov: 46.0,
        offset: new THREE.Vector3(0.0, 0.08, -0.32),
        lookOffset: new THREE.Vector3(0.0, 0.10, 0.0),
        shake: 0.04,
      },

      // 04. Ascent Rear-Quarter Chase Camera Tracking Through Cloud Layer
      ASCENT_CHASE: {
        id: "ASCENT_CHASE",
        name: "04. Ascent Chase (Rear-Quarter Profile)",
        targetMode: "VEHICLE",
        fov: 46.0,
        offset: new THREE.Vector3(0.18, 0.12, -0.32),
        lookOffset: new THREE.Vector3(0, 0.10, 0.05),
        shake: 0.03,
      },

      // 05. Ground Telephoto Long-Lens Tracking at High Altitude / Max Q
      ASCENT_LONG_LENS: {
        id: "ASCENT_LONG_LENS",
        name: "05. Ground Telephoto Long-Lens (Max Q)",
        targetMode: "VEHICLE",
        fov: 30.0,
        offset: new THREE.Vector3(0.28, 0.16, -0.42),
        lookOffset: new THREE.Vector3(0, 0.08, 0),
        shake: 0.02,
      },

      // 06. Staging Wide Perspective Framing Both Super Heavy and Ship
      STAGING_WIDE: {
        id: "STAGING_WIDE",
        name: "06. Staging Wide (Dual Vehicle Framing)",
        targetMode: "STAGING_CENTER",
        fov: 46.0,
        offset: new THREE.Vector3(0.24, 0.14, -0.36),
        lookOffset: new THREE.Vector3(0, 0.08, 0),
        shake: 0.03,
      },

      // 07. Close Framing on Vented Interstage Hot-Staging Ring
      STAGING_CLOSE: {
        id: "STAGING_CLOSE",
        name: "07. Hot-Staging Ring Close Inspection",
        targetMode: "INTERSTAGE",
        fov: 32.0,
        offset: new THREE.Vector3(0.14, 0.05, -0.18),
        lookOffset: new THREE.Vector3(0, 0.05, 0),
        shake: 0.04,
      },

      // 08. Tracking Super Heavy Booster Flip & Boostback Burn
      BOOSTER_RETURN_CHASE: {
        id: "BOOSTER_RETURN_CHASE",
        name: "08. Booster Flip & Boostback Chase",
        targetMode: "BOOSTER",
        fov: 44.0,
        offset: new THREE.Vector3(0.16, 0.08, 0.24),
        lookOffset: new THREE.Vector3(0, 0.05, 0),
        shake: 0.02,
      },

      // 09. Horizon Camera in Gulf of Mexico for Booster Soft Splashdown
      BOOSTER_GULF_WIDE: {
        id: "BOOSTER_GULF_WIDE",
        name: "09. Booster Gulf Water Landing Wide",
        targetMode: "BOOSTER",
        fov: 46.0,
        offset: new THREE.Vector3(0.06, 0.045, 0.14),
        lookOffset: new THREE.Vector3(0, 0.04, 0),
        shake: 0.02,
      },

      // 10. Starship Solo Upper Stage Accelerating Toward Orbit
      SHIP_SPACE_CHASE: {
        id: "SHIP_SPACE_CHASE",
        name: "10. Starship Space Chase (Solo Orbital Insertion)",
        targetMode: "STARSHIP",
        fov: 40.0,
        offset: new THREE.Vector3(-0.35, 0.25, -0.55),
        lookOffset: new THREE.Vector3(0, 0.1, 0),
        shake: 0.01,
      },

      // 11. Wide Orbital Framing with Curved Earth Horizon
      ORBIT_OVERVIEW: {
        id: "ORBIT_OVERVIEW",
        name: "11. Orbit Overview (Earth Horizon & Trajectory Arc)",
        targetMode: "STARSHIP",
        fov: 54.0,
        offset: new THREE.Vector3(0.75, 0.65, 0.85),
        lookOffset: new THREE.Vector3(0, 0, 0),
        shake: 0.0,
      },

      // 12. Close Telephoto on Forward PEZ Satellite Dispenser Mouth
      SATELLITE_DEPLOY_CLOSE: {
        id: "SATELLITE_DEPLOY_CLOSE",
        name: "12. Starlink V3 PEZ Dispenser Close Mouth",
        targetMode: "DISPENSER_MOUTH",
        fov: 28.0,
        offset: new THREE.Vector3(-0.16, 0.18, 0.24),
        lookOffset: new THREE.Vector3(0, 0.18, 0.12),
        shake: 0.0,
      },

      // 13. Panoramic Constellation View Showing 26 Starlinks Deploying Forward
      SATELLITE_TRAIN_WIDE: {
        id: "SATELLITE_TRAIN_WIDE",
        name: "13. Starlink Train Panoramic Separation",
        targetMode: "STARSHIP",
        fov: 50.0,
        offset: new THREE.Vector3(-0.45, 0.35, 0.85),
        lookOffset: new THREE.Vector3(0, 0.15, 0.35),
        shake: 0.0,
      },

      // 14. Cinematic Earth Limb Framing with Stainless Steel Sun Glint
      ORBITAL_EARTH_LIMB: {
        id: "ORBITAL_EARTH_LIMB",
        name: "14. Orbital Earth Limb & Hull Sun-Glint",
        targetMode: "STARSHIP",
        fov: 42.0,
        offset: new THREE.Vector3(0.55, 0.28, -0.65),
        lookOffset: new THREE.Vector3(0, 0.08, 0),
        shake: 0.0,
      },

      // 15. Following Starship Through Retrograde Flip & Deorbit Burn
      DEORBIT_CHASE: {
        id: "DEORBIT_CHASE",
        name: "15. Deorbit Burn (Retrograde Alignment)",
        targetMode: "STARSHIP",
        fov: 42.0,
        offset: new THREE.Vector3(0.38, 0.22, 0.65),
        lookOffset: new THREE.Vector3(0, 0.05, 0),
        shake: 0.02,
      },

      // 16. Hypersonic Entry at 70° Belly-Flop with Glowing Bow-Shock Plasma
      ENTRY_LONG_LENS: {
        id: "ENTRY_LONG_LENS",
        name: "16. Hypersonic Entry Interface (70° Belly AoA)",
        targetMode: "STARSHIP",
        fov: 34.0,
        offset: new THREE.Vector3(-0.45, -0.28, 0.55),
        lookOffset: new THREE.Vector3(0, 0.05, 0),
        shake: 0.05,
      },

      // 17. Exterior Drone-Style Tracking Camera During Peak Aerothermal Heating
      ENTRY_DRONE_TRACK: {
        id: "ENTRY_DRONE_TRACK",
        name: "17. Peak Heating Drone Track (Aerothermal Glow)",
        targetMode: "STARSHIP",
        fov: 44.0,
        offset: new THREE.Vector3(0.48, 0.32, 0.62),
        lookOffset: new THREE.Vector3(0, 0.08, 0),
        shake: 0.06,
      },

      // 18. Low-Altitude Descent Toward Northern Pacific Ocean Horizon
      PACIFIC_APPROACH: {
        id: "PACIFIC_APPROACH",
        name: "18. Pacific Ocean Terminal Approach",
        targetMode: "STARSHIP",
        fov: 46.0,
        offset: new THREE.Vector3(0.32, 0.20, -0.48),
        lookOffset: new THREE.Vector3(0, 0.06, 0),
        shake: 0.03,
      },

      // 19. Wide Pacific Splashdown View Showing Landing Burn & Impact (User Image 6)
      SPLASHDOWN_WIDE: {
        id: "SPLASHDOWN_WIDE",
        name: "19. Pacific Splashdown Wide (Burn & Water Touchdown)",
        targetMode: "STARSHIP",
        fov: 44.0,
        offset: new THREE.Vector3(0.10, 0.22, -0.50),
        lookOffset: new THREE.Vector3(0, 0.18, 0),
        shake: 0.02,
      },

      // 20. Surface Water-Level Camera Capturing Spray & Steam Plume
      SPLASHDOWN_WATER_LEVEL: {
        id: "SPLASHDOWN_WATER_LEVEL",
        name: "20. Water-Level Surface View (Splash & Steam Rings)",
        targetMode: "SPLASHDOWN_ZONE",
        fov: 55.0,
        offset: new THREE.Vector3(0.18, 0.035, 0.22),
        lookOffset: new THREE.Vector3(0, 0.08, 0),
        shake: 0.02,
      },

      // 21. Contemplative Lingering Aftermath Over Calm Pacific Waters
      POST_SPLASHDOWN_HOLD: {
        id: "POST_SPLASHDOWN_HOLD",
        name: "21. Post-Splashdown Horizon Hold (Mission Complete)",
        targetMode: "SPLASHDOWN_ZONE",
        fov: 55.0,
        offset: new THREE.Vector3(0.95, 0.45, 1.10),
        lookOffset: new THREE.Vector3(0, 0, 0),
        shake: 0.0,
      },
    };
  }

  // Set camera state by ID
  setCameraState(stateId, immediate = false) {
    if (!this.stateDefinitions[stateId]) return;
    this.currentStateId = stateId;
    if (this.isInteractiveMode) {
      this.setInteractionMode(false);
    }
    this.applyStatePreset(stateId, immediate);

    // Update UI select box if available
    const select = document.getElementById("cfr-camera-select");
    if (select && select.value !== stateId) {
      select.value = stateId;
    }
  }

  applyStatePreset(stateId, immediate = false) {
    const preset = this.stateDefinitions[stateId];
    if (!preset) return;

    this.desiredFov = preset.fov;
    this.shakeIntensity = preset.shake || 0.0;

    if (immediate) {
      this.currentFov = this.desiredFov;
      this.camera.fov = this.currentFov;
      this.camera.updateProjectionMatrix();
      this.isImmediateSnap = true;
    }
  }

  snapCamera() {
    this.isImmediateSnap = true;
  }

  // Update target tracking and smooth camera motion per frame
  update(deltaSec, context = {}) {
    const preset = this.stateDefinitions[this.currentStateId] || this.stateDefinitions["PAD_WIDE"];
    const vehiclePos = context.vehiclePos || new THREE.Vector3(-0.71, 2.78, 5.69);
    const boosterPos = context.boosterPos || vehiclePos;
    const velocityDir = context.velocityDir || new THREE.Vector3(0, 1, 0);

    // Determine Anchor Target Center in World Coordinates
    let anchorPos = vehiclePos;
    if (preset.targetMode === "BOOSTER") {
      anchorPos = boosterPos;
    } else if (preset.targetMode === "STAGING_CENTER") {
      anchorPos = vehiclePos.clone().add(boosterPos).multiplyScalar(0.5);
    } else if (preset.targetMode === "SPLASHDOWN_ZONE" && context.oceanPos) {
      anchorPos = context.oceanPos;
    } else if (preset.targetMode === "PAD" && context.padPos) {
      anchorPos = context.padPos;
    }

    // Free 3D Interactive Mode (User touches / orbits / zooms around active anchor)
    if (this.isInteractiveMode && this.controls && this.controls.enabled) {
      this.controls.target.copy(anchorPos);
      this.controls.update();

      const minEarthRadius = 6.3725;
      if (this.camera.position.length() < minEarthRadius) {
        this.camera.position.normalize().multiplyScalar(minEarthRadius);
      }
      return;
    }

    const effectiveVelDir = (preset.targetMode === "BOOSTER" && context.boosterVelocityDir && context.boosterVelocityDir.lengthSq() > 1e-4)
      ? context.boosterVelocityDir
      : velocityDir;

    // Compute Strictly Orthonormal Aerospace Reference Frame at Anchor Position:
    // rHat: Radial unit vector from Earth center (0,0,0) through anchor (local zenith)
    const rHat = anchorPos.clone().normalize();
    if (rHat.lengthSq() < 1e-4) rHat.set(0, 1, 0);

    const northPole = new THREE.Vector3(0, 1, 0);
    let eastHat = new THREE.Vector3().crossVectors(northPole, rHat);
    if (eastHat.lengthSq() > 1e-4) {
      eastHat.normalize();
    } else {
      eastHat.set(1, 0, 0);
    }
    const northHat = new THREE.Vector3().crossVectors(rHat, eastHat).normalize();

    // vHat: In-track unit vector along flight path (projected on tangent plane)
    let vHat = effectiveVelDir.clone().sub(rHat.clone().multiplyScalar(effectiveVelDir.dot(rHat)));
    if (vHat.lengthSq() > 1e-4) {
      vHat.normalize();
    } else {
      // Default East-Southeast launch azimuth at Starbase (~97° azimuth)
      vHat = eastHat.clone().multiplyScalar(0.96).add(northHat.clone().multiplyScalar(-0.28)).normalize();
    }

    // hHat: Cross-track lateral unit vector (strictly orthogonal to rHat and vHat)
    const hHat = new THREE.Vector3().crossVectors(rHat, vHat).normalize();

    // Map offset: (hHat * x) + (rHat * y) + (vHat * z)
    const off = preset.offset || new THREE.Vector3(0.5, 0.4, -0.6);
    const lookOff = preset.lookOffset || new THREE.Vector3(0, 0.1, 0);

    const worldEyeOffset = hHat.clone().multiplyScalar(off.x)
      .add(rHat.clone().multiplyScalar(off.y))
      .add(vHat.clone().multiplyScalar(off.z));

    const worldLookOffset = hHat.clone().multiplyScalar(lookOff.x)
      .add(rHat.clone().multiplyScalar(lookOff.y))
      .add(vHat.clone().multiplyScalar(lookOff.z));

    this.desiredEye.copy(anchorPos).add(worldEyeOffset);
    this.desiredTarget.copy(anchorPos).add(worldLookOffset);

    // Apply Camera Shake Vibration
    if (this.shakeIntensity > 0.001) {
      const s = this.shakeIntensity * 0.25;
      this.shakeOffset.set(
        (Math.random() - 0.5) * 2.0 * s,
        (Math.random() - 0.5) * 2.0 * s,
        (Math.random() - 0.5) * 2.0 * s
      );
    } else {
      this.shakeOffset.set(0, 0, 0);
    }

    const lerpFactor = Math.min(1.0, deltaSec * (1.0 / this.smoothHalfLife));

    // Smooth Interpolation or Immediate Snap
    if (this.isImmediateSnap) {
      this.currentEye.copy(this.desiredEye);
      this.currentTarget.copy(this.desiredTarget);
      this.currentFov = this.desiredFov;
      this.isImmediateSnap = false;
    } else {
      this.currentEye.lerp(this.desiredEye, lerpFactor);
      this.currentTarget.lerp(this.desiredTarget, lerpFactor);
      this.currentFov += (this.desiredFov - this.currentFov) * lerpFactor;
    }
    if (Math.abs(this.camera.fov - this.currentFov) > 0.05) {
      this.camera.fov = this.currentFov;
      this.camera.updateProjectionMatrix();
    }

    // Safety: Clamp camera altitude above Earth surface (Earth radius = 6.371 scene units = 6371 km)
    // Guarantees camera eye position never penetrates below ground/ocean level (minimum clearance +1.5 km = 0.0015 units)
    const minEarthRadius = 6.3725;
    if (this.desiredEye.length() < minEarthRadius) {
      this.desiredEye.normalize().multiplyScalar(minEarthRadius);
    }
    if (this.currentEye.length() < minEarthRadius) {
      this.currentEye.normalize().multiplyScalar(minEarthRadius);
    }

    // Position Camera with Local Zenith Up Vector (Orthonormal Aerospace Basis)
    const finalCamPos = this.currentEye.clone().add(this.shakeOffset);
    if (finalCamPos.length() < minEarthRadius) {
      finalCamPos.normalize().multiplyScalar(minEarthRadius);
    }
    this.camera.position.copy(finalCamPos);

    let upVec = rHat.clone();
    const lookDir = this.currentTarget.clone().sub(finalCamPos).normalize();
    if (Math.abs(lookDir.dot(upVec)) > 0.95) {
      upVec = hHat.clone();
    }
    this.camera.up.copy(upVec);
    this.camera.lookAt(this.currentTarget);

    if (this.controls && !this.isInteractiveMode) {
      this.controls.target.copy(this.currentTarget);
    }
  }

  // Auto Director timeline evaluator (Strict adherence to User Request: track booster to splashdown, then show upper stage travel)
  evaluateAutoDirector(time_s, activeProfileKey) {
    if (!this.isAutoDirector || this.isInteractiveMode) return;

    if (activeProfileKey === "synthetic_engineering_test") {
      if (time_s < 6.0) this.setCameraState("PAD_LOW_ANGLE");
      else if (time_s < 14.0) this.setCameraState("ENTRY_DRONE_TRACK");
      else if (time_s < 20.0) this.setCameraState("PAD_WIDE");
      else this.setCameraState("PAD_WIDE");
      return;
    }

    // Flight 14 Observed Reconstruction Choreography:
    // 1. Prelaunch and 33-Raptor Liftoff
    if (time_s <= 0.0) {
      this.setCameraState("PAD_WIDE");
    } else if (time_s < 14.0) {
      this.setCameraState("IGNITION_TRACK");
    } else if (time_s < 60.0) {
      this.setCameraState("ASCENT_CHASE");
    } else if (time_s < 138.0) {
      this.setCameraState("ASCENT_LONG_LENS");
    } else if (time_s < 155.0) {
      // 2. MECO & Hot-Staging Separation: Dual Vehicle Wide Framing
      this.setCameraState("STAGING_WIDE");
    } else if (time_s < 225.0) {
      // 3. User directive: Track Super Heavy Booster through flip & 13-engine boostback burn toward Gulf of Mexico
      this.setCameraState("BOOSTER_RETURN_CHASE");
    } else if (time_s < 395.0) {
      // 4. Track Super Heavy Booster atmospheric descent with grid fin aerodynamic guidance
      this.setCameraState("BOOSTER_RETURN_CHASE");
    } else if (time_s < 440.0) {
      // 5. User directive: Track Super Heavy Booster landing burn & soft vertical splashdown in Gulf of Mexico!
      this.setCameraState("BOOSTER_GULF_WIDE");
    } else if (time_s < 535.0) {
      // 6. User directive: "once its get separated ,, show it until its down to earth ,,then auto show the upper tage travel"
      // Pivot Auto Director back to Starship Upper Stage accelerating to SECO (T+525s) into orbit!
      this.setCameraState("SHIP_SPACE_CHASE");
    } else if (time_s < 1300.0) {
      this.setCameraState("ORBIT_OVERVIEW");
    } else if (time_s < 1500.0) {
      this.setCameraState("SATELLITE_DEPLOY_CLOSE");
    } else if (time_s < 2200.0) {
      this.setCameraState("SATELLITE_TRAIN_WIDE");
    } else if (time_s < 9900.0) {
      this.setCameraState("ORBITAL_EARTH_LIMB");
    } else if (time_s < 10100.0) {
      this.setCameraState("DEORBIT_CHASE");
    } else if (time_s < 11100.0) {
      this.setCameraState("ENTRY_LONG_LENS");
    } else if (time_s < 11335.0) {
      this.setCameraState("ENTRY_DRONE_TRACK");
    } else if (time_s < 11355.0) {
      this.setCameraState("PACIFIC_APPROACH");
    } else if (time_s < 11400.0) {
      this.setCameraState("SPLASHDOWN_WIDE");
    } else {
      this.setCameraState("POST_SPLASHDOWN_HOLD");
    }
  }
}

window.CfrCameraDirector = CfrCameraDirector;
