/**
 * Phase 10: Three.js WebGL Spatial Visualization Engine
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - PBR Earth with procedural procedural textures and atmospheric rim scattering
 *   - Procedural stainless steel Starship with heat shield belly tiles, movable flaps, and Raptor bells
 *   - Dynamic engine exhaust plume glow and plasma reentry glow
 *   - Continuous trajectory ribbon with event beacon pins
 *   - 7 cinematic and engineering camera modes
 */

class MissionSceneManager {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.width = this.canvas.clientWidth;
    this.height = this.canvas.clientHeight;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    this.earthGroup = null;
    this.starshipGroup = null;
    this.flaps = { fwdLeft: null, fwdRight: null, aftLeft: null, aftRight: null };
    this.enginePlume = null;
    this.reentryPlasmaGlow = null;
    this.trajectoryLine = null;
    this.beaconsGroup = null;

    this.currentCameraMode = "ORBIT_FOLLOW";
    this.targetPos = new THREE.Vector3(0, 7.0, 0);

    this.init();
  }

  init() {
    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x040811);
    this.scene.fog = new THREE.FogExp2(0x040811, 0.0005);

    this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 0.01, 2000);
    this.camera.position.set(0, 10, 20);

    // 2. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: "high-performance",
      alpha: true,
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;

    // 3. OrbitControls
    if (typeof THREE.OrbitControls !== "undefined") {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.minDistance = 0.05;
      this.controls.maxDistance = 250;
    }

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0x223355, 0.9);
    this.scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 2.0);
    sunLight.position.set(50, 30, 40).normalize();
    this.scene.add(sunLight);

    const rimLight = new THREE.DirectionalLight(0x00e5ff, 0.6);
    rimLight.position.set(-30, -20, -30).normalize();
    this.scene.add(rimLight);

    // 5. Environment & Celestial Objects
    this.createStarfield();
    this.createEarth();
    this.createStarship();
    this.createBeacons();

    // 6. Resize listener
    window.addEventListener("resize", () => this.onWindowResize());

    // 7. Render Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  createStarfield() {
    const starCount = 3500;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      const r = 400 + Math.random() * 400;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i] = r * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = r * Math.cos(phi);

      const tint = Math.random();
      colors[i] = 0.8 + 0.2 * tint;
      colors[i + 1] = 0.85 + 0.15 * tint;
      colors[i + 2] = 1.0;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
    });

    const starPoints = new THREE.Points(geometry, material);
    this.scene.add(starPoints);
  }

  createProceduralEarthTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");

    // Deep ocean base
    ctx.fillStyle = "#040c1a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Latitude & Longitude grid lines (15 deg intervals)
    ctx.strokeStyle = "rgba(0, 229, 255, 0.15)";
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

    // Stylized landmass blobs (North America, South America, Eurasia, Africa, Australia)
    ctx.fillStyle = "rgba(18, 42, 77, 0.85)";
    ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctx.lineWidth = 1.5;

    const continents = [
      // North America
      [[180, 80], [280, 90], [320, 160], [240, 220], [180, 180]],
      // South America
      [[260, 250], [330, 280], [310, 420], [250, 440], [240, 310]],
      // Europe & Asia
      [[480, 80], [700, 70], [880, 140], [780, 240], [540, 210], [470, 130]],
      // Africa
      [[480, 210], [580, 230], [570, 380], [510, 410], [450, 270]],
      // Australia
      [[780, 320], [860, 330], [850, 410], [770, 390]],
    ];

    continents.forEach(poly => {
      ctx.beginPath();
      ctx.moveTo(poly[0][0], poly[0][1]);
      for (let i = 1; i < poly.length; i++) {
        ctx.lineTo(poly[i][0], poly[i][1]);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }

  createEarth() {
    this.earthGroup = new THREE.Group();

    const earthRadius = 6.378137; // 1 unit = 1000 km
    const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);

    let earthTex = this.createProceduralEarthTexture();
    const loader = new THREE.TextureLoader();
    loader.load(
      "assets/textures/globeprev-clouds-on-DOpaHC5m-r2.jpg",
      (tex) => {
        if (this.earthMesh) {
          this.earthMesh.material.map = tex;
          this.earthMesh.material.needsUpdate = true;
        }
      },
      undefined,
      () => { /* silent fallback to procedural texture */ }
    );

    const earthMat = new THREE.MeshStandardMaterial({
      map: earthTex,
      roughness: 0.65,
      metalness: 0.2,
      emissive: new THREE.Color(0x020814),
      emissiveIntensity: 0.4,
    });

    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthGroup.add(this.earthMesh);

    // Atmospheric Rim Glow (Fresnel outer shell)
    const atmoGeo = new THREE.SphereGeometry(earthRadius * 1.025, 48, 48);
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vPosition;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vPosition;
        void main() {
          vec3 viewDir = normalize(-vPosition);
          float rim = 1.0 - max(dot(viewDir, vNormal), 0.0);
          rim = pow(rim, 3.2);
          vec3 atmoColor = vec3(0.0, 0.85, 1.0);
          gl_FragColor = vec4(atmoColor, rim * 0.75);
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    });

    const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    this.earthGroup.add(atmoMesh);

    this.scene.add(this.earthGroup);
  }

  createStarship() {
    this.starshipGroup = new THREE.Group();

    // Dimensional scaling: Starship height = 50m -> 0.05 scene units, diameter 9m -> 0.009 units
    // For crisp visibility across orbital distances, render vehicle with a baseline model scale:
    const vScale = 0.08;

    // 1. Stainless Steel Hull Material (PBR Metallic)
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0xd8e4ec,
      metalness: 0.92,
      roughness: 0.22,
    });

    // 2. Black Hexagonal TPS Tiles Material (Belly heat shield)
    const tileMat = new THREE.MeshStandardMaterial({
      color: 0x111317,
      metalness: 0.1,
      roughness: 0.85,
    });

    // Main Cylindrical Barrel
    const barrelGeo = new THREE.CylinderGeometry(0.045 * vScale * 10, 0.045 * vScale * 10, 0.3 * vScale * 10, 32);
    const barrelMesh = new THREE.Mesh(barrelGeo, steelMat);
    this.starshipGroup.add(barrelMesh);

    // Heat Shield Half-Cylinder Overlay on Windward (+Z local) side
    const shieldGeo = new THREE.CylinderGeometry(
      0.0455 * vScale * 10,
      0.0455 * vScale * 10,
      0.298 * vScale * 10,
      32,
      1,
      false,
      0,
      Math.PI
    );
    const shieldMesh = new THREE.Mesh(shieldGeo, tileMat);
    shieldMesh.rotation.y = Math.PI / 2;
    this.starshipGroup.add(shieldMesh);

    // Nosecone Ogive
    const noseGeo = new THREE.ConeGeometry(0.045 * vScale * 10, 0.18 * vScale * 10, 32);
    const noseMesh = new THREE.Mesh(noseGeo, steelMat);
    noseMesh.position.y = 0.24 * vScale * 10;
    this.starshipGroup.add(noseMesh);

    // Forward Flaps (Canards)
    const fwdFlapGeo = new THREE.BoxGeometry(0.06 * vScale * 10, 0.005 * vScale * 10, 0.04 * vScale * 10);
    this.flaps.fwdLeft = new THREE.Mesh(fwdFlapGeo, steelMat);
    this.flaps.fwdLeft.position.set(-0.06 * vScale * 10, 0.2 * vScale * 10, 0);
    this.starshipGroup.add(this.flaps.fwdLeft);

    this.flaps.fwdRight = new THREE.Mesh(fwdFlapGeo, steelMat);
    this.flaps.fwdRight.position.set(0.06 * vScale * 10, 0.2 * vScale * 10, 0);
    this.starshipGroup.add(this.flaps.fwdRight);

    // Aft Flaps
    const aftFlapGeo = new THREE.BoxGeometry(0.09 * vScale * 10, 0.006 * vScale * 10, 0.06 * vScale * 10);
    this.flaps.aftLeft = new THREE.Mesh(aftFlapGeo, steelMat);
    this.flaps.aftLeft.position.set(-0.08 * vScale * 10, -0.12 * vScale * 10, 0);
    this.starshipGroup.add(this.flaps.aftLeft);

    this.flaps.aftRight = new THREE.Mesh(aftFlapGeo, steelMat);
    this.flaps.aftRight.position.set(0.08 * vScale * 10, -0.12 * vScale * 10, 0);
    this.starshipGroup.add(this.flaps.aftRight);

    // Engine Exhaust Plume (Cone with additive glow)
    const plumeGeo = new THREE.ConeGeometry(0.035 * vScale * 10, 0.2 * vScale * 10, 16);
    const plumeMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.enginePlume = new THREE.Mesh(plumeGeo, plumeMat);
    this.enginePlume.position.y = -0.25 * vScale * 10;
    this.enginePlume.rotation.x = Math.PI;
    this.starshipGroup.add(this.enginePlume);

    // Reentry Plasma Glow Shell
    const plasmaGeo = new THREE.SphereGeometry(0.12 * vScale * 10, 24, 24);
    const plasmaMat = new THREE.MeshBasicMaterial({
      color: 0xff6d00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
    });
    this.reentryPlasmaGlow = new THREE.Mesh(plasmaGeo, plasmaMat);
    this.starshipGroup.add(this.reentryPlasmaGlow);

    this.scene.add(this.starshipGroup);
  }

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

    if (!trajectoryPoints || trajectoryPoints.length < 2) return;

    const positions = [];
    trajectoryPoints.forEach(pt => {
      if (pt.scene_pos) {
        positions.push(pt.scene_pos[0], pt.scene_pos[1], pt.scene_pos[2]);
      }
    });

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));

    const material = new THREE.LineBasicMaterial({
      color: 0x00e5ff,
      linewidth: 2,
      transparent: true,
      opacity: 0.85,
    });

    this.trajectoryLine = new THREE.Line(geometry, material);
    this.scene.add(this.trajectoryLine);
  }

  setCameraMode(mode) {
    this.currentCameraMode = mode;
  }

  updateVehicleState(point, profile) {
    if (!point || !point.scene_pos) return;

    // 1. Vehicle Position
    this.starshipGroup.position.set(point.scene_pos[0], point.scene_pos[1], point.scene_pos[2]);
    this.targetPos.copy(this.starshipGroup.position);

    // 2. Vehicle Attitude (Pitch orientation)
    const pitchRad = THREE.MathUtils.degToRad(point.pitch_deg || 0);
    this.starshipGroup.rotation.z = pitchRad;

    // 3. Flap Deflections
    const fwdRad = THREE.MathUtils.degToRad(point.flaps_fwd_deg || 0);
    const aftRad = THREE.MathUtils.degToRad(point.flaps_aft_deg || 0);

    if (this.flaps.fwdLeft) this.flaps.fwdLeft.rotation.x = fwdRad;
    if (this.flaps.fwdRight) this.flaps.fwdRight.rotation.x = -fwdRad;
    if (this.flaps.aftLeft) this.flaps.aftLeft.rotation.x = aftRad;
    if (this.flaps.aftRight) this.flaps.aftRight.rotation.x = -aftRad;

    // 4. Engine Plume (Thrust)
    const thrust = point.thrust_mn || 0;
    if (this.enginePlume) {
      if (thrust > 0.5) {
        this.enginePlume.material.opacity = Math.min(0.9, 0.3 + (thrust / 80.0) * 0.6);
        const scale = 1.0 + Math.random() * 0.2;
        this.enginePlume.scale.set(scale, scale * 1.5, scale);
      } else {
        this.enginePlume.material.opacity = 0.0;
      }
    }

    // 5. Reentry Plasma Shock Glow
    const heatFlux = point.heat_flux_mw_m2 || 0;
    if (this.reentryPlasmaGlow) {
      if (heatFlux > 0.05) {
        this.reentryPlasmaGlow.material.opacity = Math.min(0.85, heatFlux / 0.8);
        const hue = Math.max(0.04, 0.12 - (heatFlux / 1.0) * 0.08); // Orange to intense incandescent yellow
        this.reentryPlasmaGlow.material.color.setHSL(hue, 1.0, 0.5);
      } else {
        this.reentryPlasmaGlow.material.opacity = 0.0;
      }
    }

    // 6. Camera Position Updates
    this.updateCamera();
  }

  updateCamera() {
    const vPos = this.starshipGroup.position;

    if (this.currentCameraMode === "ORBIT_FOLLOW") {
      const offset = new THREE.Vector3(0.5, 0.3, 0.8);
      this.camera.position.lerp(vPos.clone().add(offset), 0.1);
      if (this.controls) this.controls.target.lerp(vPos, 0.1);
    } else if (this.currentCameraMode === "EARTH_GLOBAL") {
      this.camera.position.lerp(new THREE.Vector3(0, 12, 18), 0.05);
      if (this.controls) this.controls.target.lerp(new THREE.Vector3(0, 0, 0), 0.05);
    } else if (this.currentCameraMode === "STAGE_SEP") {
      const offset = new THREE.Vector3(0.2, -0.4, 0.3);
      this.camera.position.lerp(vPos.clone().add(offset), 0.1);
      if (this.controls) this.controls.target.lerp(vPos, 0.1);
    } else if (this.currentCameraMode === "PAYLOAD_BAY") {
      const offset = new THREE.Vector3(0.3, 0.2, -0.3);
      this.camera.position.lerp(vPos.clone().add(offset), 0.1);
      if (this.controls) this.controls.target.lerp(vPos, 0.1);
    } else if (this.currentCameraMode === "ENTRY_BELLY") {
      const offset = new THREE.Vector3(0, -0.4, 0.5);
      this.camera.position.lerp(vPos.clone().add(offset), 0.1);
      if (this.controls) this.controls.target.lerp(vPos, 0.1);
    } else if (this.currentCameraMode === "LANDING_PAD") {
      this.camera.position.lerp(new THREE.Vector3(0.2, 0.05, 0.3), 0.1);
      if (this.controls) this.controls.target.lerp(vPos, 0.1);
    }
    // FREE_ORBIT leaves controls untouched
  }

  onWindowResize() {
    this.width = this.canvas.clientWidth;
    this.height = this.canvas.clientHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  animate() {
    requestAnimationFrame(this.animate);

    // Subtle Earth rotation
    if (this.earthGroup) {
      this.earthGroup.rotation.y += 0.00015;
    }

    if (this.controls) {
      this.controls.update();
    }

    if (this.starshipGroup) {
      this.renderMiniGlobe(this.starshipGroup.position);
    }

    this.renderer.render(this.scene, this.camera);
  }

  renderMiniGlobe(vPos) {
    const canvas = document.getElementById("mini-globe-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Globe circle
    ctx.beginPath();
    ctx.arc(w / 2, h / 2, w / 2 - 2, 0, Math.PI * 2);
    ctx.fillStyle = "#051126";
    ctx.fill();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Lat/Lon grid
    ctx.strokeStyle = "rgba(0, 229, 255, 0.15)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(w / 2, h / 2, w / 2 - 4, (w / 2 - 4) * 0.4, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w / 2, 2);
    ctx.lineTo(w / 2, h - 2);
    ctx.stroke();

    // Vehicle position indicator
    const rNorm = Math.sqrt(vPos.x * vPos.x + vPos.y * vPos.y + vPos.z * vPos.z) || 6.378;
    const nx = vPos.x / rNorm;
    const ny = -vPos.z / rNorm;
    const vx = w / 2 + nx * (w / 2 - 8);
    const vy = h / 2 + ny * (h / 2 - 8);

    ctx.beginPath();
    ctx.arc(vx, vy, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = "#00e5ff";
    ctx.fill();
  }
}

window.MissionSceneManager = MissionSceneManager;
