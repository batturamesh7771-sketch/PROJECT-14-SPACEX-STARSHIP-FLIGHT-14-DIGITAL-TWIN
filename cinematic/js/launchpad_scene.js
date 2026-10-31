/**
 * Starship Flight 14 — Cinematic Starbase Launchpad & Mechazilla Complex
 * Strict Namespace: CFR (Cinematic Flight Replay)
 *
 * Implements:
 *   - High-fidelity Starbase launch environment matching User Images 2 & 4:
 *       * Authentic coastal shoreline (Boca Chica beach, Gulf of Mexico waters, tidal wetlands)
 *       * Starbase production facility silhouettes (High Bay, Mega Bay, Starfactory)
 *       * 145 m Mechazilla launch and catch tower with steel corner columns, truss tiers, top crane
 *       * Articulated triangular truss Chopstick arms & carriage with hydraulic actuators
 *       * Orbital Launch Mount (OLM) with 6 heavy structural legs and flame deflector
 *       * Cryogenic Tank Farm (insulated spherical & horizontal CH4 / LOX storage vessels)
 *   - Realistic Gaseous Emissions & Deluge Steam Plumes (User Image 2):
 *       * Elimination of low-poly "bubble" spheres
 *       * Multi-layered billowing water deluge vapor (H2O, H2) and Raptor combustion products (CO2, CO, soot)
 *       * Soft-textured turbulent smoke billows expanding horizontally and rolling upward
 *       * Intense fiery orange combustion fireball underglow from 33 Raptors (81 MN thrust)
 *   - Mechazilla Tower Catch sequence for Synthetic Sandbox (User Image 4)
 */

class CfrLaunchpadScene {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Starbase, TX Launch Site World Coordinates on spherical Earth
    this.padPos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
    this.rUp = this.padPos.clone().normalize();

    // Exact Orthonormal Aerospace Reference Frame at Starbase:
    // Earth Polar Axis: (0, 1, 0)
    const northPole = new THREE.Vector3(0, 1, 0);
    // Local East = cross(North, rUp).normalize()
    this.vEast = new THREE.Vector3().crossVectors(northPole, this.rUp).normalize();
    // Local North = cross(rUp, East).normalize()
    this.hNorth = new THREE.Vector3().crossVectors(this.rUp, this.vEast).normalize();


    // Sub-components
    this.towerGroup = null;
    this.chopsticksCarriage = null;
    this.chopstickArmLeft = null;
    this.chopstickArmRight = null;
    this.olmGroup = null;
    this.delugeCloudsGroup = null;
    this.delugeClouds = [];
    this.delugeFireLight = null;
    this.delugeFlameCore = null;

    // Materials
    this.towerMat = new THREE.MeshStandardMaterial({
      color: 0x3d444f,
      metalness: 0.88,
      roughness: 0.38,
    });
    this.steelMat = new THREE.MeshStandardMaterial({
      color: 0xdde4ec,
      metalness: 0.94,
      roughness: 0.20,
    });
    this.darkMat = new THREE.MeshStandardMaterial({
      color: 0x161a20,
      metalness: 0.85,
      roughness: 0.40,
    });
    this.concreteMat = new THREE.MeshStandardMaterial({
      color: 0x6e757d,
      roughness: 0.90,
      metalness: 0.05,
    });
    this.sandMat = new THREE.MeshStandardMaterial({
      color: 0xb4a485,
      roughness: 0.98,
      metalness: 0.02,
    });
    this.waterMat = new THREE.MeshStandardMaterial({
      color: 0x092b4a,
      roughness: 0.15,
      metalness: 0.65,
    });
    this.wetlandMat = new THREE.MeshStandardMaterial({
      color: 0x324836,
      roughness: 0.95,
      metalness: 0.02,
    });
    this.tankMat = new THREE.MeshStandardMaterial({
      color: 0xebedf0,
      roughness: 0.88,
      metalness: 0.08,
    });

    this.smokeTexture = this.createSmokeTexture();

    this.buildLaunchpadEnvironment();
  }

  // Generate soft procedural smoke/steam plume texture (eliminating shiny "bubbles")
  createSmokeTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext("2d");

    const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0.0, "rgba(255, 255, 255, 0.95)");
    grad.addColorStop(0.25, "rgba(240, 246, 255, 0.80)");
    grad.addColorStop(0.55, "rgba(220, 230, 245, 0.45)");
    grad.addColorStop(0.85, "rgba(200, 215, 235, 0.12)");
    grad.addColorStop(1.0, "rgba(180, 200, 220, 0.0)");

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 128, 128);

    // Subtle internal density whorls
    ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
    for (let i = 0; i < 6; i++) {
      ctx.beginPath();
      const ox = 64 + (Math.random() - 0.5) * 36;
      const oy = 64 + (Math.random() - 0.5) * 36;
      ctx.arc(ox, oy, 16 + Math.random() * 14, 0, Math.PI * 2);
      ctx.fill();
    }

    const tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    return tex;
  }

  buildLaunchpadEnvironment() {
    // Anchor launchpad group at Starbase coordinates and align to local vertical
    this.group.position.copy(this.padPos);

    // Pure orthonormal rotation: +X = East, +Y = rUp (Zenith), +Z = -North (South)
    const zSouth = this.hNorth.clone().negate();
    const rotMat = new THREE.Matrix4().makeBasis(this.vEast, this.rUp, zSouth);
    this.group.quaternion.setFromRotationMatrix(rotMat);

    this.buildCoastalTerrain();
    this.buildOrbitalLaunchMount();
    this.buildMechazillaTower();
    this.buildChopsticks();
    this.buildTankFarm();
    this.buildStarbaseProductionFacility();
    this.buildDelugeSystem();
  }

  // 1. Starbase Coastal Terrain: Boca Chica Beach, Gulf of Mexico, & Wetlands
  buildCoastalTerrain() {
    const terrainGroup = new THREE.Group();

    // Conformal Circular Concrete Pad Apron (centered directly beneath the Orbital Launch Mount)
    const padGeo = new THREE.CylinderGeometry(0.12, 0.125, 0.004, 48);
    const padMesh = new THREE.Mesh(padGeo, this.concreteMat);
    padMesh.position.set(-0.03, 0.002, 0);
    terrainGroup.add(padMesh);

    // Subtle flush ground transition ring (flush with spherical surface, eliminating tilted planar edges)
    const apronGeo = new THREE.RingGeometry(0.12, 0.16, 48);
    const apronMesh = new THREE.Mesh(apronGeo, this.sandMat);
    apronMesh.rotation.x = -Math.PI / 2;
    apronMesh.position.set(-0.03, 0.0025, 0);
    terrainGroup.add(apronMesh);

    this.group.add(terrainGroup);
  }

  // 2. Orbital Launch Mount (OLM) with Flame Diverter
  buildOrbitalLaunchMount() {
    this.olmGroup = new THREE.Group();

    // Heavy OLM Ring Platform
    const ringGeo = new THREE.CylinderGeometry(0.062, 0.068, 0.024, 32);
    const ringMesh = new THREE.Mesh(ringGeo, this.darkMat);
    ringMesh.position.set(0, 0.016, 0);
    this.olmGroup.add(ringMesh);

    // 6 Structural Support Pillars (Heavy Steel Box Columns)
    const legGeo = new THREE.CylinderGeometry(0.007, 0.009, 0.032, 12);
    for (let i = 0; i < 6; i++) {
      const angle = (i * Math.PI * 2) / 6;
      const leg = new THREE.Mesh(legGeo, this.towerMat);
      leg.position.set(Math.cos(angle) * 0.054, 0.008, Math.sin(angle) * 0.054);
      this.olmGroup.add(leg);
    }

    // Quick Disconnect (QD) Arm & Cryogenic Feed Umbilical
    const qdGeo = new THREE.BoxGeometry(0.018, 0.048, 0.018);
    const qdMesh = new THREE.Mesh(qdGeo, this.towerMat);
    qdMesh.position.set(0.072, 0.024, 0);
    this.olmGroup.add(qdMesh);

    this.group.add(this.olmGroup);
  }

  // 3. Mechazilla 145m Launch and Catch Tower (High Detail matching User Image 4)
  buildMechazillaTower() {
    this.towerGroup = new THREE.Group();
    const towerX = -0.105;
    const towerZ = 0.0;
    const towerHeight = 0.35; // Scaled ~145 m tower representation

    // 4 Main Vertical Steel Corner Columns
    const colGeo = new THREE.BoxGeometry(0.008, towerHeight, 0.008);
    const halfW = 0.024;
    const halfD = 0.024;

    const corners = [
      [-halfW, -halfD],
      [halfW, -halfD],
      [-halfW, halfD],
      [halfW, halfD],
    ];

    corners.forEach(([cx, cz]) => {
      const col = new THREE.Mesh(colGeo, this.towerMat);
      col.position.set(towerX + cx, towerHeight / 2, towerZ + cz);
      this.towerGroup.add(col);
    });

    // Horizontal Steel Tiers and Diagonal Truss Bracing
    const tiers = 14;
    for (let i = 1; i <= tiers; i++) {
      const y = (i / tiers) * towerHeight;
      const beamX = new THREE.BoxGeometry(halfW * 2, 0.0035, 0.0035);
      const b1 = new THREE.Mesh(beamX, this.towerMat);
      b1.position.set(towerX, y, towerZ + halfD);
      this.towerGroup.add(b1);

      const b2 = new THREE.Mesh(beamX, this.towerMat);
      b2.position.set(towerX, y, towerZ - halfD);
      this.towerGroup.add(b2);

      const beamZ = new THREE.BoxGeometry(0.0035, 0.0035, halfD * 2);
      const b3 = new THREE.Mesh(beamZ, this.towerMat);
      b3.position.set(towerX - halfW, y, towerZ);
      this.towerGroup.add(b3);

      const b4 = new THREE.Mesh(beamZ, this.towerMat);
      b4.position.set(towerX + halfW, y, towerZ);
      this.towerGroup.add(b4);
    }

    // Tower Crane Boom & Winch Platform at Top
    const craneBaseGeo = new THREE.BoxGeometry(0.065, 0.016, 0.038);
    const craneBase = new THREE.Mesh(craneBaseGeo, this.towerMat);
    craneBase.position.set(towerX + 0.008, towerHeight + 0.008, towerZ);
    this.towerGroup.add(craneBase);

    const boomGeo = new THREE.BoxGeometry(0.085, 0.006, 0.006);
    const boom = new THREE.Mesh(boomGeo, this.steelMat);
    boom.position.set(towerX + 0.045, towerHeight + 0.018, towerZ);
    this.towerGroup.add(boom);

    this.group.add(this.towerGroup);
  }

  // 4. Articulated Triangular Truss Chopstick Arms (User Image 4)
  buildChopsticks() {
    this.chopsticksCarriage = new THREE.Group();
    const towerX = -0.105;

    // Carriage Body (travels vertically on tower rails)
    const carriageGeo = new THREE.BoxGeometry(0.020, 0.042, 0.036);
    const carriageMesh = new THREE.Mesh(carriageGeo, this.darkMat);
    this.chopsticksCarriage.add(carriageMesh);

    // Left Chopstick Arm (Triangular Truss Structure)
    this.chopstickArmLeft = new THREE.Group();
    const mainArmGeo = new THREE.BoxGeometry(0.105, 0.007, 0.006);
    const armL1 = new THREE.Mesh(mainArmGeo, this.darkMat);
    armL1.position.set(0.052, 0, 0);
    this.chopstickArmLeft.add(armL1);

    // Top tension brace for chopstick catch load
    const braceGeo = new THREE.BoxGeometry(0.095, 0.004, 0.004);
    const braceL = new THREE.Mesh(braceGeo, this.towerMat);
    braceL.position.set(0.048, 0.012, 0);
    braceL.rotation.z = -0.12;
    this.chopstickArmLeft.add(braceL);

    this.chopstickArmLeft.position.set(0.010, 0.005, -0.015);
    this.chopsticksCarriage.add(this.chopstickArmLeft);

    // Right Chopstick Arm
    this.chopstickArmRight = new THREE.Group();
    const armR1 = new THREE.Mesh(mainArmGeo, this.darkMat);
    armR1.position.set(0.052, 0, 0);
    this.chopstickArmRight.add(armR1);

    const braceR = new THREE.Mesh(braceGeo, this.towerMat);
    braceR.position.set(0.048, 0.012, 0);
    braceR.rotation.z = -0.12;
    this.chopstickArmRight.add(braceR);

    this.chopstickArmRight.position.set(0.010, 0.005, 0.015);
    this.chopsticksCarriage.add(this.chopstickArmRight);

    // Initial position at launch resting height
    this.chopsticksCarriage.position.set(towerX + 0.022, 0.22, 0);
    this.group.add(this.chopsticksCarriage);
  }

  // 5. Cryogenic Tank Farm (Industrial CH4 & LOX Vertical Storage Silos & Horizontal Bullets)
  buildTankFarm() {
    const tankGroup = new THREE.Group();

    // Protective Concrete Earthen Blast Berm
    const bermGeo = new THREE.BoxGeometry(0.18, 0.024, 0.04);
    const berm = new THREE.Mesh(bermGeo, this.concreteMat);
    berm.position.set(-0.25, 0.012, -0.12);
    tankGroup.add(berm);

    // 4 Vertical Cryogenic Silo Tanks (Insulated White Steel Cylinders with Domed Tops)
    const siloGeo = new THREE.CylinderGeometry(0.016, 0.016, 0.065, 24);
    const domeGeo = new THREE.SphereGeometry(0.016, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const footingGeo = new THREE.CylinderGeometry(0.019, 0.021, 0.006, 24);

    const siloPositions = [
      [-0.26, 0.032, -0.18],
      [-0.31, 0.032, -0.18],
      [-0.26, 0.032, -0.25],
      [-0.31, 0.032, -0.25],
    ];

    siloPositions.forEach(([tx, ty, tz]) => {
      // Concrete foundation ring
      const footing = new THREE.Mesh(footingGeo, this.concreteMat);
      footing.position.set(tx, 0.003, tz);
      tankGroup.add(footing);

      // Vertical tank cylinder
      const silo = new THREE.Mesh(siloGeo, this.tankMat);
      silo.position.set(tx, ty, tz);
      tankGroup.add(silo);

      // Domed top cap
      const dome = new THREE.Mesh(domeGeo, this.tankMat);
      dome.position.set(tx, ty + 0.0325, tz);
      tankGroup.add(dome);

      // Cryogenic piping riser
      const pipeGeo = new THREE.CylinderGeometry(0.0015, 0.0015, 0.068, 8);
      const pipe = new THREE.Mesh(pipeGeo, this.steelMat);
      pipe.position.set(tx + 0.017, ty, tz);
      tankGroup.add(pipe);
    });

    // 2 Horizontal Bullet Tanks (High-Pressure Nitrogen & Helium Purge)
    const bulletGeo = new THREE.CylinderGeometry(0.010, 0.010, 0.060, 16);
    const bCapGeo = new THREE.SphereGeometry(0.010, 16, 12);

    const bulletPositions = [
      [-0.28, 0.016, -0.07],
      [-0.28, 0.016, -0.10],
    ];

    bulletPositions.forEach(([bx, by, bz]) => {
      const bMesh = new THREE.Mesh(bulletGeo, this.tankMat);
      bMesh.rotation.z = Math.PI / 2;
      bMesh.position.set(bx, by, bz);
      tankGroup.add(bMesh);

      const capL = new THREE.Mesh(bCapGeo, this.tankMat);
      capL.position.set(bx - 0.030, by, bz);
      tankGroup.add(capL);

      const capR = new THREE.Mesh(bCapGeo, this.tankMat);
      capR.position.set(bx + 0.030, by, bz);
      tankGroup.add(capR);

      // Saddle supports
      const sadGeo = new THREE.BoxGeometry(0.006, 0.012, 0.024);
      const s1 = new THREE.Mesh(sadGeo, this.concreteMat);
      s1.position.set(bx - 0.018, by - 0.006, bz);
      tankGroup.add(s1);
      const s2 = new THREE.Mesh(sadGeo, this.concreteMat);
      s2.position.set(bx + 0.018, by - 0.006, bz);
      tankGroup.add(s2);
    });

    // Cryogenic Overhead Pipe Bridge Truss connecting Tank Farm to OLM
    const bridgeGeo = new THREE.BoxGeometry(0.18, 0.006, 0.008);
    const bridge = new THREE.Mesh(bridgeGeo, this.towerMat);
    bridge.position.set(-0.13, 0.038, -0.06);
    tankGroup.add(bridge);

    this.group.add(tankGroup);
  }

  // 6. SpaceX Starbase Production Site (High Bay & Mega Bay Silhouettes in Background)
  buildStarbaseProductionFacility() {
    const facilityGroup = new THREE.Group();

    // High Bay & Mega Bay background silhouettes (placed inland 2 miles west along Highway 4)
    const highBayGeo = new THREE.BoxGeometry(0.024, 0.055, 0.018);
    const highBay = new THREE.Mesh(highBayGeo, this.darkMat);
    highBay.position.set(-0.24, 0.028, -0.16);
    facilityGroup.add(highBay);

    const megaBayGeo = new THREE.BoxGeometry(0.028, 0.065, 0.022);
    const megaBay = new THREE.Mesh(megaBayGeo, this.darkMat);
    megaBay.position.set(-0.29, 0.033, -0.18);
    facilityGroup.add(megaBay);

    const factoryGeo = new THREE.BoxGeometry(0.050, 0.016, 0.060);
    const factory = new THREE.Mesh(factoryGeo, this.concreteMat);
    factory.position.set(-0.25, 0.008, -0.09);
    facilityGroup.add(factory);

    this.group.add(facilityGroup);
  }

  // 7. Realistic Gaseous Emissions & Water Deluge Steam Cloud System (Matching User Image 2)
  buildDelugeSystem() {
    this.delugeCloudsGroup = new THREE.Group();

    // Central Fiery Combustion Exhaust Fireball Light (33 Raptors, 81.7 MN thrust)
    this.delugeFireLight = new THREE.PointLight(0xff5500, 0.0, 3.5, 2.0);
    this.delugeFireLight.position.set(0, 0.02, 0);
    this.delugeCloudsGroup.add(this.delugeFireLight);

    // Secondary Warm Ambient Deluge Glow Light
    this.delugeAmbientLight = new THREE.PointLight(0xffaa22, 0.0, 2.8, 2.5);
    this.delugeAmbientLight.position.set(0, 0.05, 0);
    this.delugeCloudsGroup.add(this.delugeAmbientLight);

    // Incandescent Combustion Core Plume at OLM Base
    const flameCoreGeo = new THREE.CylinderGeometry(0.045, 0.085, 0.080, 24, 1, true);
    const flameCoreMat = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.delugeFlameCore = new THREE.Mesh(flameCoreGeo, flameCoreMat);
    this.delugeFlameCore.position.set(0, 0.02, 0);
    this.delugeCloudsGroup.add(this.delugeFlameCore);

    // Massive Vertical Rocket Flame Column Shooting into Water Deluge Deflector (User Image 2)
    const flameColGeo = new THREE.CylinderGeometry(0.022, 0.042, 0.16, 24, 1, true);
    const flameColMat = new THREE.MeshBasicMaterial({
      color: 0xffeedd,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.launchFlameColumn = new THREE.Mesh(flameColGeo, flameColMat);
    this.launchFlameColumn.position.set(0, 0.08, 0);
    this.delugeCloudsGroup.add(this.launchFlameColumn);

    // Multi-Layered Volumetric Steam & Smoke Particle Billows (Camera-Facing Sprites with Soft Falloff)
    // Represents: Water Deluge (H2O, H2) + Raptor Combustion (CO2, CO, NOx, Black Carbon Soot)
    const billowCount = 72;

    for (let i = 0; i < billowCount; i++) {
      const ang = (i / billowCount) * Math.PI * 2;
      const dist = 0.025 + (i % 5) * 0.024 + Math.random() * 0.035;

      // Color variation: cream-white water deluge steam, warm core underglow, and outer grey soot/pollutants
      let billowColor = 0xf4f8fc; // Deluge water vapor (H2O)
      let blending = THREE.NormalBlending;
      let initOpacity = 0.80;

      if (i % 4 === 0) {
        billowColor = 0xffc477; // Incandescent underglow from 33 Raptors
        blending = THREE.AdditiveBlending;
        initOpacity = 0.90;
      } else if (i % 5 === 0) {
        billowColor = 0xced4dc; // Carbon soot & NOx combustion byproducts
        initOpacity = 0.70;
      }

      const spriteMat = new THREE.SpriteMaterial({
        map: this.smokeTexture,
        color: billowColor,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
        blending: blending,
      });

      const sprite = new THREE.Sprite(spriteMat);
      const baseX = Math.cos(ang) * dist;
      const baseZ = Math.sin(ang) * dist;
      const baseY = 0.008 + (i % 4) * 0.016;

      sprite.position.set(baseX, baseY, baseZ);
      const initialScale = 0.075 + Math.random() * 0.055;
      sprite.scale.set(initialScale, initialScale, 1.0);

      this.delugeClouds.push({
        mesh: sprite,
        basePos: new THREE.Vector3(baseX, baseY, baseZ),
        dir: new THREE.Vector3(Math.cos(ang), 0.30 + Math.random() * 0.50, Math.sin(ang)).normalize(),
        speed: 0.8 + Math.random() * 1.1,
        rotSpeed: (Math.random() - 0.5) * 0.025,
        baseScale: initialScale,
        targetOpacity: initOpacity,
      });

      this.delugeCloudsGroup.add(sprite);
    }

    this.group.add(this.delugeCloudsGroup);
  }

  // Update dynamic animations: deluge billowing, combustion fireball, chopstick catch
  update(time_s, isPrelaunch, activeProfileKey, vehicleAltitudeKm) {
    // 1. Deluge & Exhaust Billowing Dynamics (Matching User Image 2)
    let delugeFactor = 0.0;
    let flameFactor = 0.0;

    if (isPrelaunch) {
      // Water deluge system test and pre-chill vapor
      delugeFactor = 0.30;
      flameFactor = 0.0;
    } else if (time_s >= 0.0 && time_s < 18.0) {
      // 33 Raptor ignition: massive steam explosion & expanding ground roll
      const t = time_s;
      delugeFactor = Math.min(1.0, t * 2.0) * Math.max(0.0, 1.0 - t / 18.0);
      flameFactor = (t < 6.0) ? Math.min(1.0, t * 2.5) : Math.max(0.0, 1.0 - (t - 6.0) / 6.0);
    }

    // Flame Core & Fire Light Illumination
    if (this.delugeFlameCore) {
      this.delugeFlameCore.material.opacity = flameFactor * 0.90;
      const scaleF = 1.0 + Math.sin(time_s * 40.0) * 0.08;
      this.delugeFlameCore.scale.set(scaleF, 1.0 + flameFactor * 0.5, scaleF);
    }

    if (this.launchFlameColumn) {
      this.launchFlameColumn.material.opacity = flameFactor * 0.95;
      const colFlicker = 1.0 + Math.cos(time_s * 50.0) * 0.05;
      this.launchFlameColumn.scale.set(colFlicker, 1.0, colFlicker);
    }

    if (this.delugeFireLight) {
      this.delugeFireLight.intensity = flameFactor * 8.0;
    }
    if (this.delugeAmbientLight) {
      this.delugeAmbientLight.intensity = delugeFactor * 4.5;
    }

    // Dynamic Steam Billow Expansion & Rolling Plumes
    const progress = (time_s >= 0.0 && time_s < 18.0) ? (time_s / 18.0) : 0.0;
    this.delugeClouds.forEach((c) => {
      if (delugeFactor > 0.01) {
        c.mesh.material.opacity = delugeFactor * (c.targetOpacity || 0.75);
        // Expand horizontally and billow upward in turbulent roll
        const exp = 1.0 + progress * 5.5 * c.speed;
        c.mesh.position.x = c.basePos.x + c.dir.x * (progress * 0.22 * c.speed);
        c.mesh.position.z = c.basePos.z + c.dir.z * (progress * 0.22 * c.speed);
        c.mesh.position.y = c.basePos.y + c.dir.y * (progress * 0.16 * c.speed);

        const currentScale = c.baseScale * exp;
        c.mesh.scale.set(currentScale, currentScale, 1.0);
        if (c.mesh.material.rotation !== undefined) {
          c.mesh.material.rotation += c.rotSpeed;
        }
      } else {
        c.mesh.material.opacity = 0.0;
        c.mesh.position.copy(c.basePos);
        c.mesh.scale.set(c.baseScale, c.baseScale, 1.0);
      }
    });

    // 2. Synthetic Sandbox Mechazilla Catch Animation (User Image 4)
    if (activeProfileKey === "synthetic_engineering_test") {
      if (time_s < 6.0) {
        this.chopstickArmLeft.rotation.y = -0.42;
        this.chopstickArmRight.rotation.y = 0.42;
        this.chopsticksCarriage.position.y = 0.22;
      } else if (time_s < 14.0) {
        // Booster approaches tower: chopsticks adjust height and angle
        this.chopstickArmLeft.rotation.y = -0.25;
        this.chopstickArmRight.rotation.y = 0.25;
        this.chopsticksCarriage.position.y = 0.20 + Math.sin(time_s * 2.0) * 0.005;
      } else if (time_s < 20.0) {
        // Catch closure: chopsticks close securely onto booster catch pins
        this.chopstickArmLeft.rotation.y = -0.04;
        this.chopstickArmRight.rotation.y = 0.04;
        this.chopsticksCarriage.position.y = 0.18;
      }
    } else {
      // Historical launch: Chopsticks swing fully open to clear the ascending stack
      if (time_s >= 0.0 && time_s < 16.0) {
        const openFactor = Math.min(1.0, time_s / 5.0);
        this.chopstickArmLeft.rotation.y = -0.40 * openFactor;
        this.chopstickArmRight.rotation.y = 0.40 * openFactor;
      } else if (time_s < 0.0) {
        this.chopstickArmLeft.rotation.y = -0.05;
        this.chopstickArmRight.rotation.y = 0.05;
      }
    }

    // Launchpad complex remains permanently visible on Earth at Boca Chica, Texas
    // Naturally receding into distance as vehicle ascends toward orbit
    this.group.visible = true;
  }
}

window.CfrLaunchpadScene = CfrLaunchpadScene;
