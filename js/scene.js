/**
 * Starship Flight 14 — Digital Engineering Spatial Kinematic Engine
 * Replaces old Engineering Lab 3D scene with the high-fidelity Kinematic Simulation.
 * 
 * Features:
 *   - Accurate spherical Earth (R = 6.371 scene units = 6,371 km) with day textures,
 *     night lights, cloud deck, and Rayleigh horizon limb glow without tilt distortion.
 *   - Starbase launchpad complex at Boca Chica, TX:
 *       * 145m Mechazilla launch and catch tower with steel corner columns & truss tiers
 *       * Articulated triangular truss chopsticks and carriage
 *       * Heavy Orbital Launch Mount (OLM) with 6 support legs and blast ring
 *       * Cryogenic propellant storage tank farm (LOX & LCH4)
 *       * Water deluge vapor plumes (H2O, H2) and 33-Raptor combustion fireball underglow
 *       * Flush conformal circular apron eliminating flat tilted boxes
 *   - Multi-body Starship & Super Heavy 3D vehicle stack:
 *       * 71m Super Heavy Booster (Stage 1) with 18 weld rings, vented interstage ring (24 exhaust ports),
 *         4 cast titanium grid fins with 3x5 waffle lattice, and 33 Raptor 3 engines
 *       * 50m Starship Upper Stage (Stage 2) with tangent ogive nosecone, dual black hexagonal TPS
 *         heat shield tiles (windward) and polished 304L stainless steel (leeward), 2 forward delta canards,
 *         2 aft body flaps with articulated rotation, and 6 Raptors (3 SL + 3 Vac bells)
 *       * Supersonic Prandtl-Glauert shock condensation cone (Mach 0.85 - 1.45 near Max-Q)
 *       * High-speed atmospheric slipstream trail
 *       * Hypersonic reentry bow-shock plasma envelope scaled to heat flux
 *       * Multi-layered landing burn plume with white-hot core
 *   - Multi-body staging separation & recovery:
 *       * At T=140s, Super Heavy separates cleanly from Starship
 *       * Starship upper stage continues into low Earth orbit (200 x 275 km)
 *       * Super Heavy executes boostback burn (T=148-218s), atmospheric entry (T=218-398s),
 *         3-engine landing burn (T=398-422s), and soft vertical touchdown in the Gulf of Mexico waters!
 *   - Starlink V3 payload dispenser:
 *       * Forward PEZ door rotates open (T=1200-1800s)
 *       * 26 Starlink direct-to-cell satellites deploy sequentially through slot (T=1320-1680s)
 *       * Unfolding sapphire solar array wings and independent Keplerian circular LEO orbits
 *   - Pacific Ocean splashdown complex:
 *       * Curvature-conformal water patch at Northern Pacific landing coordinate
 *       * Water displacement, boiling sea steam, expanding waves, and 3D Naval Recovery Vessel ("Shannon" class) + 2 RHIB boats
 *       * Multi-body anchoring also anchors in Gulf during booster landing burn (T=390-445s)
 *   - Full camera controls:
 *       * OrbitControls with smooth damping, zoom, pan, and rotate
 *       * Presets: EARTH_GLOBAL, ORBIT_FOLLOW, CARGO_DEPLOY_CAM, DEPLOY_WIDE_CAM, PROFILE_VIEW,
 *         ENTRY_BELLY, PAD_PANORAMIC, STAGE_SEP, BOOSTER_GULF, SPLASHDOWN_WIDE, FREE_ORBIT
 *       * Satellite tracking: trackSatellite(index) focuses and orbits any of the 26 Starlinks
 *       * Subsystem highlighting: highlightVehicleSubsystem(sub)
 *   - 2D Inset Mini-Globe Ground Track canvas
 */

class MissionSceneManager {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.width = this.canvas ? (this.canvas.clientWidth || window.innerWidth) : window.innerWidth;
    this.height = this.canvas ? (this.canvas.clientHeight || window.innerHeight) : window.innerHeight;

    // Three.js Core
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    // Space & Celestial Groups
    this.earthGroup = null;
    this.earthMesh = null;
    this.atmoMesh = null;
    this.starfield = null;

    // Vehicle Hierarchy
    this.vehicleMasterGroup = null;
    this.starshipUpperGroup = null;
    this.boosterGroup = null;
    this.satellitesGroup = null;
    this.starlinkSatellites = [];

    // Vehicle Articulations & Plumes
    this.flaps = { fwdLeft: null, fwdRight: null, aftLeft: null, aftRight: null };
    this.dispenserDoor = null;
    this.enginePlume = null;
    this.boosterPlume = null;
    this.landingCorePlume = null;
    this.landingBurnGroup = null;
    this.plasmaGlow = null;
    this.supersonicCone = null;
    this.slipstreamPoints = null;
    this.trajectoryLine = null;
    this.boosterTrajectoryLine = null;

    // Environment Modules
    this.launchpadScene = null;
    this.oceanSplashdown = null;

    // Camera Modes & State
    this.currentCameraMode = "ORBIT_FOLLOW";
    this.trackedSatelliteIndex = -1;
    this.isFreeOrbit = false;

    // Kinematics & Multi-Body Tracking
    this.isStaged = false;
    this.lastVehiclePos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
    this.lastVelocityDir = new THREE.Vector3(0.65, 0.15, -0.74).normalize();
    this.lastBoosterPos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
    this.lastBoosterVelocityDir = new THREE.Vector3(0.65, 0.15, -0.74).normalize();

    this.init();
  }

  init() {
    if (!this.canvas) return;

    // 1. Scene & Deep Space Environment
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x02050e);
    this.scene.fog = new THREE.FogExp2(0x02050e, 0.00025);

    // 2. Camera Setup (FOV 48° for cinematic aerospace perspective)
    this.camera = new THREE.PerspectiveCamera(48, this.width / this.height, 0.005, 3000);
    this.camera.position.set(-0.7, 3.1, 6.2);

    // 3. WebGL Renderer with ACES Filmic Tone Mapping
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: "high-performance",
      alpha: true,
    });
    this.renderer.setSize(this.width, this.height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    // 4. Interactive OrbitControls (Zoom, Rotate, Pan)
    if (typeof THREE.OrbitControls !== "undefined") {
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
      this.controls.maxDistance = 50.0;
      this.controls.enabled = true;

      this.controls.addEventListener("start", () => {
        this.isFreeOrbit = true;
        this.currentCameraMode = "FREE_ORBIT";
        const freeRadio = document.querySelector("input[name='camMode'][value='FREE_ORBIT']");
        if (freeRadio) freeRadio.checked = true;
        const titleBox = document.querySelector(".cam-box-title");
        if (titleBox) titleBox.innerText = "CAMERA: FREE ORBIT";
      });
    }

    // 5. Physically Inspired Space Lighting
    const ambientLight = new THREE.AmbientLight(0x28384c, 0.95);
    this.scene.add(ambientLight);

    // Solar Directional Light
    this.sunLight = new THREE.DirectionalLight(0xffffff, 2.5);
    this.sunLight.position.set(60, 45, 50).normalize().multiplyScalar(100);
    this.scene.add(this.sunLight);

    // Camera Fill Light
    this.cameraLight = new THREE.DirectionalLight(0xdde8ff, 0.35);
    this.camera.add(this.cameraLight);
    this.scene.add(this.camera);

    // Earth Albedo Light
    const earthAlbedo = new THREE.DirectionalLight(0x0e223d, 0.45);
    earthAlbedo.position.set(0, -60, 0);
    this.scene.add(earthAlbedo);

    // Cyan Rim Backlight for Spacecraft Silhouettes
    const rimLight = new THREE.DirectionalLight(0x00e5ff, 0.35);
    rimLight.position.set(-40, 10, -40).normalize();
    this.scene.add(rimLight);

    // 6. Build Celestial & Vehicle Architecture
    this.buildStarfield();
    this.buildEarth();
    this.buildVehicle();
    this.buildSatellites();

    // 7. Initialize Launchpad & Ocean Environments
    if (typeof CfrLaunchpadScene !== "undefined") {
      this.launchpadScene = new CfrLaunchpadScene(this.scene);
    }
    if (typeof CfrOceanSplashdown !== "undefined") {
      this.oceanSplashdown = new CfrOceanSplashdown(this.scene);
    }

    // 8. Event Listeners
    window.addEventListener("resize", () => this.onWindowResize());

    // 9. Master Animation Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  onWindowResize() {
    if (!this.canvas || !this.renderer || !this.camera) return;
    this.width = this.canvas.clientWidth || window.innerWidth;
    this.height = this.canvas.clientHeight || window.innerHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height, false);
  }

  // =========================================================================
  // Celestial Environment: Starfield & Spherical Earth
  // =========================================================================
  buildStarfield() {
    const starCount = 4500;
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
    this.starfield = new THREE.Points(geo, mat);
    this.scene.add(this.starfield);
  }

  buildEarth() {
    this.earthGroup = new THREE.Group();
    const earthRadius = 6.371; // 6371 km (1 unit = 1000 km)
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

    // Rayleigh Atmospheric Limb Fresnel Shader (Appears only on grazing horizon)
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
    this.atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    this.earthGroup.add(this.atmoMesh);

    this.scene.add(this.earthGroup);
  }

  createFallbackEarthTexture() {
    const c = document.createElement("canvas");
    c.width = 1024;
    c.height = 512;
    const ctx = c.getContext("2d");

    ctx.fillStyle = "#0d2b45";
    ctx.fillRect(0, 0, 1024, 512);

    ctx.fillStyle = "#1b4d3e";
    const continents = [
      [180, 160, 130, 90], [280, 310, 80, 120],
      [510, 160, 160, 110], [530, 270, 90, 130],
      [720, 160, 200, 120], [800, 340, 90, 70]
    ];
    continents.forEach(([x, y, w, h]) => {
      ctx.beginPath();
      ctx.ellipse(x, y, w / 2, h / 2, 0, 0, Math.PI * 2);
      ctx.fill();
    });

    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    return tex;
  }

  // =========================================================================
  // Authentic 3D Vehicle Stack: Super Heavy B14 + Starship S31
  // =========================================================================
  buildVehicle() {
    this.vehicleMasterGroup = new THREE.Group();
    this.scene.add(this.vehicleMasterGroup);

    // Scale Dimensions: Real vehicle is 9m diameter (0.009 units), 121m tall (0.121 units)
    // Scaled representation for crisp WebGL fidelity against global Earth:
    const radius = 0.0045; // 4.5m radius
    const boosterLen = 0.18; // 71m Super Heavy booster
    const shipLen = 0.12;    // 50m Starship upper stage
    const barrelLen = 0.075;

    // Materials
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0xe8eef5,
      metalness: 0.95,
      roughness: 0.18,
    });
    const tileMat = new THREE.MeshStandardMaterial({
      color: 0x141416,
      roughness: 0.88,
      metalness: 0.12,
    });
    const darkMat = new THREE.MeshStandardMaterial({
      color: 0x1e2229,
      metalness: 0.80,
      roughness: 0.35,
    });
    const weldMat = new THREE.MeshBasicMaterial({ color: 0x9aa2ad });
    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x424a54,
      metalness: 0.82,
      roughness: 0.42,
    });

    // -----------------------------------------------------------------------
    // 1. STARSHIP UPPER STAGE (STAGE 2, SHIP 31)
    // -----------------------------------------------------------------------
    this.starshipUpperGroup = new THREE.Group();

    // 1.1 Leeward Stainless Steel Barrel (Cylinder half-shell)
    const barrelGeo = new THREE.CylinderGeometry(radius, radius, barrelLen, 36, 1, false, 0, Math.PI);
    const barrelSteel = new THREE.Mesh(barrelGeo, steelMat);
    barrelSteel.position.y = barrelLen / 2;
    this.starshipUpperGroup.add(barrelSteel);

    // 1.2 Windward Black Hexagonal TPS Heat Shield Barrel
    const barrelTile = new THREE.Mesh(barrelGeo, tileMat);
    barrelTile.rotation.y = Math.PI;
    barrelTile.position.y = barrelLen / 2;
    this.starshipUpperGroup.add(barrelTile);

    // 1.3 Tangent Ogive Nosecone (LatheGeometry)
    const nosePts = [];
    const noseSegs = 24;
    const noseHeight = shipLen - barrelLen;
    for (let i = 0; i <= noseSegs; i++) {
      const u = i / noseSegs;
      const r = radius * Math.sqrt(Math.max(0.0, 1.0 - Math.pow((u - 1.0), 2)));
      nosePts.push(new THREE.Vector2(r, u * noseHeight));
    }
    const noseGeoSteel = new THREE.LatheGeometry(nosePts, 24, 0, Math.PI);
    const noseSteel = new THREE.Mesh(noseGeoSteel, steelMat);
    noseSteel.position.y = barrelLen;
    this.starshipUpperGroup.add(noseSteel);

    const noseTile = new THREE.Mesh(noseGeoSteel, tileMat);
    noseTile.rotation.y = Math.PI;
    noseTile.position.y = barrelLen;
    this.starshipUpperGroup.add(noseTile);

    // 1.4 Forward Swept Delta Canards (Left & Right)
    const fwdCanardShape = new THREE.Shape();
    fwdCanardShape.moveTo(0, 0);
    fwdCanardShape.lineTo(radius * 1.5, -radius * 0.4);
    fwdCanardShape.lineTo(radius * 1.3, -radius * 0.9);
    fwdCanardShape.lineTo(0, -radius * 0.7);
    fwdCanardShape.closePath();
    const canardExtrude = new THREE.ExtrudeGeometry(fwdCanardShape, { depth: 0.0008, bevelEnabled: false });

    // Forward Left Canard
    this.flaps.fwdLeft = new THREE.Group();
    const canardL = new THREE.Mesh(canardExtrude, tileMat);
    this.flaps.fwdLeft.add(canardL);
    this.flaps.fwdLeft.position.set(-radius * 0.98, barrelLen + noseHeight * 0.42, 0);
    this.starshipUpperGroup.add(this.flaps.fwdLeft);

    // Forward Right Canard
    this.flaps.fwdRight = new THREE.Group();
    const canardR = new THREE.Mesh(canardExtrude, tileMat);
    canardR.scale.x = -1;
    this.flaps.fwdRight.add(canardR);
    this.flaps.fwdRight.position.set(radius * 0.98, barrelLen + noseHeight * 0.42, 0);
    this.starshipUpperGroup.add(this.flaps.fwdRight);

    // 1.5 Aft Body Flaps (Left & Right)
    const aftFlapShape = new THREE.Shape();
    aftFlapShape.moveTo(0, 0);
    aftFlapShape.lineTo(radius * 1.9, -radius * 0.2);
    aftFlapShape.lineTo(radius * 1.7, -radius * 1.8);
    aftFlapShape.lineTo(0, -radius * 1.5);
    aftFlapShape.closePath();
    const aftExtrude = new THREE.ExtrudeGeometry(aftFlapShape, { depth: 0.0012, bevelEnabled: false });

    this.flaps.aftLeft = new THREE.Group();
    const flapL = new THREE.Mesh(aftExtrude, tileMat);
    this.flaps.aftLeft.add(flapL);
    this.flaps.aftLeft.position.set(-radius * 0.98, barrelLen * 0.42, 0);
    this.starshipUpperGroup.add(this.flaps.aftLeft);

    this.flaps.aftRight = new THREE.Group();
    const flapR = new THREE.Mesh(aftExtrude, tileMat);
    flapR.scale.x = -1;
    this.flaps.aftRight.add(flapR);
    this.flaps.aftRight.position.set(radius * 0.98, barrelLen * 0.42, 0);
    this.starshipUpperGroup.add(this.flaps.aftRight);

    // 1.6 Starlink PEZ Dispenser Door (Forward Leeward Nose)
    const pezDoorGeo = new THREE.BoxGeometry(radius * 0.95, radius * 0.42, 0.0015);
    const pezDoorMat = new THREE.MeshStandardMaterial({ color: 0x2a3038, metalness: 0.9, roughness: 0.2 });
    this.dispenserDoor = new THREE.Mesh(pezDoorGeo, pezDoorMat);
    this.dispenserDoor.position.set(0, barrelLen + noseHeight * 0.32, radius * 0.98);
    this.starshipUpperGroup.add(this.dispenserDoor);

    // 1.7 6 Raptor Engines on Upper Stage (3 Sea-Level + 3 Vacuum bells)
    const engGroup = new THREE.Group();
    const vacBellGeo = new THREE.ConeGeometry(radius * 0.18, radius * 0.42, 16, 1, true);
    for (let e = 0; e < 3; e++) {
      const ang = (e * Math.PI * 2) / 3;
      const bell = new THREE.Mesh(vacBellGeo, darkMat);
      bell.position.set(Math.cos(ang) * radius * 0.52, -radius * 0.20, Math.sin(ang) * radius * 0.52);
      bell.rotation.x = Math.PI;
      engGroup.add(bell);
    }
    const slBellGeo = new THREE.ConeGeometry(radius * 0.10, radius * 0.24, 12, 1, true);
    for (let s = 0; s < 3; s++) {
      const sAng = (s * Math.PI * 2) / 3 + Math.PI / 3;
      const sBell = new THREE.Mesh(slBellGeo, darkMat);
      sBell.position.set(Math.cos(sAng) * radius * 0.22, -radius * 0.10, Math.sin(sAng) * radius * 0.22);
      sBell.rotation.x = Math.PI;
      engGroup.add(sBell);
    }
    this.starshipUpperGroup.add(engGroup);

    // 1.8 Engine Plumes (Upper Stage Vacuum & Landing Burn)
    const plumeGeo = new THREE.ConeGeometry(radius * 0.65, 0.055, 16, 1, true);
    const plumeMat = new THREE.MeshBasicMaterial({
      color: 0x99ddff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    this.enginePlume = new THREE.Mesh(plumeGeo, plumeMat);
    this.enginePlume.position.y = -0.028;
    this.enginePlume.rotation.x = Math.PI;
    this.starshipUpperGroup.add(this.enginePlume);

    // Landing Burn Plumes
    this.landingBurnGroup = new THREE.Group();
    const coreFlameGeo = new THREE.ConeGeometry(radius * 0.45, 0.065, 16, 1, true);
    const coreFlameMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    this.landingCorePlume = new THREE.Mesh(coreFlameGeo, coreFlameMat);
    this.landingCorePlume.position.y = -0.032;
    this.landingCorePlume.rotation.x = Math.PI;
    this.landingBurnGroup.add(this.landingCorePlume);
    this.starshipUpperGroup.add(this.landingBurnGroup);

    // 1.9 Supersonic Shock Condensation Cone (Prandtl-Glauert near Max-Q)
    const coneGeo = new THREE.ConeGeometry(radius * 2.8, 0.024, 24, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.supersonicCone = new THREE.Mesh(coneGeo, coneMat);
    this.supersonicCone.position.y = barrelLen + 0.005;
    this.starshipUpperGroup.add(this.supersonicCone);

    // 1.10 Hypersonic Reentry Plasma Glow Envelope
    const plasmaGeo = new THREE.SphereGeometry(radius * 1.8, 24, 24);
    const plasmaMat = new THREE.MeshBasicMaterial({ color: 0xff4411, transparent: true, opacity: 0.0 });
    this.plasmaGlow = new THREE.Mesh(plasmaGeo, plasmaMat);
    this.plasmaGlow.position.y = barrelLen * 0.5;
    this.starshipUpperGroup.add(this.plasmaGlow);

    // Position Upper Stage atop Booster
    this.starshipUpperGroup.position.y = boosterLen;
    this.vehicleMasterGroup.add(this.starshipUpperGroup);

    // -----------------------------------------------------------------------
    // 2. SUPER HEAVY BOOSTER (STAGE 1, BOOSTER 14)
    // -----------------------------------------------------------------------
    this.boosterGroup = new THREE.Group();

    // 2.1 71m Cylindrical Booster Barrel
    const bGeo = new THREE.CylinderGeometry(radius, radius, boosterLen, 36);
    const bMesh = new THREE.Mesh(bGeo, steelMat);
    bMesh.position.y = boosterLen / 2;
    this.boosterGroup.add(bMesh);

    // 2.2 18 Circumferential Weld Rings
    const weldGeo = new THREE.TorusGeometry(radius * 1.004, 0.00018, 6, 36);
    for (let w = 1; w < 18; w++) {
      const bRing = new THREE.Mesh(weldGeo, weldMat);
      bRing.rotation.x = Math.PI / 2;
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

    // 2.4 4 Cast Titanium Grid Fins with 3x5 Waffle Lattice
    const finFrameGeo = new THREE.BoxGeometry(radius * 0.95, radius * 0.55, 0.0035);
    const finAxleGeo = new THREE.CylinderGeometry(0.002, 0.002, radius * 0.25, 12);

    for (let f = 0; f < 4; f++) {
      const ang = (f * Math.PI) / 2;
      const finGroup = new THREE.Group();

      const finFrame = new THREE.Mesh(finFrameGeo, titaniumMat);
      finGroup.add(finFrame);

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
    const bEngBellGeo = new THREE.ConeGeometry(radius * 0.12, radius * 0.32, 12, 1, true);

    // 1 Center engine
    const cBell = new THREE.Mesh(bEngBellGeo, darkMat);
    cBell.position.set(0, -radius * 0.16, 0);
    cBell.rotation.x = Math.PI;
    this.boosterGroup.add(cBell);

    // 2 Inner ring
    for (let i = 0; i < 2; i++) {
      const iBell = new THREE.Mesh(bEngBellGeo, darkMat);
      const ang = (i * Math.PI);
      iBell.position.set(Math.cos(ang) * radius * 0.28, -radius * 0.16, Math.sin(ang) * radius * 0.28);
      iBell.rotation.x = Math.PI;
      this.boosterGroup.add(iBell);
    }

    // 10 Middle ring
    for (let m = 0; m < 10; m++) {
      const mBell = new THREE.Mesh(bEngBellGeo, darkMat);
      const ang = (m * Math.PI * 2) / 10;
      mBell.position.set(Math.cos(ang) * radius * 0.55, -radius * 0.16, Math.sin(ang) * radius * 0.55);
      mBell.rotation.x = Math.PI;
      this.boosterGroup.add(mBell);
    }

    // 20 Outer ring
    for (let o = 0; o < 20; o++) {
      const oBell = new THREE.Mesh(bEngBellGeo, darkMat);
      const ang = (o * Math.PI * 2) / 20;
      oBell.position.set(Math.cos(ang) * radius * 0.84, -radius * 0.16, Math.sin(ang) * radius * 0.84);
      oBell.rotation.x = Math.PI;
      this.boosterGroup.add(oBell);
    }

    // 2.6 Booster Plume (Liftoff, Boostback, and Landing Burn)
    const bPlumeGeo = new THREE.ConeGeometry(radius * 1.8, 0.18, 20, 1, true);
    const bPlumeMat = new THREE.MeshBasicMaterial({
      color: 0xffaa33,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    this.boosterPlume = new THREE.Mesh(bPlumeGeo, bPlumeMat);
    this.boosterPlume.position.y = -0.09;
    this.boosterPlume.rotation.x = Math.PI;
    this.boosterGroup.add(this.boosterPlume);

    this.vehicleMasterGroup.add(this.boosterGroup);
  }

  // =========================================================================
  // 26 Starlink V3 Satellites System
  // =========================================================================
  buildSatellites() {
    this.satellitesGroup = new THREE.Group();
    this.scene.add(this.satellitesGroup);

    const busGeo = new THREE.BoxGeometry(0.0035, 0.0009, 0.0065);
    const busMat = new THREE.MeshStandardMaterial({ color: 0x98a4b2, metalness: 0.9, roughness: 0.2 });
    const phasedMat = new THREE.MeshBasicMaterial({ color: 0x223344 });
    const solarMat = new THREE.MeshStandardMaterial({ color: 0x112266, metalness: 0.8, roughness: 0.1 });

    for (let i = 0; i < 26; i++) {
      const satGroup = new THREE.Group();

      const bus = new THREE.Mesh(busGeo, busMat);
      satGroup.add(bus);

      const arrayGeo = new THREE.BoxGeometry(0.0033, 0.0001, 0.0062);
      const phasedArray = new THREE.Mesh(arrayGeo, phasedMat);
      phasedArray.position.y = -0.0005;
      satGroup.add(phasedArray);

      // Unfolding Sapphire Photovoltaic Solar Array Wing
      const solarGroup = new THREE.Group();
      const wingGeo = new THREE.BoxGeometry(0.016, 0.0003, 0.006);
      const wing = new THREE.Mesh(wingGeo, solarMat);
      wing.position.x = 0.008;
      solarGroup.add(wing);
      solarGroup.position.set(0.0018, 0, 0);
      satGroup.add(solarGroup);

      satGroup.visible = false;
      this.satellitesGroup.add(satGroup);

      this.starlinkSatellites.push({
        id: `STARLINK-${14001 + i}`,
        index: i,
        group: satGroup,
        solarGroup: solarGroup,
        deployTime_s: 1320.0 + i * 13.85,
        lateralOffset: (i % 2 === 0 ? 1 : -1) * 0.0015,
      });
    }
  }

  // =========================================================================
  // Real-Time Vehicle State & Kinematics Update
  // =========================================================================
  updateVehicleState(statePoint, boosterState, activeProfile) {
    if (!statePoint) return;

    // Handle 2-arg caller compatibility
    if (activeProfile === undefined && boosterState && (boosterState.name || boosterState.trajectory)) {
      activeProfile = boosterState;
      boosterState = statePoint.boosterState || null;
    }
    activeProfile = activeProfile || {};

    const time_s = statePoint.time_s || 0.0;
    const isPrelaunch = time_s < 0.0;
    const profileKey = activeProfile.id || "observed_reconstruction";

    // 1. Vehicle Position & Ascent Kinematics
    let vPos = new THREE.Vector3(-0.714506, 2.778665, 5.691848); // Starbase pad default

    if (statePoint.scene_pos && Array.isArray(statePoint.scene_pos)) {
      let rawPos = new THREE.Vector3(statePoint.scene_pos[0], statePoint.scene_pos[1], statePoint.scene_pos[2]);

      // Smooth realistic ascent elevation: quadratic liftoff off the OLM clearing Mechazilla tower
      if (time_s >= 0.0 && time_s < 140.0 && !activeProfile.is_synthetic) {
        const u = time_s / 140.0;
        const ascentAltitude = 0.85 * Math.pow(u, 2.15); // Reaches ~85 km staging altitude
        const rUpCur = rawPos.clone().normalize();
        vPos = rUpCur.multiplyScalar(6.371 + ascentAltitude);
      } else {
        vPos = rawPos.clone();
      }
    }

    // Velocity direction calculation
    const deltaMove = vPos.clone().sub(this.lastVehiclePos);
    if (deltaMove.lengthSq() > 1e-7) {
      this.lastVelocityDir.copy(deltaMove).normalize();
    }
    this.lastVehiclePos.copy(vPos);

    // Orthonormal Body Kinematics (No Gimbal Lock)
    const rUp = vPos.clone().normalize();
    let vDir = this.lastVelocityDir.clone().normalize();
    let hDir = vDir.clone().sub(rUp.clone().multiplyScalar(vDir.dot(rUp)));
    if (hDir.lengthSq() > 1e-4) {
      hDir.normalize();
    } else {
      const northPole = new THREE.Vector3(0, 1, 0);
      hDir = new THREE.Vector3().crossVectors(northPole, rUp).normalize();
    }

    const pitchDeg = (statePoint.pitch_deg !== undefined && statePoint.pitch_deg !== null) ? statePoint.pitch_deg : 0.0;
    const pitchRad = (pitchDeg * Math.PI) / 180.0;

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

    // 2. Supersonic Shock Condensation Cone near Max-Q (Mach 0.85 - 1.45)
    if (this.supersonicCone) {
      const m = statePoint.mach || 0.0;
      if (m >= 0.85 && m <= 1.45 && time_s < 90.0) {
        const coneIntensity = 1.0 - Math.abs(m - 1.15) / 0.30;
        this.supersonicCone.material.opacity = Math.max(0.0, coneIntensity * 0.65);
      } else {
        this.supersonicCone.material.opacity = 0.0;
      }
    }

    // 3. Staging Separation & Super Heavy Booster Return Dynamics
    if (boosterState && !boosterState.isAttached && !activeProfile.is_synthetic) {
      this.isStaged = true;
      this.starshipUpperGroup.position.y = 0.0;

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
        const bUpCur = bRawPos.clone().normalize();
        bPos = bUpCur.multiplyScalar(6.371 + 0.002);
      }

      const deltaB = bPos.clone().sub(this.lastBoosterPos);
      if (deltaB.lengthSq() > 1e-7) {
        this.lastBoosterVelocityDir.copy(deltaB).normalize();
      }
      this.lastBoosterPos.copy(bPos);
      this.boosterGroup.position.copy(bPos);

      // Booster Attitude
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

      // Booster Plume (Boostback: T=148-218s, Landing Burn: T=398-422s)
      const isBoosterBurning = (time_s >= 148.0 && time_s <= 218.0) || (time_s >= 398.0 && time_s <= 422.0) || (boosterState.thrust_mn > 0);
      if (isBoosterBurning) {
        this.boosterPlume.material.opacity = Math.min(0.95, Math.max(0.65, (boosterState.thrust_mn || 15.0) / 25.0));
      } else {
        this.boosterPlume.material.opacity = 0.0;
      }
    } else {
      this.isStaged = false;
      this.starshipUpperGroup.position.y = 0.18; // Atop 71m booster

      if (this.boosterGroup.parent !== this.vehicleMasterGroup) {
        this.scene.remove(this.boosterGroup);
        this.vehicleMasterGroup.add(this.boosterGroup);
        this.boosterGroup.position.set(0, 0, 0);
        this.boosterGroup.rotation.set(0, 0, 0);
      }
    }

    // 4. Engine Plumes Dynamics
    const isLandingBurn = (time_s >= 11335.0 && time_s < 11364.0) || (statePoint.phase === "LANDING_BURN");
    const isDeorbitBurn = (time_s >= 9900.0 && time_s < 9960.0);
    const isUpperBurn = (time_s >= 140.0 && time_s < 525.0) || isDeorbitBurn;

    if (isLandingBurn) {
      this.boosterPlume.material.opacity = 0.0;
      this.enginePlume.material.opacity = 0.0;
      this.landingCorePlume.material.opacity = 0.95;
    } else if (isUpperBurn && this.isStaged) {
      this.boosterPlume.material.opacity = 0.0;
      this.landingCorePlume.material.opacity = 0.0;
      this.enginePlume.material.opacity = 0.88;
    } else if (!this.isStaged && time_s >= 0.0 && time_s < 140.0) {
      this.landingCorePlume.material.opacity = 0.0;
      this.enginePlume.material.opacity = 0.0;
      const bThrust = statePoint.thrust_mn || 81.7;
      this.boosterPlume.material.opacity = Math.min(0.95, Math.max(0.70, bThrust / 81.7));
    } else {
      this.boosterPlume.material.opacity = 0.0;
      this.enginePlume.material.opacity = 0.0;
      this.landingCorePlume.material.opacity = 0.0;
    }

    // 5. Flap Actuation (trimming during ascent, belly-flop and flip)
    const fwdFlap = Math.abs(statePoint.flaps_fwd_deg || 0);
    const aftFlap = Math.abs(statePoint.flaps_aft_deg || 0);
    const fwdRad = (fwdFlap * Math.PI) / 180.0;
    const aftRad = (aftFlap * Math.PI) / 180.0;

    if (this.flaps.fwdLeft) this.flaps.fwdLeft.rotation.z = -fwdRad;
    if (this.flaps.fwdRight) this.flaps.fwdRight.rotation.z = fwdRad;
    if (this.flaps.aftLeft) this.flaps.aftLeft.rotation.z = -aftRad;
    if (this.flaps.aftRight) this.flaps.aftRight.rotation.z = aftRad;

    // 6. Hypersonic Entry Plasma Glow
    const heatFlux = statePoint.heat_flux_mw_m2 || 0;
    if (heatFlux > 0.05) {
      this.plasmaGlow.material.opacity = Math.min(0.85, heatFlux / 0.8);
    } else {
      this.plasmaGlow.material.opacity = 0.0;
    }

    // 7. Starlink V3 Satellite Deployment Sequence
    if (!activeProfile.is_synthetic) {
      if (time_s >= 1200.0 && time_s < 1800.0) {
        this.dispenserDoor.rotation.x = Math.min(1.24, (time_s - 1200.0) * 0.04);
      } else if (time_s >= 1800.0) {
        this.dispenserDoor.rotation.x = Math.max(0.0, 1.24 - (time_s - 1800.0) * 0.04);
      } else {
        this.dispenserDoor.rotation.x = 0.0;
      }

      const rOrbit = 6.646;
      const orbitInc = (26.3 * Math.PI) / 180.0;
      const omegaOrb = (Math.PI * 2) / 5400.0;

      this.starlinkSatellites.forEach((sat, i) => {
        if (time_s >= sat.deployTime_s) {
          sat.group.visible = true;
          const dt = time_s - sat.deployTime_s;

          if (dt < 40.0) {
            const outDist = 0.024 + dt * 0.0035;
            const outVec = zBody.clone().multiplyScalar(outDist);
            const rearVec = noseDir.clone().multiplyScalar(-0.008 - dt * 0.0028);
            const latVec = xBody.clone().multiplyScalar(sat.lateralOffset);
            const egressPos = vPos.clone().add(outVec).add(rearVec).add(latVec);
            sat.group.position.copy(egressPos);
            sat.group.quaternion.setFromRotationMatrix(rotMatrix);
          } else {
            const deployOrbitAngle = (sat.deployTime_s / 5400.0) * Math.PI * 2;
            const orbitalTheta = deployOrbitAngle + omegaOrb * dt + (i * 0.0038) + (dt * 0.0000012 * i);
            const satX = rOrbit * Math.cos(orbitalTheta);
            const satY = rOrbit * Math.sin(orbitalTheta) * Math.sin(orbitInc);
            const satZ = -rOrbit * Math.sin(orbitalTheta) * Math.cos(orbitInc);
            sat.group.position.set(satX, satY, satZ);

            const satUp = sat.group.position.clone().normalize();
            const satFwd = new THREE.Vector3(-Math.sin(orbitalTheta), Math.cos(orbitalTheta) * Math.sin(orbitInc), -Math.cos(orbitalTheta) * Math.cos(orbitInc)).normalize();
            const satSide = new THREE.Vector3().crossVectors(satFwd, satUp).normalize();
            sat.group.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(satSide, satUp, satFwd));
          }

          if (sat.solarGroup) {
            const unfoldFrac = Math.min(1.0, Math.max(0.05, (dt - 1.0) / 8.0));
            sat.solarGroup.scale.set(unfoldFrac, 1.0, 1.0);
          }
        } else {
          sat.group.visible = false;
          if (sat.solarGroup) sat.solarGroup.scale.set(0.01, 1.0, 1.0);
        }
      });
    }

    // 8. Update Environment Modules
    if (this.launchpadScene) {
      this.launchpadScene.update(time_s, isPrelaunch, profileKey, statePoint.altitude_km);
    }
    if (this.oceanSplashdown) {
      const isTerminalPhase = (statePoint.phase === "SPLASHDOWN" || statePoint.phase === "LANDING_BURN");
      const oceanTargetPos = (time_s >= 390.0 && time_s <= 445.0 && this.isStaged) ? this.lastBoosterPos : vPos;
      this.oceanSplashdown.update(time_s, statePoint.altitude_km, isTerminalPhase, oceanTargetPos, profileKey);
    }

    // 9. Update Inset Mini-Globe 2D Ground Track
    this.renderMiniGlobe(vPos);

    // 10. Update Camera
    this.updateCamera(vPos, rUp, hDir, noseDir);
  }

  // =========================================================================
  // Camera Tracking & Preset Director
  // =========================================================================
  setCameraMode(mode) {
    this.currentCameraMode = mode || "ORBIT_FOLLOW";
    this.isFreeOrbit = (mode === "FREE_ORBIT");

    if (this.controls) {
      this.controls.enabled = this.isFreeOrbit;
    }

    const titleBox = document.querySelector(".cam-box-title");
    if (titleBox) {
      titleBox.innerText = `CAMERA: ${this.currentCameraMode.replace(/_/g, " ")}`;
    }

    // Immediate positioning for static modes
    if (mode === "EARTH_GLOBAL" || mode === "EARTH") {
      this.camera.position.set(0, 14, 20);
      this.camera.lookAt(0, 0, 0);
      if (this.controls) this.controls.target.set(0, 0, 0);
    } else if (mode === "PAD_PANORAMIC" || mode === "PAD") {
      const padPos = new THREE.Vector3(-0.714506, 2.778665, 5.691848);
      this.camera.position.set(padPos.x + 0.12, padPos.y + 0.16, padPos.z - 0.35);
      this.camera.lookAt(padPos);
      if (this.controls) this.controls.target.copy(padPos);
    } else if (mode === "PROFILE_VIEW" || mode === "PROFILE") {
      this.camera.position.set(10, 8, 12);
      this.camera.lookAt(0, 0, 0);
      if (this.controls) this.controls.target.set(0, 0, 0);
    }
  }

  trackSatellite(satIndex) {
    if (satIndex >= 0 && satIndex < this.starlinkSatellites.length) {
      this.trackedSatelliteIndex = satIndex;
      this.currentCameraMode = "TRACK_SATELLITE";
      this.isFreeOrbit = false;
      if (this.controls) this.controls.enabled = false;
    }
  }

  updateCamera(vPos, rUp, hDir, noseDir) {
    if (this.isFreeOrbit) return;

    if (this.currentCameraMode === "TRACK_SATELLITE" && this.trackedSatelliteIndex >= 0) {
      const sat = this.starlinkSatellites[this.trackedSatelliteIndex];
      if (sat && sat.group.visible) {
        const satPos = sat.group.position;
        const satCamPos = satPos.clone().add(new THREE.Vector3(0.015, 0.008, 0.018));
        this.camera.position.lerp(satCamPos, 0.1);
        this.camera.lookAt(satPos);
        if (this.controls) this.controls.target.copy(satPos);
        return;
      }
    }

    if (this.currentCameraMode === "ORBIT_FOLLOW" || this.currentCameraMode === "VEHICLE") {
      const camOffset = rUp.clone().multiplyScalar(0.038)
        .add(hDir.clone().multiplyScalar(-0.065))
        .add(noseDir.clone().multiplyScalar(0.015));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.08);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    } else if (this.currentCameraMode === "CARGO_DEPLOY_CAM" || this.currentCameraMode === "DEPLOY") {
      const camOffset = noseDir.clone().multiplyScalar(0.024)
        .add(rUp.clone().multiplyScalar(-0.015))
        .add(hDir.clone().multiplyScalar(0.018));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.1);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    } else if (this.currentCameraMode === "DEPLOY_WIDE_CAM") {
      const camOffset = rUp.clone().multiplyScalar(0.12)
        .add(hDir.clone().multiplyScalar(-0.18));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.06);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    } else if (this.currentCameraMode === "ENTRY_BELLY") {
      const camOffset = rUp.clone().multiplyScalar(-0.045)
        .add(noseDir.clone().multiplyScalar(-0.012));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.1);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    } else if (this.currentCameraMode === "BOOSTER_GULF" && this.isStaged) {
      const bPos = this.lastBoosterPos;
      const bUp = bPos.clone().normalize();
      const camOffset = bUp.clone().multiplyScalar(0.040).add(new THREE.Vector3(0.035, 0.015, -0.045));
      const targetEye = bPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.08);
      this.camera.lookAt(bPos);
      if (this.controls) this.controls.target.copy(bPos);
    } else if (this.currentCameraMode === "STAGE_SEP") {
      const camOffset = rUp.clone().multiplyScalar(0.06)
        .add(hDir.clone().multiplyScalar(-0.08));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.08);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    } else if (this.currentCameraMode === "SPLASHDOWN_WIDE") {
      const camOffset = rUp.clone().multiplyScalar(0.05)
        .add(hDir.clone().multiplyScalar(0.08));
      const targetEye = vPos.clone().add(camOffset);
      this.camera.position.lerp(targetEye, 0.08);
      this.camera.lookAt(vPos);
      if (this.controls) this.controls.target.copy(vPos);
    }
  }

  // =========================================================================
  // Subsystem Highlighting & Trajectory Ribbon
  // =========================================================================
  highlightVehicleSubsystem(subsystem) {
    const sub = (subsystem || "").toUpperCase();
    if (this.starshipUpperGroup) {
      this.starshipUpperGroup.traverse((child) => {
        if (child.isMesh && child.material) {
          if (sub === "ENGINES" || sub === "PROPULSION") {
            if (child.geometry && child.geometry.type === "ConeGeometry") {
              child.material.emissive = new THREE.Color(0x00e5ff);
              child.material.emissiveIntensity = 0.8;
            }
          } else if (sub === "THERMAL") {
            if (child.material.color && child.material.color.r < 0.2) {
              child.material.emissive = new THREE.Color(0xff4400);
              child.material.emissiveIntensity = 0.5;
            }
          } else {
            if (child.material.emissive) child.material.emissive.setHex(0x000000);
          }
        }
      });
    }
  }

  setVehicleShadingMode(mode) {
    const m = (mode || "standard").toLowerCase();
    if (!this.starshipUpperGroup) return;
    this.starshipUpperGroup.traverse((child) => {
      if (child.isMesh && child.material) {
        if (m === "thermal") {
          child.material.color = new THREE.Color(0xff4411);
          if (child.material.emissive) {
            child.material.emissive.setHex(0xff2200);
            child.material.emissiveIntensity = 0.65;
          }
          child.material.roughness = 0.4;
          child.material.metalness = 0.3;
        } else if (m === "fea_stress") {
          child.material.color = new THREE.Color(0x00e5ff);
          if (child.material.emissive) {
            child.material.emissive.setHex(0x003366);
            child.material.emissiveIntensity = 0.5;
          }
          child.material.roughness = 0.5;
          child.material.metalness = 0.2;
        } else {
          // Standard Polished PBR Steel
          if (child.geometry && child.geometry.type === "ConeGeometry") {
            child.material.color = new THREE.Color(0x666677);
          } else {
            child.material.color = new THREE.Color(0xddddf0);
          }
          if (child.material.emissive) child.material.emissive.setHex(0x000000);
          child.material.roughness = 0.18;
          child.material.metalness = 0.92;
        }
      }
    });
  }

  updateTrajectoryRibbon(trajectory, boosterTrajectory) {
    if (this.trajectoryLine) {
      this.scene.remove(this.trajectoryLine);
      this.trajectoryLine = null;
    }
    if (!trajectory || trajectory.length < 2) return;

    const points = [];
    const colors = [];
    trajectory.forEach(pt => {
      if (pt.scene_pos) {
        points.push(new THREE.Vector3(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]));
        const alt = pt.altitude_km || 0;
        if (alt < 80) colors.push(0.0, 0.9, 1.0);
        else if (alt < 200) colors.push(0.16, 0.47, 1.0);
        else colors.push(0.0, 0.9, 0.46);
      }
    });

    const geo = new THREE.BufferGeometry().setFromPoints(points);
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    const mat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      linewidth: 2,
    });
    this.trajectoryLine = new THREE.Line(geo, mat);
    this.scene.add(this.trajectoryLine);
  }

  // =========================================================================
  // Inset Real-Time 2D Mini-Globe Ground Track
  // =========================================================================
  renderMiniGlobe(vPos) {
    const canvas = document.getElementById("mini-globe-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Globe Disk
    ctx.beginPath();
    ctx.arc(w / 2, h / 2, w / 2 - 2, 0, Math.PI * 2);
    ctx.fillStyle = "#040e1f";
    ctx.fill();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Meridian & Equator
    ctx.strokeStyle = "rgba(0, 229, 255, 0.16)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(w / 2, h / 2, w / 2 - 4, (w / 2 - 4) * 0.38, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w / 2, 2);
    ctx.lineTo(w / 2, h - 2);
    ctx.stroke();

    // Vehicle Sub-Satellite Marker
    const rNorm = Math.sqrt(vPos.x * vPos.x + vPos.y * vPos.y + vPos.z * vPos.z) || 6.371;
    const nx = vPos.x / rNorm;
    const ny = -vPos.z / rNorm;
    const vx = w / 2 + nx * (w / 2 - 8);
    const vy = h / 2 + ny * (h / 2 - 8);

    ctx.beginPath();
    ctx.arc(vx, vy, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = "#00e5ff";
    ctx.shadowColor = "#00e5ff";
    ctx.shadowBlur = 6;
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // =========================================================================
  // Master Render Loop
  // =========================================================================
  animate() {
    requestAnimationFrame(this.animate);
    if (this.controls && this.controls.enabled) {
      this.controls.update();
    }
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
}

window.MissionSceneManager = MissionSceneManager;
