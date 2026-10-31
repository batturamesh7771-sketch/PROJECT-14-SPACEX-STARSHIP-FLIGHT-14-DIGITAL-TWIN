/**
 * Starship Flight 14 — Engineering Lab Ocean Splashdown & Naval Recovery Fleet Environment
 * Copied from verified kinematic replay module for Engineering Lab integration.
 */

function createCfrWaterTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");

  // Translucent Pacific oceanic gradient with feathered edge conforming seamlessly to Earth sphere
  const grad = ctx.createRadialGradient(256, 256, 30, 256, 256, 256);
  grad.addColorStop(0.0, "rgba(14, 58, 99, 0.95)");
  grad.addColorStop(0.6, "rgba(10, 42, 78, 0.85)");
  grad.addColorStop(0.85, "rgba(6, 28, 56, 0.40)");
  grad.addColorStop(1.0, "rgba(4, 20, 42, 0.0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 512, 512);

  // Concentric and directional wave ripples
  ctx.strokeStyle = "rgba(160, 225, 255, 0.28)";
  ctx.lineWidth = 1.6;
  for (let r = 16; r < 256; r += 16) {
    ctx.beginPath();
    ctx.arc(256, 256, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Cross-swell surface glint
  ctx.strokeStyle = "rgba(220, 245, 255, 0.18)";
  ctx.lineWidth = 1.0;
  for (let y = 12; y < 512; y += 18) {
    ctx.beginPath();
    for (let x = 0; x <= 512; x += 24) {
      const dy = Math.sin((x + y * 1.8) * 0.08) * 4.0;
      if (x === 0) ctx.moveTo(x, y + dy);
      else ctx.lineTo(x, y + dy);
    }
    ctx.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  return texture;
}

class CfrOceanSplashdown {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Sub-components
    this.waterMesh = null;
    this.burnBoilGroup = null;
    this.impactSprayGroup = null;
    this.rippleRings = [];
    this.steamClouds = [];
    this.waterLight = null;
    this.recoveryFleetGroup = null;
    this.radarScanner = null;

    // Splashdown anchor position
    this.oceanPos = new THREE.Vector3();

    this.buildOceanEnvironment();
  }

  buildOceanEnvironment() {
    const waterGeo = new THREE.CircleGeometry(0.12, 48);
    const waterMat = new THREE.MeshStandardMaterial({
      map: createCfrWaterTexture(),
      color: 0x0a2d52,
      roughness: 0.16,
      metalness: 0.82,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.94,
    });
    this.waterMesh = new THREE.Mesh(waterGeo, waterMat);
    this.waterMesh.rotation.x = -Math.PI / 2;
    this.waterMesh.position.y = 0.0005;
    this.group.add(this.waterMesh);

    // Raptor Landing Burn Boil Ring
    this.burnBoilGroup = new THREE.Group();
    const boilGeo = new THREE.RingGeometry(0.005, 0.045, 36);
    const boilMat = new THREE.MeshBasicMaterial({
      color: 0xffdf88,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
    });
    this.boilDisc = new THREE.Mesh(boilGeo, boilMat);
    this.boilDisc.rotation.x = -Math.PI / 2;
    this.boilDisc.position.y = 0.002;
    this.burnBoilGroup.add(this.boilDisc);

    const innerBoilGeo = new THREE.CircleGeometry(0.022, 32);
    const innerBoilMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
    });
    this.innerBoilDisc = new THREE.Mesh(innerBoilGeo, innerBoilMat);
    this.innerBoilDisc.rotation.x = -Math.PI / 2;
    this.innerBoilDisc.position.y = 0.0025;
    this.burnBoilGroup.add(this.innerBoilDisc);

    this.waterLight = new THREE.PointLight(0xff9922, 0.0, 0.8, 1.2);
    this.waterLight.position.set(0, 0.02, 0);
    this.burnBoilGroup.add(this.waterLight);
    this.group.add(this.burnBoilGroup);

    // Concentric Expanding Foam Ripple Rings
    for (let r = 0; r < 5; r++) {
      const ringGeo = new THREE.RingGeometry(0.008, 0.014, 36);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xebf8ff,
        transparent: true,
        opacity: 0.0,
        side: THREE.DoubleSide,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.y = 0.0018 + r * 0.0004;
      this.rippleRings.push({ mesh: ringMesh, delay: r * 0.9 });
      this.group.add(ringMesh);
    }

    // Impact Spray Plume
    this.impactSprayGroup = new THREE.Group();
    const sprayGeo = new THREE.CylinderGeometry(0.015, 0.065, 0.10, 20, 1, true);
    const sprayMat = new THREE.MeshStandardMaterial({
      color: 0xe5f5ff,
      transparent: true,
      opacity: 0.0,
      roughness: 0.9,
    });
    this.sprayMesh = new THREE.Mesh(sprayGeo, sprayMat);
    this.sprayMesh.position.y = 0.05;
    this.impactSprayGroup.add(this.sprayMesh);

    // Billowing Steam Clouds
    const steamGeo = new THREE.SphereGeometry(0.028, 12, 12);
    const steamMat = new THREE.MeshStandardMaterial({
      color: 0xf2f8ff,
      roughness: 0.95,
      transparent: true,
      opacity: 0.0,
    });

    for (let s = 0; s < 18; s++) {
      const sMesh = new THREE.Mesh(steamGeo, steamMat.clone());
      const ang = (s / 18) * Math.PI * 2;
      const dist = 0.015 + Math.random() * 0.045;
      sMesh.position.set(Math.cos(ang) * dist, 0.015 + Math.random() * 0.02, Math.sin(ang) * dist);
      this.impactSprayGroup.add(sMesh);
      this.steamClouds.push({
        mesh: sMesh,
        basePos: sMesh.position.clone(),
        speedY: 0.015 + Math.random() * 0.025,
      });
    }
    this.group.add(this.impactSprayGroup);

    // 3D SpaceX / Naval Recovery Fleet
    this.buildRecoveryFleet();

    this.group.visible = false;
  }

  buildRecoveryFleet() {
    this.recoveryFleetGroup = new THREE.Group();

    const fleetX = 0.055;
    const fleetZ = -0.035;

    const shipGroup = new THREE.Group();
    shipGroup.position.set(fleetX, 0, fleetZ);

    const navyHullMat = new THREE.MeshStandardMaterial({
      color: 0x1e2838,
      roughness: 0.40,
      metalness: 0.75,
    });
    const whiteSuperMat = new THREE.MeshStandardMaterial({
      color: 0xf0f4f8,
      roughness: 0.35,
      metalness: 0.45,
    });
    const craneOrangeMat = new THREE.MeshStandardMaterial({
      color: 0xff5500,
      roughness: 0.35,
      metalness: 0.60,
    });
    const deckMat = new THREE.MeshStandardMaterial({
      color: 0x48525e,
      roughness: 0.85,
      metalness: 0.15,
    });

    // Hull (Go Searcher / Shannon class)
    const hullGeo = new THREE.BoxGeometry(0.045, 0.008, 0.014);
    const hull = new THREE.Mesh(hullGeo, navyHullMat);
    hull.position.y = 0.004;
    shipGroup.add(hull);

    const bowGeo = new THREE.ConeGeometry(0.007, 0.014, 4);
    const bow = new THREE.Mesh(bowGeo, navyHullMat);
    bow.rotation.z = -Math.PI / 2;
    bow.position.set(0.028, 0.004, 0);
    shipGroup.add(bow);

    const deckGeo = new THREE.BoxGeometry(0.044, 0.001, 0.0135);
    const deck = new THREE.Mesh(deckGeo, deckMat);
    deck.position.y = 0.0085;
    shipGroup.add(deck);

    const bridgeGeo = new THREE.BoxGeometry(0.014, 0.012, 0.011);
    const bridge = new THREE.Mesh(bridgeGeo, whiteSuperMat);
    bridge.position.set(0.008, 0.0145, 0);
    shipGroup.add(bridge);

    const winGeo = new THREE.BoxGeometry(0.003, 0.0025, 0.0112);
    const winMat = new THREE.MeshBasicMaterial({ color: 0x112233 });
    const win = new THREE.Mesh(winGeo, winMat);
    win.position.set(0.0145, 0.017, 0);
    shipGroup.add(win);

    const mastGeo = new THREE.CylinderGeometry(0.0006, 0.0008, 0.016, 8);
    const mast = new THREE.Mesh(mastGeo, whiteSuperMat);
    mast.position.set(0.008, 0.028, 0);
    shipGroup.add(mast);

    const radarBarGeo = new THREE.BoxGeometry(0.006, 0.001, 0.0012);
    this.radarScanner = new THREE.Mesh(radarBarGeo, craneOrangeMat);
    this.radarScanner.position.set(0.008, 0.035, 0);
    shipGroup.add(this.radarScanner);

    const craneBaseGeo = new THREE.CylinderGeometry(0.002, 0.0025, 0.006, 12);
    const craneBase = new THREE.Mesh(craneBaseGeo, craneOrangeMat);
    craneBase.position.set(-0.012, 0.0115, 0.004);
    shipGroup.add(craneBase);

    const boomGeo = new THREE.BoxGeometry(0.022, 0.0018, 0.0018);
    const boom = new THREE.Mesh(boomGeo, craneOrangeMat);
    boom.position.set(-0.018, 0.018, 0.002);
    boom.rotation.z = 0.45;
    shipGroup.add(boom);

    const heliGeo = new THREE.CylinderGeometry(0.006, 0.006, 0.0008, 24);
    const heliMat = new THREE.MeshStandardMaterial({ color: 0x333b45, roughness: 0.9 });
    const helipad = new THREE.Mesh(heliGeo, heliMat);
    helipad.position.set(-0.014, 0.009, 0);
    shipGroup.add(helipad);

    const aFrameGeo = new THREE.BoxGeometry(0.002, 0.008, 0.010);
    const aFrame = new THREE.Mesh(aFrameGeo, craneOrangeMat);
    aFrame.position.set(-0.021, 0.012, 0);
    shipGroup.add(aFrame);

    this.recoveryFleetGroup.add(shipGroup);

    const rhibPositions = [
      [fleetX - 0.020, 0, fleetZ + 0.016],
      [fleetX - 0.015, 0, fleetZ - 0.020],
    ];

    rhibPositions.forEach(([rx, ry, rz]) => {
      const rhibGroup = new THREE.Group();
      rhibGroup.position.set(rx, ry, rz);

      const tubeGeo = new THREE.BoxGeometry(0.012, 0.0025, 0.006);
      const tubeMat = new THREE.MeshStandardMaterial({ color: 0xff6600, roughness: 0.5 });
      const tube = new THREE.Mesh(tubeGeo, tubeMat);
      tube.position.y = 0.002;
      rhibGroup.add(tube);

      const conGeo = new THREE.BoxGeometry(0.003, 0.004, 0.003);
      const con = new THREE.Mesh(conGeo, whiteSuperMat);
      con.position.set(0, 0.004, 0);
      rhibGroup.add(con);

      this.recoveryFleetGroup.add(rhibGroup);
    });

    this.group.add(this.recoveryFleetGroup);
  }

  update(time_s, altitude_km, isTerminalPhase, vehiclePos, activeProfileKey) {
    const isStarshipSplash = isTerminalPhase || (altitude_km !== undefined && altitude_km < 3.5 && time_s > 11300.0);
    const isBoosterSplash = (time_s >= 395.0 && time_s <= 445.0 && activeProfileKey !== "synthetic_engineering_test");

    if (!isStarshipSplash && !isBoosterSplash) {
      this.group.visible = false;
      return;
    }

    this.group.visible = true;

    if (vehiclePos) {
      const rUp = vehiclePos.clone().normalize();
      const surfPos = rUp.clone().multiplyScalar(6.371);
      this.oceanPos.copy(surfPos);
      this.group.position.copy(surfPos);
      this.group.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), rUp);
    }

    if (this.radarScanner) {
      this.radarScanner.rotation.y = time_s * 4.0;
    }

    const isLandingBurn = (time_s >= 11335.0 && time_s < 11364.0) || (time_s >= 398.0 && time_s < 422.0);
    if (isLandingBurn) {
      const burnProgress = isBoosterSplash ? (time_s - 398.0) / 24.0 : (time_s - 11335.0) / 29.0;
      const intensity = Math.min(1.0, burnProgress * 2.5);

      this.boilDisc.material.opacity = 0.88 * intensity;
      this.boilDisc.scale.setScalar(1.0 + Math.sin(time_s * 25.0) * 0.18);

      if (this.innerBoilDisc) {
        this.innerBoilDisc.material.opacity = 0.95 * intensity;
        this.innerBoilDisc.scale.setScalar(1.0 + Math.cos(time_s * 30.0) * 0.22);
      }

      if (this.waterLight) {
        this.waterLight.intensity = 5.0 * intensity;
      }
    } else {
      this.boilDisc.material.opacity = 0.0;
      if (this.innerBoilDisc) this.innerBoilDisc.material.opacity = 0.0;
      if (this.waterLight) this.waterLight.intensity = 0.0;
    }

    const isImpact = (isBoosterSplash && time_s >= 422.0) || (!isBoosterSplash && time_s >= 11364.0);
    const impactRefT = isBoosterSplash ? 422.0 : 11364.0;

    if (isImpact) {
      const impactTime = time_s - impactRefT;

      if (impactTime < 16.0) {
        const sprayFactor = Math.max(0.0, 1.0 - impactTime / 16.0);
        this.sprayMesh.material.opacity = 0.88 * sprayFactor;
        this.sprayMesh.scale.set(
          1.0 + impactTime * 0.35,
          1.0 + impactTime * 0.60,
          1.0 + impactTime * 0.35
        );
      } else {
        this.sprayMesh.material.opacity = 0.0;
      }

      const steamFactor = Math.max(0.0, 1.0 - impactTime / 60.0);
      this.steamClouds.forEach((sc, i) => {
        if (steamFactor > 0.01) {
          sc.mesh.material.opacity = steamFactor * 0.80;
          sc.mesh.position.y = sc.basePos.y + impactTime * sc.speedY;
          sc.mesh.scale.setScalar((1.0 + impactTime * 0.15) * (0.8 + (i % 3) * 0.2));
        } else {
          sc.mesh.material.opacity = 0.0;
        }
      });

      this.rippleRings.forEach((ring) => {
        const localT = (impactTime - ring.delay) % 4.5;
        if (localT > 0 && impactTime < 90.0) {
          const frac = localT / 4.5;
          ring.mesh.material.opacity = (1.0 - frac) * 0.75;
          const currentScale = 1.0 + frac * 16.0;
          ring.mesh.scale.set(currentScale, currentScale, 1.0);
        } else {
          ring.mesh.material.opacity = 0.0;
        }
      });
    } else {
      this.sprayMesh.material.opacity = 0.0;
      this.steamClouds.forEach(sc => { sc.mesh.material.opacity = 0.0; });
      this.rippleRings.forEach(r => { r.mesh.material.opacity = 0.0; });
    }

    if (this.recoveryFleetGroup) {
      this.recoveryFleetGroup.visible = !isBoosterSplash;
    }
  }
}

window.CfrOceanSplashdown = CfrOceanSplashdown;
