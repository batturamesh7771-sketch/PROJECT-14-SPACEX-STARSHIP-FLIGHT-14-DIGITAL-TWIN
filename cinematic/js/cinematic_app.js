/**
 * Starship Flight 14 — Cinematic Mission Replay Master Application
 * Strict Namespace: CFR (Cinematic Flight Replay)
 *
 * Implements:
 *   - Full WebGL 3D scene orchestrator with ACESFilmic tone mapping
 *   - Earth centered at (0, 0, 0) with radius 6.371 scene units (1 unit = 1000 km)
 *   - Authentic 3D vehicle geometry: Super Heavy booster, Starship upper stage, articulated flaps,
 *     vented interstage ring, 33 + 6 Raptor engines, and 26 individual Starlink V3 satellites
 *   - Orthonormal flight kinematics without gimbal lock
 *   - Launchpad complex (Mechazilla tower, chopsticks, OLM, deluge system) at Starbase
 *   - Pacific Ocean splashdown environment (water surface, landing burn boil, spray, ripples, steam)
 *   - Synchronization with CfrReplayController and CfrCameraDirector
 *   - Real-time telemetry HUD, 26-satellite counter, lower-third event cards, scrubber, chapter ribbon
 */

class CfrCinematicApp {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.width = window.innerWidth;
    this.height = window.innerHeight;

    // Three.js Core
    this.scene = null;
    this.camera = null;
    this.renderer = null;

    // Space & Vehicle Groups
    this.earthGroup = null;
    this.earthMesh = null;
    this.vehicleMasterGroup = null;
    this.starshipUpperGroup = null;
    this.boosterGroup = null;
    this.satellitesGroup = null;
    this.starlinkSatellites = [];

    // Articulation
    this.flaps = { fwdL: null, fwdR: null, aftL: null, aftR: null };
    this.dispenserDoor = null;
    this.enginePlume = null;
    this.boosterPlume = null;
    this.plasmaGlow = null;

    // Environment Modules
    this.launchpadScene = null;
    this.oceanSplashdown = null;

    // Controllers
    this.replayController = null;
    this.cameraDirector = null;

    // Trajectory, Staging & Velocity State
    this.isStaged = false;
    this.lastVehiclePos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
    this.lastVelocityDir = new THREE.Vector3(0.65, 0.15, -0.74).normalize();
    this.lastBoosterPos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
    this.lastBoosterVelocityDir = new THREE.Vector3(0.65, 0.15, -0.74).normalize();
    this.supersonicCone = null;
    this.slipstreamPoints = null;

    this.init();
  }

  async init() {
    try {
      this.initThree();
      this.buildStarfield();
      this.buildEarth();
      this.buildVehicle();
      this.buildSatellites();

    // Initialize Interactive OrbitControls (Zoom, Rotate, Pan)
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enableZoom = true;
    this.controls.zoomSpeed = 1.2;
    this.controls.enableRotate = true;
    this.controls.rotateSpeed = 0.8;
    this.controls.enablePan = true;
    this.controls.panSpeed = 0.8;
    this.controls.minDistance = 0.005;
    this.controls.maxDistance = 30.0;
    this.controls.enabled = false; // Enabled dynamically when user touches/drags canvas

    // Initialize Launchpad & Ocean Environments
    this.launchpadScene = new CfrLaunchpadScene(this.scene);
    this.oceanSplashdown = new CfrOceanSplashdown(this.scene);

    // Initialize Camera Director with OrbitControls link
    this.cameraDirector = new CfrCameraDirector(this.camera, { controls: this.controls });
    window.cfrCameraDirector = this.cameraDirector;

    // Seamless touch / mouse interaction engagement on drag
    let pointerStartX = 0;
    let pointerStartY = 0;

    this.canvas.addEventListener("pointerdown", (e) => {
      pointerStartX = e.clientX;
      pointerStartY = e.clientY;
    });

    this.canvas.addEventListener("pointermove", (e) => {
      if (e.buttons > 0) {
        const dx = Math.abs(e.clientX - pointerStartX);
        const dy = Math.abs(e.clientY - pointerStartY);
        if (dx > 4 || dy > 4) {
          if (!this.cameraDirector.isInteractiveMode) {
            this.cameraDirector.setInteractionMode(true);
          }
        }
      }
    });

    this.canvas.addEventListener("wheel", () => {
      if (!this.cameraDirector.isInteractiveMode) {
        this.cameraDirector.setInteractionMode(true);
      }
    }, { passive: true });

    // Load Scenario Data & Init Replay Controller
    let scenarioData = window.EMBEDDED_SCENARIO_DATA;
    if (!scenarioData) {
      try {
        const resp = await fetch("data/scenario_data.json");
        if (resp.ok) scenarioData = await resp.json();
      } catch (e) {
        console.warn("Could not fetch scenario_data.json, falling back:", e);
      }
    }
    if (!scenarioData && window.EMBEDDED_SCENARIO_DATA) {
      scenarioData = window.EMBEDDED_SCENARIO_DATA;
    }

    this.replayController = new CfrReplayController({
      scenarioData: scenarioData,
      onTick: (time_s, statePoint, boosterState, activeProfile, playState) => {
        this.onReplayTick(time_s, statePoint, boosterState, activeProfile, playState);
      },
      onProfileChange: (activeProfile, profileKey) => {
        this.onProfileChange(activeProfile, profileKey);
      },
      onEventTrigger: (eventId, time_s, activeProfile) => {
        this.onEventTrigger(eventId, time_s, activeProfile);
      },
    });
    window.cfrReplayController = this.replayController;

    this.bindUI();
    this.bindWindowResize();

    // Start Master Render Loop
    this.lastFrameTime = performance.now();
    this.renderLoop = this.renderLoop.bind(this);
    requestAnimationFrame(this.renderLoop);
    } catch (e) {
      console.error("CFR App init error:", e);
      window.__cfrInitError = (e && e.stack) ? e.stack : String(e);
    }
  }

  initThree() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x02050e);
    this.scene.fog = new THREE.FogExp2(0x02050e, 0.0001);

    this.camera = new THREE.PerspectiveCamera(48, this.width / this.height, 0.001, 5000);
    this.camera.position.set(-0.7, 3.2, 6.2);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: "high-performance",
      alpha: true,
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.35;

    // Physically Inspired Space Lighting
    const ambientLight = new THREE.AmbientLight(0x28384c, 0.95);
    this.scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 2.5);
    sunLight.position.set(60, 45, 50).normalize().multiplyScalar(100);
    this.scene.add(sunLight);

    // Subtle vehicle fill light (reduced from 1.2 to 0.2 to prevent planet wash-out)
    const vehicleFill = new THREE.DirectionalLight(0xdde8ff, 0.2);
    this.camera.add(vehicleFill);
    this.scene.add(this.camera);

    const earthAlbedo = new THREE.DirectionalLight(0x0e223d, 0.4);
    earthAlbedo.position.set(0, -60, 0);
    this.scene.add(earthAlbedo);
  }

  buildStarfield() {
    const starCount = 4000;
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(starCount * 3);
    const col = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      const r = 800 + Math.random() * 400;
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(2 * Math.random() - 1);
      pos[i] = r * Math.sin(ph) * Math.cos(th);
      pos[i + 1] = r * Math.sin(ph) * Math.sin(th);
      pos[i + 2] = r * Math.cos(ph);

      const t = Math.random();
      if (t > 0.8) { col[i] = 1.0; col[i + 1] = 0.85; col[i + 2] = 0.7; }
      else if (t > 0.6) { col[i] = 0.75; col[i + 1] = 0.9; col[i + 2] = 1.0; }
      else { col[i] = 0.95; col[i + 1] = 0.95; col[i + 2] = 1.0; }
    }
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));

    const mat = new THREE.PointsMaterial({ size: 1.5, vertexColors: true, transparent: true, opacity: 0.85 });
    this.scene.add(new THREE.Points(geo, mat));
  }

  buildEarth() {
    this.earthGroup = new THREE.Group();
    const earthRadius = 6.371; // 6371 km in scene units
    const earthGeo = new THREE.SphereGeometry(earthRadius, 96, 96);

    let earthTex = null;
    const loader = new THREE.TextureLoader();
    if (window.EMBEDDED_TEXTURES && window.EMBEDDED_TEXTURES.earthDay) {
      try {
        earthTex = loader.load(window.EMBEDDED_TEXTURES.earthDay);
      } catch (e) {
        earthTex = this.createFallbackEarthTexture();
      }
    } else {
      earthTex = this.createFallbackEarthTexture();
    }

    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTex,
      roughness: 0.85,
      metalness: 0.05,
    });
    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthGroup.add(this.earthMesh);

    // Physically Credible Rayleigh Atmospheric Limb (Transparent at normal view, blue only at horizon grazing)
    const atmoGeo = new THREE.SphereGeometry(earthRadius * 1.018, 96, 96);
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vWorldPosition;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 worldPos = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPos.xyz;
          gl_Position = projectionMatrix * viewMatrix * worldPos;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vWorldPosition;
        void main() {
          vec3 viewDir = normalize(cameraPosition - vWorldPosition);
          float cosTheta = max(0.0, dot(viewDir, vNormal));
          // Sharp Rayleigh power so the atmospheric glow only appears at the grazing horizon
          float rim = pow(1.0 - cosTheta, 5.0);
          vec3 sunDir = normalize(vec3(60.0, 45.0, 50.0));
          float sunFacing = max(0.0, dot(vNormal, sunDir) * 0.7 + 0.3);
          vec3 skyColor = mix(vec3(0.04, 0.35, 0.85), vec3(0.55, 0.80, 1.0), pow(rim, 2.0));
          gl_FragColor = vec4(skyColor, rim * sunFacing * 0.75);
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.FrontSide,
      transparent: true,
      depthWrite: false,
    });
    this.earthGroup.add(new THREE.Mesh(atmoGeo, atmoMat));

    // Centered at world origin (0, 0, 0)
    this.scene.add(this.earthGroup);
  }

  createFallbackEarthTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext("2d");

    // Deep Indigo/Navy Ocean Base
    const oceanGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    oceanGrad.addColorStop(0, "#030c22");
    oceanGrad.addColorStop(0.5, "#041436");
    oceanGrad.addColorStop(1, "#030c22");
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Natural Continental Landmasses
    ctx.fillStyle = "#1e3820"; // Temperate Forest Green
    // North America
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.25, canvas.height * 0.30, 220, 120, -0.2, 0, Math.PI * 2);
    ctx.fill();
    // South America
    ctx.fillStyle = "#26421c";
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.32, canvas.height * 0.65, 120, 190, 0.2, 0, Math.PI * 2);
    ctx.fill();
    // Eurasia
    ctx.fillStyle = "#2a3d24";
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.65, canvas.height * 0.30, 340, 140, 0.1, 0, Math.PI * 2);
    ctx.fill();
    // Africa
    ctx.fillStyle = "#4a422a"; // Arid Savanna & Sahara
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.54, canvas.height * 0.52, 160, 180, 0.1, 0, Math.PI * 2);
    ctx.fill();
    // Australia
    ctx.fillStyle = "#5c4026"; // Outback Red/Ochre
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.82, canvas.height * 0.70, 90, 70, 0, 0, Math.PI * 2);
    ctx.fill();

    // Polar Ice Caps
    ctx.fillStyle = "#e2edf8";
    ctx.fillRect(0, 0, canvas.width, 45);
    ctx.fillRect(0, canvas.height - 45, canvas.width, 45);

    // Weather / Cloud Systems
    ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
    for (let c = 0; c < 24; c++) {
      ctx.beginPath();
      const cx = (c * 88) % canvas.width;
      const cy = 200 + ((c * 47) % 600);
      ctx.ellipse(cx, cy, 140, 40, (c * 0.4), 0, Math.PI * 2);
      ctx.fill();
    }

    return new THREE.CanvasTexture(canvas);
  }

  // Build High-Fidelity 3D CAD Starship & Super Heavy Vehicle Stack (Matching FreeCAD P2 Assemblies)
  buildVehicle() {
    this.vehicleMasterGroup = new THREE.Group();

    // Visual scale: 1 scene unit = 1000 km.
    // Vehicle visual envelope on Earth globe: radius = 0.024 scene units (~24 m visual scale)
    const radius = 0.024;
    const barrelLen = 0.12;      // 34.3 m Starship fuselage tanks
    const noseLen = 0.08;        // 16.0 m Ogive nosecone
    const boosterLen = 0.18;     // 71.0 m Super Heavy booster barrel

    // Aerospace Engineering Materials
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0xecf2f8,
      metalness: 0.95,
      roughness: 0.16,
    });
    const weldMat = new THREE.MeshStandardMaterial({
      color: 0xd4dee8,
      metalness: 0.88,
      roughness: 0.35,
    });
    const tileMat = new THREE.MeshStandardMaterial({
      color: 0x0a0c10,
      metalness: 0.05,
      roughness: 0.92,
    });
    const darkMat = new THREE.MeshStandardMaterial({
      color: 0x1b1f24,
      metalness: 0.85,
      roughness: 0.35,
    });
    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x4a535e,
      metalness: 0.88,
      roughness: 0.42,
    });
    const vacNozzleMat = new THREE.MeshStandardMaterial({
      color: 0x16181b,
      metalness: 0.82,
      roughness: 0.40,
    });

    // =========================================================================
    // 1. STARSHIP UPPER STAGE (STAGE 2)
    // =========================================================================
    this.starshipUpperGroup = new THREE.Group();

    // 1.1 Leeward Stainless Barrel (AISI 304L Cold-Worked Steel)
    const barrelGeo = new THREE.CylinderGeometry(radius, radius, barrelLen, 36, 1, false, Math.PI / 2, Math.PI);
    const barrel = new THREE.Mesh(barrelGeo, steelMat);
    barrel.position.y = barrelLen / 2;
    this.starshipUpperGroup.add(barrel);

    // 1.2 Windward Hexagonal Ceramic Thermal Protection System (Black TPS Belly)
    const bellyGeo = new THREE.CylinderGeometry(radius * 1.002, radius * 1.002, barrelLen, 36, 1, false, -Math.PI / 2, Math.PI);
    const belly = new THREE.Mesh(bellyGeo, tileMat);
    belly.position.y = barrelLen / 2;
    this.starshipUpperGroup.add(belly);

    // 1.3 Circumferential Stainless Steel Weld Seams (10 Ring Welds)
    const weldGeo = new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, 0.0008, 36);
    for (let w = 1; w < 10; w++) {
      const ring = new THREE.Mesh(weldGeo, weldMat);
      ring.position.y = (w / 10.0) * barrelLen;
      this.starshipUpperGroup.add(ring);
    }

    // 1.4 Aerodynamic Flap Actuator Raceways / Longitudinal Aero Covers
    const racewayGeo = new THREE.BoxGeometry(0.002, barrelLen * 0.92, 0.0035);
    const rwL = new THREE.Mesh(racewayGeo, steelMat);
    rwL.position.set(-radius * 0.99, barrelLen * 0.50, 0);
    this.starshipUpperGroup.add(rwL);
    const rwR = new THREE.Mesh(racewayGeo, steelMat);
    rwR.position.set(radius * 0.99, barrelLen * 0.50, 0);
    this.starshipUpperGroup.add(rwR);

    // 1.5 Tangent Ogive Nosecone (Dual-Lobe: Leeward Stainless & Windward TPS)
    const nosePoints = [];
    const rho = (radius * radius + noseLen * noseLen) / (2.0 * radius);
    for (let i = 0; i <= 24; i++) {
      const y = (i / 24) * noseLen;
      const term = Math.max(0.0, rho * rho - y * y);
      const r = Math.max(0.0, Math.sqrt(term) + radius - rho);
      nosePoints.push(new THREE.Vector2(r, y));
    }
    nosePoints.push(new THREE.Vector2(0, noseLen));

    const noseSteelGeo = new THREE.LatheGeometry(nosePoints, 36, Math.PI / 2, Math.PI);
    const noseSteel = new THREE.Mesh(noseSteelGeo, steelMat);
    noseSteel.position.y = barrelLen;
    this.starshipUpperGroup.add(noseSteel);

    const noseTpsGeo = new THREE.LatheGeometry(nosePoints, 36, -Math.PI / 2, Math.PI);
    const noseTps = new THREE.Mesh(noseTpsGeo, tileMat);
    noseTps.position.y = barrelLen;
    noseTps.scale.set(1.002, 1.0, 1.002);
    this.starshipUpperGroup.add(noseTps);

    // 1.6 Forward Canards (Articulated Aerodynamic Wedge Airfoils with Cylindrical Hinge Pins)
    const canardGroup = new THREE.Group();
    const canardGeo = new THREE.BoxGeometry(radius * 1.85, 0.0032, radius * 0.95);
    const pinGeo = new THREE.CylinderGeometry(0.0025, 0.0025, radius * 0.40, 16);

    this.flaps.fwdL = new THREE.Mesh(canardGeo, steelMat);
    this.flaps.fwdL.position.set(-radius * 1.15, barrelLen + noseLen * 0.38, 0);
    const pinL = new THREE.Mesh(pinGeo, darkMat);
    pinL.rotation.z = Math.PI / 2;
    pinL.position.set(-radius * 0.35, 0, 0);
    this.flaps.fwdL.add(pinL);
    this.starshipUpperGroup.add(this.flaps.fwdL);

    this.flaps.fwdR = new THREE.Mesh(canardGeo, steelMat);
    this.flaps.fwdR.position.set(radius * 1.15, barrelLen + noseLen * 0.38, 0);
    const pinR = new THREE.Mesh(pinGeo, darkMat);
    pinR.rotation.z = Math.PI / 2;
    pinR.position.set(radius * 0.35, 0, 0);
    this.flaps.fwdR.add(pinR);
    this.starshipUpperGroup.add(this.flaps.fwdR);

    // 1.7 Aft Delta Flaps (Articulated Heavy Aerodynamic Delta Flaps with TPS Backing)
    const aftGeo = new THREE.BoxGeometry(radius * 2.35, 0.0045, radius * 1.65);
    this.flaps.aftL = new THREE.Mesh(aftGeo, steelMat);
    this.flaps.aftL.position.set(-radius * 1.35, 0.024, 0);
    this.starshipUpperGroup.add(this.flaps.aftL);

    this.flaps.aftR = new THREE.Mesh(aftGeo, steelMat);
    this.flaps.aftR.position.set(radius * 1.35, 0.024, 0);
    this.starshipUpperGroup.add(this.flaps.aftR);

    // 1.8 Forward PEZ Payload Dispenser Door & Slot (Leeward Upper Fuselage)
    this.dispenserDoor = new THREE.Group();
    const doorGeo = new THREE.BoxGeometry(radius * 0.72, 0.003, radius * 0.36);
    const doorMesh = new THREE.Mesh(doorGeo, steelMat);
    doorMesh.position.set(0, 0, radius * 0.18);
    this.dispenserDoor.add(doorMesh);
    this.dispenserDoor.position.set(0, barrelLen + noseLen * 0.22, radius * 0.85);
    this.starshipUpperGroup.add(this.dispenserDoor);

    // 1.9 Six Raptor 3 Engines on Starship Thrust Puck
    // 3 Center Sea-Level Engines (gimbal capable)
    const slBellGeo = new THREE.ConeGeometry(radius * 0.18, radius * 0.42, 16, 1, true);
    for (let e = 0; e < 3; e++) {
      const ang = (e * Math.PI * 2) / 3;
      const bell = new THREE.Mesh(slBellGeo, darkMat);
      bell.position.set(Math.cos(ang) * radius * 0.32, -radius * 0.22, Math.sin(ang) * radius * 0.32);
      bell.rotation.x = Math.PI;
      this.starshipUpperGroup.add(bell);
    }
    // 3 Outer Vacuum Engines (Large regeneratively cooled expansion bells)
    const vacBellGeo = new THREE.ConeGeometry(radius * 0.32, radius * 0.65, 18, 1, true);
    for (let e = 0; e < 3; e++) {
      const ang = (e * Math.PI * 2) / 3 + Math.PI / 3;
      const bell = new THREE.Mesh(vacBellGeo, vacNozzleMat);
      bell.position.set(Math.cos(ang) * radius * 0.65, -radius * 0.34, Math.sin(ang) * radius * 0.65);
      bell.rotation.x = Math.PI;
      this.starshipUpperGroup.add(bell);
    }

    // 1.10 Starship Engine Exhaust Plume (Vacuum / Upper Burn)
    const plumeGeo = new THREE.ConeGeometry(radius * 0.5, radius * 3.5, 16);
    const plumeMat = new THREE.MeshBasicMaterial({ color: 0x44aaff, transparent: true, opacity: 0.0 });
    this.enginePlume = new THREE.Mesh(plumeGeo, plumeMat);
    this.enginePlume.position.y = -radius * 1.7;
    this.starshipUpperGroup.add(this.enginePlume);

    // 1.11 Multi-Layered Raptor Landing Burn Plume (Matching User Image 6)
    this.landingBurnGroup = new THREE.Group();
    const coreGeo = new THREE.ConeGeometry(radius * 0.45, radius * 4.2, 16);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xfff6d0,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.landingCorePlume = new THREE.Mesh(coreGeo, coreMat);
    this.landingCorePlume.position.y = -radius * 2.1;
    this.landingBurnGroup.add(this.landingCorePlume);

    const midGeo = new THREE.ConeGeometry(radius * 0.68, radius * 5.8, 16);
    const midMat = new THREE.MeshBasicMaterial({
      color: 0xff6a00,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.landingMidPlume = new THREE.Mesh(midGeo, midMat);
    this.landingMidPlume.position.y = -radius * 2.9;
    this.landingBurnGroup.add(this.landingMidPlume);

    const haloGeo = new THREE.ConeGeometry(radius * 0.95, radius * 7.5, 16);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0xaa22ff,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.landingHaloPlume = new THREE.Mesh(haloGeo, haloMat);
    this.landingHaloPlume.position.y = -radius * 3.75;
    this.landingBurnGroup.add(this.landingHaloPlume);
    this.starshipUpperGroup.add(this.landingBurnGroup);

    // 1.12 Aerodynamic Flap Condensation Vapor Streamers
    this.flapStreamers = new THREE.Group();
    const stGeo = new THREE.CylinderGeometry(0.001, 0.005, 0.22, 8, 1, true);
    const stMat = new THREE.MeshBasicMaterial({
      color: 0xe8f4ff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
    });
    this.streamerL = new THREE.Mesh(stGeo, stMat);
    this.streamerL.position.set(-radius * 1.25, 0.11, 0);
    this.flapStreamers.add(this.streamerL);
    this.streamerR = new THREE.Mesh(stGeo, stMat.clone());
    this.streamerR.position.set(radius * 1.25, 0.11, 0);
    this.flapStreamers.add(this.streamerR);
    this.starshipUpperGroup.add(this.flapStreamers);

    // 1.13 Reentry Plasma Glow Envelope
    const plasmaGeo = new THREE.SphereGeometry(radius * 1.8, 24, 24);
    const plasmaMat = new THREE.MeshBasicMaterial({ color: 0xff4411, transparent: true, opacity: 0.0 });
    this.plasmaGlow = new THREE.Mesh(plasmaGeo, plasmaMat);
    this.plasmaGlow.position.y = barrelLen * 0.5;
    this.starshipUpperGroup.add(this.plasmaGlow);

    // Position Upper Stage atop Booster
    this.starshipUpperGroup.position.y = boosterLen;
    this.vehicleMasterGroup.add(this.starshipUpperGroup);

    // =========================================================================
    // 2. SUPER HEAVY BOOSTER (STAGE 1)
    // =========================================================================
    this.boosterGroup = new THREE.Group();

    // 2.1 71m Cylindrical Booster Barrel
    const bGeo = new THREE.CylinderGeometry(radius, radius, boosterLen, 36);
    const bMesh = new THREE.Mesh(bGeo, steelMat);
    bMesh.position.y = boosterLen / 2;
    this.boosterGroup.add(bMesh);

    // 2.2 Booster Circumferential Weld Rings (18 Rings)
    for (let w = 1; w < 18; w++) {
      const bRing = new THREE.Mesh(weldGeo, weldMat);
      bRing.position.y = (w / 18.0) * boosterLen;
      this.boosterGroup.add(bRing);
    }

    // 2.3 Vented Interstage Hot-Staging Ring (with 24 Recessed Exhaust Ports)
    const interstageHeight = radius * 0.42;
    const interstageGeo = new THREE.CylinderGeometry(radius * 1.018, radius * 1.018, interstageHeight, 36, 1, true);
    const interstageMesh = new THREE.Mesh(interstageGeo, darkMat);
    interstageMesh.position.y = boosterLen;
    this.boosterGroup.add(interstageMesh);

    const portGeo = new THREE.BoxGeometry(0.0022, interstageHeight * 0.65, 0.0042);
    for (let p = 0; p < 24; p++) {
      const pAng = (p / 24) * Math.PI * 2;
      const portMesh = new THREE.Mesh(portGeo, tileMat);
      portMesh.position.set(Math.cos(pAng) * radius * 1.02, boosterLen, Math.sin(pAng) * radius * 1.02);
      portMesh.rotation.y = -pAng;
      this.boosterGroup.add(portMesh);
    }

    // 2.4 Four Cast Titanium Grid Fins with 3x5 Waffle Lattice Geometry (User Image 4)
    const finFrameGeo = new THREE.BoxGeometry(radius * 0.95, radius * 0.55, 0.0035);
    const finAxleGeo = new THREE.CylinderGeometry(0.002, 0.002, radius * 0.25, 12);

    for (let f = 0; f < 4; f++) {
      const ang = (f * Math.PI) / 2;
      const finGroup = new THREE.Group();

      const finFrame = new THREE.Mesh(finFrameGeo, titaniumMat);
      finGroup.add(finFrame);

      // Waffle grid internal lattice bars
      const barHGeo = new THREE.BoxGeometry(radius * 0.88, 0.0008, 0.0036);
      for (let b = -2; b <= 2; b++) {
        const barH = new THREE.Mesh(barHGeo, darkMat);
        barH.position.y = (b / 3.0) * (radius * 0.22);
        finGroup.add(barH);
      }

      const axle = new THREE.Mesh(finAxleGeo, darkMat);
      axle.rotation.z = Math.PI / 2;
      axle.position.set(-radius * 0.50, 0, 0);
      finGroup.add(axle);

      finGroup.position.set(Math.cos(ang) * radius * 1.25, boosterLen - radius * 0.32, Math.sin(ang) * radius * 1.25);
      finGroup.rotation.y = ang;
      this.boosterGroup.add(finGroup);
    }

    // 2.5 Full 33 Raptor 3 Engine Cluster on Booster Base
    // Layout: 1 Center, 2 Inner Ring (R=0.28r), 10 Middle Ring (R=0.55r), 20 Outer Ring (R=0.84r)
    const bEngBellGeo = new THREE.ConeGeometry(radius * 0.12, radius * 0.32, 12, 1, true);

    // 1 Center engine
    const cBell = new THREE.Mesh(bEngBellGeo, darkMat);
    cBell.position.set(0, -radius * 0.16, 0);
    cBell.rotation.x = Math.PI;
    this.boosterGroup.add(cBell);

    // 2 Inner ring engines
    for (let i = 0; i < 2; i++) {
      const iAng = i * Math.PI;
      const iBell = new THREE.Mesh(bEngBellGeo, darkMat);
      iBell.position.set(Math.cos(iAng) * radius * 0.28, -radius * 0.16, Math.sin(iAng) * radius * 0.28);
      iBell.rotation.x = Math.PI;
      this.boosterGroup.add(iBell);
    }

    // 10 Middle ring engines
    for (let m = 0; m < 10; m++) {
      const mAng = (m / 10.0) * Math.PI * 2;
      const mBell = new THREE.Mesh(bEngBellGeo, darkMat);
      mBell.position.set(Math.cos(mAng) * radius * 0.55, -radius * 0.16, Math.sin(mAng) * radius * 0.55);
      mBell.rotation.x = Math.PI;
      this.boosterGroup.add(mBell);
    }

    // 20 Outer ring engines
    for (let o = 0; o < 20; o++) {
      const oAng = (o / 20.0) * Math.PI * 2;
      const oBell = new THREE.Mesh(bEngBellGeo, darkMat);
      oBell.position.set(Math.cos(oAng) * radius * 0.84, -radius * 0.16, Math.sin(oAng) * radius * 0.84);
      oBell.rotation.x = Math.PI;
      this.boosterGroup.add(oBell);
    }

    // 2.6 Booster Exhaust Plume (33 Raptors, 81.7 MN Thrust)
    const bPlumeGeo = new THREE.ConeGeometry(radius * 1.5, radius * 6.5, 20);
    const bPlumeMat = new THREE.MeshBasicMaterial({ color: 0xffaa33, transparent: true, opacity: 0.0 });
    this.boosterPlume = new THREE.Mesh(bPlumeGeo, bPlumeMat);
    this.boosterPlume.position.y = -radius * 3.2;
    this.boosterGroup.add(this.boosterPlume);

    this.vehicleMasterGroup.add(this.boosterGroup);

    // 2.7 Supersonic Condensation Shock Shroud (Prandtl-Glauert Singularity near Max-Q)
    const coneGeo = new THREE.ConeGeometry(radius * 1.85, radius * 2.2, 24, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.supersonicCone = new THREE.Mesh(coneGeo, coneMat);
    this.supersonicCone.position.y = boosterLen * 0.75;
    this.vehicleMasterGroup.add(this.supersonicCone);

    // 2.8 High-Speed Atmospheric Slipstream Particles (Mach 1 to Mach 6+ speed sensation)
    const slipCount = 350;
    const slipGeo = new THREE.BufferGeometry();
    const slipPositions = new Float32Array(slipCount * 3);
    for (let p = 0; p < slipCount * 3; p += 3) {
      const a = Math.random() * Math.PI * 2;
      const r = radius * (1.1 + Math.random() * 2.8);
      slipPositions[p] = Math.cos(a) * r;
      slipPositions[p + 1] = (Math.random() - 0.5) * 0.45;
      slipPositions[p + 2] = Math.sin(a) * r;
    }
    slipGeo.setAttribute("position", new THREE.BufferAttribute(slipPositions, 3));
    const slipMat = new THREE.PointsMaterial({
      color: 0xd6eaff,
      size: 1.6,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
    });
    this.slipstreamPoints = new THREE.Points(slipGeo, slipMat);
    this.vehicleMasterGroup.add(this.slipstreamPoints);

    // Initial vehicle stack rests upright at Starbase
    this.vehicleMasterGroup.position.copy(this.lastVehiclePos);
    this.scene.add(this.vehicleMasterGroup);
  }

  // Build 26 High-Fidelity Starlink V3 Spacecraft (CAD Chassis with Phased Array & Solar Array)
  buildSatellites() {
    this.satellitesGroup = new THREE.Group();

    // Satellite Bus & Panel Materials
    const busMat = new THREE.MeshStandardMaterial({
      color: 0xedf2f7,
      metalness: 0.88,
      roughness: 0.20,
    });
    const phasedArrayMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc,
      metalness: 0.35,
      roughness: 0.35,
    });
    const solarMat = new THREE.MeshStandardMaterial({
      color: 0x164488,
      metalness: 0.95,
      roughness: 0.15,
      emissive: 0x081e3a,
    });
    const darkMat = new THREE.MeshStandardMaterial({
      color: 0x1a202c,
      metalness: 0.85,
      roughness: 0.40,
    });
    const thrusterMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.85,
    });

    for (let i = 0; i < 26; i++) {
      const sat = new THREE.Group();

      // 1. Sleek Starlink V3 Chassis Bus (7m x 3.5m x 0.25m scale)
      const busGeo = new THREE.BoxGeometry(0.024, 0.0032, 0.012);
      const busMesh = new THREE.Mesh(busGeo, busMat);
      sat.add(busMesh);

      // 2. Earth-Facing Phased Array Radar Antenna Deck
      const antGeo = new THREE.BoxGeometry(0.022, 0.0008, 0.010);
      const antMesh = new THREE.Mesh(antGeo, phasedArrayMat);
      antMesh.position.set(0, -0.0018, 0);
      sat.add(antMesh);

      // 3. Autonomous Star Tracker Navigation Sensors & Optical Space Lasers
      const stGeo = new THREE.CylinderGeometry(0.0010, 0.0012, 0.0025, 8);
      const st1 = new THREE.Mesh(stGeo, darkMat);
      st1.position.set(0.010, 0.0018, 0.0035);
      sat.add(st1);
      const st2 = new THREE.Mesh(stGeo, darkMat);
      st2.position.set(0.010, 0.0018, -0.0035);
      sat.add(st2);

      // 4. Hall-Effect Electric Krypton/Argon Thruster
      const thrusterGeo = new THREE.ConeGeometry(0.0012, 0.0035, 8);
      const thruster = new THREE.Mesh(thrusterGeo, thrusterMat);
      thruster.position.set(-0.013, 0, 0);
      thruster.rotation.z = Math.PI / 2;
      sat.add(thruster);

      // 5. Deployable Photovoltaic Sapphire Solar Array Wing (Unfolds after ejection)
      const solarGroup = new THREE.Group();
      const solarWingGeo = new THREE.BoxGeometry(0.048, 0.0010, 0.012);
      const solarMesh = new THREE.Mesh(solarWingGeo, solarMat);
      solarMesh.position.set(0.026, 0, 0);
      solarGroup.add(solarMesh);
      sat.add(solarGroup);

      sat.visible = false;
      this.starlinkSatellites.push({
        group: sat,
        solarGroup: solarGroup,
        deployTime_s: 1320.0 + i * (360.0 / 26.0),
        isDeployed: false,
        lateralOffset: (i % 2 === 0 ? 0.006 : -0.006) * (1.0 + (i % 4) * 0.25),
        verticalOffset: ((i % 3) - 1.0) * 0.003,
      });
      this.satellitesGroup.add(sat);
    }
    this.scene.add(this.satellitesGroup);
  }

  // Master per-frame replay clock callback
  onReplayTick(time_s, statePoint, boosterState, activeProfile, playState) {
    const isPrelaunch = playState.isPrelaunch;
    const profileKey = this.replayController.activeProfileKey;

    // 1. Evaluate Camera Director Auto-Transitions
    this.cameraDirector.evaluateAutoDirector(time_s, profileKey);

    // 2. Position Vehicle Stack / Upper Stage
    if (statePoint && statePoint.scene_pos) {
      let rawPos = new THREE.Vector3(statePoint.scene_pos[0], statePoint.scene_pos[1], statePoint.scene_pos[2]);
      let vPos = rawPos.clone();

      // Atmospheric Ascent Visual Elevation:
      // Guarantees the 121m full stack visibly lifts off the OLM, clears the 145m Mechazilla tower in 12s,
      // and accelerates rapidly through the troposphere/stratosphere into space (reaching space staging altitude at T=140s)
      if (!activeProfile.is_synthetic && time_s < 260.0) {
        const rUpPad = this.launchpadScene.rUp;
        if (time_s <= 0.0) {
          // Resting securely on OLM platform (elevated 0.028 scene units above pad ground)
          vPos.copy(this.launchpadScene.padPos).add(rUpPad.clone().multiplyScalar(0.028));
        } else if (time_s <= 14.0) {
          // Dramatic liftoff with quadratic thrust acceleration, clearing Mechazilla tower by T=12-14s
          const u = time_s / 14.0;
          const liftoffH = 0.028 + 0.40 * (u * u);
          vPos.copy(this.launchpadScene.padPos).add(rUpPad.clone().multiplyScalar(liftoffH));
        } else if (time_s < 140.0) {
          // Powerful climb through troposphere and stratosphere to space staging altitude (0.85 units)
          const w = (time_s - 14.0) / (140.0 - 14.0);
          const ascentH = 0.428 + (0.85 - 0.428) * Math.pow(w, 0.85);
          const rUpCur = rawPos.clone().normalize();
          vPos = rUpCur.multiplyScalar(6.371 + ascentH);
        } else {
          // Smooth transition from staging altitude into true Keplerian orbital flight path
          const blend = Math.min(1.0, (time_s - 140.0) / 120.0);
          const rUpCur = rawPos.clone().normalize();
          const targetOrbitalPos = rawPos.clone();
          const stagingSpacePos = rUpCur.clone().multiplyScalar(6.371 + 0.85);
          vPos = stagingSpacePos.lerp(targetOrbitalPos, blend);
        }
      }

      // Compute velocity direction
      const deltaMove = vPos.clone().sub(this.lastVehiclePos);
      if (deltaMove.lengthSq() > 1e-7) {
        this.lastVelocityDir.copy(deltaMove).normalize();
      }
      this.lastVehiclePos.copy(vPos);

      // Orthonormal Body Kinematics
      const rUp = vPos.clone().normalize();
      let vDir = this.lastVelocityDir.clone().normalize();
      let hDir = vDir.clone().sub(rUp.clone().multiplyScalar(vDir.dot(rUp)));
      if (hDir.lengthSq() > 1e-4) {
        hDir.normalize();
      } else {
        const northPole = new THREE.Vector3(0, 1, 0);
        hDir = new THREE.Vector3().crossVectors(northPole, rUp).normalize();
      }

      // pitch_deg: 90° = vertical up, 0° = horizontal/prograde along velocity, 40° = reentry belly-flop
      const pitchDeg = (statePoint.pitch_deg !== undefined && statePoint.pitch_deg !== null) ? statePoint.pitch_deg : 0.0;
      const pitchRad = (pitchDeg * Math.PI) / 180.0;

      // Nose direction: blend from horizontal prograde (0°) up to vertical (90°)
      const noseDir = rUp.clone().multiplyScalar(Math.sin(pitchRad))
        .add(hDir.clone().multiplyScalar(Math.cos(pitchRad))).normalize();

      const bellyDir = rUp.clone().negate();
      let xBody = new THREE.Vector3().crossVectors(noseDir, bellyDir).normalize();
      if (xBody.lengthSq() < 1e-4) xBody = new THREE.Vector3().crossVectors(noseDir, rUp).normalize();
      if (xBody.lengthSq() < 1e-4) xBody = new THREE.Vector3().crossVectors(rUp, hDir).normalize();
      if (xBody.lengthSq() < 1e-4) xBody.set(1, 0, 0);
      const zBody = new THREE.Vector3().crossVectors(xBody, noseDir).normalize();

      const rotMatrix = new THREE.Matrix4().makeBasis(xBody, noseDir, zBody);
      this.vehicleMasterGroup.position.copy(vPos);
      this.vehicleMasterGroup.quaternion.setFromRotationMatrix(rotMatrix);

      // High-speed atmospheric slipstream & supersonic shock dynamics (T=15s to 140s)
      if (this.slipstreamPoints) {
        if (time_s >= 15.0 && time_s < 140.0 && statePoint.mach) {
          const m = statePoint.mach || 1.0;
          this.slipstreamPoints.material.opacity = Math.min(0.75, (m / 3.0) * 0.7);
          const posAttr = this.slipstreamPoints.geometry.attributes.position;
          for (let p = 1; p < posAttr.array.length; p += 3) {
            posAttr.array[p] -= 0.035 * Math.min(4.0, m);
            if (posAttr.array[p] < -0.25) posAttr.array[p] = 0.25;
          }
          posAttr.needsUpdate = true;
        } else {
          this.slipstreamPoints.material.opacity = 0.0;
        }
      }

      // Supersonic condensation shock cone (Prandtl-Glauert near Max-Q)
      if (this.supersonicCone) {
        const m = statePoint.mach || 0.0;
        if (m >= 0.85 && m <= 1.45 && time_s < 90.0) {
          const coneIntensity = 1.0 - Math.abs(m - 1.15) / 0.30;
          this.supersonicCone.material.opacity = Math.max(0.0, coneIntensity * 0.65);
        } else {
          this.supersonicCone.material.opacity = 0.0;
        }
      }

      // 3. Staging Separation & Independent Booster Multi-Body Dynamics
      if (boosterState && !boosterState.isAttached && !activeProfile.is_synthetic) {
        this.isStaged = true;
        // Upper stage center of thrust resets to origin once separated from booster
        this.starshipUpperGroup.position.y = 0.0;

        // Detach booster to top-level scene if not already detached
        if (this.boosterGroup.parent === this.vehicleMasterGroup) {
          this.vehicleMasterGroup.remove(this.boosterGroup);
          this.scene.add(this.boosterGroup);
        }

        let bRawPos = new THREE.Vector3(
          boosterState.scene_pos[0],
          boosterState.scene_pos[1],
          boosterState.scene_pos[2]
        );
        let bPos = bRawPos.clone();
        if (time_s < 422.0) {
          const uB = Math.max(0.0, Math.min(1.0, (time_s - 140.0) / (422.0 - 140.0)));
          const bAlt = 0.85 * Math.pow(1.0 - uB, 1.4);
          const bUpCur = bRawPos.clone().normalize();
          bPos = bUpCur.multiplyScalar(6.371 + bAlt);
        } else {
          // Settled on Gulf of Mexico water surface
          const bUpCur = bRawPos.clone().normalize();
          bPos = bUpCur.multiplyScalar(6.371 + 0.002);
        }

        const deltaB = bPos.clone().sub(this.lastBoosterPos);
        if (deltaB.lengthSq() > 1e-7) {
          this.lastBoosterVelocityDir.copy(deltaB).normalize();
        }
        this.lastBoosterPos.copy(bPos);
        this.boosterGroup.position.copy(bPos);

        // Booster attitude: point engines retrograde for boostback/landing burn, or tail down at splashdown
        const bUp = bPos.clone().normalize();
        const bPitchDeg = boosterState.altitude_km < 10.0 ? 90.0 : (boosterState.thrust_mn > 0 ? 30.0 : 60.0);
        const bPitchRad = (bPitchDeg * Math.PI) / 180.0;
        const bNoseDir = bUp.clone().multiplyScalar(Math.sin(bPitchRad))
          .add(hDir.clone().multiplyScalar(Math.cos(bPitchRad))).normalize();
        let bX = new THREE.Vector3().crossVectors(bNoseDir, bUp).normalize();
        if (bX.lengthSq() < 1e-4) bX = new THREE.Vector3().crossVectors(bUp, hDir).normalize();
        if (bX.lengthSq() < 1e-4) bX.set(1, 0, 0);
        const bZ = new THREE.Vector3().crossVectors(bX, bNoseDir).normalize();
        this.boosterGroup.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(bX, bNoseDir, bZ));

        // Booster plume during boostback (T=148-218s) or landing burn (T=398-422s)
        const isBoosterBurning = (time_s >= 148.0 && time_s <= 218.0) || (time_s >= 398.0 && time_s <= 422.0) || (boosterState.thrust_mn > 0);
        if (isBoosterBurning) {
          this.boosterPlume.material.opacity = Math.min(0.95, Math.max(0.65, (boosterState.thrust_mn || 15.0) / 25.0));
        } else {
          this.boosterPlume.material.opacity = 0.0;
        }
      } else {
        this.isStaged = false;
        // When mated atop Super Heavy, Starship sits at boosterLen height (0.18 units)
        this.starshipUpperGroup.position.y = 0.18;

        // Re-attach booster to vehicle stack if currently in scene root
        if (this.boosterGroup.parent !== this.vehicleMasterGroup) {
          this.scene.remove(this.boosterGroup);
          this.vehicleMasterGroup.add(this.boosterGroup);
          this.boosterGroup.position.set(0, 0, 0);
          this.boosterGroup.rotation.set(0, 0, 0);
        }
      }

      // 4. Engine Plumes Dynamics
      const thrustMN = statePoint.thrust_mn || 0;
      const isLandingBurn = (time_s >= 11335.0 && time_s < 11364.0) || (statePoint.phase === "LANDING_BURN");
      const isDeorbitBurn = (time_s >= 9900.0 && time_s < 9960.0);
      const isUpperBurn = (time_s >= 140.0 && time_s < 525.0) || isDeorbitBurn;

      if (isLandingBurn) {
        // Multi-layered landing burn flame (User Image 6)
        this.boosterPlume.material.opacity = 0.0;
        this.enginePlume.material.opacity = 0.0;

        const flicker = 1.0 + Math.sin(time_s * 45.0) * 0.08;
        this.landingCorePlume.material.opacity = 0.95;
        this.landingMidPlume.material.opacity = 0.88;
        this.landingHaloPlume.material.opacity = 0.65;
        this.landingMidPlume.scale.set(flicker, 1.0 + Math.cos(time_s * 30.0) * 0.12, flicker);
        this.landingHaloPlume.scale.set(flicker * 1.1, 1.0 + Math.sin(time_s * 35.0) * 0.15, flicker * 1.1);

        // Flap aerodynamic vapor streamers
        this.streamerL.material.opacity = 0.75;
        this.streamerR.material.opacity = 0.75;
      } else {
        this.landingCorePlume.material.opacity = 0.0;
        this.landingMidPlume.material.opacity = 0.0;
        this.landingHaloPlume.material.opacity = 0.0;
        this.streamerL.material.opacity = 0.0;
        this.streamerR.material.opacity = 0.0;

        if (thrustMN > 0) {
          if (!this.isStaged && time_s < 140.0) {
            this.boosterPlume.material.opacity = Math.min(0.95, Math.max(0.65, thrustMN / 70.0));
            // Atmospheric plume radial expansion with decreasing ambient density
            const radialExp = 1.0 + Math.min(1.8, (statePoint.altitude_km || 0.0) / 40.0);
            this.boosterPlume.scale.set(radialExp, 1.0, radialExp);
            this.enginePlume.material.opacity = 0.0;
          } else if (isUpperBurn) {
            this.boosterPlume.material.opacity = 0.0;
            this.enginePlume.material.opacity = Math.min(0.95, Math.max(0.65, thrustMN / 12.0));
          } else {
            this.boosterPlume.material.opacity = 0.0;
            this.enginePlume.material.opacity = 0.0;
          }
        } else {
          if (!this.isStaged) {
            this.boosterPlume.material.opacity = 0.0;
          }
          this.enginePlume.material.opacity = 0.0;
        }
      }

      // 5. Aerothermal Reentry Plasma Glow
      const heatFlux = statePoint.heat_flux_mw_m2 || 0;
      if (heatFlux > 0.05) {
        this.plasmaGlow.material.opacity = Math.min(0.85, heatFlux / 0.8);
      } else {
        this.plasmaGlow.material.opacity = 0.0;
      }

      // 6. Starlink Satellites Deployment Progression (T+1320s to T+1680s)
      let deployedCount = 0;
      if (!activeProfile.is_synthetic) {
        if (time_s >= 1200.0 && time_s < 1800.0) {
          this.dispenserDoor.rotation.x = Math.min(1.24, (time_s - 1200.0) * 0.04);
        } else if (time_s >= 1800.0) {
          this.dispenserDoor.rotation.x = Math.max(0.0, 1.24 - (time_s - 1800.0) * 0.04);
        } else {
          this.dispenserDoor.rotation.x = 0.0;
        }

        const rOrbit = 6.646; // Earth R=6.371 + 275 km LEO
        const orbitInc = (26.3 * Math.PI) / 180.0;
        const omegaOrb = (Math.PI * 2) / 5400.0;

        this.starlinkSatellites.forEach((sat, i) => {
          if (time_s >= sat.deployTime_s) {
            sat.group.visible = true;
            deployedCount++;
            const dt = time_s - sat.deployTime_s;

            if (dt < 40.0) {
              // Ejection phase: spring delta-v through PEZ door mouth
              const outDist = 0.024 + dt * 0.0035;
              const outVec = zBody.clone().multiplyScalar(outDist);
              const rearVec = noseDir.clone().multiplyScalar(-0.008 - dt * 0.0028);
              const latVec = xBody.clone().multiplyScalar(sat.lateralOffset);
              const egressPos = vPos.clone().add(outVec).add(rearVec).add(latVec);
              sat.group.position.copy(egressPos);
              sat.group.quaternion.setFromRotationMatrix(rotMatrix);
            } else {
              // True independent Keplerian circular low Earth orbit
              // Maintains constellation train around Earth permanently
              const deployOrbitAngle = (sat.deployTime_s / 5400.0) * Math.PI * 2;
              const orbitalTheta = deployOrbitAngle + omegaOrb * dt + (i * 0.0038) + (dt * 0.0000012 * i);
              const satX = rOrbit * Math.cos(orbitalTheta);
              const satY = rOrbit * Math.sin(orbitalTheta) * Math.sin(orbitInc);
              const satZ = -rOrbit * Math.sin(orbitalTheta) * Math.cos(orbitInc);

              sat.group.position.set(satX, satY, satZ);

              // Orient Earth-facing phased array to Earth center, solar wing tracking Sun
              const satUp = sat.group.position.clone().normalize();
              const satFwd = new THREE.Vector3(-Math.sin(orbitalTheta), Math.cos(orbitalTheta) * Math.sin(orbitInc), -Math.cos(orbitalTheta) * Math.cos(orbitInc)).normalize();
              const satSide = new THREE.Vector3().crossVectors(satFwd, satUp).normalize();
              sat.group.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(satSide, satUp, satFwd));
            }

            // Unfold high-efficiency sapphire photovoltaic solar array wing
            if (sat.solarGroup) {
              const unfoldFrac = Math.min(1.0, Math.max(0.05, (dt - 1.0) / 8.0));
              sat.solarGroup.scale.set(unfoldFrac, 1.0, 1.0);
            }
          } else {
            sat.group.visible = false;
            if (sat.solarGroup) sat.solarGroup.scale.set(0.01, 1.0, 1.0);
          }
        });
      } else {
        this.dispenserDoor.rotation.x = 0;
        this.starlinkSatellites.forEach(s => {
          s.group.visible = false;
          if (s.solarGroup) s.solarGroup.scale.set(0.01, 1.0, 1.0);
        });
      }

      // Update UI Satellites Badge
      const satVal = document.getElementById("cfr-sat-count");
      if (satVal) satVal.innerText = `${deployedCount} / 26 DEPLOYED`;

      // 7. Update Environment Modules
      this.launchpadScene.update(time_s, isPrelaunch, profileKey, statePoint.altitude_km);

      // Multi-Body Ocean Anchoring:
      // During Booster Return (T=390s to T=445s), anchor ocean directly under the Super Heavy booster in the Gulf of Mexico!
      // During Starship Reentry & Landing (T >= 10500s), anchor ocean directly under Starship in the Northern Pacific!
      const isBoosterPhase = (time_s >= 390.0 && time_s <= 445.0 && profileKey !== "synthetic_engineering_test");
      let oceanTargetPos = this.vehicleMasterGroup.position;
      let oceanAlt = statePoint.altitude_km;
      let isTerminalTouchdown = (time_s >= 11340.0);

      if (isBoosterPhase && boosterState && boosterState.scene_pos) {
        oceanTargetPos = this.boosterGroup ? this.boosterGroup.position : new THREE.Vector3(...boosterState.scene_pos);
        oceanAlt = boosterState.altitude_km;
        isTerminalTouchdown = (time_s >= 415.0);
      }

      this.oceanSplashdown.update(
        time_s,
        oceanAlt,
        isTerminalTouchdown,
        oceanTargetPos,
        profileKey
      );
    }

    // 8. Update UI HUD and Scrubber
    this.updateHUD(time_s, statePoint, isPrelaunch, playState, boosterState, activeProfile);
  }

  updateHUD(time_s, statePoint, isPrelaunch, playState, boosterState, activeProfile) {
    const clockEl = document.getElementById("cfr-clock-display");
    const scrubClock = document.getElementById("cfr-scrub-clock");
    const scrubInput = document.getElementById("cfr-timeline-scrub");

    let timeStr = "";
    if (isPrelaunch) {
      timeStr = `T - 00:00:${Math.ceil(playState.countdownSec).toString().padStart(2, "0")}`;
    } else {
      const totalSec = Math.floor(time_s);
      const h = Math.floor(totalSec / 3600);
      const m = Math.floor((totalSec % 3600) / 60);
      const s = totalSec % 60;
      timeStr = `T + ${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }

    if (clockEl) clockEl.innerText = timeStr;
    if (scrubClock) scrubClock.innerText = timeStr;

    // Timeline Scrubber Sync
    if (scrubInput && !scrubInput.matches(":active")) {
      scrubInput.value = (time_s / (playState.duration_s || 11364.0)) * 1000;
    }

    // Update Telemetry Grid with Multi-Body Awareness (Super Heavy Booster vs Starship Upper Stage)
    const stageEl = document.getElementById("cfr-hud-stage-name");
    const isTrackingBooster = (this.cameraDirector.currentStateId.startsWith("BOOSTER_") || (time_s >= 140.0 && time_s <= 440.0 && (!activeProfile || !activeProfile.is_synthetic)));

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.innerText = val;
    };

    if (isTrackingBooster && boosterState && !boosterState.isAttached) {
      if (stageEl) stageEl.innerText = "STAGE: SUPER HEAVY (BOOSTER 14)";
      setVal("cfr-m-alt", `${(boosterState.altitude_km !== undefined ? boosterState.altitude_km : 0).toFixed(1)} km`);
      const vel = boosterState.velocity_km_s !== undefined ? boosterState.velocity_km_s : 0;
      const mach = boosterState.mach !== undefined ? boosterState.mach : (vel * 1000.0) / 340.0;
      setVal("cfr-m-vel", `${(vel * 3600).toFixed(0)} km/h (M ${mach.toFixed(1)})`);
      setVal("cfr-m-q", `${(boosterState.dynamic_pressure_kpa !== undefined ? boosterState.dynamic_pressure_kpa : 0).toFixed(1)} kPa`);
      setVal("cfr-m-heat", "0.000 MW/m²");
      setVal("cfr-m-g", `${(boosterState.apparent_g !== undefined ? boosterState.apparent_g : 1.0).toFixed(2)} G`);
      setVal("cfr-m-thrust", `${(boosterState.thrust_mn !== undefined ? boosterState.thrust_mn : 0).toFixed(1)} MN`);
      setVal("cfr-m-mass", `${(boosterState.mass_tonnes !== undefined ? boosterState.mass_tonnes : 220).toFixed(0)} t`);
      setVal("cfr-m-pitch", `${boosterState.altitude_km < 10.0 ? "90.0°" : (boosterState.thrust_mn > 0 ? "30.0°" : "60.0°")}`);
    } else if (statePoint) {
      if (stageEl) {
        stageEl.innerText = (time_s < 140.0) ? "STAGE: FULL STACK (B14 + S31)" : "STAGE: STARSHIP (SHIP 31)";
      }
      setVal("cfr-m-alt", `${(statePoint.altitude_km !== undefined ? statePoint.altitude_km : 0).toFixed(1)} km`);
      const vel = statePoint.velocity_km_s !== undefined ? statePoint.velocity_km_s : 0;
      const mach = (vel * 1000.0) / 340.0;
      setVal("cfr-m-vel", `${(vel * 3600).toFixed(0)} km/h (M ${mach.toFixed(1)})`);
      setVal("cfr-m-q", `${(statePoint.dynamic_pressure_kpa !== undefined ? statePoint.dynamic_pressure_kpa : 0).toFixed(1)} kPa`);
      setVal("cfr-m-heat", `${(statePoint.heat_flux_mw_m2 !== undefined ? statePoint.heat_flux_mw_m2 : 0).toFixed(3)} MW/m²`);
      setVal("cfr-m-g", `${(statePoint.apparent_g !== undefined ? statePoint.apparent_g : 0.0).toFixed(2)} G`);
      setVal("cfr-m-thrust", `${(statePoint.thrust_mn !== undefined ? statePoint.thrust_mn : 0).toFixed(1)} MN`);
      setVal("cfr-m-mass", `${(statePoint.mass_tonnes !== undefined ? statePoint.mass_tonnes : 120).toFixed(0)} t`);
      setVal("cfr-m-pitch", `${(statePoint.pitch_deg !== undefined ? statePoint.pitch_deg : 0).toFixed(1)}°`);
    }

    this.updateLowerThird(time_s);
  }

  updateLowerThird(time_s) {
    if (!this.replayController) return;
    const milestones = this.replayController.milestones || [];
    let currentM = milestones[0];
    for (let i = 0; i < milestones.length; i++) {
      if (time_s >= milestones[i].time_s) {
        currentM = milestones[i];
      }
    }

    if (currentM) {
      const titleEl = document.getElementById("cfr-lt-title");
      const descEl = document.getElementById("cfr-lt-desc");
      const chapterEl = document.getElementById("cfr-lt-chapter");
      if (titleEl) titleEl.innerText = currentM.title;
      if (descEl) descEl.innerText = currentM.desc || `Broadcast Milestone: ${currentM.title} under flight dynamics verification.`;
      if (chapterEl) chapterEl.innerText = `CHAPTER: ${currentM.id}`;
    }
  }

  onProfileChange(activeProfile, profileKey) {
    this.isStaged = false;
    this.boosterGroup.position.set(0, 0, 0);
    this.boosterGroup.rotation.z = 0;

    const synthBanner = document.getElementById("cfr-synthetic-banner");
    if (synthBanner) {
      synthBanner.classList.toggle("visible", !!activeProfile.is_synthetic);
    }

    if (activeProfile.is_synthetic) {
      this.cameraDirector.setCameraState("PAD_LOW_ANGLE", true);
    } else {
      this.cameraDirector.setCameraState("PAD_WIDE", true);
    }
  }

  onEventTrigger(eventId, time_s, activeProfile) {
    if (eventId === "MISSION_COMPLETE") {
      const modal = document.getElementById("cfr-mission-complete-modal");
      if (modal) modal.style.display = "flex";
    }
  }

  // Master Three.js Render Loop
  renderLoop(timestamp) {
    const deltaSec = Math.min(0.1, (timestamp - this.lastFrameTime) / 1000.0);
    this.lastFrameTime = timestamp;

    const vehicleWorldPos = this.vehicleMasterGroup ? this.vehicleMasterGroup.position : this.lastVehiclePos;
    const boosterWorldPos = this.boosterGroup ? this.boosterGroup.getWorldPosition(new THREE.Vector3()) : vehicleWorldPos;

    this.cameraDirector.update(deltaSec, {
      vehiclePos: vehicleWorldPos,
      boosterPos: boosterWorldPos,
      velocityDir: this.lastVelocityDir,
      boosterVelocityDir: this.lastBoosterVelocityDir,
      isStaged: this.isStaged,
      padPos: this.launchpadScene.padPos,
      oceanPos: this.oceanSplashdown.oceanPos,
    });

    this.renderer.render(this.scene, this.camera);
    requestAnimationFrame(this.renderLoop);
  }

  bindUI() {
    const playBtn = document.getElementById("cfr-btn-play");
    if (playBtn) {
      playBtn.addEventListener("click", () => {
        this.replayController.togglePlay();
        playBtn.innerText = this.replayController.isPlaying ? "PAUSE" : "PLAY";
      });
    }

    const rstBtn = document.getElementById("cfr-btn-restart");
    if (rstBtn) {
      rstBtn.addEventListener("click", () => {
        this.replayController.restart();
        if (playBtn) playBtn.innerText = "PAUSE";
      });
    }

    const stepBack = document.getElementById("cfr-btn-step-back");
    if (stepBack) {
      stepBack.addEventListener("click", () => this.replayController.step(-5.0));
    }
    const stepFwd = document.getElementById("cfr-btn-step-fwd");
    if (stepFwd) {
      stepFwd.addEventListener("click", () => this.replayController.step(5.0));
    }

    document.querySelectorAll(".cfr-speed-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".cfr-speed-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.replayController.setSpeed(parseFloat(btn.dataset.speed));
      });
    });

    const scrub = document.getElementById("cfr-timeline-scrub");
    if (scrub) {
      scrub.addEventListener("input", (e) => {
        const frac = parseFloat(e.target.value) / 1000.0;
        this.replayController.seekTo(frac * this.replayController.duration_s);
      });
    }

    const camSelect = document.getElementById("cfr-camera-select");
    if (camSelect) {
      camSelect.addEventListener("change", (e) => {
        if (e.target.value === "AUTO") {
          this.cameraDirector.isAutoDirector = true;
          this.cameraDirector.setInteractionMode(false);
          this.cameraDirector.evaluateAutoDirector(this.replayController.currentTime_s, this.replayController.activeProfileKey);
        } else {
          this.cameraDirector.isAutoDirector = false;
          this.cameraDirector.setInteractionMode(false);
          this.cameraDirector.setCameraState(e.target.value, true);
        }
      });
    }

    document.querySelectorAll(".cfr-profile-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".cfr-profile-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.replayController.initProfile(btn.dataset.profile);
      });
    });

    document.querySelectorAll(".cfr-chapter-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        document.querySelectorAll(".cfr-chapter-pill").forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        const seekT = parseFloat(pill.dataset.seek || "0");
        this.replayController.seekTo(seekT);
        if (pill.dataset.camera) {
          this.cameraDirector.setInteractionMode(false);
          this.cameraDirector.setCameraState(pill.dataset.camera, true);
        }
      });
    });

    const modalClose = document.getElementById("cfr-modal-close");
    if (modalClose) {
      modalClose.addEventListener("click", () => {
        const modal = document.getElementById("cfr-mission-complete-modal");
        if (modal) modal.style.display = "none";
      });
    }

    // Interactive 3D Camera Mode Toggle (Auto Broadcast vs Free 3D Touch/Mouse Navigation)
    const camModeBtn = document.getElementById("cfr-btn-camera-mode");
    if (camModeBtn) {
      camModeBtn.addEventListener("click", () => {
        this.cameraDirector.toggleInteractionMode();
      });
    }

    // Cinema Clean View Mode (Hide all UI overlays for pure 3D space simulation)
    const cinemaBtn = document.getElementById("cfr-btn-cinema-mode");
    const showUiBtn = document.getElementById("cfr-btn-show-ui");
    const toggleCinema = () => {
      document.body.classList.toggle("cfr-cinema-clean");
      const isClean = document.body.classList.contains("cfr-cinema-clean");
      if (showUiBtn) showUiBtn.style.display = isClean ? "flex" : "none";
    };
    if (cinemaBtn) cinemaBtn.addEventListener("click", toggleCinema);
    if (showUiBtn) showUiBtn.addEventListener("click", toggleCinema);

    // Fullscreen Toggle Button (User Request 4)
    const fsBtn = document.getElementById("cfr-btn-fullscreen");
    if (fsBtn) {
      fsBtn.addEventListener("click", () => {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(err => {
            console.warn("Fullscreen error:", err);
          });
          fsBtn.innerHTML = "<span>⛶</span> EXIT FULLSCREEN";
        } else {
          if (document.exitFullscreen) document.exitFullscreen();
          fsBtn.innerHTML = "<span>⛶</span> FULLSCREEN";
        }
      });
      document.addEventListener("fullscreenchange", () => {
        if (!document.fullscreenElement) {
          fsBtn.innerHTML = "<span>⛶</span> FULLSCREEN";
        } else {
          fsBtn.innerHTML = "<span>⛶</span> EXIT FULLSCREEN";
        }
      });
    }

    // Keyboard Shortcuts (Space: Play/Pause, Esc: Exit Cinema Mode / Reset Camera)
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (document.body.classList.contains("cfr-cinema-clean")) {
          toggleCinema();
        } else if (this.cameraDirector.isInteractiveMode) {
          this.cameraDirector.setInteractionMode(false);
        }
      } else if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT") {
        e.preventDefault();
        this.replayController.togglePlay();
        if (playBtn) playBtn.innerText = this.replayController.isPlaying ? "PAUSE" : "PLAY";
      }
    });
  }

  bindWindowResize() {
    window.addEventListener("resize", () => {
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.camera.aspect = this.width / this.height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.width, this.height, false);
    });
  }
}

window.CfrCinematicApp = CfrCinematicApp;
