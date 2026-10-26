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

    // Starlink V3 26-Satellite Rocket Mouth Dispenser System
    this.dispenserGroup = null;
    this.mouthDoorPivot = null;
    this.mouthDoor = null;
    this.satellitesGroup = null;
    this.starlinkSatellites = [];
    this.selectedSatelliteIndex = 0;

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
      this.controls.enabled = false;
      this.controls.addEventListener("start", () => {
        this.currentCameraMode = "FREE_ORBIT";
        this.controls.enabled = true;
        const freeRadio = document.querySelector("input[name='camMode'][value='FREE_ORBIT']");
        if (freeRadio) freeRadio.checked = true;
        const titleBox = document.querySelector(".cam-box-title");
        if (titleBox) titleBox.innerText = "CAMERA: FREE ORBIT";
      });
    }

    // 5. Physically Inspired Space Lighting
    const ambientLight = new THREE.AmbientLight(0x28384c, 0.95);
    this.scene.add(ambientLight);

    // Primary Solar Directional Light
    this.sunLight = new THREE.DirectionalLight(0xffffff, 2.8);
    this.sunLight.position.set(60, 45, 50).normalize().multiplyScalar(100);
    this.scene.add(this.sunLight);

    // Camera Keylight (attached to camera so spacecraft is always beautifully lit from observer angle)
    this.cameraLight = new THREE.DirectionalLight(0xd5e8ff, 1.4);
    this.camera.add(this.cameraLight);
    this.scene.add(this.camera);

    // Soft Earth Albedo Upward Bounce Light
    const earthAlbedo = new THREE.DirectionalLight(0x1a447c, 1.1);
    earthAlbedo.position.set(0, -60, 0);
    this.scene.add(earthAlbedo);

    // Subtle Cyan Rim Backlight for Spacecraft Silhouettes
    const rimLight = new THREE.DirectionalLight(0x00d4ff, 0.5);
    rimLight.position.set(-40, 10, -40).normalize();
    this.scene.add(rimLight);

    // 6. Build Celestial & Vehicle Objects
    this.createStarfield();
    this.createEarth();
    this.createVehicle();
    this.createDispenserMouthAndSatellites();
    this.createBeacons();

    // 7. Event Listeners
    window.addEventListener("resize", () => this.onWindowResize());

    // 8. Master Animation Loop
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

    let earthTex = null;
    const loader = new THREE.TextureLoader();

    // Check embedded photographic NASA Earth texture (guaranteed CORS-free offline)
    if (typeof window !== "undefined" && window.EMBEDDED_TEXTURES && window.EMBEDDED_TEXTURES.earthDay) {
      try {
        earthTex = loader.load(window.EMBEDDED_TEXTURES.earthDay);
        earthTex.wrapS = THREE.RepeatWrapping;
        earthTex.wrapT = THREE.ClampToEdgeWrapping;
      } catch (e) {
        earthTex = this.createProceduralEarthTexture();
      }
    } else {
      earthTex = this.createProceduralEarthTexture();
      loader.load(
        "assets/textures/globeprev-clouds-on-DOpaHC5m-r2.jpg",
        (tex) => {
          if (this.earthMesh) {
            this.earthMesh.material.map = tex;
            this.earthMesh.material.needsUpdate = true;
          }
        },
        undefined,
        () => { /* procedural fallback */ }
      );
    }

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
    // True aerodynamic tangent ogive curve:
    // Base at y = 0 has r = radius, smoothly curving to a sharp aerodynamic tip at y = length (r = 0).
    const rho = (radius * radius + length * length) / (2.0 * radius);
    const points = [];
    const steps = 30;

    for (let i = 0; i <= steps; i++) {
      const y = (i / steps) * length;
      const term = Math.max(0.0, rho * rho - y * y);
      const r = Math.max(0.0, Math.sqrt(term) + radius - rho);
      points.push(new THREE.Vector2(r, y));
    }
    points.push(new THREE.Vector2(0, length));

    return new THREE.LatheGeometry(points, segments);
  }

  createVehicle() {
    this.vehicleMasterGroup = new THREE.Group();

    // Baseline scale factor: Starship is 50m long, 9m diameter.
    // In scene units: 1 unit = 1000 km = 1,000,000m.
    const vScale = 0.20;
    const sRadius = 0.045 * vScale * 10; // 0.09 units

    // Materials
    // 1. Brushed 304L Stainless Steel (Metallic, reflective leeward hull)
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0xe8eef6,
      metalness: 0.95,
      roughness: 0.16,
    });

    // 2. Black Hexagonal TPS Tiles (Windward heat shield belly)
    const tileMat = new THREE.MeshStandardMaterial({
      color: 0x0c0e12,
      metalness: 0.06,
      roughness: 0.90,
    });

    // 3. Dark Ceramic / Carbon Matrix (Engine bells & interstage)
    const darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x1e2228,
      metalness: 0.88,
      roughness: 0.30,
    });

    // =======================================================================
    // PART A: STARSHIP UPPER STAGE (50m length)
    // =======================================================================
    this.starshipUpperGroup = new THREE.Group();

    const barrelLength = 0.32 * vScale * 10;
    const noseLength = 0.22 * vScale * 10;

    // A1. Main Cylindrical Barrel (Solid closed leeward hull)
    const barrelGeo = new THREE.CylinderGeometry(
      sRadius, sRadius, barrelLength, 32, 1, false, Math.PI / 2, Math.PI
    );
    const barrelMesh = new THREE.Mesh(barrelGeo, steelMat);
    barrelMesh.position.y = barrelLength / 2;
    this.starshipUpperGroup.add(barrelMesh);

    // A2. Windward Black TPS Belly Barrel (Windward 180 deg)
    const bellyGeo = new THREE.CylinderGeometry(
      sRadius * 1.006, sRadius * 1.006, barrelLength, 32, 1, false, -Math.PI / 2, Math.PI
    );
    const bellyMesh = new THREE.Mesh(bellyGeo, tileMat);
    bellyMesh.position.y = barrelLength / 2;
    this.starshipUpperGroup.add(bellyMesh);

    // A3. Sleek Pointed Ogive Nosecone (Solid curved nose)
    const ogiveGeo = this.createOgiveNosecone(sRadius, noseLength, 32);
    const noseMesh = new THREE.Mesh(ogiveGeo, steelMat);
    noseMesh.position.y = barrelLength;
    this.starshipUpperGroup.add(noseMesh);

    // Windward Heat Shield Nose Cone Overlay (Windward 180 deg half-lathe)
    const shieldPoints = [];
    const rho = (sRadius * sRadius + noseLength * noseLength) / (2.0 * sRadius);
    for (let i = 0; i <= 30; i++) {
      const y = (i / 30) * noseLength;
      const term = Math.max(0.0, rho * rho - y * y);
      const r = Math.max(0.0, Math.sqrt(term) + sRadius * 1.006 - rho);
      shieldPoints.push(new THREE.Vector2(r, y));
    }
    shieldPoints.push(new THREE.Vector2(0, noseLength));
    const noseShieldGeo = new THREE.LatheGeometry(shieldPoints, 32, -Math.PI / 2, Math.PI);
    const noseShieldMesh = new THREE.Mesh(noseShieldGeo, tileMat);
    noseShieldMesh.position.y = barrelLength;
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

    // Aft Bulkhead Dome (Solid bottom closing the engine skirt, preventing hollow pipe look)
    const aftDomeGeo = new THREE.SphereGeometry(sRadius * 0.99, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
    const aftDomeMesh = new THREE.Mesh(aftDomeGeo, darkMetalMat);
    aftDomeMesh.rotation.x = Math.PI;
    aftDomeMesh.position.y = 0;
    this.starshipUpperGroup.add(aftDomeMesh);

    // A6. Engine Skirt & 6 Distinct Raptor 3 Engine Bells
    const engineSkirt = new THREE.Mesh(
      new THREE.CylinderGeometry(sRadius, sRadius * 0.98, 0.03 * vScale * 10, 32),
      darkMetalMat
    );
    engineSkirt.position.y = -0.015 * vScale * 10;
    this.starshipUpperGroup.add(engineSkirt);

    // 3 Center Sea-Level Raptor Bells
    for (let i = 0; i < 3; i++) {
      const angle = (i * Math.PI * 2) / 3 + Math.PI / 6;
      const rBell = sRadius * 0.28;
      const bellGeo = new THREE.ConeGeometry(0.010 * vScale * 10, 0.024 * vScale * 10, 16, 1, true);
      const bellMesh = new THREE.Mesh(bellGeo, darkMetalMat);
      bellMesh.position.set(Math.cos(angle) * rBell, -0.022 * vScale * 10, Math.sin(angle) * rBell);
      this.starshipUpperGroup.add(bellMesh);
    }

    // 3 Large Vacuum Raptor Bells
    for (let i = 0; i < 3; i++) {
      const angle = (i * Math.PI * 2) / 3;
      const rBell = sRadius * 0.58;
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

    // B5. Independent Super Heavy Booster for Gulf Return Branch
    this.independentBoosterGroup = new THREE.Group();
    const bIndBarrel = new THREE.Mesh(bBarrelGeo, steelMat);
    bIndBarrel.position.y = -boosterLength / 2;
    this.independentBoosterGroup.add(bIndBarrel);
    const bIndInterstage = new THREE.Mesh(interstageGeo, darkMetalMat);
    bIndInterstage.position.y = 0.025 * vScale * 10;
    this.independentBoosterGroup.add(bIndInterstage);
    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI) / 2;
      const fin = new THREE.Mesh(gridFinGeo, darkMetalMat);
      fin.position.set(Math.cos(angle) * (sRadius + 0.02 * vScale * 10), -0.04 * vScale * 10, Math.sin(angle) * (sRadius + 0.02 * vScale * 10));
      fin.rotation.y = angle;
      this.independentBoosterGroup.add(fin);
    }
    const indPlumeMat = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.independentBoosterPlume = new THREE.Mesh(bPlumeGeo, indPlumeMat);
    this.independentBoosterPlume.position.y = -boosterLength - 0.32 * vScale * 10;
    this.independentBoosterPlume.rotation.x = Math.PI;
    this.independentBoosterGroup.add(this.independentBoosterPlume);
    this.independentBoosterGroup.visible = false;
    this.scene.add(this.independentBoosterGroup);

    this.scene.add(this.vehicleMasterGroup);
  }

  // =========================================================================
  // Starlink V3 26-Satellite Rocket Mouth Dispenser Simulation
  // Targets Visual References: media_1792951657295_146a92c9.png,
  // media_1792951553611_3819560f.png, media_1792951549197_1830f39c.png
  // =========================================================================
  createDispenserMouthAndSatellites() {
    const vScale = 0.20;
    const sRadius = 0.045 * vScale * 10; // 0.09
    const barrelLength = 0.32 * vScale * 10; // 0.64
    const mouthY = barrelLength * 0.88; // 0.563 units up the barrel (just below nosecone)

    // 1. Dispenser Mouth Group (mounted on Starship Upper Stage)
    this.dispenserGroup = new THREE.Group();
    this.dispenserGroup.position.set(0, mouthY, 0);

    // Mouth Cavity Recess (Interior dark payload bay compartment)
    const cavityMat = new THREE.MeshStandardMaterial({
      color: 0x05070a,
      roughness: 0.92,
      metalness: 0.2,
    });
    const cavityGeo = new THREE.BoxGeometry(0.048, 0.015, 0.026);
    const cavityMesh = new THREE.Mesh(cavityGeo, cavityMat);
    cavityMesh.position.set(0, 0, sRadius - 0.012);
    this.dispenserGroup.add(cavityMesh);

    // Metallic Sill and Side Guide Rollers (ribbed coils on left and right)
    const rollerMat = new THREE.MeshStandardMaterial({
      color: 0x5a6370,
      metalness: 0.92,
      roughness: 0.22,
    });
    for (let side of [-0.022, 0.022]) {
      const rollerGeo = new THREE.CylinderGeometry(0.0028, 0.0028, 0.013, 16);
      const roller = new THREE.Mesh(rollerGeo, rollerMat);
      roller.position.set(side, 0, sRadius - 0.002);
      this.dispenserGroup.add(roller);
    }

    // Articulated Rocket Mouth Door (hinged at the top edge like an open mouth/visor)
    const doorMat = new THREE.MeshStandardMaterial({
      color: 0xdde6ed,
      metalness: 0.94,
      roughness: 0.20,
    });
    const doorGeo = new THREE.BoxGeometry(0.048, 0.014, 0.002);
    this.mouthDoor = new THREE.Mesh(doorGeo, doorMat);

    // Pivot positioned along the upper lip/hinge of the mouth
    this.mouthDoorPivot = new THREE.Group();
    this.mouthDoorPivot.position.set(0, 0.007, sRadius);
    this.mouthDoor.position.set(0, -0.007, 0);
    this.mouthDoorPivot.add(this.mouthDoor);
    this.dispenserGroup.add(this.mouthDoorPivot);

    this.starshipUpperGroup.add(this.dispenserGroup);

    // 2. The 26 Starlink V3 Satellites
    this.satellitesGroup = new THREE.Group();
    this.scene.add(this.satellitesGroup);

    this.starlinkSatellites = [];
    const numSats = 26;

    // Materials
    const busMat = new THREE.MeshStandardMaterial({
      color: 0x1f242d,
      metalness: 0.88,
      roughness: 0.28,
    });
    const solarMat = new THREE.MeshStandardMaterial({
      color: 0x082a66,
      metalness: 0.90,
      roughness: 0.12,
      emissive: new THREE.Color(0x021028),
      emissiveIntensity: 0.35,
    });
    const antennaMat = new THREE.MeshStandardMaterial({
      color: 0xd8e0e8,
      metalness: 0.82,
      roughness: 0.28,
    });
    const beaconMat = new THREE.MeshBasicMaterial({
      color: 0x00ffcc,
    });

    for (let i = 0; i < numSats; i++) {
      const sat = new THREE.Group();

      // Satellite Bus (Flat-pack chassis)
      const busGeo = new THREE.BoxGeometry(0.034, 0.0035, 0.048);
      const busMesh = new THREE.Mesh(busGeo, busMat);
      sat.add(busMesh);

      // Phased Array Antenna (bottom surface)
      const antGeo = new THREE.BoxGeometry(0.030, 0.0006, 0.042);
      const antMesh = new THREE.Mesh(antGeo, antennaMat);
      antMesh.position.y = -0.002;
      sat.add(antMesh);

      // 4 Guide Rollers on edges (matching user reference photos)
      for (let rx of [-0.017, 0.017]) {
        for (let rz of [-0.018, 0.018]) {
          const rGeo = new THREE.CylinderGeometry(0.002, 0.002, 0.005, 12);
          const rMesh = new THREE.Mesh(rGeo, rollerMat);
          rMesh.rotation.z = Math.PI / 2;
          rMesh.position.set(rx, 0, rz);
          sat.add(rMesh);
        }
      }

      // Deployable Solar Array Wing (hinged at rear edge)
      const wingPivot = new THREE.Group();
      wingPivot.position.set(0, 0.0025, -0.024);

      const wingGeo = new THREE.BoxGeometry(0.014, 0.0006, 0.055);
      const wingMesh = new THREE.Mesh(wingGeo, solarMat);
      wingMesh.position.set(0, 0, -0.028);
      wingPivot.add(wingMesh);
      sat.add(wingPivot);

      // Status Beacon LED
      const beaconGeo = new THREE.SphereGeometry(0.0012, 8, 8);
      const beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
      beaconMesh.position.set(0.014, 0.0025, 0.022);
      sat.add(beaconMesh);

      // Initial stowed position in mouth dispenser
      this.dispenserGroup.add(sat);
      sat.position.set(0, (i - 13) * 0.0003, sRadius - 0.010);
      sat.visible = false;

      this.starlinkSatellites.push({
        index: i,
        number: i + 1,
        id: `SAT-F14-${String(i + 1).padStart(3, "0")}`,
        deployTime_s: 1320.0 + i * 14.0, // 1320s to 1670s (Flight 14 deployment window)
        mesh: sat,
        wingPivot: wingPivot,
        beacon: beaconMesh,
        state: "ENCLOSED",
      });
    }
  }

  updateSatellites(time_s) {
    if (!this.starlinkSatellites || this.starlinkSatellites.length === 0) return;

    const deployStart = 1320.0;
    const deployEnd = 1680.0;

    // 1. Articulated Rocket Mouth Door Animation
    if (this.mouthDoorPivot) {
      if (time_s >= (deployStart - 10.0) && time_s <= (deployEnd + 30.0)) {
        // Mouth opens wide upward
        const openProg = Math.min(1.0, Math.max(0.0, (time_s - (deployStart - 10.0)) / 10.0));
        this.mouthDoorPivot.rotation.x = -openProg * 1.25; // 71 degrees open mouth!
      } else if (time_s > (deployEnd + 30.0)) {
        // Mouth closes flush
        const closeProg = Math.min(1.0, (time_s - (deployEnd + 30.0)) / 10.0);
        this.mouthDoorPivot.rotation.x = -(1.0 - closeProg) * 1.25;
      } else {
        this.mouthDoorPivot.rotation.x = 0; // Closed
      }
    }

    const vPos = this.vehicleMasterGroup.position;
    const vDir = this.lastVelocityDir.clone().normalize();
    const rUp = vPos.clone().normalize();
    const hNorm = new THREE.Vector3().crossVectors(rUp, vDir).normalize();

    // 2. Update each of the 26 Starlinks
    this.starlinkSatellites.forEach((s) => {
      const dt = time_s - s.deployTime_s;

      if (dt < 0) {
        // STOWED inside mouth rack
        if (s.mesh.parent !== this.dispenserGroup) {
          this.dispenserGroup.add(s.mesh);
        }
        s.mesh.position.set(0, (s.index - 13) * 0.0003, 0.09 - 0.010);
        s.mesh.rotation.set(0, 0, 0);
        s.wingPivot.rotation.set(0, 0, 0); // Folded
        s.beacon.material.color.setHex(0x334455);
        s.state = "ENCLOSED";
        s.mesh.visible = (time_s >= deployStart - 60.0 && s.index < 4);
      } else if (dt <= 4.0) {
        // EJECTING OUT OF ROCKET MOUTH (0 to 4s)
        s.mesh.visible = true;
        if (s.mesh.parent !== this.dispenserGroup) {
          this.dispenserGroup.add(s.mesh);
        }
        const slideU = dt / 4.0;
        // Slide out through the mouth slot along +Z
        s.mesh.position.set(0, 0, (0.09 - 0.010) + slideU * 0.045);
        s.mesh.rotation.x = slideU * 0.12;

        // Wing starts unfolding near the exit
        if (slideU > 0.6) {
          const wingU = (slideU - 0.6) / 0.4;
          s.wingPivot.rotation.y = wingU * (Math.PI / 2);
        } else {
          s.wingPivot.rotation.y = 0;
        }

        s.beacon.material.color.setHex(0x00e5ff); // Cyan active
        s.state = "EJECTING";
      } else {
        // DEPLOYED IN FREE ORBIT AHEAD OF STARSHIP
        s.mesh.visible = true;
        if (s.mesh.parent !== this.satellitesGroup) {
          this.satellitesGroup.add(s.mesh);
        }

        // Wing fully extended (90 deg)
        s.wingPivot.rotation.y = Math.PI / 2;

        // Physical forward separation & orbital drift
        const freeTime = dt - 4.0;
        const driftDist = freeTime * 0.00015;
        const latDist = Math.sin(s.index * 0.6) * Math.min(0.12, 0.015 + freeTime * 0.00005);
        const altDist = (s.index % 2 === 0 ? 0.006 : -0.006) + Math.cos(s.index) * 0.003;

        // Deploy FORWARD ahead of Starship nosecone (tip at 0.86) along orbital velocity vector
        const fwdDist = 0.88 + s.index * 0.042 + Math.min(0.60, driftDist);
        const satPos = vPos.clone()
          .add(vDir.clone().multiplyScalar(fwdDist))
          .add(hNorm.clone().multiplyScalar(latDist))
          .add(rUp.clone().multiplyScalar(altDist + 0.04));

        s.mesh.position.copy(satPos);
        s.mesh.lookAt(satPos.clone().add(vDir));

        // Pulsing telemetry beacon
        const pulse = Math.sin(time_s * 4.0 + s.index) > 0 ? 0x00ff88 : 0x008844;
        s.beacon.material.color.setHex(pulse);

        s.state = "ONLINE";
      }
    });
  }

  // =========================================================================
  // 3D Event Beacons & Trajectory Ribbon
  // =========================================================================
  createBeacons() {
    this.beaconsGroup = new THREE.Group();
    this.scene.add(this.beaconsGroup);
  }

  createMilestoneBadge(text, subtext, color = "#00e5ff") {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 72;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "rgba(4, 16, 36, 0.88)";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(4, 4, 248, 64, 10);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillRect(4, 4, 248, 64);
      ctx.strokeRect(4, 4, 248, 64);
    }

    ctx.font = "bold 20px monospace";
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.fillText(text, 128, 30);

    if (subtext) {
      ctx.font = "15px monospace";
      ctx.fillStyle = "#e0e6ed";
      ctx.fillText(subtext, 128, 54);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(0.75, 0.22, 1.0);
    return sprite;
  }

  updateTrajectoryRibbon(trajectoryPoints, boosterTrajectoryPoints) {
    if (this.trajectoryLine) {
      this.scene.remove(this.trajectoryLine);
      this.trajectoryLine.geometry.dispose();
      this.trajectoryLine.material.dispose();
      this.trajectoryLine = null;
    }
    if (this.boosterTrajectoryLine) {
      this.scene.remove(this.boosterTrajectoryLine);
      this.boosterTrajectoryLine.geometry.dispose();
      this.boosterTrajectoryLine.material.dispose();
      this.boosterTrajectoryLine = null;
    }

    // Clear old beacon pins and badge sprites
    while (this.beaconsGroup.children.length > 0) {
      const obj = this.beaconsGroup.children[0];
      this.beaconsGroup.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (obj.material.map) obj.material.map.dispose();
        obj.material.dispose();
      }
    }

    if (!trajectoryPoints || trajectoryPoints.length < 2) return;

    // 1. Starship Trajectory Ribbon
    const positions = [];
    const colors = [];

    trajectoryPoints.forEach((pt) => {
      if (pt.scene_pos) {
        positions.push(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);

        if (pt.phase === "ASCENT") {
          colors.push(0.0, 0.9, 1.0); // Cyan
        } else if (pt.phase === "ORBIT" || pt.phase === "ORBIT_NOMINAL") {
          colors.push(0.0, 0.8, 0.4); // Green
        } else if (pt.phase === "REENTRY") {
          colors.push(1.0, 0.45, 0.0); // Orange
        } else {
          colors.push(0.5, 0.2, 0.9); // Purple
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

    // 2. Super Heavy Booster Return Ribbon (Gulf of America Branch)
    if (boosterTrajectoryPoints && boosterTrajectoryPoints.length > 1) {
      const bPositions = [];
      boosterTrajectoryPoints.forEach(pt => {
        if (pt.scene_pos) {
          bPositions.push(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);
        }
      });
      const bGeo = new THREE.BufferGeometry();
      bGeo.setAttribute("position", new THREE.Float32BufferAttribute(bPositions, 3));
      const bMat = new THREE.LineBasicMaterial({
        color: 0xffaa00,
        linewidth: 2.5,
        transparent: true,
        opacity: 0.9,
      });
      this.boosterTrajectoryLine = new THREE.Line(bGeo, bMat);
      this.scene.add(this.boosterTrajectoryLine);

      // Add Booster Gulf Splashdown Pin
      const splashPt = boosterTrajectoryPoints[boosterTrajectoryPoints.length - 1];
      if (splashPt && splashPt.scene_pos) {
        const pinGeo = new THREE.SphereGeometry(0.05, 16, 16);
        const pinMat = new THREE.MeshBasicMaterial({ color: 0xffaa00 });
        const pin = new THREE.Mesh(pinGeo, pinMat);
        pin.position.set(splashPt.scene_pos[0], splashPt.scene_pos[1], splashPt.scene_pos[2]);
        this.beaconsGroup.add(pin);

        const badge = this.createMilestoneBadge("WATER LANDING", "Gulf of America (T+07:05)", "#ffaa00");
        badge.position.set(splashPt.scene_pos[0], splashPt.scene_pos[1] + 0.15, splashPt.scene_pos[2]);
        this.beaconsGroup.add(badge);
      }
    }

    // 3. Add 3D Milestone Callout Badges on Trajectory (Replicating SpaceX Trajectory Diagram)
    const addBadgeAtFraction = (frac, title, sub, color) => {
      const idx = Math.min(trajectoryPoints.length - 1, Math.floor(trajectoryPoints.length * frac));
      const pt = trajectoryPoints[idx];
      if (pt && pt.scene_pos) {
        const pinGeo = new THREE.SphereGeometry(0.04, 16, 16);
        const pinMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color) });
        const pin = new THREE.Mesh(pinGeo, pinMat);
        pin.position.set(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);
        this.beaconsGroup.add(pin);

        const badge = this.createMilestoneBadge(title, sub, color);
        badge.position.set(pt.scene_pos[0], pt.scene_pos[1] + 0.18, pt.scene_pos[2]);
        this.beaconsGroup.add(badge);
      }
    };

    addBadgeAtFraction(0.00, "LAUNCH", "Starbase T+00:00", "#00e5ff");
    addBadgeAtFraction(0.12, "HOT STAGING", "Sep T+02:42", "#00e5ff");
    addBadgeAtFraction(0.24, "ORBIT INSERTION", "275 km T+08:42", "#00e676");
    addBadgeAtFraction(0.40, "26× STARLINK DEPLOY", "T+22:00 - 28:00", "#00e5ff");
    addBadgeAtFraction(0.70, "DEORBIT BURN", "1 SL Raptor", "#ff9100");
    addBadgeAtFraction(0.85, "STARSHIP ENTRY", "EI 120km (70° AoA)", "#ff5722");
    addBadgeAtFraction(0.99, "PACIFIC SPLASHDOWN", "Northern Pacific", "#00e676");
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

    // 2. Vehicle Attitude Kinematics (Full 3D Orthonormal Basis - Zero Gimbal Lock)
    // Vehicle body axes:
    // +Y_body: Longitudinal axis (Nosecone)
    // -Z_body: Windward belly (Black hexagonal TPS tiles)
    // +Z_body: Leeward hull (Stainless steel & Starlink dispenser mouth)
    // +X_body: Starboard / right wing
    const rUp = vPos.clone().normalize();
    const vDir = this.lastVelocityDir.clone().normalize();
    
    // Local horizontal downrange vector
    let hDir = vDir.clone().sub(rUp.clone().multiplyScalar(vDir.dot(rUp))).normalize();
    if (hDir.lengthSq() < 1e-4) {
      hDir = new THREE.Vector3(1, 0, 0);
    }

    let noseDir = new THREE.Vector3();
    let bellyDir = rUp.clone().negate(); // Default belly facing nadir (toward Earth)

    if (profile && profile.is_synthetic) {
      // Synthetic Phase 7 Landing Lab
      if (time_s < 14.0) {
        // Belly-flop descent (AoA 90 deg): Nose horizontal, belly down
        noseDir.copy(hDir);
        bellyDir.copy(rUp).negate();
      } else if (time_s < 20.0) {
        // Flip maneuver: Pitching from horizontal (90 deg) to vertical tail-down (0 deg)
        const flipU = (time_s - 14.0) / 6.0;
        const angle = (Math.PI / 2) * (1.0 - flipU);
        noseDir.copy(hDir).multiplyScalar(Math.sin(angle)).add(rUp.clone().multiplyScalar(Math.cos(angle))).normalize();
        bellyDir.copy(hDir).negate();
      } else {
        // Vertical propulsive touchdown: Tail-down, nose straight up
        noseDir.copy(rUp);
        bellyDir.copy(hDir).negate();
      }
    } else {
      // Flight 14 Mission Flight Profile
      if (time_s <= 12.0) {
        // 1. Launch & Pad: Standing vertically upright
        noseDir.copy(rUp);
        bellyDir.copy(hDir).negate();
      } else if (time_s <= 162.0) {
        // 2. Ascent Gravity Turn: Pitching smoothly downrange towards horizontal
        const pitchAngleRad = THREE.MathUtils.degToRad(Math.max(4.0, 90.0 - (time_s - 12.0) * 0.58));
        noseDir.copy(rUp).multiplyScalar(Math.sin(pitchAngleRad)).add(hDir.clone().multiplyScalar(Math.cos(pitchAngleRad))).normalize();
        bellyDir.copy(rUp).negate();
      } else if (time_s <= 8100.0) {
        // 3. Orbital Powered Flight & Coast (including Starlink deployment):
        // PROGRADE! Nose pointing forward along velocity vector!
        noseDir.copy(vDir);
        bellyDir.copy(rUp).negate(); // Black TPS belly facing Earth
      } else if (time_s <= 8190.0) {
        // 4. Deorbit Burn: Retrograde flip 180 deg!
        noseDir.copy(vDir).negate();
        bellyDir.copy(rUp).negate();
      } else if (time_s <= 11200.0) {
        // 5. Hypersonic Entry: High AoA (70 deg) belly-first into oncoming relative wind
        // Nose pitched 70 deg up from -vDir
        const entryAoA = THREE.MathUtils.degToRad(70.0);
        noseDir.copy(vDir).negate().multiplyScalar(Math.cos(entryAoA)).add(rUp.clone().multiplyScalar(Math.sin(entryAoA))).normalize();
        bellyDir.copy(vDir).negate(); // Belly directly faces into airstream
      } else if (time_s <= 11240.0) {
        // 6. Subsonic Belly Flop: AoA 90 deg horizontal skydive
        noseDir.copy(hDir);
        bellyDir.copy(rUp).negate();
      } else {
        // 7. Landing Flip & Splashdown: Vertical tail-down
        noseDir.copy(rUp);
        bellyDir.copy(hDir).negate();
      }
    }

    // Build orthonormal 3x3 basis [xBody, yBody, zBody]
    const yBody = noseDir.clone().normalize();
    let xBody = new THREE.Vector3().crossVectors(yBody, bellyDir).normalize();
    if (xBody.lengthSq() < 1e-4) {
      xBody = new THREE.Vector3().crossVectors(yBody, rUp).normalize();
    }
    const zBody = new THREE.Vector3().crossVectors(xBody, yBody).normalize();

    const rotMatrix = new THREE.Matrix4().makeBasis(xBody, yBody, zBody);
    this.vehicleMasterGroup.quaternion.setFromRotationMatrix(rotMatrix);

    // 3. Staging Separation Logic
    // During ascent (t <= 140s), Booster is attached to Starship stack.
    // At staging (t > 140s), Booster detaches and independentBoosterGroup follows return branch to Gulf!
    if (profile && profile.is_synthetic) {
      this.boosterGroup.visible = false;
      if (this.independentBoosterGroup) this.independentBoosterGroup.visible = false;
      this.starshipUpperGroup.position.set(0, 0, 0);
    } else if (time_s <= 140.0) {
      this.boosterGroup.visible = true;
      this.boosterGroup.position.set(0, -0.03 * 0.85, 0);
      this.starshipUpperGroup.position.set(0, 0, 0);
      if (this.independentBoosterGroup) this.independentBoosterGroup.visible = false;
    } else {
      this.boosterGroup.visible = false;
      if (this.independentBoosterGroup && profile && profile.booster_trajectory && time_s <= 425.0) {
        const bTraj = profile.booster_trajectory;
        let bPt = bTraj[0];
        for (let i = 0; i < bTraj.length - 1; i++) {
          if (time_s >= bTraj[i].time_s && time_s <= bTraj[i + 1].time_s) {
            const u = (time_s - bTraj[i].time_s) / (bTraj[i + 1].time_s - bTraj[i].time_s);
            const p1 = bTraj[i].scene_pos;
            const p2 = bTraj[i + 1].scene_pos;
            bPt = {
              scene_pos: [
                p1[0] + u * (p2[0] - p1[0]),
                p1[1] + u * (p2[1] - p1[1]),
                p1[2] + u * (p2[2] - p1[2])
              ],
              thrust_mn: bTraj[i].thrust_mn
            };
            break;
          }
        }
        if (bPt && bPt.scene_pos) {
          this.independentBoosterGroup.visible = true;
          this.independentBoosterGroup.position.set(bPt.scene_pos[0], bPt.scene_pos[1], bPt.scene_pos[2]);
          const bPos = new THREE.Vector3(bPt.scene_pos[0], bPt.scene_pos[1], bPt.scene_pos[2]);
          const bUp = bPos.clone().normalize();
          this.independentBoosterGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), bUp);
          if (this.independentBoosterPlume) {
            this.independentBoosterPlume.material.opacity = (bPt.thrust_mn > 5.0) ? 0.9 : 0.0;
          }
        }
      } else if (this.independentBoosterGroup) {
        this.independentBoosterGroup.visible = false;
      }
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

    // 7. Update Starlink V3 Satellite Deployment Simulation
    this.updateSatellites(time_s);

    // 8. Update Camera Framing
    this.updateCamera();
  }

  // =========================================================================
  // Orbital Frame Camera Tracking & Photographic Views
  // =========================================================================
  setCameraMode(mode) {
    this.currentCameraMode = mode;
    this.snapCameraNextFrame = true;
    if (this.controls) {
      this.controls.enabled = (mode === "FREE_ORBIT");
    }
    const radio = document.querySelector(`input[name='camMode'][value='${mode}']`);
    if (radio) radio.checked = true;
    const titleBox = document.querySelector(".cam-box-title");
    if (titleBox) titleBox.innerText = `CAMERA: ${mode.replace(/_/g, " ")}`;
    this.updateCamera();
  }

  trackSatellite(index) {
    this.selectedSatelliteIndex = Math.max(0, Math.min(25, index));
    this.setCameraMode("SATELLITE_TRACK");
  }

  highlightVehicleSubsystem(subsystem) {
    const sub = (subsystem || "").toUpperCase();
    if (sub === "STARSHIP") {
      this.setCameraMode("ORBIT_FOLLOW");
      if (this.starshipUpperGroup) this.starshipUpperGroup.visible = true;
    } else if (sub === "SUPER HEAVY" || sub === "BOOSTER") {
      this.setCameraMode("STAGE_SEP");
    } else if (sub === "MOUTH" || sub === "PAYLOAD" || sub === "MOUTH / PAYLOAD") {
      this.setCameraMode("CARGO_DEPLOY_CAM");
    } else if (sub === "FLAPS") {
      this.setCameraMode("ENTRY_BELLY");
    } else if (sub === "ENGINES") {
      this.setCameraMode("STAGE_SEP");
    } else if (sub === "THERMAL") {
      this.setCameraMode("ENTRY_BELLY");
    } else if (sub === "STRUCTURAL") {
      this.setCameraMode("ORBIT_FOLLOW");
    }
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

    const applyCam = (targetPos, targetLook) => {
      this.camera.position.copy(targetPos);
      this.camera.lookAt(targetLook);
      if (this.controls) this.controls.target.copy(targetLook);
    };

    if (this.currentCameraMode === "ORBIT_FOLLOW" || this.currentCameraMode === "MISSION_VIEW") {
      // 3/4 Front-Side View matching SpaceX target UI (media_1793008843083_e04a5a48.jpg)
      // Placed ahead along vHat (+0.55), above along rHat (+0.42), and lateral along hHat (+0.65)
      const camOffset = rHat.clone().multiplyScalar(0.42)
        .add(vHat.clone().multiplyScalar(0.55))
        .add(hHat.clone().multiplyScalar(0.65));

      const targetCamPos = vPos.clone().add(camOffset);
      const lookTarget = vPos.clone().sub(vHat.clone().multiplyScalar(0.1));
      applyCam(targetCamPos, lookTarget);
    } else if (this.currentCameraMode === "CARGO_DEPLOY_CAM" || this.currentCameraMode === "PAYLOAD_BAY") {
      // Rocket Mouth Dispenser Perspective (matching media_1792951553611_3819560f.png & media_1792951549197_1830f39c.png)
      // Placed alongside forward leeward hull looking at the nose slot and emerging Starlink train
      const lookTargetLocal = new THREE.Vector3(0, 0.85, 0.15);
      const lookTargetWorld = lookTargetLocal.clone().applyQuaternion(this.vehicleMasterGroup.quaternion).add(vPos);

      const camLocalOffset = new THREE.Vector3(-0.42, 0.65, 0.55);
      const targetCamPos = camLocalOffset.applyQuaternion(this.vehicleMasterGroup.quaternion).add(vPos);
      applyCam(targetCamPos, lookTargetWorld);
    } else if (this.currentCameraMode === "DEPLOY_WIDE_CAM") {
      // Wide Orbit View of Starship & Deployed Starlink Train (matching media_1792951549197_1830f39c.png)
      const lookTargetLocal = new THREE.Vector3(0, 0.85, 0.10);
      const lookTargetWorld = lookTargetLocal.clone().applyQuaternion(this.vehicleMasterGroup.quaternion).add(vPos);

      const camLocalOffset = new THREE.Vector3(-0.85, 1.10, 1.20);
      const targetCamPos = camLocalOffset.applyQuaternion(this.vehicleMasterGroup.quaternion).add(vPos);
      applyCam(targetCamPos, lookTargetWorld);
    } else if (this.currentCameraMode === "PROFILE_VIEW") {
      // Side-elevation flight profile arc (matching media_1792951144098_5fa826c7.png)
      const profileCamPos = hHat.clone().multiplyScalar(15.5);
      applyCam(profileCamPos, new THREE.Vector3(0, 0, 0));
    } else if (this.currentCameraMode === "SATELLITE_TRACK") {
      // Up-close tracking camera focused on selected Starlink satellite
      const sat = this.starlinkSatellites[this.selectedSatelliteIndex] || this.starlinkSatellites[0];
      if (sat && sat.mesh) {
        const satWorldPos = new THREE.Vector3();
        sat.mesh.getWorldPosition(satWorldPos);
        const satCamPos = satWorldPos.clone().add(rHat.clone().multiplyScalar(0.06)).add(hHat.clone().multiplyScalar(0.05));
        applyCam(satCamPos, satWorldPos);
      }
    } else if (this.currentCameraMode === "EARTH_GLOBAL") {
      // Pull back to planetary perspective showing the full orbit ribbon
      const globalPos = new THREE.Vector3(0, 13.5, 19.5);
      applyCam(globalPos, new THREE.Vector3(0, 0, 0));
    } else if (this.currentCameraMode === "STAGE_SEP") {
      // Hot-stage separation: Starship firing engines & Booster falling back
      const camOffset = rHat.clone().multiplyScalar(0.48)
        .sub(vHat.clone().multiplyScalar(0.85))
        .add(hHat.clone().multiplyScalar(0.70));

      applyCam(vPos.clone().add(camOffset), vPos.clone().add(vHat.clone().multiplyScalar(0.20)));
    } else if (this.currentCameraMode === "ENTRY_BELLY") {
      // Direct view of the windward black TPS tile belly
      const camOffset = rHat.clone().multiplyScalar(-0.45)
        .sub(vHat.clone().multiplyScalar(0.25))
        .add(hHat.clone().multiplyScalar(0.35));

      applyCam(vPos.clone().add(camOffset), vPos);
    } else if (this.currentCameraMode === "LANDING_PAD") {
      // Ground pad observer view (for synthetic landing)
      const padPos = new THREE.Vector3(0.25, 0.08, 0.35);
      applyCam(padPos, vPos);
    }
    this.snapCameraNextFrame = false;
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

    if (this.controls && this.currentCameraMode === "FREE_ORBIT") {
      this.controls.update();
    } else {
      this.updateCamera();
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
