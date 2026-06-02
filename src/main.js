import { 
  initHand, 
  updateHandOrientation, 
  updateFingerBends, 
  resetCamera, 
  toggleGrid, 
  toggleStyle 
} from './hand3d.js';
import { RealtimePlotter } from './plotter.js';

// --- CONFIGURATION & STATE ---
const CALIBRATION_KEY = 'sign_glove_calibration_v1';
let isConnected = false;
let isSimulating = false;
let port = null;
let reader = null;
let keepReading = false;

// Calibration structures (Default 12-bit ADC ranges)
let calibration = {
  min: [1500, 1500, 1500, 1500, 1500], // Straight fingers (Default)
  max: [3000, 3000, 3000, 3000, 3000]  // Bent fingers/Fist (Default)
};

// Current raw readings (updated by serial stream)
let currentRawFingers = [0, 0, 0, 0, 0];

// Telemetry/Metrics counters
let packetCount = 0;
let packetsLastSecond = 0;
let lastTelemetryTime = performance.now();
let frameCount = 0;
let lastFpsTime = performance.now();

// Plotter reference
let plotter = null;
let simulationInterval = null;

// --- DOM ELEMENTS ---
const connectBtn = document.getElementById('connect-btn');
const mockBtn = document.getElementById('mock-btn');
const baudrateSelect = document.getElementById('baudrate-select');
const statusBadge = document.getElementById('connection-status');
const statusText = statusBadge.querySelector('.status-text');

// Calibration buttons
const calOpenBtn = document.getElementById('cal-open-btn');
const calCloseBtn = document.getElementById('cal-close-btn');
const resetCalBtn = document.getElementById('reset-cal-btn');

// Finger displays
const rawValElements = [
  document.getElementById('raw-thumb'),
  document.getElementById('raw-index'),
  document.getElementById('raw-middle'),
  document.getElementById('raw-ring'),
  document.getElementById('raw-pinky')
];
const progressElements = [
  document.getElementById('progress-thumb'),
  document.getElementById('progress-index'),
  document.getElementById('progress-middle'),
  document.getElementById('progress-ring'),
  document.getElementById('progress-pinky')
];

// Orientation displays
const valRoll = document.getElementById('val-roll');
const valPitch = document.getElementById('val-pitch');
const valAccX = document.getElementById('val-acc-x');
const valAccY = document.getElementById('val-acc-y');
const valAccZ = document.getElementById('val-acc-z');
const valGyroX = document.getElementById('val-gyro-x');
const valGyroY = document.getElementById('val-gyro-y');
const valGyroZ = document.getElementById('val-gyro-z');

// Telemetry Stats
const statFps = document.getElementById('stat-fps');
const statHz = document.getElementById('stat-hz');
const statPackets = document.getElementById('stat-packets');

// Viewport Overlays
const resetCamBtn = document.getElementById('reset-cam-btn');
const toggleGridBtn = document.getElementById('toggle-grid-btn');
const toggleMatBtn = document.getElementById('toggle-material-btn');

// Serial Monitor Elements
const serialConsoleLog = document.getElementById('serial-console-log');
const clearMonitorBtn = document.getElementById('clear-monitor-btn');
let monitorLines = [];
let lastPacketCount = 0;
let connectionCheckInterval = null;

// ==========================================================================
// APPLICATION INITIALIZATION
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // 1. Load Calibration
  loadCalibration();

  // 2. Start 3D Hand Scene
  initHand('canvas-container');

  // 3. Initialize Oscilloscope Plotter
  const plotterCanvas = document.getElementById('plotter-canvas');
  if (plotterCanvas) {
    plotter = new RealtimePlotter(plotterCanvas, 250);
  }

  // 4. Setup Event Listeners
  setupEventListeners();

  // 5. Start FPS loop
  requestAnimationFrame(fpsLoop);
});

// ==========================================================================
// EVENT HANDLERS & BUTTON BINDINGS
// ==========================================================================

function setupEventListeners() {
  // Connect / Disconnect Action
  connectBtn.addEventListener('click', toggleConnection);
  
  // Mock Mode Action
  mockBtn.addEventListener('click', toggleMockMode);

  // Calibration Actions
  calOpenBtn.addEventListener('click', () => {
    calibration.min = [...currentRawFingers];
    saveCalibration();
    showFeedbackNotification('Straight calibration set!');
  });

  calCloseBtn.addEventListener('click', () => {
    calibration.max = [...currentRawFingers];
    saveCalibration();
    showFeedbackNotification('Fist calibration set!');
  });

  resetCalBtn.addEventListener('click', () => {
    calibration.min = [1500, 1500, 1500, 1500, 1500];
    calibration.max = [3000, 3000, 3000, 3000, 3000];
    saveCalibration();
    showFeedbackNotification('Calibration reset to default.');
  });

  // Viewport Floating Controls
  resetCamBtn.addEventListener('click', resetCamera);
  
  toggleGridBtn.addEventListener('click', () => {
    const isVisible = toggleGrid();
    toggleGridBtn.classList.toggle('active', isVisible);
    toggleGridBtn.querySelector('span').textContent = isVisible ? '🌐' : '🚫';
    toggleGridBtn.querySelector('.btn-label') || (toggleGridBtn.innerHTML = `<span>${isVisible ? '🌐' : '🚫'}</span> Grid ${isVisible ? 'ON' : 'OFF'}`);
  });

  toggleMatBtn.addEventListener('click', () => {
    const currentStyle = toggleStyle();
    toggleMatBtn.innerHTML = `<span>✨</span> Style: ${currentStyle === 'glass' ? 'Glass' : 'Metal'}`;
  });

  // Handle Resize of canvas plotter
  window.addEventListener('resize', () => {
    if (plotter) plotter.resize();
  });

  // Clear Serial Monitor log
  if (clearMonitorBtn) {
    clearMonitorBtn.addEventListener('click', () => {
      monitorLines = [];
      if (serialConsoleLog) {
        serialConsoleLog.textContent = 'Console cleared. Waiting for data...';
        serialConsoleLog.classList.remove('warning-active');
      }
    });
  }
}

// ==========================================================================
// CALIBRATION ENGINE
// ==========================================================================

function saveCalibration() {
  localStorage.setItem(CALIBRATION_KEY, JSON.stringify(calibration));
}

function loadCalibration() {
  const saved = localStorage.getItem(CALIBRATION_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed.min) && Array.isArray(parsed.max)) {
        calibration = parsed;
      }
    } catch (e) {
      console.warn('Failed to parse saved calibration, using defaults.');
    }
  }
}

/**
 * Converts a raw Hall sensor reading to a finger-bend factor [0.0 – 1.0].
 *
 * Coordinate system (user-defined, fixed):
 *  • Neutral centre  = 2000  → bend = 1.0 (finger fully curled)
 *  • Full deflection = ±500+ → bend = 0.0 (finger straight: raw ≤ 1500 OR raw ≥ 2500)
 *  • Linear ramp between 2000 and ±500 deflection from 2000
 *
 * Direction is symmetric: the magnet can be pushed either way.
 */
function normalizeFinger(raw) {
  const CENTER    = 2000;  // Neutral Hall sensor value (finger curled)
  const FULL_BEND = 500;   // Deflection at or above this → 0.0 (finger straight)

  const deviation = Math.abs(raw - CENTER);

  if (deviation >= FULL_BEND) return 0.0;    // Beyond full-bend threshold → straight

  // Linear scaling: 2000 is 1.0 (curled), moving towards ±500 deflection decreases bend to 0.0 (straight)
  return 1.0 - (deviation / FULL_BEND);
}

// ==========================================================================
// TELEMETRY RECEPTION & PARSING
// ==========================================================================

/**
 * Parses comma-separated values from the serial stream line-by-line.
 * Expected elements:
 * 0: thumbVal (int)
 * 1: indexVal (int)
 * 2: middleVal (int)
 * 3: ringVal (int)
 * 4: pinkyVal (int)
 * 5: roll (float)
 * 6: pitch (float)
 * 7: accX (int)
 * 8: accY (int)
 * 9: accZ (int)
 * 10: gyroX (int)
 * 11: gyroY (int)
 * 12: gyroZ (int)
 */
function logToSerialMonitor(line) {
  if (!serialConsoleLog) return;
  serialConsoleLog.classList.remove('warning-active');
  monitorLines.push(line);
  if (monitorLines.length > 6) {
    monitorLines.shift();
  }
  serialConsoleLog.textContent = monitorLines.join('\n');
}

function parseLine(line) {
  if (!line) return;
  logToSerialMonitor(line);

  let thumbRaw, indexRaw, middleRaw, ringRaw, pinkyRaw;
  let roll, pitch;
  let ax, ay, az;
  let gx, gy, gz;

  const trimmed = line.trim();

  // Check if it is a JSON packet
  if (trimmed.startsWith('{')) {
    try {
      const data = JSON.parse(trimmed);
      thumbRaw = parseInt(data.thumb);
      indexRaw = parseInt(data.index);
      middleRaw = parseInt(data.middle);
      ringRaw = parseInt(data.ring);
      // Support both "little" (from the JSON firmware) and "pinky"
      pinkyRaw = parseInt(data.pinky !== undefined ? data.pinky : data.little);

      roll = parseFloat(data.roll);
      pitch = parseFloat(data.pitch);

      // Support shorthand and full names
      ax = parseInt(data.ax !== undefined ? data.ax : data.accX);
      ay = parseInt(data.ay !== undefined ? data.ay : data.accY);
      az = parseInt(data.az !== undefined ? data.az : data.accZ);

      gx = parseInt(data.gx !== undefined ? data.gx : data.gyroX);
      gy = parseInt(data.gy !== undefined ? data.gy : data.gyroY);
      gz = parseInt(data.gz !== undefined ? data.gz : data.gyroZ);
    } catch (e) {
      console.warn("Failed to parse JSON serial packet:", e);
      return;
    }
  } else {
    // Fall back to CSV parsing
    const tokens = trimmed.split(',');
    if (tokens.length < 13) return; // Discard corrupted packages

    thumbRaw  = parseInt(tokens[0]);
    indexRaw  = parseInt(tokens[1]);
    middleRaw = parseInt(tokens[2]);
    ringRaw   = parseInt(tokens[3]);
    pinkyRaw  = parseInt(tokens[4]);

    roll  = parseFloat(tokens[5]);
    pitch = parseFloat(tokens[6]);

    ax = parseInt(tokens[7]);
    ay = parseInt(tokens[8]);
    az = parseInt(tokens[9]);

    gx = parseInt(tokens[10]);
    gy = parseInt(tokens[11]);
    gz = parseInt(tokens[12]);
  }

  // Validate numeric conversion
  if ([thumbRaw, indexRaw, middleRaw, ringRaw, pinkyRaw, roll, pitch, ax, ay, az, gx, gy, gz].some(isNaN)) {
    return;
  }

  // 2. Cache raw values for calibration logic
  currentRawFingers = [thumbRaw, indexRaw, middleRaw, ringRaw, pinkyRaw];

  // 3. Normalize finger bends using fixed-centre Hall model
  //    (symmetric deviation from 2000; dead zone ±100; full bend at ±500)
  const thumbBend  = normalizeFinger(thumbRaw);
  const indexBend  = normalizeFinger(indexRaw);
  const middleBend = normalizeFinger(middleRaw);
  const ringBend   = normalizeFinger(ringRaw);
  const pinkyBend  = normalizeFinger(pinkyRaw);

  // 4. Show raw & bend values in sidebar
  currentRawFingers = [thumbRaw, indexRaw, middleRaw, ringRaw, pinkyRaw];
  const bends = [thumbBend, indexBend, middleBend, ringBend, pinkyBend];

  // 4. Update 3D Model
  updateHandOrientation(roll, pitch);
  updateFingerBends(bends);

  // 5. Update Oscilloscope Plotter
  if (plotter) {
    plotter.addData({
      thumb: thumbBend,
      index: indexBend,
      middle: middleBend,
      ring: ringBend,
      pinky: pinkyBend,
      roll: roll,
      pitch: pitch
    });
  }

  // 6. Update UI Dashboard Numeric Diagnostics
  updateUIDashboard(currentRawFingers, bends, roll, pitch, ax, ay, az, gx, gy, gz);

  // 7. Update metrics
  packetCount++;
  packetsLastSecond++;
  updateDataRateHz();
}

/**
 * Updates DOM controls with current telemetry values.
 */
function updateUIDashboard(rawFingers, bends, roll, pitch, ax, ay, az, gx, gy, gz) {
  // Update raw values text
  for (let i = 0; i < 5; i++) {
    rawValElements[i].textContent = rawFingers[i];
    progressElements[i].style.width = `${bends[i] * 100}%`;
  }

  // IMU Values
  valRoll.textContent = `${roll.toFixed(1)}°`;
  valPitch.textContent = `${pitch.toFixed(1)}°`;
  
  valAccX.textContent = ax;
  valAccY.textContent = ay;
  valAccZ.textContent = az;
  
  valGyroX.textContent = gx;
  valGyroY.textContent = gy;
  valGyroZ.textContent = gz;

  statPackets.textContent = packetCount;
}

// ==========================================================================
// WEB SERIAL API BRIDGE
// ==========================================================================

async function toggleConnection() {
  if (isConnected) {
    await disconnectSerial();
  } else {
    await connectSerial();
  }
}

async function connectSerial() {
  if (!('serial' in navigator)) {
    alert('Web Serial is not supported in this browser. Please run this dashboard on a Chromium-based browser (Chrome, Edge, or Opera) to connect directly to the glove.');
    return;
  }

  // Disable simulation if running
  if (isSimulating) stopSimulation();

  try {
    // 1. Request port selection from user
    port = await navigator.serial.requestPort();
    const baudRate = parseInt(baudrateSelect.value) || 115200;

    // 2. Open serial connection
    await port.open({ baudRate });
    
    // Assert DTR/RTS signals. This releases ESP32 dev boards from reset.
    try {
      await port.setSignals({ dataTerminalReady: true, requestToSend: true });
    } catch (sigErr) {
      console.warn("Could not assert serial control signals (DTR/RTS):", sigErr);
    }
    
    isConnected = true;
    keepReading = true;

    // 3. Update connection UI status
    setUIConnected(true);
    
    if (serialConsoleLog) {
      serialConsoleLog.textContent = "Port opened. Waiting for data stream...";
      serialConsoleLog.classList.remove('warning-active');
    }

    // 4. Start connection packet checker (diagnose zero-data rate)
    if (connectionCheckInterval) clearInterval(connectionCheckInterval);
    lastPacketCount = 0;
    let checksWithNoData = 0;
    
    connectionCheckInterval = setInterval(() => {
      if (isConnected && !isSimulating) {
        if (packetCount === lastPacketCount) {
          checksWithNoData++;
          if (checksWithNoData >= 3) { // 3 seconds of no data
            if (serialConsoleLog) {
              serialConsoleLog.textContent = `⚠️ Connected but receiving no data.\n\nTroubleshooting:\n1. If Bluetooth, ensure you selected the OUTGOING COM port, not the Incoming port.\n2. Verify the ESP32 is powered ON.\n3. Make sure the baud rate is set to 115200.`;
              serialConsoleLog.classList.add('warning-active');
            }
          }
        } else {
          checksWithNoData = 0;
          lastPacketCount = packetCount;
        }
      }
    }, 1000);

    // 5. Start asynchronous stream loop
    readSerialLoop();
  } catch (err) {
    console.error('Serial connection failed:', err);
    alert(`Could not connect to port: ${err.message}`);
    setUIConnected(false);
  }
}

async function disconnectSerial() {
  keepReading = false;
  
  if (connectionCheckInterval) {
    clearInterval(connectionCheckInterval);
    connectionCheckInterval = null;
  }
  
  if (reader) {
    try {
      await reader.cancel();
    } catch (e) {
      // Stream cancel errors can be ignored
    }
  }

  if (port) {
    try {
      await port.close();
    } catch (e) {
      console.error('Error closing port:', e);
    }
  }

  port = null;
  reader = null;
  isConnected = false;
  
  setUIConnected(false);
  showFeedbackNotification('Glove disconnected.');
}

/**
 * High-performance serial chunk-reader loop.
 * Resolves binary chunks, decodes, buffers, and dispatches full lines.
 */
async function readSerialLoop() {
  const decoder = new TextDecoder();
  let textBuffer = '';

  while (port && port.readable && keepReading) {
    try {
      reader = port.readable.getReader();
      
      while (keepReading) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        
        // Decode chunk bytes and buffer
        const chunkText = decoder.decode(value);
        textBuffer += chunkText;
        
        // Parse complete lines split by newlines
        let lines = textBuffer.split('\n');
        // Save back any trailing partial line fragment
        textBuffer = lines.pop();

        for (const line of lines) {
          parseLine(line.trim());
        }
      }
    } catch (err) {
      console.error('Error during serial read loop:', err);
      // Auto-disconnect on critical link failure (e.g. cable pulled)
      if (isConnected) {
        disconnectSerial();
      }
      break;
    } finally {
      if (reader) {
        reader.releaseLock();
      }
    }
  }
}

// ==========================================================================
// TELEMETRY SIMULATOR (MOCK MODE)
// ==========================================================================

function toggleMockMode() {
  if (isSimulating) {
    stopSimulation();
  } else {
    startSimulation();
  }
}

function startSimulation() {
  if (isConnected) disconnectSerial();

  isSimulating = true;
  setUISimulating(true);

  let angle = 0;
  
  // ESP32 sends data every 50ms (20Hz)
  simulationInterval = setInterval(() => {
    angle += 0.05;

    // Simulate smooth sine-wave pitch and roll
    const roll  = Math.sin(angle) * 45.0;          // ±45°
    const pitch = Math.cos(angle * 0.7) * 30.0;    // ±30°

    // Simulate Hall sensor values oscillating around the 2000 neutral centre.
    // Amplitude of 700 takes values from 1300 – 2700, exercising:
    //   • neutral center (|dev| = 0)  → finger fully curled (1.0)
    //   • ramp zone (0–500 dev)       → partial straightness
    //   • full deflection (|dev|>=500) → finger fully straight (0.0: val ≤ 1500 or ≥ 2500)
    // Each finger is phase-shifted to produce a cascading wave effect.
    const thumbRaw  = Math.round(2000 + Math.sin(angle)         * 700);
    const indexRaw  = Math.round(2000 + Math.sin(angle - 0.5)   * 700);
    const middleRaw = Math.round(2000 + Math.sin(angle - 1.0)   * 700);
    const ringRaw   = Math.round(2000 + Math.sin(angle - 1.5)   * 700);
    const pinkyRaw  = Math.round(2000 + Math.sin(angle - 2.0)   * 700);

    // Simulated IMU readings
    const ax = Math.round(Math.sin(angle)       * 8000);
    const ay = Math.round(Math.cos(angle)       * 6000);
    const az = Math.round(Math.sin(angle * 1.5) * 16000);
    const gx = Math.round(Math.cos(angle)       * 200);
    const gy = Math.round(Math.sin(angle)       * 300);
    const gz = Math.round(Math.cos(angle * 1.2) * 150);

    // Assemble mock CSV packet
    const simulatedLine = `${thumbRaw},${indexRaw},${middleRaw},${ringRaw},${pinkyRaw},${roll.toFixed(2)},${pitch.toFixed(2)},${ax},${ay},${az},${gx},${gy},${gz}`;
    parseLine(simulatedLine);
  }, 50);

  showFeedbackNotification('Simulation started.');
}

function stopSimulation() {
  if (simulationInterval) {
    clearInterval(simulationInterval);
    simulationInterval = null;
  }
  isSimulating = false;
  setUISimulating(false);
  showFeedbackNotification('Simulation stopped.');
}

// ==========================================================================
// UI STATE STATE MACHINE & NOTIFICATIONS
// ==========================================================================

function setUIConnected(connected) {
  if (connected) {
    statusBadge.className = 'status-badge connected';
    statusText.textContent = 'Connected';
    connectBtn.className = 'btn btn-secondary';
    connectBtn.querySelector('.btn-label').textContent = 'Disconnect';
    connectBtn.querySelector('.btn-icon').textContent = '🔌';
    
    // Enable Calibration
    calOpenBtn.removeAttribute('disabled');
    calCloseBtn.removeAttribute('disabled');
  } else {
    statusBadge.className = 'status-badge disconnected';
    statusText.textContent = 'Disconnected';
    connectBtn.className = 'btn btn-primary';
    connectBtn.querySelector('.btn-label').textContent = 'Connect Glove';
    connectBtn.querySelector('.btn-icon').textContent = '⚡';
    
    // Disable Calibration
    calOpenBtn.setAttribute('disabled', 'true');
    calCloseBtn.setAttribute('disabled', 'true');
    statHz.textContent = '0.0 Hz';
  }
}

function setUISimulating(simulating) {
  if (simulating) {
    statusBadge.className = 'status-badge simulating';
    statusText.textContent = 'Simulating';
    mockBtn.className = 'btn btn-secondary active';
    mockBtn.querySelector('.btn-label').textContent = 'Stop Sim';
    mockBtn.querySelector('.btn-icon').textContent = '⏹️';
    
    // Enable Calibration during simulation for ease of UI testing
    calOpenBtn.removeAttribute('disabled');
    calCloseBtn.removeAttribute('disabled');
  } else {
    statusBadge.className = 'status-badge disconnected';
    statusText.textContent = 'Disconnected';
    mockBtn.className = 'btn btn-secondary';
    mockBtn.querySelector('.btn-label').textContent = 'Simulate Glove';
    mockBtn.querySelector('.btn-icon').textContent = '🎮';
    
    // Disable Calibration
    calOpenBtn.setAttribute('disabled', 'true');
    calCloseBtn.setAttribute('disabled', 'true');
    statHz.textContent = '0.0 Hz';
  }
}

/**
 * Calculates Hz data rate of incoming parsed serial signals.
 */
function updateDataRateHz() {
  const now = performance.now();
  const timeDiff = now - lastTelemetryTime;
  
  if (timeDiff >= 1000) {
    const hz = (packetsLastSecond / timeDiff) * 1000;
    statHz.textContent = `${hz.toFixed(1)} Hz`;
    packetsLastSecond = 0;
    lastTelemetryTime = now;
  }
}

/**
 * Calculates 3D Canvas FPS (frames per second).
 */
function fpsLoop() {
  frameCount++;
  const now = performance.now();
  const elapsed = now - lastFpsTime;

  if (elapsed >= 1000) {
    const fps = Math.round((frameCount / elapsed) * 1000);
    statFps.textContent = fps;
    frameCount = 0;
    lastFpsTime = now;
  }

  requestAnimationFrame(fpsLoop);
}

/**
 * Dynamic feedback notification banner.
 */
function showFeedbackNotification(message) {
  let feedbackDiv = document.getElementById('feedback-notification');
  if (!feedbackDiv) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.id = 'feedback-notification';
    feedbackDiv.style.position = 'fixed';
    feedbackDiv.style.bottom = '50px';
    feedbackDiv.style.right = '20px';
    feedbackDiv.style.background = 'rgba(168, 85, 247, 0.9)';
    feedbackDiv.style.color = '#fff';
    feedbackDiv.style.padding = '0.8rem 1.5rem';
    feedbackDiv.style.borderRadius = '8px';
    feedbackDiv.style.fontSize = '0.9rem';
    feedbackDiv.style.fontWeight = '600';
    feedbackDiv.style.zIndex = '9999';
    feedbackDiv.style.pointerEvents = 'none';
    feedbackDiv.style.boxShadow = '0 4px 12px rgba(168, 85, 247, 0.4)';
    feedbackDiv.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
    feedbackDiv.style.transform = 'translateY(20px)';
    feedbackDiv.style.opacity = '0';
    document.body.appendChild(feedbackDiv);
  }

  feedbackDiv.textContent = message;
  feedbackDiv.style.opacity = '1';
  feedbackDiv.style.transform = 'translateY(0px)';

  // Fade out after 2.5s
  setTimeout(() => {
    feedbackDiv.style.opacity = '0';
    feedbackDiv.style.transform = 'translateY(20px)';
  }, 2500);
}
