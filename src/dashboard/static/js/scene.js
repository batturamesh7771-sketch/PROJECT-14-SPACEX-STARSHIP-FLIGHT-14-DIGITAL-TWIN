/**
 * Phase 10: Three.js WebGL Spatial Visualization Engine
 * Starship Flight 14 Digital Engineering Lab
 * Target Visual Hierarchy: Screenshot B (SpaceX Mission Control)
 *
 * Implements:
 *   - Realistic spherical Earth with high-res textures and thin sunlit atmospheric limb Fresnel glow
 *   - Authentic Starship & Super Heavy 3D geometry:
 *       * Sleek tangent ogive nosecone (LatheGeometry)
 *       * Dual windward (black hexagonal TPS tiles) & leeward (polished 304L stainless steel) hulls
 *       * Articulated forward swept delta canards & aft body flaps
 *       * Super Heavy Booster with 4 grid fins, vented interstage ring, and 33 Raptor engine cluster
 *       * Staging separation animation (full stack during ascent, staging drift, upper stage solo)
 *   - Dynamic Raptor exhaust plume scaled to thrust (MN)
 *   - Hypersonic incandescent bow shock plasma envelope scaled to heat flux (MW/m²)
 *   - Continuous glowing 3D trajectory ribbon with event beacon pins
 *   - Orbital local-frame camera tracking framing curved Earth limb without clipping
 *   - Inset real-time 2D mini-globe ground track canvas
 */

class MissionSceneManager {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.width = this.canvas.clientWidth || window.innerWidth;
    this.height = this.canvas.clientHeight || window.innerHeight;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    // Celestial & Scene Groups
    this.earthGroup = null;
    this.earthMesh = null;
    this.atmoMesh = null;
    this.vehicleMasterGroup = null;
    this.starshipUpperGroup = null;
    this.boosterGroup = null;

    // Movable Flaps
    this.flaps = {
      fwdLeft: null,
      fwdRight: null,
      aftLeft: null,
      aftRight: null,
    };

    // Visual Effects
    this.enginePlume = null;
    this.boosterPlume = null;
    this.reentryPlasmaGlow = null;
    this.trajectoryLine = null;
    this.beaconsGroup = null;

    // Camera & Framing
    this.currentCameraMode = "ORBIT_FOLLOW";
    this.sunDirection = new THREE.Vector3(50, 30, 40).normalize();
    this.lastVehiclePos = new THREE.Vector3(0, 7.0, 0);
    this.lastVelocityDir = new THREE.Vector3(1, 0, 0);

    this.init();
  }

  init() {
    // 1. Scene & Space Environment
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x02050e);
    this.scene.fog = new THREE.FogExp2(0x02050e, 0.0003);

    // 2. Camera Setup (FOV 48 deg for cinematic perspective)
    this.camera = new THREE.PerspectiveCamera(48, this.width / this.height, 0.01, 3000);
    this.camera.position.set(0, 9, 15);

    // 3. WebGL Renderer with High-Fidelity Tone Mapping
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: "high-performance",
      alpha: true,
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    // 4. OrbitControls
    if (typeof THREE.OrbitControls !== "undefined") {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.minDistance = 0.15;
      this.controls.maxDistance = 500;
    }

    // 5. Physically Inspired Space Lighting
    const ambientLight = new THREE.AmbientLight(0x1a2638, 0.65);
    this.scene.add(ambientLight);

    // Primary Solar Directional Light
    const sunLight = new THREE.DirectionalLight(0xffffff, 2.4);
    sunLight.position.copy(this.sunDirection).multiplyScalar(100);
    this.scene.add(sunLight);

    // Soft Earth Albedo Upward Bounce Light
    const earthAlbedo = new THREE.DirectionalLight(0x1c4480, 0.85);
    earthAlbedo.position.set(0, -50, 0);
    this.scene.add(earthAlbedo);

    // Subtle Cyan Rim Backlight for Spacecraft Silhouettes
    const rimLight = new THREE.DirectionalLight(0x00d4ff, 0.4);
    rimLight.position.set(-40, 10, -40).normalize();
    this.scene.add(rimLight);

    // 6. Build Celestial & Vehicle Objects
    this.createStarfield();
    this.createEarth();
    this.createVehicle();
    this.createBeacons();

    // 7. Event Listeners
    window.addEventListener("resize", () => this.onWindowResize());

    // 8. Master Animation Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  // =========================================================================
  // Starfield Generator
  // =========================================================================
  createStarfield() {
    const starCount = 4500;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      const r = 500 + Math.random() * 500;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i] = r * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = r * Math.cos(phi);

      const tint = Math.random();
      if (tint > 0.85) {
        colors[i] = 1.0; colors[i + 1] = 0.85; colors[i + 2] = 0.7; // Warm yellow/orange
      } else if (tint > 0.6) {
        colors[i] = 0.75; colors[i + 1] = 0.9; colors[i + 2] = 1.0; // Blue-white
      } else {
        colors[i] = 0.95; colors[i + 1] = 0.95; colors[i + 2] = 1.0; // Crisp white
      }
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.6,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
    });

    const starPoints = new THREE.Points(geometry, material);
    this.scene.add(starPoints);
  }

  // =========================================================================
  // Earth & Atmospheric Scattering (Solving Blown-out Clipped Slab Defect)
  // =========================================================================
  createProceduralEarthTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext("2d");

    // 1. Deep Oceanic Gradient with Bathymetry
    const oceanGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    oceanGrad.addColorStop(0.0, "#081d3d");
    oceanGrad.addColorStop(0.2, "#04142b");
    oceanGrad.addColorStop(0.5, "#020c1e");
    oceanGrad.addColorStop(0.8, "#04142b");
    oceanGrad.addColorStop(1.0, "#081d3d");
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle equatorial shallow banks (Bahamas, Coral Reefs)
    ctx.fillStyle = "rgba(0, 180, 216, 0.18)";
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.28, canvas.height * 0.44, 45, 18, 0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.82, canvas.height * 0.65, 60, 25, -0.1, 0, Math.PI * 2);
    ctx.fill();

    // 2. Lat/Lon Subtle Reference Grid
    ctx.strokeStyle = "rgba(0, 229, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let lat = 0; lat <= canvas.height; lat += canvas.height / 12) {
      ctx.beginPath();
      ctx.moveTo(0, lat);
      ctx.lineTo(canvas.width, lat);
      ctx.stroke();
    }
    for (let lon = 0; lon <= canvas.width; lon += canvas.width / 24) {
      ctx.beginPath();
      ctx.moveTo(lon, 0);
      ctx.lineTo(lon, canvas.height);
      ctx.stroke();
    }

    // 3. Organic Landmass Helper with Smooth Curves
    const drawLand = (pts, fillColor, strokeColor = "rgba(0, 229, 255, 0.3)") => {
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) {
        const xc = (pts[i - 1][0] + pts[i][0]) / 2;
        const yc = (pts[i - 1][1] + pts[i][1]) / 2;
        ctx.quadraticCurveTo(pts[i - 1][0], pts[i - 1][1], xc, yc);
      }
      ctx.closePath();
      ctx.fillStyle = fillColor;
      ctx.fill();
      if (strokeColor) {
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1.8;
        ctx.stroke();
      }
    };

    // North America (Boca Chica launch site at ~[550, 410])
    const northAmerica = [
      [320, 160], [420, 180], [580, 220], [680, 290], [640, 360], [560, 420],
      [520, 480], [480, 440], [430, 410], [360, 340], [310, 260], [280, 180]
    ];
    drawLand(northAmerica, "#1e3f20");

    // South America
    const southAmerica = [
      [520, 500], [640, 520], [720, 600], [680, 780], [580, 890], [520, 850],
      [490, 720], [480, 580]
    ];
    drawLand(southAmerica, "#15331b");

    // Eurasia
    const eurasia = [
      [960, 160], [1180, 140], [1440, 160], [1720, 220], [1820, 340], [1650, 460],
      [1450, 430], [1280, 480], [1120, 420], [980, 380], [920, 270]
    ];
    drawLand(eurasia, "#224128");

    // Africa
    const africa = [
      [980, 410], [1180, 430], [1280, 530], [1220, 720], [1120, 820], [1020, 780],
      [940, 620], [920, 490]
    ];
    drawLand(africa, "#3b4823");

    // Australia
    const australia = [
      [1520, 640], [1680, 620], [1750, 720], [1680, 820], [1520, 800], [1460, 710]
    ];
    drawLand(australia, "#4d4221");

    // 4. White Polar Ice Caps
    ctx.fillStyle = "rgba(235, 245, 255, 0.92)";
    // North pole
    ctx.beginPath();
    ctx.ellipse(canvas.width / 2, 25, canvas.width * 0.48, 55, 0, 0, Math.PI * 2);
    ctx.fill();
    // South pole
    ctx.beginPath();
    ctx.ellipse(canvas.width / 2, canvas.height - 20, canvas.width * 0.52, 65, 0, 0, Math.PI * 2);
    ctx.fill();

    // 5. Realistic Atmospheric Swirling Clouds (Semi-Transparent White Ribbons)
    ctx.fillStyle = "rgba(255, 255, 255, 0.62)";
    for (let c = 0; c < 8; c++) {
      const cx = (c / 8) * canvas.width + 100;
      const cy = 200 + Math.sin(c * 1.2) * 120;
      ctx.beginPath();
      ctx.ellipse(cx, cy, 140, 45, 0.3 * Math.sin(c), 0, Math.PI * 2);
      ctx.fill();

      // Secondary cloud wisps
      ctx.beginPath();
      ctx.ellipse(cx + 60, cy + 30, 90, 28, -0.2 * Math.cos(c), 0, Math.PI * 2);
      ctx.fill();
    }

    // Mid-latitude cloud bands
    ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
    for (let y = 160; y <= 860; y += 180) {
      ctx.beginPath();
      ctx.ellipse(canvas.width / 2, y, canvas.width * 0.5, 30, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }

  createEarth() {
    this.earthGroup = new THREE.Group();

    // Scale factor: 1 Three.js unit = 1,000 km.
    // Earth equatorial radius = 6,378.137 km -> 6.378137 units.
    const earthRadius = 6.378137;
    const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);

    let earthTex = this.createProceduralEarthTexture();
    const loader = new THREE.TextureLoader();

    // Load High-Resolution Earth Maps
    loader.load(
      "assets/textures/globeprev-clouds-on-DOpaHC5m-r2.jpg",
      (tex) => {
        if (this.earthMesh) {
          this.earthMesh.material.map = tex;
          this.earthMesh.material.needsUpdate = true;
        }
      },
      undefined,
      () => { /* silent procedural fallback */ }
    );

    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTex,
      roughness: 0.65,
      metalness: 0.15,
      emissive: new THREE.Color(0x020818),
      emissiveIntensity: 0.35,
    });

    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthGroup.add(this.earthMesh);

    // Realistic Thin Atmospheric Limb Glow (Outer envelope: ~76 km above surface)
    // Uses FrontSide Fresnel falloff weighted by the solar vector so it only glows on the sunlit limb!
    const atmoRadius = earthRadius * 1.012;
    const atmoGeo = new THREE.SphereGeometry(atmoRadius, 64, 64);

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
        uniform vec3 uSunDirection;
        void main() {
          vec3 viewDir = normalize(cameraPosition - vWorldPosition);
          float rim = 1.0 - max(dot(viewDir, vNormal), 0.0);
          rim = pow(rim, 3.8);

          // Sunlight incidence factor (illuminates daytime limb, dark on night side)
          float sunDot = max(dot(normalize(vWorldPosition), uSunDirection), 0.0);
          float sunFactor = sunDot * 0.85 + 0.15;

          vec3 atmoColor = vec3(0.05, 0.72, 1.0);
          float alpha = rim * sunFactor * 0.85;

          gl_FragColor = vec4(atmoColor, alpha);
        }
      `,
      uniforms: {
        uSunDirection: { value: this.sunDirection },
      },
      blending: THREE.AdditiveBlending,
      side: THREE.FrontSide,
      transparent: true,
      depthWrite: false,
    });

    this.atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    this.earthGroup.add(this.atmoMesh);

    this.scene.add(this.earthGroup);
  }

  // =========================================================================
  // Authentic Starship & Super Heavy 3D Vehicle Geometry
  // =========================================================================
  createOgiveNosecone(radius, length, segments = 32) {
    // Generates a tangent ogive curve: r(y) = sqrt(rho^2 - (L - y)^2) + R - rho
    const rho = (radius * radius + length * length) / (2.0 * radius);
    const points = [];
    const steps = 24;

    for (let i = 0; i <= steps; i++) {
      const y = (i / steps) * length;
      const term = rho * rho - Math.pow(length - y, 2);
      const r = Math.max(0.0, Math.sqrt(Math.max(0, term)) + radius - rho);
      points.push(new THREE.Vector2(r, y));
    }

    return new THREE.LatheGeometry(points, segments);
  }

  createVehicle() {
    this.vehicleMasterGroup = new THREE.Group();

    // Baseline scale factor: Starship is 50m long, 9m diameter.
    // In scene units: 1 unit = 1000 km = 1,000,000m.
    // For crisp WebGL visibility across orbital ranges, we use a vehicle display scale:
    const vScale = 0.20;
    const sRadius = 0.045 * vScale * 10; // 0.09 units

    // Materials
    // 1. Brushed 304L Stainless Steel (Leeward hull)
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0xdde6ed,
      metalness: 0.94,
      roughness: 0.20,
    });

    // 2. Black Hexagonal TPS Tiles (Windward belly heat shield)
    const tileMat = new THREE.MeshStandardMaterial({
      color: 0x121418,
      metalness: 0.08,
      roughness: 0.88,
    });

    // 3. Dark Ceramic / Carbon Matrix (Engine bells & interstage)
    const darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x22262c,
      metalness: 0.85,
      roughness: 0.35,
    });

    // =======================================================================
    // PART A: STARSHIP UPPER STAGE (50m length)
    // =======================================================================
    this.starshipUpperGroup = new THREE.Group();

    const barrelLength = 0.32 * vScale * 10;
    const noseLength = 0.22 * vScale * 10;

    // A1. Main Cylindrical Barrel (Leeward 180 deg)
    const barrelGeo = new THREE.CylinderGeometry(
      sRadius, sRadius, barrelLength, 32, 1, false, Math.PI / 2, Math.PI
    );
    const barrelMesh = new THREE.Mesh(barrelGeo, steelMat);
    barrelMesh.position.y = barrelLength / 2;
    this.starshipUpperGroup.add(barrelMesh);

    // A2. Windward Black TPS Belly Barrel (Windward 180 deg)
    const bellyGeo = new THREE.CylinderGeometry(
      sRadius * 1.004, sRadius * 1.004, barrelLength, 32, 1, false, -Math.PI / 2, Math.PI
    );
    const bellyMesh = new THREE.Mesh(bellyGeo, tileMat);
    bellyMesh.position.y = barrelLength / 2;
    this.starshipUpperGroup.add(bellyMesh);

    // A3. Sleek Ogive Nosecone
    const ogiveGeo = this.createOgiveNosecone(sRadius, noseLength, 32);
    const noseMesh = new THREE.Mesh(ogiveGeo, steelMat);
    noseMesh.position.y = barrelLength;
    this.starshipUpperGroup.add(noseMesh);

    // Windward Heat Shield Nose Cone Overlay
    const noseShieldGeo = new THREE.CylinderGeometry(
      sRadius * 0.99, 0.001, noseLength, 32, 1, false, -Math.PI / 2, Math.PI
    );
    const noseShieldMesh = new THREE.Mesh(noseShieldGeo, tileMat);
    noseShieldMesh.position.y = barrelLength + noseLength / 2;
    this.starshipUpperGroup.add(noseShieldMesh);

    // A4. Aerodynamic Forward Flaps (Sculpted Swept Delta Canards)
    const fwdFlapShape = new THREE.Shape();
    fwdFlapShape.moveTo(0, 0);
    fwdFlapShape.lineTo(0.045 * vScale * 10, -0.015 * vScale * 10);
    fwdFlapShape.lineTo(0.035 * vScale * 10, -0.055 * vScale * 10);
    fwdFlapShape.lineTo(0, -0.040 * vScale * 10);
    fwdFlapShape.closePath();

    const extrudeSettings = { depth: 0.004 * vScale * 10, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.001, bevelThickness: 0.001 };
    const fwdFlapGeo = new THREE.ExtrudeGeometry(fwdFlapShape, extrudeSettings);

    this.flaps.fwdLeft = new THREE.Mesh(fwdFlapGeo, steelMat);
    this.flaps.fwdLeft.position.set(-sRadius - 0.002, barrelLength + noseLength * 0.35, 0);
    this.flaps.fwdLeft.rotation.y = -Math.PI / 2;
    this.starshipUpperGroup.add(this.flaps.fwdLeft);

    this.flaps.fwdRight = new THREE.Mesh(fwdFlapGeo, steelMat);
    this.flaps.fwdRight.position.set(sRadius + 0.002, barrelLength + noseLength * 0.35, 0);
    this.flaps.fwdRight.rotation.y = Math.PI / 2;
    this.starshipUpperGroup.add(this.flaps.fwdRight);

    // A5. Aerodynamic Aft Body Flaps (Conforming Wings)
    const aftFlapShape = new THREE.Shape();
    aftFlapShape.moveTo(0, 0);
    aftFlapShape.lineTo(0.065 * vScale * 10, -0.02 * vScale * 10);
    aftFlapShape.lineTo(0.055 * vScale * 10, -0.11 * vScale * 10);
    aftFlapShape.lineTo(0, -0.095 * vScale * 10);
    aftFlapShape.closePath();

    const aftFlapGeo = new THREE.ExtrudeGeometry(aftFlapShape, extrudeSettings);

    this.flaps.aftLeft = new THREE.Mesh(aftFlapGeo, steelMat);
    this.flaps.aftLeft.position.set(-sRadius - 0.002, barrelLength * 0.28, 0);
    this.flaps.aftLeft.rotation.y = -Math.PI / 2;
    this.starshipUpperGroup.add(this.flaps.aftLeft);

    this.flaps.aftRight = new THREE.Mesh(aftFlapGeo, steelMat);
    this.flaps.aftRight.position.set(sRadius + 0.002, barrelLength * 0.28, 0);
    this.flaps.aftRight.rotation.y = Math.PI / 2;
    this.starshipUpperGroup.add(this.flaps.aftRight);

    // A6. Raptor Vacuum & Sea-Level Engine Nozzles
    const engineSkirt = new THREE.Mesh(
      new THREE.CylinderGeometry(sRadius, sRadius * 0.98, 0.03 * vScale * 10, 32),
      darkMetalMat
    );
    engineSkirt.position.y = -0.015 * vScale * 10;
    this.starshipUpperGroup.add(engineSkirt);

    // 3 Large Vacuum Raptor Bells
    for (let i = 0; i < 3; i++) {
      const angle = (i * Math.PI * 2) / 3;
      const rBell = sRadius * 0.55;
      const bellGeo = new THREE.ConeGeometry(0.016 * vScale * 10, 0.035 * vScale * 10, 16, 1, true);
      const bellMesh = new THREE.Mesh(bellGeo, darkMetalMat);
      bellMesh.position.set(Math.cos(angle) * rBell, -0.035 * vScale * 10, Math.sin(angle) * rBell);
      this.starshipUpperGroup.add(bellMesh);
    }

    // A7. Starship Engine Exhaust Plume (Multi-Nozzle Glow)
    const plumeGeo = new THREE.ConeGeometry(0.042 * vScale * 10, 0.35 * vScale * 10, 24);
    const plumeMat = new THREE.MeshBasicMaterial({
      color: 0x00d4ff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.enginePlume = new THREE.Mesh(plumeGeo, plumeMat);
    this.enginePlume.position.y = -0.19 * vScale * 10;
    this.enginePlume.rotation.x = Math.PI;
    this.starshipUpperGroup.add(this.enginePlume);

    // A8. Hypersonic Reentry Plasma Shock Envelope
    const plasmaGeo = new THREE.SphereGeometry(sRadius * 1.5, 32, 32);
    const plasmaMat = new THREE.MeshBasicMaterial({
      color: 0xff6d00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
    });
    this.reentryPlasmaGlow = new THREE.Mesh(plasmaGeo, plasmaMat);
    this.reentryPlasmaGlow.position.y = barrelLength * 0.45;
    this.reentryPlasmaGlow.scale.set(1.1, 2.2, 1.3);
    this.starshipUpperGroup.add(this.reentryPlasmaGlow);

    this.vehicleMasterGroup.add(this.starshipUpperGroup);

    // =======================================================================
    // PART B: SUPER HEAVY BOOSTER (70m length, rendered during ascent)
    // =======================================================================
    this.boosterGroup = new THREE.Group();

    const boosterLength = 0.55 * vScale * 10;

    // B1. Booster Main Propellant Tank Barrel
    const bBarrelGeo = new THREE.CylinderGeometry(sRadius, sRadius, boosterLength, 32);
    const bBarrelMesh = new THREE.Mesh(bBarrelGeo, steelMat);
    bBarrelMesh.position.y = -boosterLength / 2;
    this.boosterGroup.add(bBarrelMesh);

    // B2. Vented Interstage Hot-Staging Ring
    const interstageGeo = new THREE.CylinderGeometry(sRadius, sRadius, 0.05 * vScale * 10, 32, 1, true);
    const interstageMesh = new THREE.Mesh(interstageGeo, darkMetalMat);
    interstageMesh.position.y = 0.025 * vScale * 10;
    this.boosterGroup.add(interstageMesh);

    // B3. 4 Booster Titanium Grid Fins
    const gridFinGeo = new THREE.BoxGeometry(0.04 * vScale * 10, 0.003 * vScale * 10, 0.03 * vScale * 10);
    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI) / 2;
      const fin = new THREE.Mesh(gridFinGeo, darkMetalMat);
      fin.position.set(Math.cos(angle) * (sRadius + 0.02 * vScale * 10), -0.04 * vScale * 10, Math.sin(angle) * (sRadius + 0.02 * vScale * 10));
      fin.rotation.y = angle;
      this.boosterGroup.add(fin);
    }

    // B4. 33 Raptor Engine Cluster Plume
    const bPlumeGeo = new THREE.ConeGeometry(sRadius * 1.3, 0.65 * vScale * 10, 24);
    const bPlumeMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.boosterPlume = new THREE.Mesh(bPlumeGeo, bPlumeMat);
    this.boosterPlume.position.y = -boosterLength - 0.32 * vScale * 10;
    this.boosterPlume.rotation.x = Math.PI;
    this.boosterGroup.add(this.boosterPlume);

    this.boosterGroup.position.y = -0.03 * vScale * 10;
    this.vehicleMasterGroup.add(this.boosterGroup);

    this.scene.add(this.vehicleMasterGroup);
  }

  // =========================================================================
  // 3D Event Beacons & Trajectory Ribbon
  // =========================================================================
  createBeacons() {
    this.beaconsGroup = new THREE.Group();
    this.scene.add(this.beaconsGroup);
  }

  updateTrajectoryRibbon(trajectoryPoints) {
    if (this.trajectoryLine) {
      this.scene.remove(this.trajectoryLine);
      this.trajectoryLine.geometry.dispose();
      this.trajectoryLine.material.dispose();
      this.trajectoryLine = null;
    }

    // Clear old beacon pins
    while (this.beaconsGroup.children.length > 0) {
      const obj = this.beaconsGroup.children[0];
      this.beaconsGroup.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    }

    if (!trajectoryPoints || trajectoryPoints.length < 2) return;

    const positions = [];
    const colors = [];

    trajectoryPoints.forEach((pt, idx) => {
      if (pt.scene_pos) {
        positions.push(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);

        // Gradient ribbon coloring by flight phase
        if (pt.phase === "ASCENT") {
          colors.push(0.0, 0.9, 1.0); // Cyan
        } else if (pt.phase === "ORBIT" || pt.phase === "ORBIT_NOMINAL") {
          colors.push(0.0, 0.8, 0.4); // Green
        } else if (pt.phase === "REENTRY") {
          colors.push(1.0, 0.45, 0.0); // Orange
        } else {
          colors.push(0.5, 0.2, 0.9); // Purple
        }

        // Add 3D Event Beacon Pins at major milestones
        if (idx === 0 || idx === Math.floor(trajectoryPoints.length * 0.15) || idx === Math.floor(trajectoryPoints.length * 0.5) || idx === trajectoryPoints.length - 1) {
          const pinGeo = new THREE.SphereGeometry(0.04, 16, 16);
          const pinMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
          const pin = new THREE.Mesh(pinGeo, pinMat);
          pin.position.set(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);
          this.beaconsGroup.add(pin);
        }
      }
    });

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

    const material = new THREE.LineBasicMaterial({
      vertexColors: true,
      linewidth: 2.5,
      transparent: true,
      opacity: 0.88,
    });

    this.trajectoryLine = new THREE.Line(geometry, material);
    this.scene.add(this.trajectoryLine);
  }

  // =========================================================================
  // State Updates & Real-Time Physical Interpolation
  // =========================================================================
  updateVehicleState(point, profile) {
    if (!point || !point.scene_pos) return;

    const time_s = point.time_s || 0;
    const vPos = new THREE.Vector3(point.scene_pos[0], point.scene_pos[1], point.scene_pos[2]);

    // 1. Vehicle Position
    this.vehicleMasterGroup.position.copy(vPos);

    // Compute velocity direction vector
    const deltaMove = vPos.clone().sub(this.lastVehiclePos);
    if (deltaMove.lengthSq() > 1e-7) {
      this.lastVelocityDir.copy(deltaMove).normalize();
    }
    this.lastVehiclePos.copy(vPos);

    // 2. Vehicle Attitude (Pitch & Orbital Heading)
    const pitchRad = THREE.MathUtils.degToRad(point.pitch_deg || 0);
    this.vehicleMasterGroup.rotation.z = pitchRad;

    // Align yaw tangent to orbital trajectory
    const heading = Math.atan2(this.lastVelocityDir.x, this.lastVelocityDir.z);
    this.vehicleMasterGroup.rotation.y = heading;

    // 3. Staging Separation Logic
    // During ascent (t <= 162s), Booster is attached to Starship.
    // At staging (t > 162s), Booster separates and drifts away.
    if (profile && profile.is_synthetic) {
      this.boosterGroup.visible = false;
      this.starshipUpperGroup.position.set(0, 0, 0);
    } else if (time_s <= 162.0) {
      this.boosterGroup.visible = true;
      this.boosterGroup.position.set(0, -0.03 * 0.85, 0);
      this.starshipUpperGroup.position.set(0, 0, 0);
    } else if (time_s <= 260.0) {
      // Hot-staging drift: Booster moves backward along separation axis
      const sepDist = (time_s - 162.0) * 0.003;
      this.boosterGroup.visible = true;
      this.boosterGroup.position.set(0, -0.03 * 0.85 - sepDist, -sepDist * 0.5);
    } else {
      // Expended / Separated
      this.boosterGroup.visible = false;
    }

    // 4. Aerodynamic Flap Deflections (Forward & Aft)
    const fwdRad = THREE.MathUtils.degToRad(point.flaps_fwd_deg || 0);
    const aftRad = THREE.MathUtils.degToRad(point.flaps_aft_deg || 0);

    if (this.flaps.fwdLeft) this.flaps.fwdLeft.rotation.x = fwdRad;
    if (this.flaps.fwdRight) this.flaps.fwdRight.rotation.x = -fwdRad;
    if (this.flaps.aftLeft) this.flaps.aftLeft.rotation.x = aftRad;
    if (this.flaps.aftRight) this.flaps.aftRight.rotation.x = -aftRad;

    // 5. Raptor Engine Plumes (Thrust Driven)
    const thrust = point.thrust_mn || 0;
    if (this.boosterPlume && this.boosterGroup.visible) {
      if (thrust > 10.0) {
        this.boosterPlume.material.opacity = Math.min(0.95, 0.4 + (thrust / 75.0) * 0.55);
        const flicker = 1.0 + (Math.random() - 0.5) * 0.15;
        this.boosterPlume.scale.set(flicker, flicker * 1.3, flicker);
      } else {
        this.boosterPlume.material.opacity = 0.0;
      }
    }

    if (this.enginePlume) {
      if (thrust > 0.5 && (!this.boosterGroup.visible || time_s > 162.0)) {
        this.enginePlume.material.opacity = Math.min(0.92, 0.35 + (thrust / 15.0) * 0.6);
        const flicker = 1.0 + (Math.random() - 0.5) * 0.18;
        this.enginePlume.scale.set(flicker, flicker * 1.4, flicker);
      } else {
        this.enginePlume.material.opacity = 0.0;
      }
    }

    // 6. Hypersonic Reentry Plasma Shock Glow (Heat Flux Driven)
    const heatFlux = point.heat_flux_mw_m2 || 0;
    if (this.reentryPlasmaGlow) {
      if (heatFlux > 0.04) {
        this.reentryPlasmaGlow.material.opacity = Math.min(0.88, heatFlux / 0.75);
        // Thermal spectrum: dark orange (800K) to incandescent yellow-white (1600K)
        const hue = Math.max(0.04, 0.11 - (heatFlux / 1.0) * 0.07);
        this.reentryPlasmaGlow.material.color.setHSL(hue, 1.0, 0.52);
      } else {
        this.reentryPlasmaGlow.material.opacity = 0.0;
      }
    }

    // 7. Update Camera Framing
    this.updateCamera();
  }

  // =========================================================================
  // Orbital Frame Camera Tracking (Solving Horizon & Earth Clipping)
  // =========================================================================
  setCameraMode(mode) {
    this.currentCameraMode = mode;
  }

  updateCamera() {
    const vPos = this.vehicleMasterGroup.position;

    // Local Orbital Reference Frame:
    // rHat: Radial unit vector pointing from Earth center through vehicle
    // vHat: In-track unit vector along vehicle velocity direction
    // hHat: Cross-track normal unit vector
    const rHat = vPos.clone().normalize();
    const vHat = this.lastVelocityDir.clone().normalize();
    const hHat = new THREE.Vector3().crossVectors(rHat, vHat).normalize();

    if (this.currentCameraMode === "ORBIT_FOLLOW") {
      // Cinematic over-the-shoulder follow framing curved Earth limb below
      // Position: slightly above (+rHat), behind (-vHat), and to the side (+hHat)
      const camOffset = rHat.clone().multiplyScalar(0.42)
        .sub(vHat.clone().multiplyScalar(0.78))
        .add(hHat.clone().multiplyScalar(0.48));

      const targetCamPos = vPos.clone().add(camOffset);
      const lookTarget = vPos.clone().add(vHat.clone().multiplyScalar(0.15));

      this.camera.position.lerp(targetCamPos, 0.08);
      if (this.controls) {
        this.controls.target.lerp(lookTarget, 0.08);
      }
    } else if (this.currentCameraMode === "EARTH_GLOBAL") {
      // Pull back to planetary perspective showing the full orbit ribbon
      const globalPos = new THREE.Vector3(0, 13.5, 19.5);
      this.camera.position.lerp(globalPos, 0.04);
      if (this.controls) {
        this.controls.target.lerp(new THREE.Vector3(0, 0, 0), 0.04);
      }
    } else if (this.currentCameraMode === "STAGE_SEP") {
      // Focus on the interstage separation interface
      const camOffset = rHat.clone().multiplyScalar(0.18)
        .sub(vHat.clone().multiplyScalar(0.35))
        .sub(hHat.clone().multiplyScalar(0.25));

      this.camera.position.lerp(vPos.clone().add(camOffset), 0.1);
      if (this.controls) {
        this.controls.target.lerp(vPos, 0.1);
      }
    } else if (this.currentCameraMode === "PAYLOAD_BAY") {
      // Starlink dispenser perspective
      const camOffset = rHat.clone().multiplyScalar(0.25)
        .add(vHat.clone().multiplyScalar(0.22))
        .add(hHat.clone().multiplyScalar(0.25));

      this.camera.position.lerp(vPos.clone().add(camOffset), 0.1);
      if (this.controls) {
        this.controls.target.lerp(vPos, 0.1);
      }
    } else if (this.currentCameraMode === "ENTRY_BELLY") {
      // Direct view of the windward black TPS tile belly
      const camOffset = rHat.clone().multiplyScalar(-0.45)
        .sub(vHat.clone().multiplyScalar(0.25))
        .add(hHat.clone().multiplyScalar(0.35));

      this.camera.position.lerp(vPos.clone().add(camOffset), 0.08);
      if (this.controls) {
        this.controls.target.lerp(vPos, 0.08);
      }
    } else if (this.currentCameraMode === "LANDING_PAD") {
      // Ground pad observer view (for synthetic landing)
      const padPos = new THREE.Vector3(0.25, 0.08, 0.35);
      this.camera.position.lerp(padPos, 0.08);
      if (this.controls) {
        this.controls.target.lerp(vPos, 0.08);
      }
    }
    // "FREE_ORBIT" leaves OrbitControls in full interactive control
  }

  onWindowResize() {
    this.width = this.canvas.clientWidth || window.innerWidth;
    this.height = this.canvas.clientHeight || window.innerHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  animate() {
    requestAnimationFrame(this.animate);

    // Subtle realistic Earth rotation (15 arcsec/sec in real time)
    if (this.earthGroup) {
      this.earthGroup.rotation.y += 0.00012;
    }

    if (this.controls) {
      this.controls.update();
    }

    if (this.vehicleMasterGroup) {
      this.renderMiniGlobe(this.vehicleMasterGroup.position);
    }

    this.renderer.render(this.scene, this.camera);
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

    // Dark Earth Globe Circle
    ctx.beginPath();
    ctx.arc(w / 2, h / 2, w / 2 - 2, 0, Math.PI * 2);
    ctx.fillStyle = "#040e1f";
    ctx.fill();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Equator and Meridian Grid Lines
    ctx.strokeStyle = "rgba(0, 229, 255, 0.16)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(w / 2, h / 2, w / 2 - 4, (w / 2 - 4) * 0.38, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w / 2, 2);
    ctx.lineTo(w / 2, h - 2);
    ctx.stroke();

    // Sub-satellite position dot
    const rNorm = Math.sqrt(vPos.x * vPos.x + vPos.y * vPos.y + vPos.z * vPos.z) || 6.378;
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
}

window.MissionSceneManager = MissionSceneManager;
