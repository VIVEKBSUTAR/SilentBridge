import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Configuration constants
const LERP_FACTOR = 0.15; // Smooths out sensor noise
const JOINT_MAX_MCP = 1.25; // ~70 degrees max bend
const JOINT_MAX_PIP = 1.5;  // ~85 degrees max bend
const JOINT_MAX_DIP = 0.9;  // ~50 degrees max bend

let scene, camera, renderer, controls;
let wristGroup; // Root pivot of the entire hand
let handRestGroup; // Default rest orientation (palm down, pointing away)
let gridHelper;

// 3D Acceleration Viewport Scene Variables
let sceneAccel, cameraAccel, rendererAccel, controlsAccel, arrowHelperAccel;
let arrowX, arrowY, arrowZ;
let gravX = 0, gravY = 0, gravZ = 0;
let smoothLinX = 0, smoothLinY = 0, smoothLinZ = 0;
let isGravInitialized = false;

// Finger references for joint rotation
const fingers = {
  thumb:  { joints: [] },
  index:  { joints: [] },
  middle: { joints: [] },
  ring:   { joints: [] },
  pinky:  { joints: [] }
};

// Target variables for smooth interpolation (lerping)
let targetRoll = 0;
let targetPitch = 0;
let currentRoll = 0;
let currentPitch = 0;

let currentStyle = 'glass'; // 'glass' or 'cyber'
const handMaterials = {
  glass: {
    skin: null,
    joint: null,
    bone: null
  },
  cyber: {
    skin: null,
    joint: null,
    bone: null
  }
};

/**
 * Initializes the 3D Scene inside the specified DOM container.
 * @param {string} containerId - The ID of the container element
 */
export function initHand(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // 1. Scene Setup
  scene = new THREE.Scene();
  scene.background = null; // Transparent background to match CSS container

  // 2. Camera Setup
  camera = new THREE.PerspectiveCamera(
    45, 
    container.clientWidth / container.clientHeight, 
    0.1, 
    100
  );
  camera.position.set(0, 4, 10); // Look down at the hand

  // 3. Renderer Setup
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  container.appendChild(renderer.domElement);

  // 4. Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 3;
  controls.maxDistance = 20;
  controls.maxPolarAngle = Math.PI / 2 + 0.1; // Don't go below grid ground

  // 5. Lighting Setup (Rich lighting for physical glass material)
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambientLight);

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
  mainLight.position.set(5, 10, 7);
  mainLight.castShadow = true;
  mainLight.shadow.mapSize.width = 2048;
  mainLight.shadow.mapSize.height = 2048;
  mainLight.shadow.bias = -0.001;
  scene.add(mainLight);

  const blueLight = new THREE.PointLight(0x06b6d4, 2.5, 15);
  blueLight.position.set(-4, 3, -2);
  scene.add(blueLight);

  const purpleLight = new THREE.PointLight(0xa855f7, 2.5, 15);
  purpleLight.position.set(4, -2, 3);
  scene.add(purpleLight);

  // 6. Grid Helper (Floor)
  gridHelper = new THREE.GridHelper(20, 20, 0xa855f7, 0x1e293b);
  gridHelper.position.y = -2.5;
  scene.add(gridHelper);

  // 7. Materials Setup
  initMaterials();

  // 8. Build Hand Model
  buildHand();

  // 9. Window Resize Handler
  window.addEventListener('resize', onWindowResize);

  // 10. Start Animation Loop
  animate();
}

/**
 * Initializes the 3D Acceleration scene inside the specified DOM container.
 * @param {string} containerId - The ID of the container element
 */
export function initAccel(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // 1. Scene Setup
  sceneAccel = new THREE.Scene();
  sceneAccel.background = null; // Transparent background to match CSS container

  // 2. Camera Setup
  cameraAccel = new THREE.PerspectiveCamera(
    45, 
    container.clientWidth / container.clientHeight, 
    0.1, 
    100
  );
  cameraAccel.position.set(0, 2.5, 4);

  // 3. Renderer Setup
  rendererAccel = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  rendererAccel.setSize(container.clientWidth, container.clientHeight);
  rendererAccel.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(rendererAccel.domElement);

  // 4. Controls
  controlsAccel = new OrbitControls(cameraAccel, rendererAccel.domElement);
  controlsAccel.enableDamping = true;
  controlsAccel.dampingFactor = 0.05;
  controlsAccel.minDistance = 1.5;
  controlsAccel.maxDistance = 10;

  // 5. Lighting Setup
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  sceneAccel.add(ambientLight);

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.0);
  mainLight.position.set(5, 5, 5);
  sceneAccel.add(mainLight);

  // 6. Grid Helper (Floor)
  const gridHelperAccel = new THREE.GridHelper(6, 6, 0xa855f7, 0x1e293b);
  gridHelperAccel.position.y = -1.5;
  sceneAccel.add(gridHelperAccel);

  // 7. Wireframe sphere boundary
  const sphereGeo = new THREE.SphereGeometry(1.5, 32, 32);
  const sphereMat = new THREE.MeshBasicMaterial({
    color: 0x06b6d4,
    wireframe: true,
    transparent: true,
    opacity: 0.15
  });
  const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
  sceneAccel.add(sphereMesh);

  // 8. Dynamic Axis-Specific Arrow Helpers (acting as dynamic axes)
  // arrowX: Red/Coral (X-axis)
  arrowX = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 0.15, 0xef4444, 0.04, 0.016);
  sceneAccel.add(arrowX);

  // arrowY: Green/Lime (Y-axis)
  arrowY = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 0), 0.15, 0x10b981, 0.04, 0.016);
  sceneAccel.add(arrowY);

  // arrowZ: Blue/Cyan (Z-axis)
  arrowZ = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0, 0), 0.15, 0x3b82f6, 0.04, 0.016);
  sceneAccel.add(arrowZ);

  // 9. Arrow Helper for Combined Net Acceleration Direction (Neon Gold)
  const dir = new THREE.Vector3(0, -1, 0);
  const origin = new THREE.Vector3(0, 0, 0);
  arrowHelperAccel = new THREE.ArrowHelper(dir, origin, 0.15, 0xfacc15, 0.04, 0.016);
  sceneAccel.add(arrowHelperAccel);
}

/**
 * Instantiates the materials used for both glassmorphism and robotic look.
 */
function initMaterials() {
  // --- Glassmorphism Style ---
  handMaterials.glass.skin = new THREE.MeshPhysicalMaterial({
    color: 0x0d1e36,
    metalness: 0.1,
    roughness: 0.15,
    transmission: 0.7, // High transparency
    thickness: 1.2,
    transparent: true,
    opacity: 0.7,
    side: THREE.DoubleSide
  });

  handMaterials.glass.bone = new THREE.MeshPhysicalMaterial({
    color: 0x1e293b,
    metalness: 0.8,
    roughness: 0.3,
    transmission: 0.2,
    transparent: true,
    opacity: 0.9
  });

  // --- Robotic Cyberpunk Style ---
  handMaterials.cyber.skin = new THREE.MeshStandardMaterial({
    color: 0x111827, // Slate-900
    metalness: 0.85,
    roughness: 0.25,
    wireframe: false
  });

  handMaterials.cyber.bone = new THREE.MeshStandardMaterial({
    color: 0x374151, // Slate-700
    metalness: 0.9,
    roughness: 0.4
  });
}

/**
 * Procedurally creates the 3D hand model with a root wrist, palm, and five fingers.
 */
function buildHand() {
  // Root wrist group — all hand geometry lives here.
  // Euler order ZXY: roll (Z) is parent to pitch (X) to model wrist anatomy.
  wristGroup = new THREE.Group();
  wristGroup.rotation.order = 'ZXY';
  wristGroup.position.set(0, -0.5, 0);
  scene.add(wristGroup);

  // Setup rest group to rotate hand flat (fingers pointing along -Z, palm facing -Y)
  // Our procedurally generated geometry points along +Y, with palm facing +Z.
  handRestGroup = new THREE.Group();
  handRestGroup.rotation.order = 'XYZ';
  handRestGroup.rotation.x = -Math.PI / 2; // Point fingers along -Z, palm facing +Y
  handRestGroup.rotation.z = Math.PI;      // Rotate 180 deg around longitudinal axis, palm facing -Y
  wristGroup.add(handRestGroup);

  // Forearm/wrist base cylinder
  const wristBaseGeo = new THREE.CylinderGeometry(0.7, 0.8, 0.8, 16);
  const wristBaseMesh = new THREE.Mesh(wristBaseGeo, handMaterials[currentStyle].skin);
  wristBaseMesh.position.y = -0.8;
  wristBaseMesh.castShadow = true;
  wristBaseMesh.receiveShadow = true;
  handRestGroup.add(wristBaseMesh);

  // Palm / Metacarpal slab
  const palmShape = new THREE.BoxGeometry(2.3, 1.8, 0.4);
  const palmMesh = new THREE.Mesh(palmShape, handMaterials[currentStyle].skin);
  palmMesh.position.set(0, 0.5, 0);
  palmMesh.castShadow = true;
  palmMesh.receiveShadow = true;
  handRestGroup.add(palmMesh);

  // Glowing palm-centre orb
  const palmCoreGeo = new THREE.SphereGeometry(0.35, 16, 16);
  const palmCoreMat = new THREE.MeshBasicMaterial({
    color: 0xa855f7,
    transparent: true,
    opacity: 0.85
  });
  const palmCoreMesh = new THREE.Mesh(palmCoreGeo, palmCoreMat);
  palmCoreMesh.position.set(0, 0.4, 0.21); // slightly in front of palm face
  handRestGroup.add(palmCoreMesh);

  // Finger colour palette (matches CSS / sidebar colour codes)
  const fingerColors = {
    thumb:  0xec4899,
    index:  0x3b82f6,
    middle: 0x06b6d4,
    ring:   0xeab308,
    pinky:  0x8b5cf6
  };

  // Build five fingers (positions relative to palm centre)
  createFinger('thumb',  new THREE.Vector3(-1.15, 0.2,  0.25), 1.05, 0.14, fingerColors.thumb);
  createFinger('index',  new THREE.Vector3(-0.8,  1.4,  0.0),  1.45, 0.12, fingerColors.index);
  createFinger('middle', new THREE.Vector3(-0.25, 1.5,  0.0),  1.55, 0.12, fingerColors.middle);
  createFinger('ring',   new THREE.Vector3( 0.3,  1.4,  0.0),  1.45, 0.12, fingerColors.ring);
  createFinger('pinky',  new THREE.Vector3( 0.85, 1.2,  0.0),  1.15, 0.10, fingerColors.pinky);
}

/**
 * Creates a hierarchical finger structure parented to the wrist group.
 */
function createFinger(name, startPos, totalLength, radius, glowColor) {
  // Distinct phalanges lengths (approx 45% / 33% / 22% of total length)
  const lenProximal = totalLength * 0.45;
  const lenIntermediate = totalLength * 0.33;
  const lenDistal = totalLength * 0.22;

  // Material setup for glowing joint sphere
  const jointMaterial = new THREE.MeshBasicMaterial({
    color: glowColor,
    transparent: true,
    opacity: 0.95
  });

  const skinMat = handMaterials[currentStyle].skin;
  const boneMat = handMaterials[currentStyle].bone;

  // --- 1. MCP (Metacophalangeal Joint) ---
  const mcpGroup = new THREE.Group();
  mcpGroup.position.copy(startPos);
  
  // Custom orientation for thumb to oppose palm realistically
  if (name === 'thumb') {
    mcpGroup.rotation.set(0, -0.4, 0.5); // Angled outwards and forwards
  }

  handRestGroup.add(mcpGroup);

  // MCP Joint Sphere
  const mcpSphere = new THREE.Mesh(new THREE.SphereGeometry(radius * 1.3, 16, 16), jointMaterial);
  mcpGroup.add(mcpSphere);

  // Proximal Phalanx (Bone segment)
  const proximalGroup = new THREE.Group();
  mcpGroup.add(proximalGroup);
  
  const bone1 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.9, radius * 1.0, lenProximal - (radius * 1.5), 12), boneMat);
  bone1.position.y = lenProximal / 2;
  bone1.castShadow = true;
  bone1.receiveShadow = true;
  proximalGroup.add(bone1);
  
  const shell1 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 1.1, radius * 1.2, lenProximal, 12), skinMat);
  shell1.position.y = lenProximal / 2;
  shell1.castShadow = true;
  shell1.receiveShadow = true;
  proximalGroup.add(shell1);

  // --- 2. PIP (Proximal Interphalangeal Joint) ---
  const pipGroup = new THREE.Group();
  pipGroup.position.y = lenProximal;
  proximalGroup.add(pipGroup);

  // PIP Joint Sphere
  const pipSphere = new THREE.Mesh(new THREE.SphereGeometry(radius * 1.15, 12, 12), jointMaterial);
  pipGroup.add(pipSphere);

  // Intermediate Phalanx (Bone segment)
  const intermediateGroup = new THREE.Group();
  pipGroup.add(intermediateGroup);

  const bone2 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.75, radius * 0.85, lenIntermediate - (radius * 1.2), 12), boneMat);
  bone2.position.y = lenIntermediate / 2;
  bone2.castShadow = true;
  bone2.receiveShadow = true;
  intermediateGroup.add(bone2);

  const shell2 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.95, radius * 1.05, lenIntermediate, 12), skinMat);
  shell2.position.y = lenIntermediate / 2;
  shell2.castShadow = true;
  shell2.receiveShadow = true;
  intermediateGroup.add(shell2);

  // --- 3. DIP (Distal Interphalangeal Joint) ---
  const dipGroup = new THREE.Group();
  dipGroup.position.y = lenIntermediate;
  intermediateGroup.add(dipGroup);

  // DIP Joint Sphere
  const dipSphere = new THREE.Mesh(new THREE.SphereGeometry(radius * 1.0, 12, 12), jointMaterial);
  dipGroup.add(dipSphere);

  // Distal Phalanx (Bone segment)
  const distalGroup = new THREE.Group();
  dipGroup.add(distalGroup);

  const bone3 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.55, radius * 0.7, lenDistal - (radius * 1.0), 12), boneMat);
  bone3.position.y = lenDistal / 2;
  bone3.castShadow = true;
  bone3.receiveShadow = true;
  distalGroup.add(bone3);

  const shell3 = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.75, radius * 0.9, lenDistal, 12), skinMat);
  shell3.position.y = lenDistal / 2;
  shell3.castShadow = true;
  shell3.receiveShadow = true;
  distalGroup.add(shell3);

  // --- 4. Fingertip ---
  const tipSphere = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.85, 12, 12), jointMaterial);
  tipSphere.position.y = lenDistal;
  distalGroup.add(tipSphere);

  // Save references for rotational manipulation
  // joints[0] = MCP, joints[1] = PIP, joints[2] = DIP
  fingers[name].joints = [mcpGroup, pipGroup, dipGroup];
}

/**
 * Main animation rendering loop. Handles smooth interpolation.
 */
function animate() {
  requestAnimationFrame(animate);

  // 1. Smooth interpolation (lerp) to filter high-frequency sensor noise
  currentRoll  += (targetRoll  - currentRoll)  * LERP_FACTOR;
  currentPitch += (targetPitch - currentPitch) * LERP_FACTOR;

  if (wristGroup) {
    const DEG = Math.PI / 180.0;

    // --- Roll → Z axis (forearm long axis = pronation / supination) ---
    // The MPU6050 sits on the BACK of the hand.
    // At rest (palm down), roll ≈ 0°.
    // We map roll directly to the Z-axis (longitudinal axis of the flat hand).
    wristGroup.rotation.z = currentRoll * DEG;

    // --- Pitch → X axis (wrist flexion / extension) ---
    // pitch = 0° when hand is horizontal; negative when fingertips tilt downward.
    // A negative rotation around X tilts the fingers downward.
    wristGroup.rotation.x = currentPitch * DEG;
  }

  // 2. Render and controls update for Hand Viewport
  if (controls) controls.update();
  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }

  // 3. Render and controls update for Acceleration Viewport
  if (controlsAccel) controlsAccel.update();
  if (rendererAccel && sceneAccel && cameraAccel) {
    rendererAccel.render(sceneAccel, cameraAccel);
  }
}

/**
 * Handle resizing of the viewport canvas.
 */
function onWindowResize() {
  if (renderer && camera) {
    const container = renderer.domElement.parentElement;
    if (container) {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }
  }

  if (rendererAccel && cameraAccel) {
    const containerAccel = rendererAccel.domElement.parentElement;
    if (containerAccel) {
      cameraAccel.aspect = containerAccel.clientWidth / containerAccel.clientHeight;
      cameraAccel.updateProjectionMatrix();
      rendererAccel.setSize(containerAccel.clientWidth, containerAccel.clientHeight);
    }
  }
}

// ==========================================================================
// EXPOSED API METHODS FOR DASHBOARD COUPLING
// ==========================================================================

/**
 * Smoothly updates the hand model pitch and roll targets.
 * @param {number} roll - Roll angle in degrees
 * @param {number} pitch - Pitch angle in degrees
 */
export function updateHandOrientation(roll, pitch) {
  // Safety checks to prevent NaN breaking the scene
  if (isNaN(roll) || isNaN(pitch)) return;
  
  targetRoll = roll;
  targetPitch = pitch;
}

/**
 * Updates the 3D acceleration arrow helper direction and length.
 * @param {number} ax - Accel X raw
 * @param {number} ay - Accel Y raw
 * @param {number} az - Accel Z raw
 */
export function updateAcceleration(ax, ay, az) {
  if (!arrowHelperAccel || !arrowX || !arrowY || !arrowZ) return;
  if (isNaN(ax) || isNaN(ay) || isNaN(az)) return;

  // Initialize gravity baseline on first packet
  if (!isGravInitialized) {
    gravX = ax;
    gravY = ay;
    gravZ = az;
    isGravInitialized = true;
  }

  // Leaky integrator to estimate/track the gravity vector components (slow changes)
  const alpha = 0.96;
  gravX = alpha * gravX + (1 - alpha) * ax;
  gravY = alpha * gravY + (1 - alpha) * ay;
  gravZ = alpha * gravZ + (1 - alpha) * az;

  // Subtract gravity to isolate dynamic linear acceleration (hand movement)
  const linX = ax - gravX;
  const linY = ay - gravY;
  const linZ = az - gravZ;

  // Low-pass filter to smooth the resulting motion vector for visual persistence and decay
  const smoothFactor = 0.15;
  smoothLinX += (linX - smoothLinX) * smoothFactor;
  smoothLinY += (linY - smoothLinY) * smoothFactor;
  smoothLinZ += (linZ - smoothLinZ) * smoothFactor;

  // Map to 3D Viewport coordinate space (oriented to point in direction of hand motion):
  // - Lateral motion (Y sensor axis) -> X viewport axis (negated to match movement direction)
  // - Vertical motion (Z sensor axis) -> Y viewport axis (negated to match movement direction)
  // - Longitudinal motion (X sensor axis) -> Z viewport axis (straight mapping: negative is forward)
  const valX = -smoothLinY;
  const valY = -smoothLinZ;
  const valZ = smoothLinX;

  // 1. Update Axis-Specific Arrow Helpers (Red, Green, Blue)
  // We use a small threshold to filter out resting sensor noise
  const NOISE_THRESHOLD = 150;

  // Update X Axis Arrow (Red)
  if (Math.abs(valX) > NOISE_THRESHOLD) {
    const lenX = Math.min(1.5, (Math.abs(valX) / 4000.0) * 1.2 + 0.15);
    arrowX.setDirection(new THREE.Vector3(valX >= 0 ? 1 : -1, 0, 0));
    arrowX.setLength(lenX, 0.2 * lenX, 0.08 * lenX);
  } else {
    // Reset to small resting size acting as coordinate helper
    arrowX.setDirection(new THREE.Vector3(1, 0, 0));
    arrowX.setLength(0.15, 0.03, 0.012);
  }

  // Update Y Axis Arrow (Green)
  if (Math.abs(valY) > NOISE_THRESHOLD) {
    const lenY = Math.min(1.5, (Math.abs(valY) / 4000.0) * 1.2 + 0.15);
    arrowY.setDirection(new THREE.Vector3(0, valY >= 0 ? 1 : -1, 0));
    arrowY.setLength(lenY, 0.2 * lenY, 0.08 * lenY);
  } else {
    // Reset to small resting size acting as coordinate helper
    arrowY.setDirection(new THREE.Vector3(0, 1, 0));
    arrowY.setLength(0.15, 0.03, 0.012);
  }

  // Update Z Axis Arrow (Blue)
  if (Math.abs(valZ) > NOISE_THRESHOLD) {
    const lenZ = Math.min(1.5, (Math.abs(valZ) / 4000.0) * 1.2 + 0.15);
    arrowZ.setDirection(new THREE.Vector3(0, 0, valZ >= 0 ? 1 : -1));
    arrowZ.setLength(lenZ, 0.2 * lenZ, 0.08 * lenZ);
  } else {
    // Reset to small resting size acting as coordinate helper
    arrowZ.setDirection(new THREE.Vector3(0, 0, 1));
    arrowZ.setLength(0.15, 0.03, 0.012);
  }

  // 2. Update Combined Net Acceleration Vector Arrow (Gold)
  const netVector = new THREE.Vector3(valX, valY, valZ);
  const netMag = netVector.length();

  if (netMag > NOISE_THRESHOLD) {
    const dir = netVector.clone().normalize();
    arrowHelperAccel.setDirection(dir);
    const lenNet = Math.min(2.5, (netMag / 4000.0) * 1.5 + 0.15);
    arrowHelperAccel.setLength(lenNet, 0.2 * lenNet, 0.08 * lenNet);
    arrowHelperAccel.visible = true;
  } else {
    arrowHelperAccel.visible = false;
  }
}

/**
 * Resets the gravity tracking baseline. Call when connecting or starting simulation.
 */
export function resetGravityTracker() {
  isGravInitialized = false;
  gravX = 0;
  gravY = 0;
  gravZ = 0;
  smoothLinX = 0;
  smoothLinY = 0;
  smoothLinZ = 0;
}

/**
 * Updates individual finger joints based on normalized bending factors [0.0 - 1.0].
 * @param {number[]} bends - Array of 5 numbers representing [Thumb, Index, Middle, Ring, Pinky]
 */
export function updateFingerBends(bends) {
  if (!Array.isArray(bends) || bends.length < 5) return;

  const fingerKeys = ['thumb', 'index', 'middle', 'ring', 'pinky'];
  
  fingerKeys.forEach((key, i) => {
    const val = bends[i];
    if (isNaN(val)) return;

    const jointRefs = fingers[key].joints;
    if (jointRefs.length < 3) return;

    if (key === 'thumb') {
      // Thumb Opposition Movement:
      // Rotates forward on X (MCP/IP) and slightly inward on Y (opposition)
      jointRefs[0].rotation.x = -val * (JOINT_MAX_MCP * 0.6); // MCP
      jointRefs[0].rotation.z = val * 0.3; // Swing inward
      jointRefs[1].rotation.x = -val * JOINT_MAX_PIP; // IP joint
      jointRefs[2].rotation.x = -val * (JOINT_MAX_DIP * 0.2); // DIP (minor bend)
    } else {
      // Standard Finger Curl (MCP, PIP, DIP curl inwards on local X axis)
      jointRefs[0].rotation.x = -val * JOINT_MAX_MCP; // MCP bend
      jointRefs[1].rotation.x = -val * JOINT_MAX_PIP; // PIP bend
      jointRefs[2].rotation.x = -val * JOINT_MAX_DIP; // DIP bend
    }
  });
}

/**
 * Resets camera back to default angle.
 */
export function resetCamera() {
  if (camera && controls) {
    // Slightly above and in front — gives a natural 3/4 view of the hand
    camera.position.set(0, 5, 11);
    controls.target.set(0, 0.5, 0);
    controls.update();
  }
}

/**
 * Toggles visibility of the grid helper.
 * @returns {boolean} - New grid state (true = ON, false = OFF)
 */
export function toggleGrid() {
  if (gridHelper) {
    gridHelper.visible = !gridHelper.visible;
    return gridHelper.visible;
  }
  return false;
}

/**
 * Cycles or toggles hand material styles (glassmorphism vs robotic slate).
 * @returns {string} - The active style identifier ('glass' | 'cyber')
 */
export function toggleStyle() {
  currentStyle = currentStyle === 'glass' ? 'cyber' : 'glass';
  
  // Recursively update scene child mesh materials
  wristGroup.traverse((child) => {
    if (child.isMesh) {
      // If it's a bone or skin, update to the active style's material
      if (child.geometry.type === 'CylinderGeometry') {
        // Is it the bone cylinder (inner) or shell cylinder (outer)?
        if (child.material === handMaterials.glass.bone || child.material === handMaterials.cyber.bone) {
          child.material = handMaterials[currentStyle].bone;
        } else {
          child.material = handMaterials[currentStyle].skin;
        }
      } else if (child.geometry.type === 'BoxGeometry') {
        child.material = handMaterials[currentStyle].skin;
      }
    }
  });

  return currentStyle;
}
